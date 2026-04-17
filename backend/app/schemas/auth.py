# app/schemas/auth.py
"""Pydantic v2 schemas for authentication endpoints."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    """POST /auth/register request body."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(default="PATIENT", pattern="^(PATIENT|DOCTOR)$")
    full_name: str = Field(..., min_length=1, max_length=200)
    date_of_birth: str = Field(
        ..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="ISO8601 date"
    )
    phone_number: str | None = None
    # Doctor-specific fields (required if role=DOCTOR)
    license_number: str | None = None
    specialization: str | None = None


class RegisterResponse(BaseModel):
    """POST /auth/register response body."""

    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    email: str
    role: str
    message: str = "Verification email sent."


class LoginRequest(BaseModel):
    """POST /auth/login request body."""

    email: EmailStr
    password: str


class UserInfo(BaseModel):
    """User info included in login response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    email: str


class LoginResponse(BaseModel):
    """POST /auth/login response body."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserInfo


class RefreshRequest(BaseModel):
    """POST /auth/refresh request body."""

    refresh_token: str


class RefreshResponse(BaseModel):
    """POST /auth/refresh response body."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int
