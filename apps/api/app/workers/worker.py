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
# Sprint 1 Workers
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
            # Return merged results with bulk flag
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
# Worker Settings
# ------------------------------------------------------------------


class WorkerSettings:
    """ARQ WorkerSettings for PixelMind AI job queue."""

    functions: ClassVar[list[object]] = [
        process_receipt_scanner,
        process_invoice_reader,
        process_business_card_scanner,
    ]
    redis_settings: ClassVar[RedisSettings] = RedisSettings.from_dsn(settings.REDIS_URL)
    queue_name: ClassVar[str] = "pixelmind:jobs"
    max_jobs: ClassVar[int] = 10
    job_timeout: ClassVar[int] = 300  # 5-minute max per CV job
    health_check_interval: ClassVar[int] = 30
