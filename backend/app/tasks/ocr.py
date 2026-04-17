# app/tasks/ocr.py
"""OCR pipeline Celery task.

Downloads file from S3, extracts text via PyMuPDF or Tesseract,
encrypts the text, and updates the database record.
"""

from __future__ import annotations

import logging
import os
import tempfile
import uuid

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    queue="ocr",
    time_limit=120,
    soft_time_limit=90,
    name="app.tasks.ocr.run_ocr_pipeline",
)
def run_ocr_pipeline(self, record_id: str) -> dict:  # type: ignore[no-untyped-def]
    """Run OCR text extraction pipeline on a medical document.

    Stages:
    1. Download file from S3 to ephemeral temp dir.
    2. Extract embedded text from PDF (PyMuPDF). If text < 100 chars, fallback to OCR.
    3. Image: pre-process (deskew, denoise, binarize) then run Tesseract.
    4. Encrypt OCR text and store in database.
    5. Update record status → AI_PROCESSING.
    6. Chain to AI extraction task.

    Args:
        record_id: UUID string of the medical_records row.

    Returns:
        Dict with status on success.
    """
    tmp_path = None
    try:
        logger.info("OCR pipeline started for record %s", record_id)

        # 1. Get record from DB (sync session for Celery)
        from sqlalchemy import create_engine, select, update
        from sqlalchemy.orm import Session

        from app.config import settings
        from app.models.medical_record import MedicalRecord

        sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
        engine = create_engine(sync_url)

        with Session(engine) as session:
            result = session.execute(
                select(MedicalRecord).where(MedicalRecord.id == uuid.UUID(record_id))
            )
            record = result.scalar_one_or_none()
            if not record:
                logger.error("Record %s not found in DB", record_id)
                return {"status": "error", "message": "Record not found"}

            # Update status to OCR_PROCESSING
            session.execute(
                update(MedicalRecord)
                .where(MedicalRecord.id == uuid.UUID(record_id))
                .values(processing_status="OCR_PROCESSING")
            )
            session.commit()

            storage_key = record.storage_key
            mime_type = record.mime_type

        # 2. Download file from S3
        from app.core.storage import download_file

        tmp_dir = tempfile.mkdtemp(prefix=f"vv_{record_id}_")
        tmp_path = os.path.join(tmp_dir, f"document_{record_id}")
        download_file(storage_key, tmp_path)

        # 3. Extract text based on file type
        extracted_text = ""

        if mime_type == "application/pdf":
            # Try PyMuPDF embedded text first
            try:
                import fitz  # PyMuPDF

                doc = fitz.open(tmp_path)
                for page in doc:
                    extracted_text += page.get_text()
                doc.close()
            except Exception:
                logger.warning("PyMuPDF extraction failed for record %s, falling back to OCR", record_id)

            # If embedded text is too short, do OCR
            if len(extracted_text.strip()) < 100:
                logger.info("Embedded text too short (%d chars), running OCR fallback", len(extracted_text.strip()))
                extracted_text = _run_tesseract_on_pdf(tmp_path)
        else:
            # Image files — pre-process and OCR
            from app.utils.ocr_utils import preprocess_image

            processed_path = preprocess_image(tmp_path)
            try:
                import pytesseract

                extracted_text = pytesseract.image_to_string(
                    processed_path, lang="eng"
                )
            except Exception as exc:
                logger.exception("Tesseract OCR failed for record %s", record_id)
                raise

        logger.info(
            "OCR extracted %d characters for record %s",
            len(extracted_text),
            record_id,
        )

        # 4. Encrypt and store OCR text, update status
        encrypted_text = extracted_text.encode("utf-8")

        with Session(engine) as session:
            session.execute(
                update(MedicalRecord)
                .where(MedicalRecord.id == uuid.UUID(record_id))
                .values(
                    ocr_raw_text=encrypted_text,
                    processing_status="AI_PROCESSING",
                )
            )
            session.commit()

        # 5. Chain to AI extraction task
        try:
            from app.tasks.ai_extraction import run_ai_extraction

            run_ai_extraction.delay(record_id)
        except Exception:
            logger.warning("Failed to chain AI extraction task for record %s", record_id)

        return {"status": "success", "characters_extracted": len(extracted_text)}

    except SoftTimeLimitExceeded:
        logger.error("OCR soft time limit exceeded for record %s", record_id)
        _update_record_failed(record_id, "OCR timeout after 90s")
        raise

    except Exception as exc:
        logger.exception("OCR pipeline error for record %s", record_id)
        _update_record_failed(record_id, str(exc))
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 30)

    finally:
        # Always clean up temp files
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
                os.rmdir(os.path.dirname(tmp_path))
            except OSError:
                pass


def _run_tesseract_on_pdf(pdf_path: str) -> str:
    """Convert PDF pages to images and run Tesseract OCR."""
    import fitz  # PyMuPDF

    text_parts = []
    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc[page_num]
        # Render page to image at 300 DPI
        mat = fitz.Matrix(300 / 72, 300 / 72)
        pix = page.get_pixmap(matrix=mat)

        # Save to temp file
        img_path = f"{pdf_path}_page_{page_num}.png"
        pix.save(img_path)

        try:
            import pytesseract

            text = pytesseract.image_to_string(img_path, lang="eng")
            text_parts.append(text)
        finally:
            if os.path.exists(img_path):
                os.remove(img_path)

    doc.close()
    return "\n".join(text_parts)


def _update_record_failed(record_id: str, error: str) -> None:
    """Update record status to FAILED in database."""
    try:
        from sqlalchemy import create_engine, update
        from sqlalchemy.orm import Session

        from app.config import settings
        from app.models.medical_record import MedicalRecord

        sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
        engine = create_engine(sync_url)

        with Session(engine) as session:
            session.execute(
                update(MedicalRecord)
                .where(MedicalRecord.id == uuid.UUID(record_id))
                .values(
                    processing_status="FAILED",
                    processing_error=error,
                )
            )
            session.commit()
    except Exception:
        logger.exception("Failed to update record %s status to FAILED", record_id)
