# app/repositories/medication_repo.py
"""Database query layer for Medication model."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medication import Medication


async def create_medication(
    db: AsyncSession,
    *,
    patient_id: uuid.UUID,
    name: bytes,
    generic_name: bytes | None = None,
    dosage: str | None = None,
    frequency: str | None = None,
    route: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    prescribed_by: str | None = None,
    notes: bytes | None = None,
    source_record_id: uuid.UUID | None = None,
) -> Medication:
    """Create a new medication entry for a patient."""
    medication = Medication(
        patient_id=patient_id,
        name=name,
        generic_name=generic_name,
        dosage=dosage,
        frequency=frequency,
        route=route,
        start_date=start_date,
        end_date=end_date,
        prescribed_by=prescribed_by,
        notes=notes,
        source_record_id=source_record_id,
    )
    db.add(medication)
    await db.flush()
    return medication


async def list_patient_medications(
    patient_id: uuid.UUID,
    db: AsyncSession,
    *,
    active_only: bool = True,
) -> list[Medication]:
    """List medications for a patient.

    Args:
        patient_id: Owner patient profile ID.
        db: Async database session.
        active_only: If True, only return active medications.

    Returns:
        List of Medication instances.
    """
    query = select(Medication).where(Medication.patient_id == patient_id)
    if active_only:
        query = query.where(Medication.is_active == True)  # noqa: E712
    query = query.order_by(Medication.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_medication_for_patient(
    medication_id: uuid.UUID,
    patient_id: uuid.UUID,
    db: AsyncSession,
) -> Medication | None:
    """Fetch a medication with patient ownership check."""
    result = await db.execute(
        select(Medication).where(
            Medication.id == medication_id,
            Medication.patient_id == patient_id,
        )
    )
    return result.scalar_one_or_none()


async def update_medication(
    medication_id: uuid.UUID,
    patient_id: uuid.UUID,
    db: AsyncSession,
    **kwargs: ...,
) -> Medication | None:
    """Update a medication's fields."""
    values = {k: v for k, v in kwargs.items() if v is not None}
    if not values:
        return await get_medication_for_patient(medication_id, patient_id, db)

    await db.execute(
        update(Medication)
        .where(Medication.id == medication_id, Medication.patient_id == patient_id)
        .values(**values)
    )
    return await get_medication_for_patient(medication_id, patient_id, db)
