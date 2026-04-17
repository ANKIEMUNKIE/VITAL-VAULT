# app/core/storage.py
"""S3/MinIO object storage client wrapper.

Handles file upload, download, and pre-signed URL generation.
Pre-signed URLs have a maximum TTL of 15 minutes per security policy.
"""

from __future__ import annotations

import logging
from typing import BinaryIO

import boto3
from botocore.config import Config as BotoConfig

from app.config import settings

logger = logging.getLogger(__name__)

# Maximum TTL for pre-signed URLs (seconds)
PRESIGNED_URL_TTL = 900  # 15 minutes


def _get_s3_client():  # type: ignore[no-untyped-def]
    """Create a boto3 S3 client configured for MinIO or AWS S3."""
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION,
        config=BotoConfig(signature_version="s3v4"),
    )


def ensure_bucket_exists() -> None:
    """Create the storage bucket if it doesn't exist."""
    client = _get_s3_client()
    try:
        client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
    except client.exceptions.ClientError:
        client.create_bucket(Bucket=settings.S3_BUCKET_NAME)
        logger.info("Created S3 bucket: %s", settings.S3_BUCKET_NAME)


def upload_file(
    file_obj: BinaryIO,
    storage_key: str,
    content_type: str,
) -> str:
    """Upload a file to object storage.

    Args:
        file_obj: File-like binary object.
        storage_key: S3 object key.
        content_type: MIME type of the file.

    Returns:
        The storage key of the uploaded object.
    """
    client = _get_s3_client()
    client.upload_fileobj(
        Fileobj=file_obj,
        Bucket=settings.S3_BUCKET_NAME,
        Key=storage_key,
        ExtraArgs={"ContentType": content_type},
    )
    logger.info("Uploaded file to S3: %s", storage_key)
    return storage_key


def download_file(storage_key: str, destination_path: str) -> str:
    """Download a file from object storage to a local path.

    Args:
        storage_key: S3 object key.
        destination_path: Local file path to save to.

    Returns:
        The destination path.
    """
    client = _get_s3_client()
    client.download_file(
        Bucket=settings.S3_BUCKET_NAME,
        Key=storage_key,
        Filename=destination_path,
    )
    return destination_path


def generate_presigned_url(storage_key: str) -> str:
    """Generate a pre-signed URL for temporary file access.

    TTL is capped at 15 minutes per security policy.

    Args:
        storage_key: S3 object key.

    Returns:
        Pre-signed URL string.
    """
    client = _get_s3_client()
    return client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.S3_BUCKET_NAME,
            "Key": storage_key,
        },
        ExpiresIn=PRESIGNED_URL_TTL,
    )


def delete_file(storage_key: str) -> None:
    """Delete a file from object storage.

    Args:
        storage_key: S3 object key to delete.
    """
    client = _get_s3_client()
    client.delete_object(
        Bucket=settings.S3_BUCKET_NAME,
        Key=storage_key,
    )
    logger.info("Deleted file from S3: %s", storage_key)
