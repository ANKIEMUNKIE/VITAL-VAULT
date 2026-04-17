# app/dependencies.py
"""Shared FastAPI dependencies for database sessions, authentication, and role checking."""

from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.database import get_db
from app.models.user import User

# Bearer token scheme for Swagger UI
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate JWT from Authorization header, return the User.

    Raises:
        HTTPException 401: If token is missing, invalid, or user not found.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(credentials.credentials)
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
            )
        user_id = uuid.UUID(user_id_str)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)  # noqa: E712
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )

    return user


async def get_current_patient(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency that ensures the current user is a PATIENT with a profile.

    Raises:
        HTTPException 403: If user is not a patient.
        HTTPException 404: If patient profile is not found.
    """
    if current_user.role != "PATIENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can access this resource",
        )
    if current_user.patient_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found. Please complete registration.",
        )
    return current_user


async def get_current_doctor(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency that ensures the current user is a verified DOCTOR.

    Raises:
        HTTPException 403: If user is not a doctor or not verified.
    """
    if current_user.role != "DOCTOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can access this resource",
        )
    if current_user.doctor_profile is None or not current_user.doctor_profile.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor profile not verified",
        )
    return current_user
