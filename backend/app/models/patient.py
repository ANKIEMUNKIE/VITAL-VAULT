# app/models/patient.py
"""PatientProfile ORM model with encrypted PHI columns."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, LargeBinary, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PatientProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Patient profile containing personally identifiable health information.

    PHI columns (full_name, date_of_birth, allergies, emergency_contact)
    are stored as LargeBinary and encrypted at the application layer
    using pgcrypto pgp_sym_encrypt/decrypt.
    """

    __tablename__ = "patient_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    full_name: Mapped[bytes] = mapped_column(
        LargeBinary, nullable=False, comment="Encrypted via pgcrypto"
    )
    date_of_birth: Mapped[bytes] = mapped_column(
        LargeBinary, nullable=False, comment="Encrypted via pgcrypto"
    )
    gender: Mapped[str | None] = mapped_column(Text, nullable=True)
    blood_group: Mapped[str | None] = mapped_column(Text, nullable=True)
    allergies: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True, comment="Encrypted JSON array"
    )
    emergency_contact: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True, comment="Encrypted JSON object"
    )
    storage_used_bytes: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0"
    )
    storage_quota_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=524288000,  # 500 MB
        server_default="524288000",
    )

    # --- Relationships (string refs to avoid circular imports) ---
    user = relationship("User", back_populates="patient_profile")
    medical_records = relationship(
        "MedicalRecord", back_populates="patient", lazy="noload"
    )
    medications = relationship(
        "Medication", back_populates="patient", lazy="noload"
    )
    reminders = relationship(
        "Reminder", back_populates="patient", lazy="noload"
    )
    appointments = relationship(
        "Appointment", back_populates="patient", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<PatientProfile id={self.id} user_id={self.user_id}>"
