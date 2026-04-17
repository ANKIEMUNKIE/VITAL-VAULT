# app/routers/records.py
"""Medical records router — upload, list, detail, status, delete, share."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_action
from app.core.exceptions import (
    InsufficientStorageException,
    InvalidFileTypeException,
    RecordNotFoundException,
)
from app.database import get_db
from app.dependencies import get_current_patient
from app.models.user import User
from app.repositories import record_repo
from app.schemas.common import PaginationMeta
from app.schemas.record import (
    ExtractionPatchRequest,
    RecordDetailResponse,
    RecordListItem,
    RecordListResponse,
    RecordStatusResponse,
    RecordUploadResponse,
    ShareRecordRequest,
)
from app.services.record_service import RecordService

router = APIRouter(prefix="/records", tags=["Medical Records"])


@router.post(
    "/upload",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=RecordUploadResponse,
    summary="Upload a medical document",
    description="Upload a PDF or image. Returns immediately; AI processing is async.",
)
async def upload_record(
    request: Request,
    file: UploadFile = File(...),
    title: str | None = Form(None),
    category_slug: str | None = Form(None),
    document_date: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_patient),
) -> RecordUploadResponse:
    """Upload a medical document for async AI processing."""
    try:
        doc_date = None
        if document_date:
            doc_date = date.fromisoformat(document_date)

        service = RecordService(db)
        result = await service.initiate_upload(
            file=file,
            patient_id=current_user.patient_profile.id,
            title=title,
            category_slug=category_slug,
            document_date=doc_date,
        )

        await log_action(
            db,
            actor_user_id=current_user.id,
            action="RECORD_UPLOADED",
            resource_type="MedicalRecord",
            resource_id=result.record_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        return result

    except InvalidFileTypeException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except InsufficientStorageException as e:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(e),
        )


@router.get(
    "",
    response_model=RecordListResponse,
    summary="List medical records",
    description="List records with optional filtering by category, date, and tags.",
)
async def list_records(
    category: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_patient),
) -> RecordListResponse:
    """List patient's medical records with pagination."""
    from_d = date.fromisoformat(from_date) if from_date else None
    to_d = date.fromisoformat(to_date) if to_date else None

    records, total = await record_repo.list_patient_records(
        current_user.patient_profile.id,
        db,
        category_slug=category,
        from_date=from_d,
        to_date=to_d,
        page=page,
        limit=limit,
    )

    return RecordListResponse(
        data=[
            RecordListItem(
                id=r.id,
                title=r.title,
                category=None,
                document_date=r.document_date,
                processing_status=r.processing_status,
                tags=r.tags,
                file_size_bytes=r.file_size_bytes,
                created_at=r.created_at,
            )
            for r in records
        ],
        pagination=PaginationMeta(page=page, limit=limit, total=total),
    )


@router.get(
    "/{record_id}",
    response_model=RecordDetailResponse,
    summary="Get record details",
    description="Full record including extraction data and download URL.",
)
async def get_record(
    record_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_patient),
) -> RecordDetailResponse:
    """Get detailed record information."""
    try:
        service = RecordService(db)
        result = await service.get_record_detail(
            record_id=record_id,
            patient_id=current_user.patient_profile.id,
        )

        await log_action(
            db,
            actor_user_id=current_user.id,
            action="RECORD_VIEWED",
            resource_type="MedicalRecord",
            resource_id=record_id,
            ip_address=request.client.host if request.client else None,
        )

        return result

    except RecordNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found",
        )


@router.get(
    "/{record_id}/status",
    response_model=RecordStatusResponse,
    summary="Check processing status",
    description="Lightweight polling endpoint for document processing status.",
)
async def get_record_status(
    record_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_patient),
) -> RecordStatusResponse:
    """Check record processing status."""
    try:
        service = RecordService(db)
        return await service.get_record_status(
            record_id=record_id,
            patient_id=current_user.patient_profile.id,
        )
    except RecordNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found",
        )


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a record",
    description="Soft delete. Permanent erasure scheduled per GDPR policy.",
)
async def delete_record(
    record_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_patient),
) -> Response:
    """Soft delete a medical record."""
    try:
        await record_repo.soft_delete_record(
            record_id,
            current_user.patient_profile.id,
            db,
        )
        await log_action(
            db,
            actor_user_id=current_user.id,
            action="RECORD_DELETED",
            resource_type="MedicalRecord",
            resource_id=record_id,
            ip_address=request.client.host if request.client else None,
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except RecordNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found",
        )


