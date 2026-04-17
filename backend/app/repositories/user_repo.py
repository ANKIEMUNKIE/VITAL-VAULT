# app/repositories/user_repo.py
"""Database query layer for User and RefreshToken models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import RefreshToken, User


async def get_user_by_email(
    email: str,
    db: AsyncSession,
) -> User | None:
    """Fetch a user by email address.

    Args:
        email: The email to look up.
        db: Async database session.

    Returns:
        User instance or None.
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(
    user_id: uuid.UUID,
    db: AsyncSession,
) -> User | None:
    """Fetch a user by UUID.

    Args:
        user_id: The user's UUID.
        db: Async database session.

    Returns:
        User instance or None.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    *,
    email: str,
    password_hash: str,
    role: str,
    phone_number: str | None = None,
) -> User:
    """Create a new user.

    Args:
        db: Async database session.
        email: User email.
        password_hash: Bcrypt-hashed password.
        role: User role string.
        phone_number: Optional phone number.

    Returns:
        The created User instance.
    """
    user = User(
        email=email,
        password_hash=password_hash,
        role=role,
        phone_number=phone_number,
    )
    db.add(user)
    await db.flush()
    return user


async def update_last_login(
    user_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Update the last_login_at timestamp and reset failed_login_count."""
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            last_login_at=datetime.now(timezone.utc),
            failed_login_count=0,
            locked_until=None,
        )
    )


async def increment_failed_login(
    user_id: uuid.UUID,
    db: AsyncSession,
    locked_until: datetime | None = None,
) -> None:
    """Increment failed login count and optionally lock the account."""
    stmt = (
        update(User)
        .where(User.id == user_id)
        .values(
            failed_login_count=User.failed_login_count + 1,
            locked_until=locked_until,
        )
    )
    await db.execute(stmt)


# ---------- Refresh Tokens ----------

async def store_refresh_token(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    token_hash: str,
    expires_at: datetime,
) -> RefreshToken:
    """Store a hashed refresh token in the database."""
    token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(token)
    await db.flush()
    return token


async def get_refresh_token_by_hash(
    token_hash: str,
    db: AsyncSession,
) -> RefreshToken | None:
    """Fetch a refresh token by its hash."""
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False,  # noqa: E712
        )
    )
    return result.scalar_one_or_none()


async def revoke_refresh_token(
    token_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Mark a refresh token as revoked."""
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.id == token_id)
        .values(is_revoked=True)
    )


async def revoke_all_user_tokens(
    user_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Revoke all refresh tokens for a user (e.g., on password change)."""
    await db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False,  # noqa: E712
        )
        .values(is_revoked=True)
    )
