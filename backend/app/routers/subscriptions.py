# app/routers/subscriptions.py
"""Subscriptions router — tier info, usage stats, upgrade prompts."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_patient
from app.models.user import User

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


TIER_LIMITS = {
    "FREE": {
        "max_records": 10,
        "max_storage_mb": 512,
        "max_reminders": 5,
        "max_shared_doctors": 1,
        "ai_extractions_per_month": 10,
        "features": ["Basic OCR", "AI Extraction", "1 Doctor Share"],
    },
    "PRO": {
        "max_records": 200,
        "max_storage_mb": 5120,
        "max_reminders": 50,
        "max_shared_doctors": 10,
        "ai_extractions_per_month": 100,
        "features": ["Unlimited OCR", "Advanced AI", "10 Doctor Shares", "Priority Processing", "Data Export"],
    },
    "ENTERPRISE": {
        "max_records": -1,
        "max_storage_mb": -1,
        "max_reminders": -1,
        "max_shared_doctors": -1,
        "ai_extractions_per_month": -1,
        "features": ["Unlimited Everything", "HIPAA BAA", "Dedicated Support", "Custom Integrations"],
    },
}


@router.get(
    "/me",
    summary="Get current subscription",
    description="Returns the user's active subscription tier, limits, and usage.",
)
async def get_my_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_patient),
) -> dict:
    """Return subscription tier and current usage for the authenticated user."""
    from app.models.medical_record import MedicalRecord
    from app.models.reminder import Reminder
    from sqlalchemy import func, select

    patient_id = current_user.patient_profile.id

    # Determine tier from subscription table (default FREE)
    tier = "FREE"
    try:
        from app.models.subscription import Subscription
        result = await db.execute(
            select(Subscription)
            .where(
                Subscription.patient_id == patient_id,
                Subscription.is_active == True,  # noqa: E712
            )
        )
        sub = result.scalar_one_or_none()
        if sub:
            tier = sub.tier
    except Exception:
        pass  # Model may not exist yet — default to FREE

    limits = TIER_LIMITS.get(tier, TIER_LIMITS["FREE"])

    # Count current usage
    records_result = await db.execute(
        select(func.count(MedicalRecord.id)).where(
            MedicalRecord.patient_id == patient_id,
            MedicalRecord.deleted_at.is_(None),
        )
    )
    record_count = records_result.scalar() or 0

    reminders_result = await db.execute(
        select(func.count(Reminder.id)).where(
            Reminder.patient_id == patient_id,
            Reminder.is_active == True,  # noqa: E712
        )
    )
    reminder_count = reminders_result.scalar() or 0

    # Storage bytes used
    storage_result = await db.execute(
        select(func.sum(MedicalRecord.file_size_bytes)).where(
            MedicalRecord.patient_id == patient_id,
            MedicalRecord.deleted_at.is_(None),
        )
    )
    storage_bytes = storage_result.scalar() or 0
    storage_mb = round(storage_bytes / (1024 * 1024), 2)

    return {
        "tier": tier,
        "limits": limits,
        "usage": {
            "records": record_count,
            "reminders": reminder_count,
            "storage_mb": storage_mb,
        },
        "percentages": {
            "records": min(100, round(record_count / limits["max_records"] * 100, 1)) if limits["max_records"] > 0 else 0,
            "storage": min(100, round(storage_mb / limits["max_storage_mb"] * 100, 1)) if limits["max_storage_mb"] > 0 else 0,
            "reminders": min(100, round(reminder_count / limits["max_reminders"] * 100, 1)) if limits["max_reminders"] > 0 else 0,
        },
    }
