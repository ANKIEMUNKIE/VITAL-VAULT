# app/routers/appointments.py
"""Appointments router — CRUD operations."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_action
from app.database import get_db
from app.dependencies import get_current_patient
from app.models.user import User
from app.repositories import appointment_repo
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentListResponse,
    AppointmentResponse,
    AppointmentUpdate,
)

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.get(
    "",
    response_model=AppointmentListResponse,
    summary="List appointments",
    description="List patient's appointments with optional status filter.",
)
async def list_appointments(
    appointment_status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_patient),
) -> AppointmentListResponse:
    """List patient's appointments."""
    appointments = await appointment_repo.list_patient_appointments(
        current_user.patient_profile.id, db, status=appointment_status
    )

    return AppointmentListResponse(
        data=[
            AppointmentResponse(
                id=a.id,
                title=a.title,
                doctor_id=a.doctor_id,
                appointment_at=a.appointment_at,
                location=a.location,
                notes=(
                    a.notes.decode("utf-8")
                    if isinstance(a.notes, bytes) and a.notes
                    else None
                ),
                status=a.status,
                reminder_sent=a.reminder_sent,
                created_at=a.created_at,
            )
            for a in appointments
        ]
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=AppointmentResponse,
    summary="Create an appointment",
)
async def create_appointment(
    body: AppointmentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_patient),
) -> AppointmentResponse:
    """Create a new appointment."""
    appointment = await appointment_repo.create_appointment(
        db,
        patient_id=current_user.patient_profile.id,
        title=body.title,
        appointment_at=body.appointment_at,
        doctor_id=body.doctor_id,
        location=body.location,
        notes=body.notes.encode("utf-8") if body.notes else None,
    )

    await log_action(
        db,
        actor_user_id=current_user.id,
        action="APPOINTMENT_CREATED",
        resource_type="Appointment",
        resource_id=appointment.id,
        ip_address=request.client.host if request.client else None,
    )

    return AppointmentResponse(
        id=appointment.id,
        title=appointment.title,
        doctor_id=appointment.doctor_id,
        appointment_at=appointment.appointment_at,
        location=appointment.location,
        notes=body.notes,
        status=appointment.status,
        reminder_sent=appointment.reminder_sent,
        created_at=appointment.created_at,
    )


@router.patch(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Update an appointment",
)
async def update_appointment(
    appointment_id: uuid.UUID,
    body: AppointmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_patient),
) -> AppointmentResponse:
    """Update appointment details or status."""
    update_kwargs = {}
    if body.title is not None:
        update_kwargs["title"] = body.title
    if body.appointment_at is not None:
        update_kwargs["appointment_at"] = body.appointment_at
    if body.location is not None:
        update_kwargs["location"] = body.location
    if body.status is not None:
        update_kwargs["status"] = body.status
    if body.notes is not None:
        update_kwargs["notes"] = body.notes.encode("utf-8")

    appointment = await appointment_repo.update_appointment(
        appointment_id,
        current_user.patient_profile.id,
        db,
        **update_kwargs,
    )
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )

    return AppointmentResponse(
        id=appointment.id,
        title=appointment.title,
        doctor_id=appointment.doctor_id,
        appointment_at=appointment.appointment_at,
        location=appointment.location,
        notes=(
            appointment.notes.decode("utf-8")
            if isinstance(appointment.notes, bytes) and appointment.notes
            else None
        ),
        status=appointment.status,
        reminder_sent=appointment.reminder_sent,
        created_at=appointment.created_at,
    )


@router.delete(
    "/{appointment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel an appointment",
)
async def delete_appointment(
    appointment_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_patient),
) -> Response:
    """Cancel/delete an appointment."""
    deleted = await appointment_repo.delete_appointment(
        appointment_id, current_user.patient_profile.id, db
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )

    await log_action(
        db,
        actor_user_id=current_user.id,
        action="APPOINTMENT_CANCELLED",
        resource_type="Appointment",
        resource_id=appointment_id,
        ip_address=request.client.host if request.client else None,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
