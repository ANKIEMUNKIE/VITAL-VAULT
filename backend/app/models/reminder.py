# app/models/reminder.py
"""Reminder ORM model with iCal RRULE and multi-channel delivery."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Reminder(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Patient reminder for medications, appointments, or custom events.

    Supports iCal RRULE for recurrence and multi-channel delivery
    (PUSH, EMAIL, SMS).
    """

    __tablename__ = "reminders"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    medication_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("medications.id"), nullable=True
    )
    record_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("medical_records.id"), nullable=True
    )
    reminder_type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        index=True,
        comment="MEDICATION | APPOINTMENT | FOLLOW_UP | VACCINATION | CUSTOM",
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    recurrence_rule: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="iCal RRULE string"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    delivery_channels = mapped_column(
        ARRAY(Text), nullable=False, server_default="{PUSH}"
    )
    last_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # --- Relationships (string refs to avoid circular imports) ---
    patient = relationship("PatientProfile", back_populates="reminders")
    medication = relationship("Medication", back_populates="reminders")

    def __repr__(self) -> str:
        return f"<Reminder id={self.id} type={self.reminder_type} active={self.is_active}>"
