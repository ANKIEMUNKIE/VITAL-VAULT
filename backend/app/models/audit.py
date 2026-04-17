# app/models/audit.py
"""AuditLog ORM model — immutable log of PHI access and mutation events."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Text, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AuditLog(Base):
    """Immutable audit trail for all PHI access and data mutations.

    Captures actor, target, action, resource type/id, network metadata,
    and arbitrary event metadata. Retained for 6 years per HIPAA.

    This table is append-only — no UPDATE or DELETE operations are permitted.
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    target_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        index=True,
        comment="RECORD_VIEWED, RECORD_UPLOADED, REMINDER_CREATED, etc.",
    )
    resource_type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="MedicalRecord, Reminder, User, etc.",
    )
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} action={self.action}>"
