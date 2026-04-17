# app/utils/rrule_utils.py
"""iCal RRULE utilities for reminder recurrence.

Converts human-readable frequency strings to iCal RRULE format
and computes next occurrence dates.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


# Common frequency string to RRULE mapping
FREQUENCY_RRULE_MAP = {
    "once daily": "FREQ=DAILY;BYHOUR=8",
    "twice daily": "FREQ=DAILY;BYHOUR=8,20",
    "three times daily": "FREQ=DAILY;BYHOUR=8,14,20",
    "every 6 hours": "FREQ=HOURLY;INTERVAL=6",
    "every 8 hours": "FREQ=HOURLY;INTERVAL=8",
    "every 12 hours": "FREQ=HOURLY;INTERVAL=12",
    "once weekly": "FREQ=WEEKLY",
    "twice weekly": "FREQ=WEEKLY;INTERVAL=1;BYDAY=MO,TH",
    "daily": "FREQ=DAILY;BYHOUR=8",
    "weekly": "FREQ=WEEKLY",
    "monthly": "FREQ=MONTHLY",
}


def frequency_to_rrule(frequency: str) -> str | None:
    """Convert a human-readable frequency string to iCal RRULE.

    Args:
        frequency: Frequency string (e.g., 'twice daily', 'once daily').

    Returns:
        iCal RRULE string or None if unrecognized.
    """
    normalized = frequency.strip().lower()
    return FREQUENCY_RRULE_MAP.get(normalized)


def compute_next_occurrence(
    rrule: str,
    last_run: datetime | None = None,
) -> datetime | None:
    """Compute the next occurrence based on an RRULE.

    Simple implementation for common rules. For full RFC 5545 compliance,
    use python-dateutil.rrule in a future iteration.

    Args:
        rrule: iCal RRULE string.
        last_run: Last execution time; defaults to now.

    Returns:
        Next occurrence datetime or None.
    """
    now = last_run or datetime.now(timezone.utc)

    if "FREQ=DAILY" in rrule:
        return now + timedelta(days=1)
    elif "FREQ=HOURLY" in rrule:
        # Extract interval
        interval = 1
        for part in rrule.split(";"):
            if part.startswith("INTERVAL="):
                interval = int(part.split("=")[1])
        return now + timedelta(hours=interval)
    elif "FREQ=WEEKLY" in rrule:
        return now + timedelta(weeks=1)
    elif "FREQ=MONTHLY" in rrule:
        return now + timedelta(days=30)

    return None
