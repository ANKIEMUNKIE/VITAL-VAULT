# app/routers/auth.py
"""Authentication router — register, login, refresh, logout."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_action
from app.core.exceptions import (
    AccountLockedException,
    DuplicateEmailException,
    InvalidCredentialsException,
    TokenExpiredException,
    TokenRevokedException,
)
from app.database import get_db
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=RegisterResponse,
    summary="Register a new user",
    description="Create a new PATIENT or DOCTOR account with profile. Rate limited: 3/minute per IP.",
)
async def register(
    body: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> RegisterResponse:
    """Register a new user account."""
    try:
        service = AuthService(db)
        result = await service.register(
            email=body.email,
            password=body.password,
            role=body.role,
            full_name=body.full_name,
            date_of_birth=body.date_of_birth,
            phone_number=body.phone_number,
            license_number=body.license_number,
            specialization=body.specialization,
        )

        await log_action(
            db,
            actor_user_id=result["user_id"],
            action="USER_REGISTERED",
            resource_type="User",
            resource_id=result["user_id"],
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        return RegisterResponse(**result)

    except DuplicateEmailException:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Authenticate and obtain tokens",
    description="Login with email and password. Rate limited: 5/minute per IP.",
)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Authenticate user and return tokens."""
    try:
        service = AuthService(db)
        result = await service.login(email=body.email, password=body.password)

        await log_action(
            db,
            actor_user_id=result["user"]["id"],
            action="USER_LOGIN",
            resource_type="User",
            resource_id=result["user"]["id"],
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        return LoginResponse(**result)

    except InvalidCredentialsException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    except AccountLockedException as e:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=str(e),
        )


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new access token.",
)
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> RefreshResponse:
    """Refresh an access token."""
    try:
        service = AuthService(db)
        result = await service.refresh_token(refresh_token=body.refresh_token)
        return RefreshResponse(**result)

    except (TokenExpiredException, TokenRevokedException):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout and revoke refresh token",
    description="Revoke the provided refresh token server-side.",
)
async def logout(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Revoke refresh token on logout."""
    service = AuthService(db)
    await service.logout(refresh_token=body.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
