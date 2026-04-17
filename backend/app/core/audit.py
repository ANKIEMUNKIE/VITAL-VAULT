# app/core/audit.py
"""Audit logging helper for HIPAA-compliant action tracking.

Every endpoint that accesses or mutates PHI must call log_action().
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def log_action(
    db: AsyncSession,
    *,
    actor_user_id: uuid.UUID | None = None,
    target_user_id: uuid.UUID | None = None,
    action: str,
    resource_type: str,
    resource_id: uuid.UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    request_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Insert an immutable audit log entry.

    This function is designed to never throw — audit failures are logged
    but should not break the primary operation.

    Args:
        db: Async database session.
        actor_user_id: User who performed the action.
        target_user_id: User affected by the action (for PHI access).
        action: Action identifier (e.g., RECORD_UPLOADED, RECORD_VIEWED).
        resource_type: Entity type (e.g., MedicalRecord, Reminder).
        resource_id: UUID of the affected resource.
        ip_address: Client IP address.
        user_agent: Client user agent string.
        request_id: Request correlation ID.
        metadata: Additional event context.
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        stmt = insert(AuditLog).values(
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            metadata_=metadata,
        )
        await db.execute(stmt)
        # Note: commit is handled by the session context manager in get_db
    except Exception:
        logger.exception(
            "Failed to write audit log: action=%s resource=%s",
            action,
            resource_id,
        )
