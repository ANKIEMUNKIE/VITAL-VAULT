# app/models/clinic.py
"""Clinic and ClinicMembership ORM models for B2B tier."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Clinic(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """B2B clinic entity.

    Represents a healthcare facility that can have multiple
    doctors and admin users via ClinicMembership.
    """

    __tablename__ = "clinics"

    name: Mapped[str] = mapped_column(Text, nullable=False)
    license_number: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True
    )
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_email: Mapped[str] = mapped_column(Text, nullable=False)
    api_key_hash: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Hashed API key for B2B integration"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    # --- Relationships ---
    memberships: Mapped[list[ClinicMembership]] = relationship(
        "ClinicMembership", back_populates="clinic", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<Clinic id={self.id} name={self.name}>"


class ClinicMembership(Base, UUIDPrimaryKeyMixin):
    """Junction table linking users to clinics with a role.

    Roles: DOCTOR, ADMIN, RECEPTIONIST.
    """

    __tablename__ = "clinic_memberships"
    __table_args__ = (
        # Unique constraint: one role per user per clinic
        {"comment": "UNIQUE(clinic_id, user_id) enforced"},
    )

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="DOCTOR | ADMIN | RECEPTIONIST",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # --- Relationships (lazy string references to avoid circular imports) ---
    clinic: Mapped[Clinic] = relationship(
        "Clinic", back_populates="memberships"
    )
    user = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<ClinicMembership clinic={self.clinic_id} user={self.user_id} role={self.role}>"
