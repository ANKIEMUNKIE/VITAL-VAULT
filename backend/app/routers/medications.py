# app/routers/medications.py
"""Medications router — CRUD operations for patient medication list."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_action
from app.database import get_db
from app.dependencies import get_current_patient
from app.models.user import User
from app.repositories import medication_repo
from app.schemas.medication import (
    MedicationCreate,
    MedicationListResponse,
    MedicationResponse,
    MedicationUpdate,
)

router = APIRouter(prefix="/medications", tags=["Medications"])


@router.get(
    "",
    response_model=MedicationListResponse,
    summary="List medications",
    description="List patient's medications. Defaults to active only.",
)
async def list_medications(
    active: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_patient),
) -> MedicationListResponse:
    """List patient's medications."""
    meds = await medication_repo.list_patient_medications(
        current_user.patient_profile.id, db, active_only=active
    )

    return MedicationListResponse(
        data=[
            MedicationResponse(
                id=m.id,
                name=m.name.decode("utf-8") if isinstance(m.name, bytes) else m.name,
                generic_name=(
                    m.generic_name.decode("utf-8")
                    if isinstance(m.generic_name, bytes) and m.generic_name
                    else None
                ),
                dosage=m.dosage,
                frequency=m.frequency,
                route=m.route,
                start_date=m.start_date,
                end_date=m.end_date,
                is_active=m.is_active,
                prescribed_by=m.prescribed_by,
                notes=(
                    m.notes.decode("utf-8")
                    if isinstance(m.notes, bytes) and m.notes
                    else None
                ),
                source_record_id=m.source_record_id,
                created_at=m.created_at,
            )
            for m in meds
        ]
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=MedicationResponse,
    summary="Create a medication entry",
    description="Manually create a medication entry.",
)
async def create_medication(
    body: MedicationCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_patient),
) -> MedicationResponse:
    """Create a new medication entry."""
    med = await medication_repo.create_medication(
        db,
        patient_id=current_user.patient_profile.id,
        name=body.name.encode("utf-8"),
        generic_name=body.generic_name.encode("utf-8") if body.generic_name else None,
        dosage=body.dosage,
        frequency=body.frequency,
        route=body.route,
        start_date=body.start_date,
        end_date=body.end_date,
        prescribed_by=body.prescribed_by,
        notes=body.notes.encode("utf-8") if body.notes else None,
        source_record_id=body.source_record_id,
    )

    await log_action(
        db,
        actor_user_id=current_user.id,
        action="MEDICATION_CREATED",
        resource_type="Medication",
        resource_id=med.id,
        ip_address=request.client.host if request.client else None,
    )

    return MedicationResponse(
        id=med.id,
        name=body.name,
        generic_name=body.generic_name,
        dosage=med.dosage,
        frequency=med.frequency,
        route=med.route,
        start_date=med.start_date,
        end_date=med.end_date,
        is_active=med.is_active,
        prescribed_by=med.prescribed_by,
        notes=body.notes,
        source_record_id=med.source_record_id,
        created_at=med.created_at,
    )


@router.patch(
    "/{medication_id}",
    response_model=MedicationResponse,
    summary="Update a medication",
    description="Update medication fields including is_active.",
)
async def update_medication(
    medication_id: uuid.UUID,
    body: MedicationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_patient),
) -> MedicationResponse:
    """Update a medication."""
    update_kwargs = {}
    if body.name is not None:
        update_kwargs["name"] = body.name.encode("utf-8")
    if body.generic_name is not None:
        update_kwargs["generic_name"] = body.generic_name.encode("utf-8")
    if body.dosage is not None:
        update_kwargs["dosage"] = body.dosage
    if body.frequency is not None:
        update_kwargs["frequency"] = body.frequency
    if body.route is not None:
        update_kwargs["route"] = body.route
    if body.is_active is not None:
        update_kwargs["is_active"] = body.is_active
    if body.notes is not None:
        update_kwargs["notes"] = body.notes.encode("utf-8")

    med = await medication_repo.update_medication(
        medication_id,
        current_user.patient_profile.id,
        db,
        **update_kwargs,
    )
    if not med:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found",
        )

    return MedicationResponse(
        id=med.id,
        name=med.name.decode("utf-8") if isinstance(med.name, bytes) else med.name,
        generic_name=(
            med.generic_name.decode("utf-8")
            if isinstance(med.generic_name, bytes) and med.generic_name
            else None
        ),
        dosage=med.dosage,
        frequency=med.frequency,
        route=med.route,
        start_date=med.start_date,
        end_date=med.end_date,
        is_active=med.is_active,
        prescribed_by=med.prescribed_by,
        notes=(
            med.notes.decode("utf-8")
            if isinstance(med.notes, bytes) and med.notes
            else None
        ),
        source_record_id=med.source_record_id,
        created_at=med.created_at,
    )
