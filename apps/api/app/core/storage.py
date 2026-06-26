"""Cloudflare R2 (S3-compatible) storage client."""

from __future__ import annotations

from typing import Any
import uuid

from app.core.config import settings


def _make_client() -> Any:
    """Create a boto3 S3 client lazily — avoids import-time connection errors."""
    import boto3
    from botocore.config import Config

    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


class R2Client:
    """Thread-safe Cloudflare R2 client wrapping boto3.

    The boto3 client is created lazily on first use so that importing this
    module during tests doesn't require real R2 credentials.
    """

    def __init__(self) -> None:
        self._client: Any = None
        self.bucket = settings.R2_BUCKET_NAME

    def _get_client(self) -> Any:
        if self._client is None:
            self._client = _make_client()
        return self._client

    def upload_file(self, file_bytes: bytes, content_type: str, prefix: str = "uploads") -> str:
        """Upload bytes to R2. Returns the public object key."""
        key = f"{prefix}/{uuid.uuid4().hex}{_ext_for_mime(content_type)}"
        self._get_client().put_object(
            Bucket=self.bucket,
            Key=key,
            Body=file_bytes,
            ContentType=content_type,
        )
        return key

    def delete_file(self, key: str) -> None:
        """Delete an object from R2."""
        self._get_client().delete_object(Bucket=self.bucket, Key=key)

    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate a pre-signed GET URL."""
        url: str = self._get_client().generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )
        return url

    def public_url(self, key: str) -> str:
        """Return the public CDN URL for a key."""
        return f"{settings.R2_PUBLIC_URL}/{key}"


def _ext_for_mime(mime: str) -> str:
    """Return file extension for a MIME type."""
    mapping = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/heic": ".heic",
        "application/pdf": ".pdf",
    }
    return mapping.get(mime, "")


r2: R2Client = R2Client()
