# app/models/medication.py
"""Medication ORM model with encrypted sensitive fields."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, LargeBinary, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Medication(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Patient medication entry.

    Can be manually created or AI-extracted from a medical record.
    Sensitive fields (name, generic_name, notes) are encrypted.
    """

    __tablename__ = "medications"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_record_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("medical_records.id"), nullable=True
    )
    name: Mapped[bytes] = mapped_column(
        LargeBinary, nullable=False, comment="Encrypted medication name"
    )
    generic_name: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True, comment="Encrypted generic name"
    )
    dosage: Mapped[str | None] = mapped_column(Text, nullable=True)
    frequency: Mapped[str | None] = mapped_column(Text, nullable=True)
    route: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(
        Date, nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    prescribed_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True, comment="Encrypted notes"
    )

    # --- Relationships (string refs to avoid circular imports) ---
    patient = relationship("PatientProfile", back_populates="medications")
    source_record = relationship("MedicalRecord", lazy="selectin")
    reminders = relationship("Reminder", back_populates="medication", lazy="noload")

    def __repr__(self) -> str:
        return f"<Medication id={self.id} active={self.is_active}>"
