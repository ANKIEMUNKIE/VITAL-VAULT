# app/models/__init__.py
"""SQLAlchemy ORM models — barrel export for Alembic autogenerate discovery."""

from __future__ import annotations

from app.models.base import Base
from app.models.user import User, RefreshToken
from app.models.patient import PatientProfile
from app.models.doctor import DoctorProfile
from app.models.category import DocumentCategory
from app.models.medical_record import MedicalRecord, RecordExtraction
from app.models.medication import Medication
from app.models.reminder import Reminder
from app.models.appointment import Appointment
from app.models.subscription import SubscriptionTier, Subscription
from app.models.audit import AuditLog
from app.models.clinic import Clinic, ClinicMembership

__all__ = [
    "Base",
    "User",
    "RefreshToken",
    "PatientProfile",
    "DoctorProfile",
    "DocumentCategory",
    "MedicalRecord",
    "RecordExtraction",
    "Medication",
    "Reminder",
    "Appointment",
    "SubscriptionTier",
    "Subscription",
    "AuditLog",
    "Clinic",
    "ClinicMembership",
]
