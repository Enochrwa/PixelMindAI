"""File upload endpoint with MIME + Pillow validation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
import magic
from PIL import Image
from pydantic import BaseModel

from app.core.config import settings
from app.core.storage import r2
from app.db.models.job import UploadedFile
from app.db.session import get_db
from app.utils.auth_deps import get_current_user

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.models.user import User

router = APIRouter(prefix="/files", tags=["Files"])

MAX_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


class FileUploadResponse(BaseModel):
    """Response from a successful upload."""

    file_id: str
    original_url: str
    mime_type: str
    size_bytes: int
    expires_at: str


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileUploadResponse:
    """Upload + validate an image or PDF; store on Cloudflare R2."""
    file_bytes = await file.read()

    if len(file_bytes) > MAX_BYTES:
        raise HTTPException(400, f"File too large (max {settings.MAX_UPLOAD_SIZE_MB}MB)")

    # Layer 1: MIME type via file magic bytes
    detected_mime = magic.from_buffer(file_bytes, mime=True)
    if detected_mime not in settings.ALLOWED_MIME_TYPES:
        raise HTTPException(400, f"File type '{detected_mime}' is not allowed")

    # Layer 2: Pillow image integrity check (skip for PDF)
    if detected_mime != "application/pdf":
        try:
            import io

            img = Image.open(io.BytesIO(file_bytes))
            img.verify()
        except Exception as exc:
            raise HTTPException(400, "File is corrupt or not a valid image") from exc

    # Upload to R2
    r2_key = r2.upload_file(file_bytes, detected_mime)

    expires_at = datetime.now(UTC) + timedelta(hours=settings.FREE_FILE_RETENTION_HOURS)

    uploaded = UploadedFile(
        user_id=current_user.id,
        original_filename=file.filename or "upload",
        r2_key=r2_key,
        mime_type=detected_mime,
        size_bytes=len(file_bytes),
        expires_at=expires_at,
    )
    db.add(uploaded)
    await db.commit()
    await db.refresh(uploaded)

    return FileUploadResponse(
        file_id=uploaded.id,
        original_url=r2.public_url(r2_key),
        mime_type=detected_mime,
        size_bytes=len(file_bytes),
        expires_at=expires_at.isoformat(),
    )
