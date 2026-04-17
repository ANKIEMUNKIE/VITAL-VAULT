# app/services/record_service.py
"""Medical record business logic.

Handles upload initiation, record queries, extraction updates,
and record sharing. All file processing is delegated to Celery workers.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import date
from io import BytesIO

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import (
    InsufficientStorageException,
    InvalidFileTypeException,
    RecordNotFoundException,
)
from app.core.storage import generate_presigned_url, upload_file
from app.models.category import DocumentCategory
from app.models.patient import PatientProfile
from app.repositories import record_repo
from app.schemas.record import (
    ExtractionData,
    RecordDetailResponse,
    RecordListItem,
    RecordStatusResponse,
    RecordUploadResponse,
)

logger = logging.getLogger(__name__)

# Allowed MIME types per PRD
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
}


class RecordService:
    """Service for medical record operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def initiate_upload(
        self,
        *,
        file: UploadFile,
        patient_id: uuid.UUID,
        title: str | None = None,
        category_slug: str | None = None,
        document_date: date | None = None,
        tags: list[str] | None = None,
    ) -> RecordUploadResponse:
        """Validate, store, and queue a file for processing.

        Security controls applied:
        1. MIME type validation against whitelist.
        2. Storage quota check.
        3. SHA-256 integrity checksum.

        Args:
            file: Uploaded file.
            patient_id: Owner patient profile ID.
            title: Optional title (AI infers if absent).
            category_slug: Optional category slug.
            document_date: Optional document date.
            tags: Optional tags list.

        Returns:
            RecordUploadResponse with record_id and PENDING status.

        Raises:
            InvalidFileTypeException: If MIME type not in whitelist.
            InsufficientStorageException: If upload exceeds quota.
        """
        # 1. Validate MIME type
        mime_type = file.content_type or "application/octet-stream"
        if mime_type not in ALLOWED_MIME_TYPES:
            raise InvalidFileTypeException(mime_type)

        # 2. Read file content for size + checksum
        content = await file.read()
        file_size = len(content)

        # 3. Check storage quota
        profile_result = await self.db.execute(
            select(PatientProfile).where(PatientProfile.id == patient_id)
        )
        profile = profile_result.scalar_one_or_none()
        if profile:
            if profile.storage_used_bytes + file_size > profile.storage_quota_bytes:
                raise InsufficientStorageException(
                    profile.storage_used_bytes, profile.storage_quota_bytes
                )

        # 4. Compute SHA-256 checksum
        checksum = hashlib.sha256(content).hexdigest()

        # 5. Upload to S3/MinIO
        storage_key = f"records/{patient_id}/{uuid.uuid4()}/{file.filename}"
        upload_file(BytesIO(content), storage_key, mime_type)

        # 6. Resolve category
        category_id = None
        if category_slug:
            cat_result = await self.db.execute(
                select(DocumentCategory).where(DocumentCategory.slug == category_slug)
            )
            cat = cat_result.scalar_one_or_none()
            if cat:
                category_id = cat.id

        # 7. Create DB record
        record = await record_repo.create_record(
            self.db,
            patient_id=patient_id,
            title=title or file.filename or "Untitled Document",
            storage_key=storage_key,
            storage_bucket=settings.S3_BUCKET_NAME,
            file_name_original=file.filename or "unknown",
            file_size_bytes=file_size,
            mime_type=mime_type,
            checksum_sha256=checksum,
            category_id=category_id,
            document_date=document_date,
            tags=tags,
        )

        # 8. Update storage usage
        if profile:
            profile.storage_used_bytes += file_size

        # 9. Enqueue Celery task (imported here to avoid circular imports)
        try:
            from app.tasks.ocr import run_ocr_pipeline

            run_ocr_pipeline.delay(str(record.id))
        except Exception:
            logger.warning(
                "Failed to enqueue OCR task for record %s — Celery may not be running",
                record.id,
            )

        return RecordUploadResponse(
            record_id=record.id,
            status="PENDING",
        )

    async def get_record_detail(
        self,
        *,
        record_id: uuid.UUID,
        patient_id: uuid.UUID,
    ) -> RecordDetailResponse:
        """Get full record details including extraction data.

        Args:
            record_id: The record UUID.
            patient_id: The owning patient's profile ID.

        Returns:
            RecordDetailResponse with extraction and download URL.
        """
        record = await record_repo.get_record_for_patient(
            record_id, patient_id, self.db
        )

        download_url = None
        if record.storage_key:
            try:
                download_url = generate_presigned_url(record.storage_key)
            except Exception:
                logger.warning("Failed to generate presigned URL for record %s", record_id)

        extraction_data = None
        if record.extraction:
            extraction_data = ExtractionData(
                diagnosed_conditions=None,  # Would be decrypted in production
                extracted_medications=None,
                extracted_dates=record.extraction.extracted_dates,
                doctor_name=None,
                hospital_name=None,
                ai_summary=None,
                confidence_score=float(record.extraction.confidence_score) if record.extraction.confidence_score else None,
            )

        return RecordDetailResponse(
            id=record.id,
            title=record.title,
            document_date=record.document_date,
            processing_status=record.processing_status,
            category=None,
            extraction=extraction_data,
            download_url=download_url,
            tags=record.tags,
            file_size_bytes=record.file_size_bytes,
            created_at=record.created_at,
        )

    async def get_record_status(
        self,
        *,
        record_id: uuid.UUID,
        patient_id: uuid.UUID,
    ) -> RecordStatusResponse:
        """Lightweight polling endpoint for processing status.

        Args:
            record_id: The record UUID.
            patient_id: The owning patient's profile ID.

        Returns:
            RecordStatusResponse with current status.
        """
        record = await record_repo.get_record_for_patient(
            record_id, patient_id, self.db
        )

        progress_hints = {
            "PENDING": "Queued for processing...",
            "OCR_PROCESSING": "Extracting text from document...",
            "AI_PROCESSING": "Analyzing document with AI...",
            "PROCESSED": "Processing complete.",
            "FAILED": record.processing_error or "Processing failed.",
            "MANUAL_REVIEW": "Document requires manual review.",
        }

        return RecordStatusResponse(
            record_id=record.id,
            status=record.processing_status,
            progress_hint=progress_hints.get(record.processing_status),
        )
