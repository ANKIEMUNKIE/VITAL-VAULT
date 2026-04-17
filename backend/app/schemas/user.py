# app/schemas/user.py
"""Pydantic v2 schemas for user and subscription endpoints."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class UserProfile(BaseModel):
    """GET /users/me response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    role: str
    phone_number: str | None = None
    is_email_verified: bool
    mfa_enabled: bool
    full_name: str | None = None  # Decrypted from patient/doctor profile
    date_of_birth: str | None = None
    gender: str | None = None
    blood_group: str | None = None
    created_at: datetime


class UserProfileUpdate(BaseModel):
    """PATCH /users/me request body."""

    phone_number: str | None = None
    gender: str | None = None
    blood_group: str | None = None
    emergency_contact: dict | None = None


class StorageStats(BaseModel):
    """GET /users/me/storage response."""

    storage_used_bytes: int
    storage_quota_bytes: int
    usage_percentage: float
    records_count: int


class SubscriptionInfo(BaseModel):
    """GET /subscriptions/me response."""

    model_config = ConfigDict(from_attributes=True)

    tier_slug: str
    tier_label: str
    status: str
    storage_quota_bytes: int
    max_reminders: int | None = None
    ai_summaries_enabled: bool
    price_monthly_cents: int
    current_period_end: date | None = None
