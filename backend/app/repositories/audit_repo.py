# app/repositories/audit_repo.py
"""Database query layer for AuditLog model."""

from __future__ import annotations

# Audit log queries are minimal — the log_action helper in core/audit.py
# handles inserts. This module provides read queries for admin endpoints.

import uuid
from datetime import date, datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def list_audit_logs(
    db: AsyncSession,
    *,
    actor_user_id: uuid.UUID | None = None,
    target_user_id: uuid.UUID | None = None,
    action: str | None = None,
    from_date: date | None = None,
    page: int = 1,
    limit: int = 50,
) -> tuple[list[AuditLog], int]:
    """List audit logs with optional filters and pagination.

    Args:
        db: Async database session.
        actor_user_id: Filter by actor.
        target_user_id: Filter by target.
        action: Filter by action type.
        from_date: Filter logs from this date.
        page: Page number (1-indexed).
        limit: Items per page.

    Returns:
        Tuple of (logs list, total count).
    """
    query = select(AuditLog)
    count_query = select(func.count(AuditLog.id))

    if actor_user_id:
        query = query.where(AuditLog.actor_user_id == actor_user_id)
        count_query = count_query.where(AuditLog.actor_user_id == actor_user_id)
    if target_user_id:
        query = query.where(AuditLog.target_user_id == target_user_id)
        count_query = count_query.where(AuditLog.target_user_id == target_user_id)
    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)
    if from_date:
        query = query.where(AuditLog.created_at >= datetime.combine(from_date, datetime.min.time()))
        count_query = count_query.where(AuditLog.created_at >= datetime.combine(from_date, datetime.min.time()))

    query = query.order_by(AuditLog.created_at.desc())
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    logs = list(result.scalars().all())

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    return logs, total
