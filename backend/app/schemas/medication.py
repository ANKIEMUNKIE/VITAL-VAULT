# app/schemas/medication.py
"""Pydantic v2 schemas for medication endpoints."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class MedicationCreate(BaseModel):
    """POST /medications request body."""

    name: str = Field(..., min_length=1, max_length=200)
    generic_name: str | None = None
    dosage: str | None = None
    frequency: str | None = None
    route: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    prescribed_by: str | None = None
    notes: str | None = None
    source_record_id: uuid.UUID | None = None


class MedicationUpdate(BaseModel):
    """PATCH /medications/{id} request body."""

    name: str | None = None
    generic_name: str | None = None
    dosage: str | None = None
    frequency: str | None = None
    route: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool | None = None
    prescribed_by: str | None = None
    notes: str | None = None


class MedicationResponse(BaseModel):
    """Medication response object."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str  # Decrypted by service layer
    generic_name: str | None = None
    dosage: str | None = None
    frequency: str | None = None
    route: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool
    prescribed_by: str | None = None
    notes: str | None = None
    source_record_id: uuid.UUID | None = None
    created_at: datetime


class MedicationListResponse(BaseModel):
    """GET /medications response."""

    data: list[MedicationResponse]
