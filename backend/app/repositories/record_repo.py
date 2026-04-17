# app/repositories/record_repo.py
"""Database query layer for MedicalRecord and RecordExtraction models.

All queries are scoped by patient_id to enforce ownership — never trust
path parameters alone without verifying ownership.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import RecordNotFoundException
from app.models.medical_record import MedicalRecord, RecordExtraction


async def create_record(
    db: AsyncSession,
    *,
    patient_id: uuid.UUID,
    title: str,
    storage_key: str,
    storage_bucket: str,
    file_name_original: str,
    file_size_bytes: int,
    mime_type: str,
    checksum_sha256: str,
    category_id: int | None = None,
    document_date: date | None = None,
    tags: list[str] | None = None,
) -> MedicalRecord:
    """Insert a new medical record row with status=PENDING.

    Args:
        db: Async database session.
        patient_id: Owner patient profile ID.
        title: Document title.
        storage_key: S3/MinIO object key.
        storage_bucket: Storage bucket name.
        file_name_original: Original uploaded filename.
        file_size_bytes: File size in bytes.
        mime_type: MIME type of the file.
        checksum_sha256: SHA-256 checksum for integrity.
        category_id: Optional document category ID.
        document_date: Optional date on the document.
        tags: Optional list of tags.

    Returns:
        The created MedicalRecord instance.
    """
    record = MedicalRecord(
        patient_id=patient_id,
        title=title,
        storage_key=storage_key,
        storage_bucket=storage_bucket,
        file_name_original=file_name_original,
        file_size_bytes=file_size_bytes,
        mime_type=mime_type,
        checksum_sha256=checksum_sha256,
        category_id=category_id,
        document_date=document_date,
        tags=tags or [],
    )
    db.add(record)
    await db.flush()
    return record


async def get_record_for_patient(
    record_id: uuid.UUID,
    patient_id: uuid.UUID,
    db: AsyncSession,
) -> MedicalRecord:
    """Fetch a medical record with ownership verification.

    Args:
        record_id: The record UUID to fetch.
        patient_id: The owning patient's profile ID.
        db: Async database session.

    Returns:
        MedicalRecord instance.

    Raises:
        RecordNotFoundException: If not found or not owned.
    """
    result = await db.execute(
        select(MedicalRecord).where(
            MedicalRecord.id == record_id,
            MedicalRecord.patient_id == patient_id,
            MedicalRecord.is_deleted == False,  # noqa: E712
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise RecordNotFoundException(record_id)
    return record


async def list_patient_records(
    patient_id: uuid.UUID,
    db: AsyncSession,
    *,
    category_slug: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    tags: list[str] | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[MedicalRecord], int]:
    """List medical records for a patient with optional filters and pagination.

    Args:
        patient_id: Owner patient profile ID.
        db: Async database session.
        category_slug: Optional category filter.
        from_date: Optional start date filter.
        to_date: Optional end date filter.
        tags: Optional tags filter.
        page: Page number (1-indexed).
        limit: Items per page.

    Returns:
        Tuple of (records list, total count).
    """
    base_query = (
        select(MedicalRecord)
        .where(
            MedicalRecord.patient_id == patient_id,
            MedicalRecord.is_deleted == False,  # noqa: E712
        )
    )
    count_query = (
        select(func.count(MedicalRecord.id))
        .where(
            MedicalRecord.patient_id == patient_id,
            MedicalRecord.is_deleted == False,  # noqa: E712
        )
    )

    if from_date:
        base_query = base_query.where(MedicalRecord.document_date >= from_date)
        count_query = count_query.where(MedicalRecord.document_date >= from_date)
    if to_date:
        base_query = base_query.where(MedicalRecord.document_date <= to_date)
        count_query = count_query.where(MedicalRecord.document_date <= to_date)

    base_query = base_query.order_by(MedicalRecord.document_date.desc())
    offset = (page - 1) * limit
    base_query = base_query.offset(offset).limit(limit)

    result = await db.execute(base_query)
    records = list(result.scalars().all())

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    return records, total


async def update_record_status(
    record_id: uuid.UUID,
    status: str,
    db: AsyncSession,
    *,
    error: str | None = None,
    ocr_raw_text: bytes | None = None,
) -> None:
    """Update a record's processing status.

    Args:
        record_id: The record UUID.
        status: New processing status.
        db: Async database session.
        error: Optional error message for FAILED status.
        ocr_raw_text: Optional encrypted OCR text.
    """
    values: dict = {"processing_status": status}
    if error:
        values["processing_error"] = error
    if ocr_raw_text:
        values["ocr_raw_text"] = ocr_raw_text

    await db.execute(
        update(MedicalRecord)
        .where(MedicalRecord.id == record_id)
        .values(**values)
    )


async def soft_delete_record(
    record_id: uuid.UUID,
    patient_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Soft delete a medical record.

    Args:
        record_id: The record UUID.
        patient_id: The owning patient's profile ID for ownership check.
        db: Async database session.
    """
    record = await get_record_for_patient(record_id, patient_id, db)
    await db.execute(
        update(MedicalRecord)
        .where(MedicalRecord.id == record.id)
        .values(
            is_deleted=True,
            deleted_at=datetime.now(timezone.utc),
        )
    )


async def create_extraction(
    db: AsyncSession,
    *,
    record_id: uuid.UUID,
    diagnosed_conditions: bytes | None = None,
    extracted_medications: bytes | None = None,
    extracted_dates: dict | None = None,
    doctor_name: bytes | None = None,
    hospital_name: bytes | None = None,
    ai_summary: bytes | None = None,
    confidence_score: float | None = None,
    extraction_model: str | None = None,
    extraction_version: str | None = None,
) -> RecordExtraction:
    """Insert an AI extraction result for a record."""
    extraction = RecordExtraction(
        record_id=record_id,
        diagnosed_conditions=diagnosed_conditions,
        extracted_medications=extracted_medications,
        extracted_dates=extracted_dates,
        doctor_name=doctor_name,
        hospital_name=hospital_name,
        ai_summary=ai_summary,
        confidence_score=confidence_score,
        extraction_model=extraction_model,
        extraction_version=extraction_version,
    )
    db.add(extraction)
    await db.flush()
    return extraction
