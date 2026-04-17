# app/repositories/reminder_repo.py
"""Database query layer for Reminder model."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reminder import Reminder


async def create_reminder(
    db: AsyncSession,
    *,
    patient_id: uuid.UUID,
    title: str,
    reminder_type: str,
    scheduled_at: datetime,
    medication_id: uuid.UUID | None = None,
    record_id: uuid.UUID | None = None,
    body: str | None = None,
    recurrence_rule: str | None = None,
    delivery_channels: list[str] | None = None,
) -> Reminder:
    """Create a new reminder for a patient."""
    reminder = Reminder(
        patient_id=patient_id,
        title=title,
        reminder_type=reminder_type,
        scheduled_at=scheduled_at,
        medication_id=medication_id,
        record_id=record_id,
        body=body,
        recurrence_rule=recurrence_rule,
        delivery_channels=delivery_channels or ["PUSH"],
        next_run_at=scheduled_at,
    )
    db.add(reminder)
    await db.flush()
    return reminder


async def list_patient_reminders(
    patient_id: uuid.UUID,
    db: AsyncSession,
) -> list[Reminder]:
    """List all reminders for a patient, ordered by scheduled time."""
    result = await db.execute(
        select(Reminder)
        .where(Reminder.patient_id == patient_id)
        .order_by(Reminder.scheduled_at.asc())
    )
    return list(result.scalars().all())


async def get_reminder_for_patient(
    reminder_id: uuid.UUID,
    patient_id: uuid.UUID,
    db: AsyncSession,
) -> Reminder | None:
    """Fetch a reminder with patient ownership check."""
    result = await db.execute(
        select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.patient_id == patient_id,
        )
    )
    return result.scalar_one_or_none()


async def update_reminder(
    reminder_id: uuid.UUID,
    patient_id: uuid.UUID,
    db: AsyncSession,
    **kwargs: ...,
) -> Reminder | None:
    """Update a reminder's fields."""
    # Filter out None values
    values = {k: v for k, v in kwargs.items() if v is not None}
    if not values:
        return await get_reminder_for_patient(reminder_id, patient_id, db)

    await db.execute(
        update(Reminder)
        .where(Reminder.id == reminder_id, Reminder.patient_id == patient_id)
        .values(**values)
    )
    return await get_reminder_for_patient(reminder_id, patient_id, db)


async def delete_reminder(
    reminder_id: uuid.UUID,
    patient_id: uuid.UUID,
    db: AsyncSession,
) -> bool:
    """Delete a reminder. Returns True if deleted."""
    result = await db.execute(
        delete(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.patient_id == patient_id,
        )
    )
    return result.rowcount > 0  # type: ignore[union-attr]


async def get_due_reminders(
    db: AsyncSession,
) -> list[Reminder]:
    """Fetch all active reminders that are due (next_run_at <= now)."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Reminder).where(
            Reminder.is_active == True,  # noqa: E712
            Reminder.next_run_at <= now,
        )
    )
    return list(result.scalars().all())


async def count_active_reminders(
    patient_id: uuid.UUID,
    db: AsyncSession,
) -> int:
    """Count active reminders for a patient (for tier limit checking)."""
    result = await db.execute(
        select(func.count(Reminder.id)).where(
            Reminder.patient_id == patient_id,
            Reminder.is_active == True,  # noqa: E712
        )
    )
    return result.scalar() or 0
