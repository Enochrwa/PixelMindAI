"""OCR tool endpoints — Sprint 1 (S1-06).

Universal async pattern:
  POST /tools/{slug}/process  → enqueue job → return {job_id} HTTP 202
  GET  /tools/{slug}/export/{job_id}?format=csv → stream download
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select

from app.core.queue import enqueue_job
from app.db.models.job import ProcessingJob, UploadedFile
from app.db.session import get_db
from app.utils.auth_deps import get_current_user

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.models.user import User

router = APIRouter(prefix="/tools", tags=["Tools"])

# Slugs handled in this sprint
SPRINT_ONE_TOOLS = {"receipt-scanner", "invoice-reader", "business-card-scanner"}

# Credit costs per tool
CREDIT_COSTS: dict[str, int] = {
    "receipt-scanner": 1,
    "invoice-reader": 2,
    "business-card-scanner": 1,
}


# ------------------------------------------------------------------
# Request / Response models
# ------------------------------------------------------------------


class ProcessRequest(BaseModel):
    """Base process request."""

    file_id: str


class InvoiceProcessRequest(BaseModel):
    """Invoice-specific options."""

    file_id: str
    options: dict[str, Any] | None = None


class BizCardProcessRequest(BaseModel):
    """Business card supports bulk file_ids."""

    file_id: str | None = None
    file_ids: list[str] | None = None
    export_format: str = "vcf"


class ProcessResponse(BaseModel):
    """Returned immediately when a job is enqueued."""

    job_id: str
    status: str = "QUEUED"
    message: str = "Job enqueued. Poll GET /api/v1/jobs/{job_id} for result."


# ------------------------------------------------------------------
# Helper
# ------------------------------------------------------------------


async def _validate_file_and_deduct(
    file_id: str,
    tool_slug: str,
    user: User,
    db: AsyncSession,
) -> tuple[UploadedFile, ProcessingJob]:
    """Validate file ownership and create a job record."""
    result = await db.execute(
        select(UploadedFile).where(
            UploadedFile.id == file_id,
            UploadedFile.user_id == user.id,
        )
    )
    file_record = result.scalar_one_or_none()
    if not file_record:
        raise HTTPException(404, f"File {file_id!r} not found")

    credits_cost = CREDIT_COSTS.get(tool_slug, 1)
    if user.credits_remaining < credits_cost:
        raise HTTPException(
            402,
            {
                "error": "insufficient_credits",
                "credits_needed": credits_cost,
                "credits_remaining": user.credits_remaining,
                "upgrade_url": "/pricing",
            },
        )

    # Deduct credits
    user.credits_remaining -= credits_cost

    # Create job record
    job = ProcessingJob(
        user_id=user.id,
        file_id=file_id,
        tool_slug=tool_slug,
        status="QUEUED",
        credits_used=credits_cost,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return file_record, job


# ------------------------------------------------------------------
# Receipt Scanner
# ------------------------------------------------------------------


@router.post("/receipt-scanner/process", response_model=ProcessResponse, status_code=202)
async def process_receipt(
    body: ProcessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProcessResponse:
    """Enqueue a receipt scanning job."""
    file_record, job = await _validate_file_and_deduct(
        body.file_id, "receipt-scanner", current_user, db
    )
    from app.core.storage import r2

    file_url = r2.public_url(file_record.r2_key)

    await enqueue_job(
        "process_receipt_scanner",
        job.id,
        file_url,
        _queue_name="pixelmind:jobs",
    )
    return ProcessResponse(job_id=job.id)


# ------------------------------------------------------------------
# Invoice Reader
# ------------------------------------------------------------------


@router.post("/invoice-reader/process", response_model=ProcessResponse, status_code=202)
async def process_invoice(
    body: InvoiceProcessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProcessResponse:
    """Enqueue an invoice reading job."""
    options = body.options or {}
    multi_page: bool = bool(options.get("multi_page", False))

    file_record, job = await _validate_file_and_deduct(
        body.file_id, "invoice-reader", current_user, db
    )
    from app.core.storage import r2

    file_url = r2.public_url(file_record.r2_key)

    await enqueue_job(
        "process_invoice_reader",
        job.id,
        file_url,
        multi_page,
        _queue_name="pixelmind:jobs",
    )
    return ProcessResponse(job_id=job.id)


# ------------------------------------------------------------------
# Business Card Scanner
# ------------------------------------------------------------------


@router.post("/business-card-scanner/process", response_model=ProcessResponse, status_code=202)
async def process_business_card(
    body: BizCardProcessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProcessResponse:
    """Enqueue a business card scanning job (single or bulk)."""
    # Resolve file IDs
    if body.file_ids:
        file_ids = body.file_ids
    elif body.file_id:
        file_ids = [body.file_id]
    else:
        raise HTTPException(400, "Provide file_id or file_ids")

    from app.core.storage import r2

    file_urls: list[str] = []
    job: ProcessingJob | None = None

    for fid in file_ids:
        file_record, job = await _validate_file_and_deduct(
            fid, "business-card-scanner", current_user, db
        )
        file_urls.append(r2.public_url(file_record.r2_key))

    if job is None:
        raise HTTPException(400, "No valid files")

    await enqueue_job(
        "process_business_card_scanner",
        job.id,
        file_urls,
        body.export_format,
        _queue_name="pixelmind:jobs",
    )
    return ProcessResponse(job_id=job.id)


# ------------------------------------------------------------------
# Export endpoint (CSV / VCF download)
# ------------------------------------------------------------------


@router.get("/{slug}/export/{job_id}")
async def export_result(
    slug: str,
    job_id: str,
    format: str = Query(default="json", pattern="^(json|csv|vcf|qb_csv)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse | dict[str, Any]:
    """Download the result of a completed job in the requested format."""
    if slug not in SPRINT_ONE_TOOLS:
        raise HTTPException(404, f"Tool {slug!r} not found")

    result_row = await db.execute(
        select(ProcessingJob).where(
            ProcessingJob.id == job_id,
            ProcessingJob.user_id == current_user.id,
            ProcessingJob.tool_slug == slug,
        )
    )
    job = result_row.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status != "COMPLETED":
        raise HTTPException(400, f"Job is {job.status}, not COMPLETED")

    result_data: dict[str, Any] = job.result_json or {}

    if format == "json":
        return result_data

    if format == "csv":
        if slug == "receipt-scanner":
            from app.cv.tools.receipt_scanner import ReceiptScanner

            content = ReceiptScanner().to_csv(result_data)
        elif slug == "invoice-reader":
            from app.cv.tools.invoice_reader import InvoiceReader

            content = InvoiceReader().to_csv(result_data)
        else:
            # Business card → CSV
            from app.cv.tools.business_card_scanner import BusinessCardScanner

            content = BusinessCardScanner().to_csv(result_data)
        return StreamingResponse(
            io.StringIO(content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={slug}_{job_id[:8]}.csv"},
        )

    if format == "vcf" and slug == "business-card-scanner":
        from app.cv.tools.business_card_scanner import BusinessCardScanner

        content = BusinessCardScanner().to_vcf(result_data)
        return StreamingResponse(
            io.StringIO(content),
            media_type="text/vcard",
            headers={"Content-Disposition": f"attachment; filename=contact_{job_id[:8]}.vcf"},
        )

    if format == "qb_csv" and slug == "receipt-scanner":
        from app.cv.tools.receipt_scanner import ReceiptScanner

        content = ReceiptScanner().to_quickbooks_csv(result_data)
        return StreamingResponse(
            io.StringIO(content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=quickbooks_{job_id[:8]}.csv"},
        )

    raise HTTPException(400, f"Format {format!r} not supported for {slug!r}")
