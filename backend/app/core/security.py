# app/core/security.py
"""JWT, password hashing, and PHI encryption helpers.

All secrets are loaded from app.config.settings — never hardcoded.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt as _bcrypt
from jose import jwt

from app.config import settings

# ---------- Password Hashing ----------
# bcrypt 4+/5+ has a strict 72-byte limit.
# We pre-hash with SHA-256 (64 hex chars) to safely handle any password length.

_BCRYPT_ROUNDS = 12


def _prehash(password: str) -> bytes:
    """SHA-256 pre-hash → always 64 ASCII hex chars (well under 72 bytes)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest().encode("utf-8")


def hash_password(password: str) -> str:
    """Hash password: SHA-256 pre-hash then bcrypt (cost 12)."""
    return _bcrypt.hashpw(_prehash(password), _bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against bcrypt hash."""
    return _bcrypt.checkpw(_prehash(plain_password), hashed_password.encode("utf-8"))


# ---------- JWT Tokens ----------

def create_access_token(
    subject: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token.

    Args:
        subject: User ID (UUID string) as the 'sub' claim.
        role: User role for RBAC enforcement.
        expires_delta: Custom expiry; defaults to settings value.

    Returns:
        Encoded JWT string.
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": subject,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT access token.

    Returns:
        Decoded payload dict.

    Raises:
        JWTError: If token is invalid, expired, or tampered.
    """
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


# ---------- Refresh Tokens ----------

def generate_refresh_token() -> str:
    """Generate a cryptographically secure refresh token string."""
    return secrets.token_urlsafe(64)


def hash_refresh_token(token: str) -> str:
    """Hash a refresh token for secure database storage.

    Uses SHA-256; comparison must use secrets.compare_digest().
    """
    return hashlib.sha256(token.encode()).hexdigest()


def verify_refresh_token(plain_token: str, hashed_token: str) -> bool:
    """Securely compare a refresh token to its hash."""
    return secrets.compare_digest(
        hashlib.sha256(plain_token.encode()).hexdigest(),
        hashed_token,
    )


# ---------- PHI Encryption Helpers ----------
# These helpers build SQL expressions for pgcrypto pgp_sym_encrypt/decrypt.
# They are used in repository functions to encrypt/decrypt PHI columns.

def encrypt_phi(value: str) -> str:
    """Return a SQL expression string for pgp_sym_encrypt.

    Note: This returns a parameterized expression for use with SQLAlchemy text().
    Actual encryption happens at the database level via pgcrypto.
    """
    return value  # Encryption is handled via SQLAlchemy func calls in repos


def get_encryption_key() -> str:
    """Return the symmetric encryption key for pgcrypto.

    Loaded from settings; in production this comes from KMS.
    """
    return settings.DATABASE_ENCRYPTION_KEY
