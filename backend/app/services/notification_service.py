# app/services/notification_service.py
"""Notification dispatch service.

Phase 1: Logging stubs. Full SendGrid/Twilio/FCM integrations
will be added in a future phase.
"""

from __future__ import annotations

import logging
import uuid

logger = logging.getLogger(__name__)


async def send_processing_complete(
    patient_id: uuid.UUID,
    record_id: uuid.UUID,
    title: str,
) -> None:
    """Notify patient that document processing is complete.

    Args:
        patient_id: Patient profile ID.
        record_id: Processed record ID.
        title: Document title.
    """
    # Phase 1: Log only. Replace with actual push/email in Phase 2.
    logger.info(
        "NOTIFICATION [STUB]: Processing complete for patient=%s record=%s title='%s'",
        patient_id,
        record_id,
        title,
    )


async def send_processing_failed(
    patient_id: uuid.UUID,
    record_id: uuid.UUID,
    error: str,
) -> None:
    """Notify patient that document processing failed.

    Args:
        patient_id: Patient profile ID.
        record_id: Failed record ID.
        error: Error description.
    """
    logger.info(
        "NOTIFICATION [STUB]: Processing failed for patient=%s record=%s error='%s'",
        patient_id,
        record_id,
        error,
    )


async def send_reminder_notification(
    patient_id: uuid.UUID,
    reminder_title: str,
    channels: list[str],
) -> None:
    """Dispatch a reminder notification via specified channels.

    Args:
        patient_id: Patient profile ID.
        reminder_title: Reminder title text.
        channels: List of channels (PUSH, EMAIL, SMS).
    """
    logger.info(
        "NOTIFICATION [STUB]: Reminder for patient=%s title='%s' channels=%s",
        patient_id,
        reminder_title,
        channels,
    )
