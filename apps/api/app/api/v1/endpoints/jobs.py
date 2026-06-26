"""Job status polling endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.db.models.job import ProcessingJob
from app.db.session import get_db
from app.utils.auth_deps import get_current_user

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.models.user import User

router = APIRouter(prefix="/jobs", tags=["Jobs"])


class JobStatusResponse(BaseModel):
    """Job status response."""

    job_id: str
    status: str
    tool_slug: str
    result: object | None = None
    error: str | None = None
    credits_used: int
    processing_time_ms: int | None = None


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobStatusResponse:
    """Poll the status of an async processing job."""
    result = await db.execute(
        select(ProcessingJob).where(
            ProcessingJob.id == job_id, ProcessingJob.user_id == current_user.id
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        tool_slug=job.tool_slug,
        result=job.result_json,
        error=job.error_message,
        credits_used=job.credits_used,
        processing_time_ms=job.processing_time_ms,
    )
