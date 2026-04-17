# app/schemas/record.py
"""Pydantic v2 schemas for medical record endpoints."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PaginationMeta


class CategoryInfo(BaseModel):
    """Embedded category reference."""

    model_config = ConfigDict(from_attributes=True)

    slug: str
    label: str


class ExtractionData(BaseModel):
    """AI-extracted structured data from a medical record."""

    model_config = ConfigDict(from_attributes=True)

    diagnosed_conditions: list[str] | None = None
    extracted_medications: list[dict] | None = None
    extracted_dates: dict | None = None
    doctor_name: str | None = None
    hospital_name: str | None = None
    ai_summary: str | None = None
    confidence_score: float | None = None


class RecordUploadResponse(BaseModel):
    """POST /records/upload — 202 Accepted response."""

    record_id: uuid.UUID
    status: str = "PENDING"
    message: str = "Document queued for AI processing."
    estimated_processing_seconds: int = 30


class RecordListItem(BaseModel):
    """Single item in the record list response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    category: CategoryInfo | None = None
    document_date: date | None = None
    processing_status: str
    tags: list[str] | None = None
    file_size_bytes: int
    created_at: datetime


class RecordListResponse(BaseModel):
    """GET /records response with pagination."""

    data: list[RecordListItem]
    pagination: PaginationMeta


class RecordDetailResponse(BaseModel):
    """GET /records/{record_id} — full record with extraction."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    document_date: date | None = None
    processing_status: str
    category: CategoryInfo | None = None
    extraction: ExtractionData | None = None
    download_url: str | None = None
    tags: list[str] | None = None
    file_size_bytes: int
    created_at: datetime


class RecordStatusResponse(BaseModel):
    """GET /records/{record_id}/status — lightweight polling."""

    record_id: uuid.UUID
    status: str
    progress_hint: str | None = None


class ExtractionPatchRequest(BaseModel):
    """PATCH /records/{record_id}/extraction — manual correction."""

    diagnosed_conditions: list[str] | None = None
    extracted_medications: list[dict] | None = None
    extracted_dates: dict | None = None
    doctor_name: str | None = None
    hospital_name: str | None = None


class ShareRecordRequest(BaseModel):
    """POST /records/{record_id}/share request body."""

    doctor_user_id: uuid.UUID
    expires_at: datetime | None = None
