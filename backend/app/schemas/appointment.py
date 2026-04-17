# app/schemas/appointment.py
"""Pydantic v2 schemas for appointment endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AppointmentCreate(BaseModel):
    """POST /appointments request body."""

    title: str = Field(..., min_length=1, max_length=500)
    doctor_id: uuid.UUID | None = None
    appointment_at: datetime
    location: str | None = None
    notes: str | None = None


class AppointmentUpdate(BaseModel):
    """PATCH /appointments/{id} request body."""

    title: str | None = None
    appointment_at: datetime | None = None
    location: str | None = None
    notes: str | None = None
    status: str | None = Field(
        None, pattern="^(SCHEDULED|COMPLETED|CANCELLED|MISSED)$"
    )


class AppointmentResponse(BaseModel):
    """Appointment response object."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    doctor_id: uuid.UUID | None = None
    appointment_at: datetime
    location: str | None = None
    notes: str | None = None  # Decrypted by service layer
    status: str
    reminder_sent: bool
    created_at: datetime


class AppointmentListResponse(BaseModel):
    """GET /appointments response."""

    data: list[AppointmentResponse]
