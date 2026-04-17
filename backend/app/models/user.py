# app/models/user.py
"""User and RefreshToken ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Central identity table supporting multi-role system.

    Roles: PATIENT, DOCTOR, ADMIN, CLINIC_ADMIN.
    Includes MFA, account lockout, and email verification fields.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True, index=True
    )
    phone_number: Mapped[str | None] = mapped_column(Text, nullable=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="PATIENT | DOCTOR | ADMIN | CLINIC_ADMIN",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    is_email_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    mfa_secret: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="TOTP secret (encrypted)"
    )
    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    failed_login_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # --- Relationships (string refs to avoid circular imports) ---
    patient_profile = relationship(
        "PatientProfile", back_populates="user", uselist=False, lazy="selectin"
    )
    doctor_profile = relationship(
        "DoctorProfile", back_populates="user", uselist=False, lazy="selectin"
    )
    subscriptions = relationship(
        "Subscription", back_populates="user", lazy="selectin"
    )
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"


class RefreshToken(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Refresh token storage for secure session management.

    Tokens are stored as hashed values. Supports explicit revocation.
    """

    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    is_revoked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    # --- Relationships ---
    user = relationship("User", back_populates="refresh_tokens")

    def __repr__(self) -> str:
        return f"<RefreshToken id={self.id} user_id={self.user_id} revoked={self.is_revoked}>"
