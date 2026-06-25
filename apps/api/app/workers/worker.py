"""ARQ async worker — all CV processing jobs run here."""

from __future__ import annotations

import time
from typing import Any

import structlog
from arq.connections import RedisSettings

from app.core.config import settings

logger = structlog.get_logger()


async def process_receipt_scanner(ctx: dict[str, Any], job_id: str, file_url: str) -> dict[str, Any]:
    """Worker: run receipt scanner on uploaded image."""
    import httpx
    from app.cv.tools.receipt_scanner import ReceiptScanner

    start = time.time()
    logger.info("receipt_scanner.start", job_id=job_id)

    async with httpx.AsyncClient() as client:
        resp = await client.get(file_url)
        image_bytes = resp.content

    scanner = ReceiptScanner()
    result = scanner.process(image_bytes)
    elapsed = int((time.time() - start) * 1000)
    logger.info("receipt_scanner.done", job_id=job_id, ms=elapsed)
    return result


class WorkerSettings:
    """ARQ WorkerSettings for PixelMind AI job queue."""

    functions = [process_receipt_scanner]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    queue_name = "pixelmind:jobs"
    max_jobs = 10
    job_timeout = 300  # 5-minute max per CV job
    health_check_interval = 30
