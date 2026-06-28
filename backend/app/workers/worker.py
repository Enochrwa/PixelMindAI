"""ARQ async worker — all CV processing jobs run here."""

from __future__ import annotations

import time
from typing import Any, ClassVar

from arq.connections import RedisSettings
import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger()


# ------------------------------------------------------------------
# Job update helper
# ------------------------------------------------------------------


async def _update_job(
    job_id: str,
    status: str,
    result: dict[str, Any] | None = None,
    error: str | None = None,
    elapsed_ms: int | None = None,
) -> None:
    """Update processing_jobs row via direct DB access."""
    from sqlalchemy import select

    from app.db.models.job import ProcessingJob
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        row = await db.execute(select(ProcessingJob).where(ProcessingJob.id == job_id))
        job = row.scalar_one_or_none()
        if job:
            job.status = status
            if result is not None:
                job.result_json = result
            if error is not None:
                job.error_message = error
            if elapsed_ms is not None:
                job.processing_time_ms = elapsed_ms
            await db.commit()


async def _fetch_image(url: str) -> bytes:
    """Download image bytes from URL."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        raw: bytes = bytes(resp.content)
        return raw


# ------------------------------------------------------------------
# Sprint 1 Workers — OCR Tools
# ------------------------------------------------------------------


async def process_receipt_scanner(
    _ctx: dict[str, Any],
    job_id: str,
    file_url: str,
) -> dict[str, Any]:
    """Worker: run receipt scanner on uploaded image."""
    start = time.time()
    logger.info("receipt_scanner.start", job_id=job_id)
    await _update_job(job_id, "PROCESSING")

    try:
        image_bytes = await _fetch_image(file_url)
        from app.cv.tools.receipt_scanner import ReceiptScanner

        result = ReceiptScanner().process(image_bytes)
        elapsed = int((time.time() - start) * 1000)
        await _update_job(job_id, "COMPLETED", result=result, elapsed_ms=elapsed)
        logger.info("receipt_scanner.done", job_id=job_id, ms=elapsed)
        return result
    except Exception as exc:
        elapsed = int((time.time() - start) * 1000)
        logger.error("receipt_scanner.failed", job_id=job_id, error=str(exc))
        await _update_job(job_id, "FAILED", error=str(exc), elapsed_ms=elapsed)
        raise


async def process_invoice_reader(
    _ctx: dict[str, Any],
    job_id: str,
    file_url: str,
    multi_page: bool = False,
) -> dict[str, Any]:
    """Worker: run invoice reader on uploaded image or PDF."""
    start = time.time()
    logger.info("invoice_reader.start", job_id=job_id)
    await _update_job(job_id, "PROCESSING")

    try:
        image_bytes = await _fetch_image(file_url)
        from app.cv.tools.invoice_reader import InvoiceReader

        result = InvoiceReader().process(image_bytes, multi_page=multi_page)
        elapsed = int((time.time() - start) * 1000)
        await _update_job(job_id, "COMPLETED", result=result, elapsed_ms=elapsed)
        logger.info("invoice_reader.done", job_id=job_id, ms=elapsed)
        return result
    except Exception as exc:
        elapsed = int((time.time() - start) * 1000)
        logger.error("invoice_reader.failed", job_id=job_id, error=str(exc))
        await _update_job(job_id, "FAILED", error=str(exc), elapsed_ms=elapsed)
        raise


async def process_business_card_scanner(
    _ctx: dict[str, Any],
    job_id: str,
    file_urls: list[str],
    _export_format: str = "vcf",
) -> dict[str, Any]:
    """Worker: run business card scanner on one or more images."""
    start = time.time()
    logger.info("biz_card_scanner.start", job_id=job_id, count=len(file_urls))
    await _update_job(job_id, "PROCESSING")

    try:
        from app.cv.tools.business_card_scanner import BusinessCardScanner

        scanner = BusinessCardScanner()

        if len(file_urls) == 1:
            image_bytes = await _fetch_image(file_urls[0])
            result = scanner.process(image_bytes)
        else:
            images = []
            for url in file_urls:
                images.append(await _fetch_image(url))
            results = scanner.process_bulk(images)
            result = {"bulk": True, "count": len(results), "contacts": results}

        elapsed = int((time.time() - start) * 1000)
        await _update_job(job_id, "COMPLETED", result=result, elapsed_ms=elapsed)
        logger.info("biz_card_scanner.done", job_id=job_id, ms=elapsed)
        return result
    except Exception as exc:
        elapsed = int((time.time() - start) * 1000)
        logger.error("biz_card_scanner.failed", job_id=job_id, error=str(exc))
        await _update_job(job_id, "FAILED", error=str(exc), elapsed_ms=elapsed)
        raise


# ------------------------------------------------------------------
# Sprint 2 Workers — Document AI Advanced
# ------------------------------------------------------------------


async def process_handwriting_ocr(
    _ctx: dict[str, Any],
    job_id: str,
    file_url: str,
    structure_mode: bool = True,
) -> dict[str, Any]:
    """Worker: convert handwritten image to digital text."""
    start = time.time()
    logger.info("handwriting_ocr.start", job_id=job_id)
    await _update_job(job_id, "PROCESSING")

    try:
        image_bytes = await _fetch_image(file_url)
        from app.cv.tools.handwriting_ocr import HandwritingOCR

        result = HandwritingOCR().process(image_bytes, structure_mode=structure_mode)
        elapsed = int((time.time() - start) * 1000)
        await _update_job(job_id, "COMPLETED", result=result, elapsed_ms=elapsed)
        logger.info("handwriting_ocr.done", job_id=job_id, ms=elapsed)
        return result
    except Exception as exc:
        elapsed = int((time.time() - start) * 1000)
        logger.error("handwriting_ocr.failed", job_id=job_id, error=str(exc))
        await _update_job(job_id, "FAILED", error=str(exc), elapsed_ms=elapsed)
        raise


async def process_menu_scanner(
    _ctx: dict[str, Any],
    job_id: str,
    file_url: str,
    export_format: str = "json",
    pos_format: bool = False,
) -> dict[str, Any]:
    """Worker: digitize restaurant menu from photo."""
    start = time.time()
    logger.info("menu_scanner.start", job_id=job_id)
    await _update_job(job_id, "PROCESSING")

    try:
        image_bytes = await _fetch_image(file_url)
        from app.cv.tools.menu_scanner import MenuScanner

        result = MenuScanner().process(
            image_bytes, export_format=export_format, pos_format=pos_format
        )
        elapsed = int((time.time() - start) * 1000)
        await _update_job(job_id, "COMPLETED", result=result, elapsed_ms=elapsed)
        logger.info("menu_scanner.done", job_id=job_id, ms=elapsed)
        return result
    except Exception as exc:
        elapsed = int((time.time() - start) * 1000)
        logger.error("menu_scanner.failed", job_id=job_id, error=str(exc))
        await _update_job(job_id, "FAILED", error=str(exc), elapsed_ms=elapsed)
        raise


async def process_document_scanner(
    _ctx: dict[str, Any],
    job_id: str,
    file_urls: list[str],
    mode: str = "original_enhanced",
) -> dict[str, Any]:
    """Worker: scan, crop, deskew document(s) and produce PDF."""
    start = time.time()
    logger.info("document_scanner.start", job_id=job_id, pages=len(file_urls))
    await _update_job(job_id, "PROCESSING")

    try:
        import base64

        from app.cv.tools.document_scanner import DocumentScanner

        scanner = DocumentScanner()
        images = [await _fetch_image(url) for url in file_urls]

        if len(images) == 1:
            result = scanner.process(images[0], mode=mode)
        else:
            pdf_bytes = scanner.process_pdf(images, mode=mode)
            result = {
                "format": "pdf",
                "mode": mode,
                "page_count": len(images),
                "pdf_b64": base64.b64encode(pdf_bytes).decode(),
            }

        elapsed = int((time.time() - start) * 1000)
        await _update_job(job_id, "COMPLETED", result=result, elapsed_ms=elapsed)
        logger.info("document_scanner.done", job_id=job_id, ms=elapsed)
        return result
    except Exception as exc:
        elapsed = int((time.time() - start) * 1000)
        logger.error("document_scanner.failed", job_id=job_id, error=str(exc))
        await _update_job(job_id, "FAILED", error=str(exc), elapsed_ms=elapsed)
        raise


async def process_signature_extractor(
    _ctx: dict[str, Any],
    job_id: str,
    file_url: str,
) -> dict[str, Any]:
    """Worker: extract signatures from document image."""
    start = time.time()
    logger.info("signature_extractor.start", job_id=job_id)
    await _update_job(job_id, "PROCESSING")

    try:
        image_bytes = await _fetch_image(file_url)
        from app.cv.tools.signature_extractor import SignatureExtractor

        result = SignatureExtractor().process(image_bytes)
        elapsed = int((time.time() - start) * 1000)
        await _update_job(job_id, "COMPLETED", result=result, elapsed_ms=elapsed)
        logger.info("signature_extractor.done", job_id=job_id, ms=elapsed)
        return result
    except Exception as exc:
        elapsed = int((time.time() - start) * 1000)
        logger.error("signature_extractor.failed", job_id=job_id, error=str(exc))
        await _update_job(job_id, "FAILED", error=str(exc), elapsed_ms=elapsed)
        raise


async def process_form_field_reader(
    _ctx: dict[str, Any],
    job_id: str,
    file_url: str,
) -> dict[str, Any]:
    """Worker: extract form field responses from filled form image."""
    start = time.time()
    logger.info("form_field_reader.start", job_id=job_id)
    await _update_job(job_id, "PROCESSING")

    try:
        image_bytes = await _fetch_image(file_url)
        from app.cv.tools.form_field_reader import FormFieldReader

        result = FormFieldReader().process(image_bytes)
        elapsed = int((time.time() - start) * 1000)
        await _update_job(job_id, "COMPLETED", result=result, elapsed_ms=elapsed)
        logger.info("form_field_reader.done", job_id=job_id, ms=elapsed)
        return result
    except Exception as exc:
        elapsed = int((time.time() - start) * 1000)
        logger.error("form_field_reader.failed", job_id=job_id, error=str(exc))
        await _update_job(job_id, "FAILED", error=str(exc), elapsed_ms=elapsed)
        raise


# ------------------------------------------------------------------
# Photo Intelligence Workers
# ------------------------------------------------------------------


async def process_background_remover(
    _ctx: dict[str, Any],
    job_id: str,
    file_url: str,
    bg_mode: str = "transparent",
    bg_color_hex: str = "#FFFFFF",
    bg_blur_radius: int = 21,
) -> dict[str, Any]:
    """Worker: remove background from image with configurable bg mode (S3-01)."""
    start = time.time()
    logger.info("background_remover.start", job_id=job_id, bg_mode=bg_mode)
    await _update_job(job_id, "PROCESSING")

    try:
        image_bytes = await _fetch_image(file_url)
        from app.cv.photo.background_remover import BackgroundRemover

        result = BackgroundRemover().process(
            image_bytes,
            bg_mode=bg_mode,
            bg_color_hex=bg_color_hex,
            bg_blur_radius=bg_blur_radius,
        )
        elapsed = int((time.time() - start) * 1000)
        await _update_job(job_id, "COMPLETED", result=result, elapsed_ms=elapsed)
        logger.info("background_remover.done", job_id=job_id, ms=elapsed)
        return result
    except Exception as exc:
        elapsed = int((time.time() - start) * 1000)
        logger.error("background_remover.failed", job_id=job_id, error=str(exc))
        await _update_job(job_id, "FAILED", error=str(exc), elapsed_ms=elapsed)
        raise


async def process_passport_photo(
    _ctx: dict[str, Any],
    job_id: str,
    file_url: str,
    country_code: str = "us",
) -> dict[str, Any]:
    """Worker: generate country-compliant passport photo (S3-02)."""
    start = time.time()
    logger.info("passport_photo.start", job_id=job_id, country_code=country_code)
    await _update_job(job_id, "PROCESSING")

    try:
        image_bytes = await _fetch_image(file_url)
        from app.cv.photo.passport_photo import PassportPhotoGenerator

        result = PassportPhotoGenerator().process(image_bytes, country_code=country_code)
        elapsed = int((time.time() - start) * 1000)
        await _update_job(job_id, "COMPLETED", result=result, elapsed_ms=elapsed)
        logger.info("passport_photo.done", job_id=job_id, ms=elapsed)
        return result
    except Exception as exc:
        elapsed = int((time.time() - start) * 1000)
        logger.error("passport_photo.failed", job_id=job_id, error=str(exc))
        await _update_job(job_id, "FAILED", error=str(exc), elapsed_ms=elapsed)
        raise


# ------------------------------------------------------------------
# Creator Studio Workers
# ------------------------------------------------------------------


async def process_caption_lens(
    _ctx: dict[str, Any],
    job_id: str,
    file_url: str,
) -> dict[str, Any]:
    """Worker: generate image caption."""
    start = time.time()
    logger.info("caption_lens.start", job_id=job_id)
    await _update_job(job_id, "PROCESSING")

    try:
        image_bytes = await _fetch_image(file_url)
        from app.cv.creator.caption_lens import CaptionLens

        result = CaptionLens().process(image_bytes)
        elapsed = int((time.time() - start) * 1000)
        await _update_job(job_id, "COMPLETED", result=result, elapsed_ms=elapsed)
        logger.info("caption_lens.done", job_id=job_id, ms=elapsed)
        return result
    except Exception as exc:
        elapsed = int((time.time() - start) * 1000)
        logger.error("caption_lens.failed", job_id=job_id, error=str(exc))
        await _update_job(job_id, "FAILED", error=str(exc), elapsed_ms=elapsed)
        raise


# ------------------------------------------------------------------
# Business Intel Workers
# ------------------------------------------------------------------


async def process_shelf_counter(
    _ctx: dict[str, Any],
    job_id: str,
    file_url: str,
) -> dict[str, Any]:
    """Worker: count items on retail shelf."""
    start = time.time()
    logger.info("shelf_counter.start", job_id=job_id)
    await _update_job(job_id, "PROCESSING")

    try:
        image_bytes = await _fetch_image(file_url)
        from app.cv.business.shelf_counter import ShelfCounter

        result = ShelfCounter().process(image_bytes)
        elapsed = int((time.time() - start) * 1000)
        await _update_job(job_id, "COMPLETED", result=result, elapsed_ms=elapsed)
        logger.info("shelf_counter.done", job_id=job_id, ms=elapsed)
        return result
    except Exception as exc:
        elapsed = int((time.time() - start) * 1000)
        logger.error("shelf_counter.failed", job_id=job_id, error=str(exc))
        await _update_job(job_id, "FAILED", error=str(exc), elapsed_ms=elapsed)
        raise


# ------------------------------------------------------------------
# Agriculture AI Workers
# ------------------------------------------------------------------


async def process_plant_disease_detector(
    _ctx: dict[str, Any],
    job_id: str,
    file_url: str,
) -> dict[str, Any]:
    """Worker: detect plant diseases."""
    start = time.time()
    logger.info("plant_disease_detector.start", job_id=job_id)
    await _update_job(job_id, "PROCESSING")

    try:
        image_bytes = await _fetch_image(file_url)
        from app.cv.agriculture.plant_disease_detector import PlantDiseaseDetector

        result = PlantDiseaseDetector().process(image_bytes)
        elapsed = int((time.time() - start) * 1000)
        await _update_job(job_id, "COMPLETED", result=result, elapsed_ms=elapsed)
        logger.info("plant_disease_detector.done", job_id=job_id, ms=elapsed)
        return result
    except Exception as exc:
        elapsed = int((time.time() - start) * 1000)
        logger.error("plant_disease_detector.failed", job_id=job_id, error=str(exc))
        await _update_job(job_id, "FAILED", error=str(exc), elapsed_ms=elapsed)
        raise


# ------------------------------------------------------------------
# Entertainment Workers
# ------------------------------------------------------------------


async def process_age_predictor(
    _ctx: dict[str, Any],
    job_id: str,
    file_url: str,
) -> dict[str, Any]:
    """Worker: predict apparent age from face image."""
    start = time.time()
    logger.info("age_predictor.start", job_id=job_id)
    await _update_job(job_id, "PROCESSING")

    try:
        image_bytes = await _fetch_image(file_url)
        from app.cv.entertainment.age_predictor import AgePredictor

        result = AgePredictor().process(image_bytes)
        elapsed = int((time.time() - start) * 1000)
        await _update_job(job_id, "COMPLETED", result=result, elapsed_ms=elapsed)
        logger.info("age_predictor.done", job_id=job_id, ms=elapsed)
        return result
    except Exception as exc:
        elapsed = int((time.time() - start) * 1000)
        logger.error("age_predictor.failed", job_id=job_id, error=str(exc))
        await _update_job(job_id, "FAILED", error=str(exc), elapsed_ms=elapsed)
        raise


# ------------------------------------------------------------------
# Worker Settings
# ------------------------------------------------------------------


class WorkerSettings:
    """ARQ WorkerSettings for PixelMind AI job queue."""

    functions: ClassVar[list[object]] = [
        # OCR & Documents (Sprint 1)
        process_receipt_scanner,
        process_invoice_reader,
        process_business_card_scanner,
        # Document AI Advanced (Sprint 2)
        process_handwriting_ocr,
        process_menu_scanner,
        process_document_scanner,
        process_signature_extractor,
        process_form_field_reader,
        # Photo Intelligence (Sprint 3)
        process_background_remover,
        process_passport_photo,
        # Creator Studio
        process_caption_lens,
        # Business Intel
        process_shelf_counter,
        # Agriculture AI
        process_plant_disease_detector,
        # Entertainment
        process_age_predictor,
    ]
    redis_settings: ClassVar[RedisSettings] = RedisSettings.from_dsn(settings.REDIS_URL)
    queue_name: ClassVar[str] = "pixelmind:jobs"
    max_jobs: ClassVar[int] = 10
    job_timeout: ClassVar[int] = 300  # 5-minute max per CV job
    health_check_interval: ClassVar[int] = 30
