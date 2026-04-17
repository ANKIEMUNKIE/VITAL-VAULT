# app/models/appointment.py
"""Appointment ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, LargeBinary, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Appointment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Patient appointment with optional doctor reference.

    Status lifecycle: SCHEDULED → COMPLETED | CANCELLED | MISSED.
    """

    __tablename__ = "appointments"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    doctor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doctor_profiles.id"), nullable=True, index=True
    )
    source_record_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("medical_records.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)
    appointment_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    notes: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True, comment="Encrypted notes"
    )
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="SCHEDULED",
        server_default="SCHEDULED",
        comment="SCHEDULED | COMPLETED | CANCELLED | MISSED",
    )
    reminder_sent: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    # --- Relationships (string refs to avoid circular imports) ---
    patient = relationship("PatientProfile", back_populates="appointments")
    doctor = relationship("DoctorProfile", back_populates="appointments")
    source_record = relationship("MedicalRecord", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Appointment id={self.id} status={self.status}>"
