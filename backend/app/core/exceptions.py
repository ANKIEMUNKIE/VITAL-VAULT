# app/core/exceptions.py
"""Custom exception classes for Vital-Vault.

All application-level exceptions inherit from VitalVaultBaseException.
FastAPI exception handlers in main.py map these to structured HTTP error responses.
"""

from __future__ import annotations

import uuid


class VitalVaultBaseException(Exception):
    """Base exception for all Vital-Vault errors."""

    pass


class RecordNotFoundException(VitalVaultBaseException):
    """Raised when a medical record is not found or not owned by the patient."""

    def __init__(self, record_id: uuid.UUID) -> None:
        self.record_id = record_id
        super().__init__(f"Medical record {record_id} not found.")


class UserNotFoundException(VitalVaultBaseException):
    """Raised when a user is not found."""

    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        super().__init__(f"User not found: {identifier}")


class DuplicateEmailException(VitalVaultBaseException):
    """Raised when attempting to register with an existing email."""

    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"Email already registered: {email}")


class InvalidCredentialsException(VitalVaultBaseException):
    """Raised on invalid login credentials."""

    def __init__(self) -> None:
        super().__init__("Invalid email or password.")


class AccountLockedException(VitalVaultBaseException):
    """Raised when account is locked due to too many failed login attempts."""

    def __init__(self, locked_until: str) -> None:
        self.locked_until = locked_until
        super().__init__(f"Account locked until {locked_until}.")


class TokenExpiredException(VitalVaultBaseException):
    """Raised when a JWT or refresh token has expired."""

    def __init__(self) -> None:
        super().__init__("Token has expired.")


class TokenRevokedException(VitalVaultBaseException):
    """Raised when a refresh token has been revoked."""

    def __init__(self) -> None:
        super().__init__("Token has been revoked.")


class PermissionDeniedException(VitalVaultBaseException):
    """Raised when user lacks required role or ownership."""

    def __init__(self, detail: str = "Permission denied.") -> None:
        self.detail = detail
        super().__init__(detail)


class InsufficientStorageException(VitalVaultBaseException):
    """Raised when upload would exceed patient's storage quota."""

    def __init__(self, used: int, quota: int) -> None:
        self.used = used
        self.quota = quota
        super().__init__(
            f"Storage quota exceeded: {used}/{quota} bytes used."
        )


class InvalidFileTypeException(VitalVaultBaseException):
    """Raised when uploaded file type is not in the whitelist."""

    def __init__(self, mime_type: str) -> None:
        self.mime_type = mime_type
        super().__init__(f"File type not allowed: {mime_type}")


class OCRTimeoutException(VitalVaultBaseException):
    """Raised when OCR processing exceeds time limit."""

    def __init__(self, record_id: str) -> None:
        self.record_id = record_id
        super().__init__(f"OCR timeout for record {record_id}")


class AIExtractionFailedException(VitalVaultBaseException):
    """Raised when AI extraction fails."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"AI extraction failed: {reason}")


class ReminderLimitExceededException(VitalVaultBaseException):
    """Raised when user hits the maximum reminder count for their tier."""

    def __init__(self, max_reminders: int) -> None:
        self.max_reminders = max_reminders
        super().__init__(f"Maximum {max_reminders} reminders allowed for your plan.")
