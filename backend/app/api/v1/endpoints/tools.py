"""Tool processing endpoints.

Universal async pattern:
  POST /tools/{slug}/process  → enqueue job → return {job_id} HTTP 202
  GET  /tools/{slug}/export/{job_id}?format=csv → stream download
"""

from __future__ import annotations

import base64
import io
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
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

# All supported tool slugs
SUPPORTED_TOOLS: set[str] = {
    # OCR & Documents (Sprint 1)
    "receipt-scanner",
    "invoice-reader",
    "business-card-scanner",
    # Document AI Advanced (Sprint 2)
    "handwriting-ocr",
    "menu-scanner",
    "document-scanner",
    "signature-extractor",
    "form-field-reader",
    # Photo Intelligence (Sprint 3)
    "background-remover",
    "passport-photo",
    # Creator Studio
    "caption-lens",
    # Business Intel
    "shelf-counter",
    # Agriculture AI
    "plant-disease-detector",
    # Entertainment
    "age-predictor",
}

# Sprint 1 tools (export supported)
SPRINT_ONE_TOOLS = {"receipt-scanner", "invoice-reader", "business-card-scanner"}

# Sprint 2 tools (export supported)
SPRINT_TWO_TOOLS = {
    "handwriting-ocr",
    "menu-scanner",
    "document-scanner",
    "signature-extractor",
    "form-field-reader",
}

# Sprint 3 tools
SPRINT_THREE_TOOLS = {"background-remover", "passport-photo"}

