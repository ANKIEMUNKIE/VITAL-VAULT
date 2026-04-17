# app/tasks/ai_extraction.py
"""AI extraction Celery task using Cerebras API.

Extracts structured medical entities from OCR text and stores
them in the record_extractions table. After extraction:
  - Auto-creates Medication rows for each extracted medication
  - Auto-creates Reminder rows for each medication
  - Auto-creates Appointment for follow_up_by date if present
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    queue="ai",
    time_limit=180,
    soft_time_limit=150,
    name="app.tasks.ai_extraction.run_ai_extraction",
)
def run_ai_extraction(self, record_id: str) -> dict:  # type: ignore[no-untyped-def]
    """Extract structured medical entities from OCR text using Cerebras API.

    Stages:
    1. Load record + OCR text from DB.
    2. Call Cerebras API with extraction prompt.
    3. Parse and validate response with Pydantic.
    4. INSERT record_extractions row.
    5. Auto-create Medications + Reminders from extracted meds.
    6. Auto-create Appointment from follow_up_by date.
    7. Update record status → PROCESSED.
    """
    try:
        logger.info("AI extraction started for record %s", record_id)

        from sqlalchemy import create_engine, select, update
        from sqlalchemy.orm import Session

        from app.config import settings

        # Check if API key is configured
        if not settings.CEREBRAS_API_KEY:
            logger.warning(
                "CEREBRAS_API_KEY not configured — skipping AI extraction for record %s. "
                "Setting status to MANUAL_REVIEW.",
                record_id,
            )
            _update_record_status(record_id, "MANUAL_REVIEW", "CEREBRAS_API_KEY not configured")
            return {"status": "skipped", "reason": "API key not configured"}

        from app.models.medical_record import MedicalRecord

        sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
        engine = create_engine(sync_url)

        # 1. Load record
        with Session(engine) as session:
            result = session.execute(
                select(MedicalRecord).where(MedicalRecord.id == uuid.UUID(record_id))
            )
            record = result.scalar_one_or_none()
            if not record:
                logger.error("Record %s not found", record_id)
                return {"status": "error", "message": "Record not found"}

            if not record.ocr_raw_text:
                logger.warning("No OCR text for record %s", record_id)
                _update_record_status(record_id, "MANUAL_REVIEW", "No OCR text available")
                return {"status": "skipped", "reason": "No OCR text"}

            # 2. Decrypt OCR text
            ocr_text = record.ocr_raw_text.decode("utf-8")
            patient_id = str(record.patient_id)
            record_uuid = record.id

        # 3. Call Cerebras API
        from app.services.ai_service import call_cerebras_extraction

        extraction_result = call_cerebras_extraction(ocr_text)

        if not extraction_result:
            _update_record_status(record_id, "MANUAL_REVIEW", "AI returned empty result")
            return {"status": "failed", "reason": "Empty extraction"}

        # 4. Store extraction in DB
        from app.models.medical_record import RecordExtraction

        with Session(engine) as session:
            extraction = RecordExtraction(
                record_id=uuid.UUID(record_id),
                diagnosed_conditions=(
                    json.dumps(extraction_result.get("diagnosed_conditions", [])).encode("utf-8")
                ),
                extracted_medications=(
                    json.dumps(extraction_result.get("extracted_medications", [])).encode("utf-8")
                ),
                extracted_dates=extraction_result.get("extracted_dates"),
                doctor_name=(
                    extraction_result.get("doctor_name", "").encode("utf-8")
                    if extraction_result.get("doctor_name")
                    else None
                ),
                hospital_name=(
                    extraction_result.get("hospital_name", "").encode("utf-8")
                    if extraction_result.get("hospital_name")
                    else None
                ),
                ai_summary=(
                    extraction_result.get("ai_summary", "").encode("utf-8")
                    if extraction_result.get("ai_summary")
                    else None
                ),
                confidence_score=extraction_result.get("confidence_score"),
                extraction_model=settings.CEREBRAS_MODEL,
                extraction_version="1.0.0",
            )
            session.add(extraction)

            # 5. Update record status to PROCESSED
            session.execute(
                update(MedicalRecord)
                .where(MedicalRecord.id == uuid.UUID(record_id))
                .values(processing_status="PROCESSED")
            )
            session.commit()

        # 6. Auto-create Medications + Reminders from extracted medications
        extracted_meds = extraction_result.get("extracted_medications", []) or []
        for med_data in extracted_meds:
            if not med_data.get("name"):
                continue
            try:
                _create_medication_and_reminder(
                    engine=engine,
                    patient_id=patient_id,
                    record_id=record_id,
                    med_data=med_data,
                    doctor_name=extraction_result.get("doctor_name"),
                )
            except Exception:
                logger.exception(
                    "Failed to create medication from extraction for record %s", record_id
                )

        # 7. Auto-create Appointment from follow_up_by date
        extracted_dates = extraction_result.get("extracted_dates") or {}
        follow_up = extracted_dates.get("follow_up_by") or extracted_dates.get("next_appointment")
        if follow_up:
            try:
                _create_followup_appointment(
                    engine=engine,
                    patient_id=patient_id,
                    record_id=record_id,
                    follow_up_date=follow_up,
                    doctor_name=extraction_result.get("doctor_name"),
                )
            except Exception:
                logger.exception(
                    "Failed to create follow-up appointment for record %s", record_id
                )

        # 8. Trigger notification
        try:
            from app.tasks.notifications import send_processing_complete_notification

            send_processing_complete_notification.delay(patient_id, record_id)
        except Exception:
            logger.warning("Failed to queue notification for record %s", record_id)

        logger.info("AI extraction completed for record %s", record_id)
        return {"status": "success", "confidence": extraction_result.get("confidence_score")}

    except SoftTimeLimitExceeded:
        logger.error("AI extraction soft time limit exceeded for record %s", record_id)
        _update_record_status(record_id, "MANUAL_REVIEW", "AI extraction timeout")
        raise

    except Exception as exc:
        logger.exception("AI extraction failed for record %s", record_id)
        _update_record_status(record_id, "FAILED", str(exc))
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 30)


def _create_medication_and_reminder(
    engine: object,
    patient_id: str,
    record_id: str,
    med_data: dict,
    doctor_name: str | None = None,
) -> None:
    """Upsert a Medication row and create a daily Reminder for it."""
    from sqlalchemy.orm import Session

    from app.models.medication import Medication
    from app.models.reminder import Reminder

    with Session(engine) as session:  # type: ignore[arg-type]
        med = Medication(
            patient_id=uuid.UUID(patient_id),
            source_record_id=uuid.UUID(record_id),
            name=med_data["name"].encode("utf-8"),
            generic_name=(
                med_data.get("generic_name", "").encode("utf-8")
                if med_data.get("generic_name")
                else None
            ),
            dosage=med_data.get("dosage"),
            frequency=med_data.get("frequency"),
            route=med_data.get("route"),
            prescribed_by=doctor_name,
            is_active=True,
        )
        session.add(med)
        session.flush()  # get med.id

        # Create a reminder for this medication
        # Schedule for 8 AM tomorrow, repeating daily
        now = datetime.now(timezone.utc)
        reminder_title = f"Take {med_data['name']}"
        if med_data.get("dosage"):
            reminder_title += f" {med_data['dosage']}"

        reminder = Reminder(
            patient_id=uuid.UUID(patient_id),
            medication_id=med.id,
            record_id=uuid.UUID(record_id),
            reminder_type="MEDICATION",
            title=reminder_title,
            body=f"Frequency: {med_data.get('frequency', 'as prescribed')}",
            scheduled_at=now.replace(hour=8, minute=0, second=0, microsecond=0),
            recurrence_rule="FREQ=DAILY",
            is_active=True,
            delivery_channels=["PUSH"],
        )
        session.add(reminder)
        session.commit()

        logger.info(
            "Created medication '%s' and reminder for patient %s from record %s",
            med_data["name"],
            patient_id,
            record_id,
        )


def _create_followup_appointment(
    engine: object,
    patient_id: str,
    record_id: str,
    follow_up_date: str,
    doctor_name: str | None = None,
) -> None:
    """Create an Appointment row for the extracted follow-up date."""
    from datetime import date

    from sqlalchemy.orm import Session

    from app.models.appointment import Appointment

    try:
        appt_date = date.fromisoformat(follow_up_date)
    except (ValueError, TypeError):
        logger.warning("Invalid follow-up date '%s' for record %s", follow_up_date, record_id)
        return

    with Session(engine) as session:  # type: ignore[arg-type]
        appt = Appointment(
            patient_id=uuid.UUID(patient_id),
            source_record_id=uuid.UUID(record_id),
            title=f"Follow-up{'  with ' + doctor_name if doctor_name else ''}",
            appointment_at=datetime.combine(appt_date, datetime.min.time()).replace(
                tzinfo=timezone.utc
            ),
            status="SCHEDULED",
        )
        session.add(appt)
        session.commit()

        logger.info(
            "Created follow-up appointment on %s for patient %s from record %s",
            follow_up_date,
            patient_id,
            record_id,
        )


def _update_record_status(record_id: str, status: str, error: str | None = None) -> None:
    """Update record processing status in database."""
    try:
        from sqlalchemy import create_engine, update
        from sqlalchemy.orm import Session

        from app.config import settings
        from app.models.medical_record import MedicalRecord

        sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
        engine = create_engine(sync_url)

        with Session(engine) as session:
            values: dict = {"processing_status": status}
            if error:
                values["processing_error"] = error
            session.execute(
                update(MedicalRecord)
                .where(MedicalRecord.id == uuid.UUID(record_id))
                .values(**values)
            )
            session.commit()
    except Exception:
        logger.exception("Failed to update record %s status", record_id)
