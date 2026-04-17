# app/tasks/celery_app.py
"""Celery application configuration with Redis broker.

Queue routing, beat schedule, and serialization settings.
"""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "vital_vault",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task routing — each task type goes to its own queue
    task_routes={
        "app.tasks.ocr.*": {"queue": "ocr"},
        "app.tasks.ai_extraction.*": {"queue": "ai"},
        "app.tasks.notifications.*": {"queue": "notifications"},
        "app.tasks.reminders.*": {"queue": "reminders"},
        "app.tasks.maintenance.*": {"queue": "default"},
    },

    # Beat schedule for recurring tasks
    beat_schedule={
        "dispatch-due-reminders": {
            "task": "app.tasks.reminders.dispatch_due_reminders",
            "schedule": crontab(minute="*"),  # Every minute
        },
        "cleanup-expired-tokens": {
            "task": "app.tasks.maintenance.cleanup_expired_tokens",
            "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM UTC
        },
        "gdpr-hard-delete": {
            "task": "app.tasks.maintenance.gdpr_hard_delete",
            "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM UTC
        },
    },

    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Auto-discover tasks
celery_app.autodiscover_tasks([
    "app.tasks",
])