# Credit costs per tool
CREDIT_COSTS: dict[str, int] = {
    "receipt-scanner": 1,
    "invoice-reader": 2,
    "business-card-scanner": 1,
    # Sprint 2
    "handwriting-ocr": 2,
    "menu-scanner": 2,
    "document-scanner": 1,
    "signature-extractor": 1,
    "form-field-reader": 2,
    # Photo Intelligence (Sprint 3)
    "background-remover": 2,
    "passport-photo": 2,
    "caption-lens": 1,
    "shelf-counter": 2,
    "plant-disease-detector": 1,
    "age-predictor": 1,
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


class HandwritingProcessRequest(BaseModel):
    """Handwriting OCR options."""

    file_id: str
    options: dict[str, Any] | None = None


class MenuProcessRequest(BaseModel):
    """Menu Scanner options."""

    file_id: str
    options: dict[str, Any] | None = None


class DocumentScannerRequest(BaseModel):
    """Document Scanner — single or multi-page."""

    file_id: str | None = None
    file_ids: list[str] | None = None
    options: dict[str, Any] | None = None


class SignatureExtractorRequest(BaseModel):
    """Signature Extractor request."""

    file_id: str


class FormFieldRequest(BaseModel):
    """Form Field Reader request."""

    file_id: str


class BackgroundRemoverRequest(BaseModel):
    """Background Remover request with options."""

    file_id: str
    options: dict[str, Any] | None = None


class PassportPhotoRequest(BaseModel):
    """Passport Photo request with options."""

    file_id: str
    options: dict[str, Any] | None = None


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
# Sprint 2 — Document AI Advanced endpoints (S2-06)
# ------------------------------------------------------------------


@router.post("/handwriting-ocr/process", response_model=ProcessResponse, status_code=202)
async def process_handwriting_ocr(
    body: HandwritingProcessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProcessResponse:
    """Enqueue a handwriting OCR job."""
    options = body.options or {}
    structure_mode: bool = bool(options.get("structure_mode", True))

    file_record, job = await _validate_file_and_deduct(
        body.file_id, "handwriting-ocr", current_user, db
    )
    from app.core.storage import r2

    file_url = r2.public_url(file_record.r2_key)
    await enqueue_job(
        "process_handwriting_ocr",
        job.id,
        file_url,
        structure_mode,
        _queue_name="pixelmind:jobs",
    )
    return ProcessResponse(job_id=job.id)


@router.post("/menu-scanner/process", response_model=ProcessResponse, status_code=202)
async def process_menu_scanner(
    body: MenuProcessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProcessResponse:
    """Enqueue a menu scanning job."""
    options = body.options or {}
    export_format: str = str(options.get("export_format", "json"))
    pos_format: bool = bool(options.get("pos_format", False))

    file_record, job = await _validate_file_and_deduct(
        body.file_id, "menu-scanner", current_user, db
    )
    from app.core.storage import r2

    file_url = r2.public_url(file_record.r2_key)
    await enqueue_job(
        "process_menu_scanner",
        job.id,
        file_url,
        export_format,
        pos_format,
        _queue_name="pixelmind:jobs",
    )
    return ProcessResponse(job_id=job.id)


@router.post("/document-scanner/process", response_model=ProcessResponse, status_code=202)
async def process_document_scanner(
    body: DocumentScannerRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProcessResponse:
    """Enqueue a document scanning job (single or multi-page)."""
    options = body.options or {}
    scan_mode: str = str(options.get("mode", "original_enhanced"))

    file_ids = body.file_ids if body.file_ids else ([body.file_id] if body.file_id else None)
    if not file_ids:
        raise HTTPException(400, "Provide file_id or file_ids")

    from app.core.storage import r2

    file_urls: list[str] = []
    job: ProcessingJob | None = None
    for fid in file_ids:
        file_record, job = await _validate_file_and_deduct(
            fid, "document-scanner", current_user, db
        )
        file_urls.append(r2.public_url(file_record.r2_key))

    if job is None:
        raise HTTPException(400, "No valid files")

    await enqueue_job(
        "process_document_scanner",
        job.id,
        file_urls,
        scan_mode,
        _queue_name="pixelmind:jobs",
    )
    return ProcessResponse(job_id=job.id)


@router.post("/signature-extractor/process", response_model=ProcessResponse, status_code=202)
async def process_signature_extractor(
    body: SignatureExtractorRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProcessResponse:
    """Enqueue a signature extraction job."""
    file_record, job = await _validate_file_and_deduct(
        body.file_id, "signature-extractor", current_user, db
    )
    from app.core.storage import r2

    file_url = r2.public_url(file_record.r2_key)
    await enqueue_job(
        "process_signature_extractor",
        job.id,
        file_url,
        _queue_name="pixelmind:jobs",
    )
    return ProcessResponse(job_id=job.id)


@router.post("/form-field-reader/process", response_model=ProcessResponse, status_code=202)
async def process_form_field_reader(
    body: FormFieldRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProcessResponse:
    """Enqueue a form field reading job."""
    file_record, job = await _validate_file_and_deduct(
        body.file_id, "form-field-reader", current_user, db
    )
    from app.core.storage import r2

    file_url = r2.public_url(file_record.r2_key)
    await enqueue_job(
        "process_form_field_reader",
        job.id,
        file_url,
        _queue_name="pixelmind:jobs",
    )
    return ProcessResponse(job_id=job.id)


# ------------------------------------------------------------------
# Background Remover
# ------------------------------------------------------------------


@router.post("/background-remover/process", response_model=ProcessResponse, status_code=202)
async def process_background_remover(
    body: BackgroundRemoverRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProcessResponse:
    """Enqueue a background removal job with configurable options."""
    options = body.options or {}
    bg_mode: str = str(options.get("bg_mode", "transparent"))
    bg_color_hex: str = str(options.get("bg_color_hex", "#FFFFFF"))
    bg_blur_radius: int = int(options.get("bg_blur_radius", 21))

    file_record, job = await _validate_file_and_deduct(
        body.file_id, "background-remover", current_user, db
    )
    from app.core.storage import r2

    file_url = r2.public_url(file_record.r2_key)
    await enqueue_job(
        "process_background_remover",
        job.id,
        file_url,
        bg_mode,
        bg_color_hex,
        bg_blur_radius,
        _queue_name="pixelmind:jobs",
    )
    return ProcessResponse(job_id=job.id)


# ------------------------------------------------------------------
# Passport Photo Generator (Sprint 3)
# ------------------------------------------------------------------


@router.post("/passport-photo/process", response_model=ProcessResponse, status_code=202)
async def process_passport_photo(
    body: PassportPhotoRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProcessResponse:
    """Enqueue a passport photo generation job."""
    options = body.options or {}
    country_code: str = str(options.get("country_code", "us"))

    file_record, job = await _validate_file_and_deduct(
        body.file_id, "passport-photo", current_user, db
    )
    from app.core.storage import r2

    file_url = r2.public_url(file_record.r2_key)
    await enqueue_job(
        "process_passport_photo",
        job.id,
        file_url,
        country_code,
        _queue_name="pixelmind:jobs",
    )
    return ProcessResponse(job_id=job.id)


@router.get("/passport-photo/countries", response_model=None)
async def list_passport_countries() -> list[dict[str, object]]:
    """Return all available country passport specs. No auth required."""
    import json
    from pathlib import Path

    specs_path = Path(__file__).parent.parent.parent.parent / "cv" / "data" / "passport_specs.json"
    with specs_path.open() as f:
        specs: dict[str, Any] = json.load(f)

    countries: list[dict[str, object]] = []
    for code, spec in specs.items():
        countries.append(
            {
                "code": code,
                "name": spec["name"],
                "flag": spec.get("flag", ""),
                "width_mm": spec["width_mm"],
                "height_mm": spec["height_mm"],
                "dpi": spec["dpi"],
                "bg_color": spec["bg_color_hex"],
            }
        )
    return sorted(countries, key=lambda c: str(c["name"]))


# ------------------------------------------------------------------
# Caption Lens
# ------------------------------------------------------------------


@router.post("/caption-lens/process", response_model=ProcessResponse, status_code=202)
async def process_caption_lens(
    body: ProcessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProcessResponse:
    """Enqueue a caption generation job."""
    file_record, job = await _validate_file_and_deduct(
        body.file_id, "caption-lens", current_user, db
    )
    from app.core.storage import r2

    file_url = r2.public_url(file_record.r2_key)
    await enqueue_job(
        "process_caption_lens",
        job.id,
        file_url,
        _queue_name="pixelmind:jobs",
    )
    return ProcessResponse(job_id=job.id)


# ------------------------------------------------------------------
# Shelf Counter
# ------------------------------------------------------------------


@router.post("/shelf-counter/process", response_model=ProcessResponse, status_code=202)
async def process_shelf_counter(
    body: ProcessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProcessResponse:
    """Enqueue a shelf counting job."""
    file_record, job = await _validate_file_and_deduct(
        body.file_id, "shelf-counter", current_user, db
    )
    from app.core.storage import r2

    file_url = r2.public_url(file_record.r2_key)
    await enqueue_job(
        "process_shelf_counter",
        job.id,
        file_url,
        _queue_name="pixelmind:jobs",
    )
    return ProcessResponse(job_id=job.id)


# ------------------------------------------------------------------
# Plant Disease Detector
# ------------------------------------------------------------------


@router.post("/plant-disease-detector/process", response_model=ProcessResponse, status_code=202)
async def process_plant_disease(
    body: ProcessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProcessResponse:
    """Enqueue a plant disease detection job."""
    file_record, job = await _validate_file_and_deduct(
        body.file_id, "plant-disease-detector", current_user, db
    )
    from app.core.storage import r2

    file_url = r2.public_url(file_record.r2_key)
    await enqueue_job(
        "process_plant_disease_detector",
        job.id,
        file_url,
        _queue_name="pixelmind:jobs",
    )
    return ProcessResponse(job_id=job.id)


# ------------------------------------------------------------------
# Age Predictor
# ------------------------------------------------------------------


@router.post("/age-predictor/process", response_model=ProcessResponse, status_code=202)
async def process_age_predictor(
    body: ProcessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProcessResponse:
    """Enqueue an age prediction job."""
    file_record, job = await _validate_file_and_deduct(
        body.file_id, "age-predictor", current_user, db
    )
    from app.core.storage import r2

    file_url = r2.public_url(file_record.r2_key)
    await enqueue_job(
        "process_age_predictor",
        job.id,
        file_url,
        _queue_name="pixelmind:jobs",
    )
    return ProcessResponse(job_id=job.id)


# ------------------------------------------------------------------
# Export endpoint (CSV / VCF download)
# ------------------------------------------------------------------


@router.get("/{slug}/export/{job_id}", response_model=None)
async def export_result(
    slug: str,
    job_id: str,
    format: str = Query(default="json", pattern="^(json|csv|vcf|qb_csv|png|jpeg)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JSONResponse | StreamingResponse:
    """Download the result of a completed job in the requested format."""
    if slug not in SUPPORTED_TOOLS:
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
        return JSONResponse(content=result_data)

    if format == "csv":
        if slug == "receipt-scanner":
            from app.cv.tools.receipt_scanner import ReceiptScanner

            content = ReceiptScanner().to_csv(result_data)
        elif slug == "invoice-reader":
            from app.cv.tools.invoice_reader import InvoiceReader

            content = InvoiceReader().to_csv(result_data)
        elif slug == "business-card-scanner":
            from app.cv.tools.business_card_scanner import BusinessCardScanner

            content = BusinessCardScanner().to_csv(result_data)
        elif slug == "menu-scanner":
            from app.cv.tools.menu_scanner import MenuScanner

            content = MenuScanner().to_csv(result_data)
        elif slug == "handwriting-ocr":
            from app.cv.tools.handwriting_ocr import HandwritingOCR

            content = HandwritingOCR.to_txt(result_data)
        else:
            # Generic CSV for other tools
            import csv as csv_mod

            buf = io.StringIO()
            writer = csv_mod.writer(buf)
            writer.writerow(["key", "value"])
            for k, v in result_data.items():
                writer.writerow([k, str(v)])
            content = buf.getvalue()
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

    # Sprint 3 photo exports
    if slug == "background-remover":
        result_b64 = result_data.get("result_image_b64", "")
        fmt_str = result_data.get("format", "png")
        if result_b64:
            img_bytes = base64.b64decode(result_b64)
            media = "image/png" if fmt_str == "png" else "image/jpeg"
            ext = fmt_str
            return StreamingResponse(
                io.BytesIO(img_bytes),
                media_type=media,
                headers={
                    "Content-Disposition": f"attachment; filename=bg_removed_{job_id[:8]}.{ext}"
                },
            )

    if slug == "passport-photo":
        result_b64 = result_data.get("result_image_b64", "")
        if result_b64:
            img_bytes = base64.b64decode(result_b64)
            country = result_data.get("country_code", "passport")
            return StreamingResponse(
                io.BytesIO(img_bytes),
                media_type="image/jpeg",
                headers={
                    "Content-Disposition": f"attachment; filename=passport_{country}_{job_id[:8]}.jpg"  # noqa: E501
                },
            )

    raise HTTPException(400, f"Format {format!r} not supported for {slug!r}")
