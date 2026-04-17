# app/tasks/notifications.py
"""Notification Celery tasks."""

from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    queue="notifications",
    time_limit=30,
    name="app.tasks.notifications.send_processing_complete_notification",
)
def send_processing_complete_notification(patient_id: str, record_id: str) -> dict:
    """Send notification that document processing is complete.

    Phase 1: Logging stub. Replace with actual push/email in Phase 2.

    Args:
        patient_id: Patient profile UUID string.
        record_id: Medical record UUID string.

    Returns:
        Dict with notification status.
    """
    logger.info(
        "NOTIFICATION: Document processed — patient=%s record=%s",
        patient_id,
        record_id,
    )
    return {"status": "sent", "patient_id": patient_id, "record_id": record_id}


@shared_task(
    queue="notifications",
    time_limit=30,
    name="app.tasks.notifications.send_processing_failed_notification",
)
def send_processing_failed_notification(patient_id: str, record_id: str, error: str) -> dict:
    """Send notification that document processing failed.

    Args:
        patient_id: Patient profile UUID string.
        record_id: Medical record UUID string.
        error: Error description.

    Returns:
        Dict with notification status.
    """
    logger.info(
        "NOTIFICATION: Processing failed — patient=%s record=%s error='%s'",
        patient_id,
        record_id,
        error,
    )
    return {"status": "sent", "patient_id": patient_id, "record_id": record_id}
