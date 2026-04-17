# app/schemas/timeline.py
"""Pydantic v2 schemas for the timeline endpoint."""

from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict


class TimelineEvent(BaseModel):
    """Single event on the patient timeline."""

    model_config = ConfigDict(from_attributes=True)

    type: str  # RECORD, APPOINTMENT
    record_id: uuid.UUID | None = None
    appointment_id: uuid.UUID | None = None
    title: str
    category: str | None = None
    summary: str | None = None
    doctor: str | None = None
    tags: list[str] | None = None


class TimelineDay(BaseModel):
    """All events grouped by date."""

    date: date
    events: list[TimelineEvent]


class TimelineResponse(BaseModel):
    """GET /patients/{patient_id}/timeline response."""

    patient_id: uuid.UUID
    timeline: list[TimelineDay]
