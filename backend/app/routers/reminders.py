# app/routers/reminders.py
"""Reminders router — CRUD operations for medication and appointment reminders."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_action
from app.database import get_db
from app.dependencies import get_current_patient
from app.models.user import User
from app.repositories import reminder_repo
from app.schemas.reminder import (
    ReminderCreate,
    ReminderListResponse,
    ReminderResponse,
    ReminderUpdate,
)

router = APIRouter(prefix="/reminders", tags=["Reminders"])


@router.get(
    "",
    response_model=ReminderListResponse,
    summary="List reminders",
    description="List all reminders for the authenticated patient.",
)
async def list_reminders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_patient),
) -> ReminderListResponse:
    """List patient's reminders."""
    reminders = await reminder_repo.list_patient_reminders(
        current_user.patient_profile.id, db
    )
    return ReminderListResponse(
        data=[ReminderResponse.model_validate(r) for r in reminders]
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ReminderResponse,
    summary="Create a reminder",
    description="Create a new medication, appointment, or custom reminder.",
)
async def create_reminder(
    body: ReminderCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_patient),
) -> ReminderResponse:
    """Create a new reminder."""
    reminder = await reminder_repo.create_reminder(
        db,
        patient_id=current_user.patient_profile.id,
        title=body.title,
        reminder_type=body.reminder_type,
        scheduled_at=body.scheduled_at,
        medication_id=body.medication_id,
        record_id=body.record_id,
        body=body.body,
        recurrence_rule=body.recurrence_rule,
        delivery_channels=body.delivery_channels,
    )

    await log_action(
        db,
        actor_user_id=current_user.id,
        action="REMINDER_CREATED",
        resource_type="Reminder",
        resource_id=reminder.id,
        ip_address=request.client.host if request.client else None,
    )

    return ReminderResponse.model_validate(reminder)


@router.patch(
    "/{reminder_id}",
    response_model=ReminderResponse,
    summary="Update a reminder",
    description="Update reminder title, schedule, or active status.",
)
async def update_reminder(
    reminder_id: uuid.UUID,
    body: ReminderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_patient),
) -> ReminderResponse:
    """Update an existing reminder."""
    reminder = await reminder_repo.update_reminder(
        reminder_id,
        current_user.patient_profile.id,
        db,
        title=body.title,
        scheduled_at=body.scheduled_at,
        recurrence_rule=body.recurrence_rule,
        is_active=body.is_active,
        delivery_channels=body.delivery_channels,
        body=body.body,
    )
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found",
        )
    return ReminderResponse.model_validate(reminder)


@router.delete(
    "/{reminder_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a reminder",
)
async def delete_reminder(
    reminder_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_patient),
) -> Response:
    """Delete a reminder."""
    deleted = await reminder_repo.delete_reminder(
        reminder_id, current_user.patient_profile.id, db
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found",
        )

    await log_action(
        db,
        actor_user_id=current_user.id,
        action="REMINDER_DELETED",
        resource_type="Reminder",
        resource_id=reminder_id,
        ip_address=request.client.host if request.client else None,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
