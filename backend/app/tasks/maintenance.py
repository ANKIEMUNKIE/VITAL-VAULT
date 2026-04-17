# app/tasks/maintenance.py
"""Scheduled maintenance tasks — cleanup and GDPR compliance."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    queue="default",
    name="app.tasks.maintenance.cleanup_expired_tokens",
)
def cleanup_expired_tokens() -> dict:
    """Delete expired and revoked refresh tokens from the database.

    Runs daily at 2 AM UTC via Celery Beat.

    Returns:
        Dict with count of deleted tokens.
    """
    from sqlalchemy import create_engine, delete
    from sqlalchemy.orm import Session

    from app.config import settings
    from app.models.user import RefreshToken

    sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)

    now = datetime.now(timezone.utc)

    with Session(engine) as session:
        result = session.execute(
            delete(RefreshToken).where(
                (RefreshToken.expires_at < now) | (RefreshToken.is_revoked == True)  # noqa: E712
            )
        )
        deleted = result.rowcount
        session.commit()

    logger.info("Cleaned up %d expired/revoked refresh tokens", deleted)
    return {"deleted_tokens": deleted}


@shared_task(
    queue="default",
    name="app.tasks.maintenance.gdpr_hard_delete",
)
def gdpr_hard_delete() -> dict:
    """Permanently delete soft-deleted records older than 30 days.

    Implements GDPR Right to Erasure compliance.
    Runs daily at 3 AM UTC via Celery Beat.

    Returns:
        Dict with count of permanently deleted records.
    """
    from sqlalchemy import create_engine, delete
    from sqlalchemy.orm import Session

    from app.config import settings
    from app.core.storage import delete_file
    from app.models.medical_record import MedicalRecord, RecordExtraction

    sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    deleted_count = 0

    with Session(engine) as session:
        # Find records to permanently delete
        from sqlalchemy import select

        result = session.execute(
            select(MedicalRecord).where(
                MedicalRecord.is_deleted == True,  # noqa: E712
                MedicalRecord.deleted_at <= cutoff,
            )
        )
        records = list(result.scalars().all())

        for record in records:
            try:
                # Delete from object storage
                delete_file(record.storage_key)

                # Delete extraction data
                session.execute(
                    delete(RecordExtraction).where(
                        RecordExtraction.record_id == record.id
                    )
                )

                # Delete record
                session.execute(
                    delete(MedicalRecord).where(MedicalRecord.id == record.id)
                )

                deleted_count += 1
                logger.info("GDPR hard deleted record %s", record.id)

            except Exception:
                logger.exception("Failed to hard delete record %s", record.id)

        session.commit()

    logger.info("GDPR hard delete completed — %d records permanently erased", deleted_count)
    return {"permanently_deleted": deleted_count}