@router.post(
    "/{record_id}/share",
    status_code=status.HTTP_200_OK,
    summary="Share record with a doctor",
    description="Grant a doctor access to view a specific record.",
)
async def share_record(
    record_id: uuid.UUID,
    body: ShareRecordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_patient),
) -> dict:
    """Share a record with a doctor."""
    try:
        record = await record_repo.get_record_for_patient(
            record_id, current_user.patient_profile.id, db
        )

        shared_list = list(record.shared_with_doctor or [])
        if str(body.doctor_user_id) not in [str(d) for d in shared_list]:
            shared_list.append(body.doctor_user_id)

        from sqlalchemy import update
        from app.models.medical_record import MedicalRecord

        await db.execute(
            update(MedicalRecord)
            .where(MedicalRecord.id == record_id)
            .values(shared_with_doctor=shared_list)
        )

        await log_action(
            db,
            actor_user_id=current_user.id,
            target_user_id=body.doctor_user_id,
            action="RECORD_SHARED",
            resource_type="MedicalRecord",
            resource_id=record_id,
            ip_address=request.client.host if request.client else None,
        )

        return {"message": "Record shared successfully"}

    except RecordNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found",
        )


@router.delete(
    "/{record_id}/share/{doctor_user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke record sharing",
    description="Revoke a doctor's access to a specific record.",
)
async def revoke_share(
    record_id: uuid.UUID,
    doctor_user_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_patient),
) -> Response:
    """Revoke a doctor's access to a record."""
    try:
        record = await record_repo.get_record_for_patient(
            record_id, current_user.patient_profile.id, db
        )

        shared_list = [
            d for d in (record.shared_with_doctor or [])
            if str(d) != str(doctor_user_id)
        ]

        from sqlalchemy import update as sa_update
        from app.models.medical_record import MedicalRecord

        await db.execute(
            sa_update(MedicalRecord)
            .where(MedicalRecord.id == record_id)
            .values(shared_with_doctor=shared_list)
        )

        await log_action(
            db,
            actor_user_id=current_user.id,
            target_user_id=doctor_user_id,
            action="RECORD_SHARE_REVOKED",
            resource_type="MedicalRecord",
            resource_id=record_id,
            ip_address=request.client.host if request.client else None,
        )

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except RecordNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found",
        )


@router.patch(
    "/{record_id}/extraction",
    status_code=status.HTTP_200_OK,
    summary="Correct AI extraction",
    description="Allow patient to manually correct AI-extracted fields.",
)
async def patch_extraction(
    record_id: uuid.UUID,
    body: ExtractionPatchRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_patient),
) -> dict:
    """Manually correct AI extraction fields for a record."""
    import json
    from sqlalchemy import select, update as sa_update
    from app.models.medical_record import MedicalRecord, RecordExtraction

    # Verify ownership
    try:
        await record_repo.get_record_for_patient(record_id, current_user.patient_profile.id, db)
    except RecordNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")

    # Fetch/upsert extraction row
    result = await db.execute(
        select(RecordExtraction).where(RecordExtraction.record_id == record_id)
    )
    extraction = result.scalar_one_or_none()

    updates: dict = {"manually_corrected": True}

    if body.diagnosed_conditions is not None:
        updates["diagnosed_conditions"] = json.dumps(body.diagnosed_conditions).encode("utf-8")
    if body.extracted_medications is not None:
        updates["extracted_medications"] = json.dumps(body.extracted_medications).encode("utf-8")
    if body.doctor_name is not None:
        updates["doctor_name"] = body.doctor_name.encode("utf-8")
    if body.hospital_name is not None:
        updates["hospital_name"] = body.hospital_name.encode("utf-8")
    if body.ai_summary is not None:
        updates["ai_summary"] = body.ai_summary.encode("utf-8")

    if extraction:
        await db.execute(
            sa_update(RecordExtraction)
            .where(RecordExtraction.record_id == record_id)
            .values(**updates)
        )
    else:
        new_ext = RecordExtraction(record_id=record_id, **updates)
        db.add(new_ext)

    await db.commit()

    await log_action(
        db,
        actor_user_id=current_user.id,
        action="EXTRACTION_CORRECTED",
        resource_type="RecordExtraction",
        resource_id=record_id,
        ip_address=request.client.host if request.client else None,
    )

    return {"message": "Extraction updated successfully"}
