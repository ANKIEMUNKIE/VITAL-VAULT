# app/models/doctor.py
"""DoctorProfile ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DoctorProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Doctor profile with license verification.

    Doctors must be verified (is_verified=True) before they can
    access shared patient records.
    """

    __tablename__ = "doctor_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    license_number: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True
    )
    specialization: Mapped[str] = mapped_column(Text, nullable=False)
    clinic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), nullable=True, index=True
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    # --- Relationships (string refs to avoid circular imports) ---
    user = relationship("User", back_populates="doctor_profile")
    clinic = relationship("Clinic", lazy="selectin")
    appointments = relationship(
        "Appointment", back_populates="doctor", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<DoctorProfile id={self.id} license={self.license_number}>"
