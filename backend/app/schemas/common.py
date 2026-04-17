# app/schemas/common.py
"""Shared Pydantic response models for pagination and errors."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PaginationMeta(BaseModel):
    """Standard pagination metadata returned with all list endpoints."""

    model_config = ConfigDict(from_attributes=True)

    page: int
    limit: int
    total: int


class ErrorDetail(BaseModel):
    """Structured error detail."""

    code: str
    message: str
    request_id: str | None = None


class ErrorResponse(BaseModel):
    """Standard error response envelope per API contract."""

    error: ErrorDetail
