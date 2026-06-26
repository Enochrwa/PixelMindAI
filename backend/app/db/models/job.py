"""Processing job and file ORM models."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003  # SQLAlchemy Mapped[datetime] needs runtime import
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.db.models.user import User


class UploadedFile(UUIDMixin, TimestampMixin, Base):
    """Uploaded file metadata."""

    __tablename__ = "files"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    r2_key: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ProcessingJob(UUIDMixin, TimestampMixin, Base):
    """Async CV processing job."""

    __tablename__ = "processing_jobs"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    file_id: Mapped[str] = mapped_column(ForeignKey("files.id"), nullable=False)
    tool_slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20), default="QUEUED", nullable=False, index=True
    )  # QUEUED | PROCESSING | COMPLETED | FAILED
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    credits_used: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    user: Mapped[User] = relationship("User", back_populates="jobs")
