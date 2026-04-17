# app/routers/users.py
"""User profile and subscription router."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.medical_record import MedicalRecord
from app.models.user import User
from app.schemas.user import (
    StorageStats,
    SubscriptionInfo,
    UserProfile,
    UserProfileUpdate,
)

router = APIRouter(tags=["User Profile"])


@router.get(
    "/users/me",
    response_model=UserProfile,
    summary="Get current user profile",
    description="Returns the authenticated user's profile information.",
)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
) -> UserProfile:
    """Get current user profile."""
    full_name = None
    date_of_birth = None
    gender = None
    blood_group = None

    if current_user.patient_profile:
        p = current_user.patient_profile
        full_name = p.full_name.decode("utf-8") if isinstance(p.full_name, bytes) else None
        date_of_birth = p.date_of_birth.decode("utf-8") if isinstance(p.date_of_birth, bytes) else None
        gender = p.gender
        blood_group = p.blood_group
    elif current_user.doctor_profile:
        full_name = current_user.doctor_profile.full_name

    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        phone_number=current_user.phone_number,
        is_email_verified=current_user.is_email_verified,
        mfa_enabled=current_user.mfa_enabled,
        full_name=full_name,
        date_of_birth=date_of_birth,
        gender=gender,
        blood_group=blood_group,
        created_at=current_user.created_at,
    )


@router.patch(
    "/users/me",
    response_model=UserProfile,
    summary="Update user profile",
)
async def update_profile(
    body: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserProfile:
    """Update user profile fields."""
    if body.phone_number is not None:
        current_user.phone_number = body.phone_number

    if current_user.patient_profile:
        p = current_user.patient_profile
        if body.gender is not None:
            p.gender = body.gender
        if body.blood_group is not None:
            p.blood_group = body.blood_group

    await db.flush()
    return await get_my_profile(current_user)


@router.get(
    "/users/me/storage",
    response_model=StorageStats,
    summary="Get storage usage",
    description="Returns storage usage statistics for the authenticated patient.",
)
async def get_storage_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StorageStats:
    """Get storage usage statistics."""
    if not current_user.patient_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients have storage stats",
        )

    p = current_user.patient_profile
    count_result = await db.execute(
        select(func.count(MedicalRecord.id)).where(
            MedicalRecord.patient_id == p.id,
            MedicalRecord.is_deleted == False,  # noqa: E712
        )
    )
    records_count = count_result.scalar() or 0

    usage_pct = (p.storage_used_bytes / p.storage_quota_bytes * 100) if p.storage_quota_bytes > 0 else 0

    return StorageStats(
        storage_used_bytes=p.storage_used_bytes,
        storage_quota_bytes=p.storage_quota_bytes,
        usage_percentage=round(usage_pct, 2),
        records_count=records_count,
    )

# Old subscription endpoint removed to avoid conflict

@router.get(
    "/users/me/data-export",
    summary="Export all personal data (GDPR)",
    description="Returns a full JSON export of all data held for the authenticated patient.",
)
async def export_my_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """GDPR data portability — full patient data export."""
    from datetime import datetime, timezone
    from sqlalchemy import select as sa_select

    if not current_user.patient_profile:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patients only")

    patient_id = current_user.patient_profile.id

    from app.models.medication import Medication
    from app.models.reminder import Reminder
    from app.models.appointment import Appointment

    # Fetch medications
    meds_result = await db.execute(
        sa_select(Medication).where(Medication.patient_id == patient_id)
    )
    medications = [
        {
            "name": m.name.decode("utf-8") if isinstance(m.name, bytes) else m.name,
            "dosage": m.dosage,
            "frequency": m.frequency,
            "route": m.route,
            "is_active": m.is_active,
            "start_date": str(m.start_date) if m.start_date else None,
            "prescribed_by": m.prescribed_by,
        }
        for m in meds_result.scalars().all()
    ]

    # Fetch records (metadata only — no binaries)
    records_result = await db.execute(
        sa_select(MedicalRecord).where(
            MedicalRecord.patient_id == patient_id,
            MedicalRecord.deleted_at.is_(None),
        )
    )
    records = [
        {
            "title": r.title,
            "category": r.category_slug,
            "document_date": str(r.document_date) if r.document_date else None,
            "processing_status": r.processing_status,
            "file_size_bytes": r.file_size_bytes,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records_result.scalars().all()
    ]

    # Fetch appointments
    appts_result = await db.execute(
        sa_select(Appointment).where(Appointment.patient_id == patient_id)
    )
    appointments = [
        {
            "title": a.title,
            "appointment_at": a.appointment_at.isoformat() if a.appointment_at else None,
            "location": a.location,
            "status": a.status,
        }
        for a in appts_result.scalars().all()
    ]

    # Fetch reminders
    reminders_result = await db.execute(
        sa_select(Reminder).where(Reminder.patient_id == patient_id)
    )
    reminders = [
        {
            "title": r.title,
            "reminder_type": r.reminder_type,
            "scheduled_at": r.scheduled_at.isoformat() if r.scheduled_at else None,
            "recurrence_rule": r.recurrence_rule,
            "is_active": r.is_active,
        }
        for r in reminders_result.scalars().all()
    ]

    return {
        "export_generated_at": datetime.now(timezone.utc).isoformat(),
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "role": current_user.role,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        },
        "records": records,
        "medications": medications,
        "appointments": appointments,
        "reminders": reminders,
        "total_counts": {
            "records": len(records),
            "medications": len(medications),
            "appointments": len(appointments),
            "reminders": len(reminders),
        },
    }
