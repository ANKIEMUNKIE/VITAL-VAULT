# app/core/rbac.py
"""Role-Based Access Control (RBAC) enforcement dependencies.

Usage in routers:
    @router.get("/admin/users")
    async def list_users(user=Depends(require_role("ADMIN"))):
        ...
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from fastapi import Depends, HTTPException, status


class UserRole(StrEnum):
    """Supported user roles."""

    PATIENT = "PATIENT"
    DOCTOR = "DOCTOR"
    ADMIN = "ADMIN"
    CLINIC_ADMIN = "CLINIC_ADMIN"


def require_role(*roles: str) -> Any:
    """FastAPI dependency factory that enforces role-based access.

    Args:
        *roles: One or more allowed role strings.

    Returns:
        A FastAPI dependency that checks the current user's role.

    Raises:
        HTTPException 403 if the user's role is not in the allowed set.
    """
    from app.dependencies import get_current_user

    async def _role_checker(
        current_user: Any = Depends(get_current_user),
    ) -> Any:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {', '.join(roles)}",
            )
        return current_user

    return _role_checker
