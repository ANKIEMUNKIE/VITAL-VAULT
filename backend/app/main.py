# app/main.py
"""FastAPI application factory with middleware, exception handlers, and router registration."""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.exceptions import (
    AccountLockedException,
    DuplicateEmailException,
    InsufficientStorageException,
    InvalidCredentialsException,
    InvalidFileTypeException,
    PermissionDeniedException,
    RecordNotFoundException,
    ReminderLimitExceededException,
    TokenExpiredException,
    TokenRevokedException,
    VitalVaultBaseException,
)

# Configure logging — never log PHI
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    """Application lifespan: startup and shutdown events."""
    logger.info("Vital-Vault API starting up (%s)", settings.APP_ENV)

    # Ensure S3 bucket exists on startup
    try:
        from app.core.storage import ensure_bucket_exists

        ensure_bucket_exists()
    except Exception:
        logger.warning("Could not ensure S3 bucket exists — MinIO may not be running")

    yield

    logger.info("Vital-Vault API shutting down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description="HIPAA/GDPR-compliant Digital Medical Locker API",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # --- CORS Middleware ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Request ID Middleware ---
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # --- Security Headers Middleware ---
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        return response

    # --- Global Exception Handlers ---
    @app.exception_handler(RecordNotFoundException)
    async def record_not_found_handler(request: Request, exc: RecordNotFoundException) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": "RECORD_NOT_FOUND",
                    "message": str(exc),
                    "request_id": getattr(request.state, "request_id", None),
                }
            },
        )

    @app.exception_handler(PermissionDeniedException)
    async def permission_denied_handler(request: Request, exc: PermissionDeniedException) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": {
                    "code": "PERMISSION_DENIED",
                    "message": str(exc),
                    "request_id": getattr(request.state, "request_id", None),
                }
            },
        )

    @app.exception_handler(InvalidCredentialsException)
    async def invalid_creds_handler(request: Request, exc: InvalidCredentialsException) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": str(exc),
                    "request_id": getattr(request.state, "request_id", None),
                }
            },
        )

    @app.exception_handler(DuplicateEmailException)
    async def duplicate_email_handler(request: Request, exc: DuplicateEmailException) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": {
                    "code": "DUPLICATE_EMAIL",
                    "message": str(exc),
                    "request_id": getattr(request.state, "request_id", None),
                }
            },
        )

    @app.exception_handler(InsufficientStorageException)
    async def storage_handler(request: Request, exc: InsufficientStorageException) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={
                "error": {
                    "code": "STORAGE_QUOTA_EXCEEDED",
                    "message": str(exc),
                    "request_id": getattr(request.state, "request_id", None),
                }
            },
        )

    @app.exception_handler(VitalVaultBaseException)
    async def base_exception_handler(request: Request, exc: VitalVaultBaseException) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(exc),
                    "request_id": getattr(request.state, "request_id", None),
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request data",
                    "details": exc.errors(),
                    "request_id": getattr(request.state, "request_id", None),
                }
            },
        )

    # --- Register Routers ---
    from app.routers import (
        admin,
        appointments,
        auth,
        medications,
        records,
        reminders,
        subscriptions,
        timeline,
        users,
    )

    api_prefix = "/api/v1"
    app.include_router(auth.router, prefix=api_prefix)
    app.include_router(records.router, prefix=api_prefix)
    app.include_router(timeline.router, prefix=api_prefix)
    app.include_router(reminders.router, prefix=api_prefix)
    app.include_router(medications.router, prefix=api_prefix)
    app.include_router(appointments.router, prefix=api_prefix)
    app.include_router(users.router, prefix=api_prefix)
    app.include_router(admin.router, prefix=api_prefix)
    app.include_router(subscriptions.router, prefix=api_prefix)

    # --- Health Check ---
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict:
        return {"status": "healthy", "version": "1.0.0"}

    return app


# Create the app instance
app = create_app()
