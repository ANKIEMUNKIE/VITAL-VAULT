# app/config.py
"""Application configuration via Pydantic Settings.

All secrets and configuration are loaded from environment variables or .env file.
Never hardcode any secrets in source code.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the Vital-Vault backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    APP_NAME: str = "Vital-Vault"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"
    ALLOWED_ORIGINS: str = "http://localhost:3000,https://vital-vault.vercel.app"

    # --- JWT ---
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    JWT_ALGORITHM: str = "HS256"

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://vitalvault:vitalvault@localhost:5432/vitalvault"
    DIRECT_URL: str | None = None
    DATABASE_ENCRYPTION_KEY: str = "change-me-encryption-key"

    # --- Redis ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- Object Storage (S3 / MinIO) ---
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "vital-vault-records"
    S3_REGION: str = "us-east-1"

    # --- AI (Cerebras) ---
    CEREBRAS_API_KEY: str = ""
    CEREBRAS_API_URL: str = "https://api.cerebras.ai/v1/chat/completions"
    CEREBRAS_MODEL: str = "llama3.1-8b"

    # --- Notifications (stubs for Phase 1) ---
    SENDGRID_API_KEY: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    FCM_SERVER_KEY: str = ""

    # --- Stripe ---
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # --- Rate Limiting ---
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_AUTH: str = "10/minute"

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse comma-separated origins into a list."""
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()
