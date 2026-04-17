# app/tasks/__init__.py
"""Explicit task imports so Celery autodiscover registers all @shared_task functions."""

from app.tasks import ai_extraction  # noqa: F401
from app.tasks import maintenance  # noqa: F401
from app.tasks import notifications  # noqa: F401
from app.tasks import ocr  # noqa: F401
from app.tasks import reminders  # noqa: F401
