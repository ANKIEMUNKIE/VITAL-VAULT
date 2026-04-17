# app/tasks/reminders.py
"""Reminder dispatch Celery tasks — runs via Beat every minute.

Dispatches due reminders, computes next run via RRULE parsing,
and deactivates completed one-time reminders.
"""

from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    queue="reminders",
    name="app.tasks.reminders.dispatch_due_reminders",
)
def dispatch_due_reminders() -> dict:
    """Check for due reminders and dispatch notifications.

    Runs every minute via Celery Beat. Fetches all active reminders
    where next_run_at <= now, sends notification, and computes next run.

    Returns:
        Dict with count of dispatched and failed reminders.
    """
    from datetime import datetime, timezone

    from sqlalchemy import create_engine, select, update
    from sqlalchemy.orm import Session

    from app.config import settings
    from app.models.reminder import Reminder

    sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)

    dispatched = 0
    failed = 0
    now = datetime.now(timezone.utc)

    with Session(engine) as session:
        result = session.execute(
            select(Reminder).where(
                Reminder.is_active == True,  # noqa: E712
                Reminder.next_run_at <= now,
            )
        )
        due_reminders = list(result.scalars().all())

        for reminder in due_reminders:
            try:
                # Log dispatch (Phase 4: replace with real push/email)
                logger.info(
                    "DISPATCH REMINDER id=%s patient=%s title='%s' channels=%s",
                    reminder.id,
                    reminder.patient_id,
                    reminder.title,
                    reminder.delivery_channels,
                )

                # Compute next run
                next_run = _compute_next_run(reminder, now)
                is_still_active = next_run is not None

                session.execute(
                    update(Reminder)
                    .where(Reminder.id == reminder.id)
                    .values(
                        last_sent_at=now,
                        is_active=is_still_active,
                        next_run_at=next_run,
                        send_count=(reminder.send_count or 0) + 1,
                    )
                )
                dispatched += 1

            except Exception:
                logger.exception("Failed to dispatch reminder %s", reminder.id)
                failed += 1

        session.commit()

    logger.info("Dispatched %d reminders, %d failed", dispatched, failed)
    return {"dispatched": dispatched, "failed": failed}


def _compute_next_run(reminder, now: datetime) -> datetime | None:  # type: ignore[no-untyped-def]
    """Compute next run time based on RRULE string.

    Supports: FREQ=DAILY, FREQ=WEEKLY, FREQ=MONTHLY, FREQ=HOURLY,
    FREQ=DAILY;BYHOUR=8,20, INTERVAL=N modifiers.
    """
    from datetime import datetime, timedelta, timezone

    if not reminder.recurrence_rule:
        return None  # One-time reminder — no next run

    rule = reminder.recurrence_rule.upper()
    parts = {k: v for k, v in (p.split("=") for p in rule.split(";") if "=" in p)}

    freq = parts.get("FREQ", "DAILY")
    interval = int(parts.get("INTERVAL", "1"))
    byhour = [int(h) for h in parts.get("BYHOUR", "").split(",") if h]
    count = parts.get("COUNT")

    # Check COUNT limit
    if count and (reminder.send_count or 0) >= int(count):
        return None

    # Check UNTIL
    until_str = parts.get("UNTIL")
    if until_str:
        try:
            until = datetime.fromisoformat(until_str[:8])  # YYYYMMDD
            if now.date() >= until.date():
                return None
        except Exception:
            pass

    if byhour:
        # FREQ=DAILY;BYHOUR=8,20  → next occurrence of one of those hours
        upcoming_hours = sorted(
            [
                now.replace(hour=h, minute=0, second=0, microsecond=0)
                + (timedelta(days=0) if now.hour < h else timedelta(days=1))
                for h in byhour
            ]
        )
        return upcoming_hours[0] if upcoming_hours else None

    if freq == "HOURLY":
        return now + timedelta(hours=interval)
    if freq == "DAILY":
        return now + timedelta(days=interval)
    if freq == "WEEKLY":
        return now + timedelta(weeks=interval)
    if freq == "MONTHLY":
        # Naive: add 30 * interval days
        return now + timedelta(days=30 * interval)
    if freq == "YEARLY":
        return now + timedelta(days=365 * interval)

    # Fallback: daily
    return now + timedelta(days=1)
