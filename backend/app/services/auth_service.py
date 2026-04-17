# app/services/auth_service.py
"""Authentication business logic.

Handles registration, login with lockout, token management, and MFA.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import (
    AccountLockedException,
    DuplicateEmailException,
    InvalidCredentialsException,
    TokenExpiredException,
    TokenRevokedException,
)
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
    verify_refresh_token,
)
from app.models.patient import PatientProfile
from app.models.doctor import DoctorProfile
from app.repositories import user_repo


# Account lockout thresholds (progressive)
LOCKOUT_THRESHOLDS = [
    (5, timedelta(minutes=15)),
    (10, timedelta(minutes=30)),
    (15, timedelta(minutes=120)),
]


class AuthService:
    """Service handling all authentication operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register(
        self,
        *,
        email: str,
        password: str,
        role: str,
        full_name: str,
        date_of_birth: str,
        phone_number: str | None = None,
        license_number: str | None = None,
        specialization: str | None = None,
    ) -> dict:
        """Register a new user with profile creation.

        Args:
            email: User email.
            password: Plaintext password (will be hashed).
            role: PATIENT or DOCTOR.
            full_name: User's full name.
            date_of_birth: Date of birth as ISO8601 string.
            phone_number: Optional phone number.
            license_number: Required for DOCTOR role.
            specialization: Required for DOCTOR role.

        Returns:
            Dict with user_id, email, role, and confirmation message.

        Raises:
            DuplicateEmailException: If email already exists.
        """
        existing = await user_repo.get_user_by_email(email, self.db)
        if existing:
            raise DuplicateEmailException(email)

        hashed = hash_password(password)
        user = await user_repo.create_user(
            self.db,
            email=email,
            password_hash=hashed,
            role=role,
            phone_number=phone_number,
        )

        # Create role-specific profile
        if role == "PATIENT":
            profile = PatientProfile(
                user_id=user.id,
                full_name=full_name.encode("utf-8"),
                date_of_birth=date_of_birth.encode("utf-8"),
            )
            self.db.add(profile)

        elif role == "DOCTOR":
            profile = DoctorProfile(
                user_id=user.id,
                full_name=full_name,
                license_number=license_number or "",
                specialization=specialization or "",
            )
            self.db.add(profile)

        # Create a default Free subscription
        from app.models.subscription import Subscription
        from sqlalchemy import select
        from app.models.subscription import SubscriptionTier

        tier_result = await self.db.execute(
            select(SubscriptionTier).where(SubscriptionTier.slug == "free")
        )
        free_tier = tier_result.scalar_one_or_none()
        if free_tier:
            sub = Subscription(user_id=user.id, tier_id=free_tier.id)
            self.db.add(sub)

        await self.db.flush()

        return {
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
        }

    async def login(
        self,
        *,
        email: str,
        password: str,
    ) -> dict:
        """Authenticate a user and return tokens.

        Implements progressive account lockout on failed attempts.

        Args:
            email: User email.
            password: Plaintext password.

        Returns:
            Dict with access_token, refresh_token, expires_in, and user info.

        Raises:
            InvalidCredentialsException: On wrong email or password.
            AccountLockedException: If account is locked due to failed attempts.
        """
        user = await user_repo.get_user_by_email(email, self.db)
        if not user:
            raise InvalidCredentialsException()

        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            raise AccountLockedException(user.locked_until.isoformat())

        # Verify password
        if not verify_password(password, user.password_hash):
            # Determine lockout duration based on failed count
            locked_until = None
            for threshold, duration in LOCKOUT_THRESHOLDS:
                if user.failed_login_count + 1 >= threshold:
                    locked_until = datetime.now(timezone.utc) + duration

            await user_repo.increment_failed_login(
                user.id, self.db, locked_until=locked_until
            )
            raise InvalidCredentialsException()

        # Success — generate tokens
        access_token = create_access_token(
            subject=str(user.id),
            role=user.role,
        )

        raw_refresh = generate_refresh_token()
        hashed_refresh = hash_refresh_token(raw_refresh)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        await user_repo.store_refresh_token(
            self.db,
            user_id=user.id,
            token_hash=hashed_refresh,
            expires_at=expires_at,
        )

        await user_repo.update_last_login(user.id, self.db)

        return {
            "access_token": access_token,
            "refresh_token": raw_refresh,
            "token_type": "Bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "role": user.role,
                "email": user.email,
            },
        }

    async def refresh_token(self, *, refresh_token: str) -> dict:
        """Issue a new access token using a valid refresh token.

        Args:
            refresh_token: Raw refresh token string.

        Returns:
            Dict with new access_token and expires_in.

        Raises:
            TokenExpiredException: If refresh token is expired.
            TokenRevokedException: If refresh token has been revoked.
        """
        hashed = hash_refresh_token(refresh_token)
        token_record = await user_repo.get_refresh_token_by_hash(hashed, self.db)

        if not token_record:
            raise TokenRevokedException()

        if token_record.expires_at < datetime.now(timezone.utc):
            raise TokenExpiredException()

        user = await user_repo.get_user_by_id(token_record.user_id, self.db)
        if not user:
            raise TokenRevokedException()

        access_token = create_access_token(
            subject=str(user.id),
            role=user.role,
        )

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def logout(self, *, refresh_token: str) -> None:
        """Revoke a refresh token on logout.

        Args:
            refresh_token: Raw refresh token string.
        """
        hashed = hash_refresh_token(refresh_token)
        token_record = await user_repo.get_refresh_token_by_hash(hashed, self.db)
        if token_record:
            await user_repo.revoke_refresh_token(token_record.id, self.db)
