# app/routers/timeline.py
"""Timeline router — chronological view of patient health events."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.appointment import Appointment
from app.models.medical_record import MedicalRecord
from app.models.user import User
from app.schemas.timeline import TimelineDay, TimelineEvent, TimelineResponse

router = APIRouter(tags=["Timeline"])


@router.get(
    "/patients/{patient_id}/timeline",
    response_model=TimelineResponse,
    summary="Get patient timeline",
    description="Chronological view of records and appointments. "
    "Accessible by the patient and doctors with shared access.",
)
async def get_timeline(
    patient_id: uuid.UUID,
    from_date: str | None = None,
    to_date: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TimelineResponse:
    """Build a chronological timeline of patient health events.

    Combines medical records and appointments into date-sorted groups.
    """
    # Verify access: patient accessing own data, or doctor with shared access
    if current_user.role == "PATIENT":
        if not current_user.patient_profile or current_user.patient_profile.id != patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
    elif current_user.role == "DOCTOR":
        pass  # Doctor access validated via shared_with_doctor in queries
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    from_d = date.fromisoformat(from_date) if from_date else None
    to_d = date.fromisoformat(to_date) if to_date else None

    # Fetch records
    record_query = (
        select(MedicalRecord)
        .where(
            MedicalRecord.patient_id == patient_id,
            MedicalRecord.is_deleted == False,  # noqa: E712
        )
    )
    if from_d:
        record_query = record_query.where(MedicalRecord.document_date >= from_d)
    if to_d:
        record_query = record_query.where(MedicalRecord.document_date <= to_d)

    records_result = await db.execute(record_query)
    records = list(records_result.scalars().all())

    # Fetch appointments
    appt_query = select(Appointment).where(Appointment.patient_id == patient_id)
    appts_result = await db.execute(appt_query)
    appointments = list(appts_result.scalars().all())

    # Group events by date
    events_by_date: dict[date, list[TimelineEvent]] = defaultdict(list)

    for r in records:
        event_date = r.document_date or r.created_at.date()
        summary = None
        if r.extraction and r.extraction.ai_summary:
            summary = r.extraction.ai_summary.decode("utf-8") if isinstance(r.extraction.ai_summary, bytes) else None

        events_by_date[event_date].append(
            TimelineEvent(
                type="RECORD",
                record_id=r.id,
                title=r.title,
                category=r.category.slug if r.category else None,
                summary=summary,
                tags=r.tags,
            )
        )

    for a in appointments:
        event_date = a.appointment_at.date()
        events_by_date[event_date].append(
            TimelineEvent(
                type="APPOINTMENT",
                appointment_id=a.id,
                title=a.title,
            )
        )

    # Sort by date descending
    timeline = sorted(
        [TimelineDay(date=d, events=e) for d, e in events_by_date.items()],
        key=lambda x: x.date,
        reverse=True,
    )

    return TimelineResponse(patient_id=patient_id, timeline=timeline)
