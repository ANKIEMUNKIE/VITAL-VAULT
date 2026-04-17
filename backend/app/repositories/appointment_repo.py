# app/repositories/appointment_repo.py
"""Database query layer for Appointment model."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment


async def create_appointment(
    db: AsyncSession,
    *,
    patient_id: uuid.UUID,
    title: str,
    appointment_at: datetime,
    doctor_id: uuid.UUID | None = None,
    location: str | None = None,
    notes: bytes | None = None,
    source_record_id: uuid.UUID | None = None,
) -> Appointment:
    """Create a new appointment."""
    appointment = Appointment(
        patient_id=patient_id,
        title=title,
        appointment_at=appointment_at,
        doctor_id=doctor_id,
        location=location,
        notes=notes,
        source_record_id=source_record_id,
    )
    db.add(appointment)
    await db.flush()
    return appointment


async def list_patient_appointments(
    patient_id: uuid.UUID,
    db: AsyncSession,
    *,
    status: str | None = None,
    from_date: date | None = None,
) -> list[Appointment]:
    """List appointments for a patient with optional filters."""
    query = select(Appointment).where(Appointment.patient_id == patient_id)
    if status:
        query = query.where(Appointment.status == status)
    if from_date:
        query = query.where(Appointment.appointment_at >= datetime.combine(from_date, datetime.min.time()))
    query = query.order_by(Appointment.appointment_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_appointment_for_patient(
    appointment_id: uuid.UUID,
    patient_id: uuid.UUID,
    db: AsyncSession,
) -> Appointment | None:
    """Fetch appointment with ownership check."""
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.patient_id == patient_id,
        )
    )
    return result.scalar_one_or_none()


async def update_appointment(
    appointment_id: uuid.UUID,
    patient_id: uuid.UUID,
    db: AsyncSession,
    **kwargs: ...,
) -> Appointment | None:
    """Update appointment fields."""
    values = {k: v for k, v in kwargs.items() if v is not None}
    if not values:
        return await get_appointment_for_patient(appointment_id, patient_id, db)

    await db.execute(
        update(Appointment)
        .where(Appointment.id == appointment_id, Appointment.patient_id == patient_id)
        .values(**values)
    )
    return await get_appointment_for_patient(appointment_id, patient_id, db)


async def delete_appointment(
    appointment_id: uuid.UUID,
    patient_id: uuid.UUID,
    db: AsyncSession,
) -> bool:
    """Cancel/delete an appointment. Returns True if deleted."""
    result = await db.execute(
        delete(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.patient_id == patient_id,
        )
    )
    return result.rowcount > 0  # type: ignore[union-attr]
