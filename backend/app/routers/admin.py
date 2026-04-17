# app/routers/admin.py
"""Admin and doctor-specific endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_doctor
from app.models.medical_record import MedicalRecord
from app.models.user import User

router = APIRouter(tags=["Doctor / Admin"])


@router.get(
    "/doctor/patients",
    summary="List doctor's patients",
    description="Returns patients who have shared records with this doctor.",
)
async def list_doctor_patients(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
) -> dict:
    """List patients who have shared records with the authenticated doctor."""
    # Find records shared with this doctor
    result = await db.execute(
        select(MedicalRecord.patient_id)
        .where(
            MedicalRecord.shared_with_doctor.any(current_user.id),  # type: ignore[attr-defined]
            MedicalRecord.is_deleted == False,  # noqa: E712
        )
        .distinct()
    )
    patient_ids = list(result.scalars().all())

    return {
        "patients": [{"patient_id": str(pid)} for pid in patient_ids],
        "total": len(patient_ids),
    }
