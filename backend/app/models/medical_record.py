# app/models/medical_record.py
"""MedicalRecord and RecordExtraction ORM models."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    LargeBinary,
    Numeric,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class MedicalRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Uploaded medical document with processing pipeline status.

    Processing lifecycle: PENDING → OCR_PROCESSING → AI_PROCESSING → PROCESSED
    On failure: → FAILED or MANUAL_REVIEW.
    """

    __tablename__ = "medical_records"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("document_categories.id"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    document_date: Mapped[date | None] = mapped_column(
        Date, nullable=True
    )

    # Storage metadata
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    storage_bucket: Mapped[str] = mapped_column(Text, nullable=False)
    file_name_original: Mapped[str] = mapped_column(Text, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(Text, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(Text, nullable=False)

    # Processing status
    processing_status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="PENDING",
        server_default="PENDING",
        index=True,
        comment="PENDING | OCR_PROCESSING | AI_PROCESSING | PROCESSED | FAILED | MANUAL_REVIEW",
    )
    processing_error: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    # OCR raw text (encrypted)
    ocr_raw_text: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True, comment="Encrypted OCR text"
    )

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Sharing and tagging
    shared_with_doctor = mapped_column(
        ARRAY(UUID(as_uuid=True)),
        server_default="{}",
    )
    tags = mapped_column(
        ARRAY(Text),
        server_default="{}",
    )

    # --- Relationships (string refs to avoid circular imports) ---
    patient = relationship("PatientProfile", back_populates="medical_records")
    category = relationship("DocumentCategory", lazy="selectin")
    extraction = relationship(
        "RecordExtraction",
        back_populates="record",
        uselist=False,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<MedicalRecord id={self.id} status={self.processing_status}>"


class RecordExtraction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """AI-extracted structured data from a medical record.

    Stores extracted entities (conditions, medications, dates, etc.)
    in encrypted binary columns with JSONB for dates.
    """

    __tablename__ = "record_extractions"

    record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("medical_records.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Extracted entities (encrypted)
    diagnosed_conditions: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True, comment="Encrypted JSON array"
    )
    extracted_medications: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True, comment="Encrypted JSON array"
    )
    extracted_dates: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )
    doctor_name: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True, comment="Encrypted"
    )
    hospital_name: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True, comment="Encrypted"
    )
    ai_summary: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True, comment="Encrypted AI summary"
    )

    # Confidence and versioning
    confidence_score: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 3), nullable=True
    )
    extraction_model: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="AI model identifier"
    )
    extraction_version: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Extraction pipeline version"
    )

    # Manual corrections
    manually_corrected: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    manual_corrections: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )

    # --- Relationships ---
    record = relationship("MedicalRecord", back_populates="extraction")

    def __repr__(self) -> str:
        return f"<RecordExtraction id={self.id} record_id={self.record_id}>"
