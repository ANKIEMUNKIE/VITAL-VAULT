# app/schemas/reminder.py
"""Pydantic v2 schemas for reminder endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReminderCreate(BaseModel):
    """POST /reminders request body."""

    title: str = Field(..., min_length=1, max_length=500)
    reminder_type: str = Field(
        ..., pattern="^(MEDICATION|APPOINTMENT|FOLLOW_UP|VACCINATION|CUSTOM)$"
    )
    medication_id: uuid.UUID | None = None
    record_id: uuid.UUID | None = None
    scheduled_at: datetime
    recurrence_rule: str | None = None
    delivery_channels: list[str] = ["PUSH"]
    body: str | None = None


class ReminderUpdate(BaseModel):
    """PATCH /reminders/{id} request body."""

    title: str | None = None
    scheduled_at: datetime | None = None
    recurrence_rule: str | None = None
    is_active: bool | None = None
    delivery_channels: list[str] | None = None
    body: str | None = None


class ReminderResponse(BaseModel):
    """Reminder response object."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    reminder_type: str
    scheduled_at: datetime
    recurrence_rule: str | None = None
    is_active: bool
    delivery_channels: list[str]
    body: str | None = None
    medication_id: uuid.UUID | None = None
    last_sent_at: datetime | None = None
    next_run_at: datetime | None = None
    created_at: datetime


class ReminderListResponse(BaseModel):
    """GET /reminders response."""

    data: list[ReminderResponse]
