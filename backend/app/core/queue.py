"""ARQ job queue helpers for async CV processing.

Falls back to in-process async execution when Redis is unavailable,
so the app works correctly even without a running Redis instance.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from collections.abc import Callable


# ---------------------------------------------------------------------------
# Worker function registry — populated at first use
# ---------------------------------------------------------------------------

_WORKER_REGISTRY: dict[str, Any] | None = None


def _get_worker_registry() -> dict[str, Any]:
    global _WORKER_REGISTRY
    if _WORKER_REGISTRY is not None:
        return _WORKER_REGISTRY

    from app.workers.worker import (
        process_age_predictor,
        process_background_remover,
        process_business_card_scanner,
        process_caption_lens,
        process_invoice_reader,
        process_plant_disease_detector,
        process_receipt_scanner,
        process_shelf_counter,
    )

    _WORKER_REGISTRY = {
        "process_receipt_scanner": process_receipt_scanner,
        "process_invoice_reader": process_invoice_reader,
        "process_business_card_scanner": process_business_card_scanner,
        "process_background_remover": process_background_remover,
        "process_caption_lens": process_caption_lens,
        "process_shelf_counter": process_shelf_counter,
        "process_plant_disease_detector": process_plant_disease_detector,
        "process_age_predictor": process_age_predictor,
    }
    return _WORKER_REGISTRY


# ---------------------------------------------------------------------------
# Redis helpers (optional)
# ---------------------------------------------------------------------------


async def _try_enqueue_via_redis(
    func_name: str,
    *args: Any,
    _queue_name: str,
    **kwargs: Any,
) -> str | None:
    """Attempt to enqueue via ARQ/Redis. Returns job_id or None on failure."""
    try:
        from arq import create_pool
        from arq.connections import RedisSettings

        from app.core.config import settings

        pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
        job = await pool.enqueue_job(func_name, *args, _queue_name=_queue_name, **kwargs)
        return job.job_id if job else None
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Redis unavailable (%s); falling back to in-process execution for %s",
            exc,
            func_name,
        )
        return None


# ---------------------------------------------------------------------------
# In-process fallback
# ---------------------------------------------------------------------------


async def _run_in_process(func_name: str, *args: Any, **kwargs: Any) -> None:
    """Run the worker function directly in the current process (no Redis needed)."""
    registry = _get_worker_registry()
    fn = registry.get(func_name)
    if fn is None:
        logger.error("No in-process worker found for %s", func_name)
        return

    # Worker functions expect `_ctx` as first positional arg (ARQ convention)
    ctx: dict[str, Any] = {}
    try:
        await fn(ctx, *args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        # Errors are already handled inside each worker (they call _update_job FAILED)
        logger.error("In-process worker %s raised: %s", func_name, exc)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def enqueue_job(
    func: "str | Callable[..., Any]",
    *args: Any,
    _queue_name: str = "pixelmind:jobs",
    **kwargs: Any,
) -> str:
    """Enqueue a job via Redis/ARQ, or run it in-process if Redis is down.

    Always returns the job_id string that was already persisted in the DB by
    the caller — the caller creates the DB row before calling us.
    """
    func_name = func if isinstance(func, str) else func.__name__

    # Try Redis first
    redis_job_id = await _try_enqueue_via_redis(
        func_name, *args, _queue_name=_queue_name, **kwargs
    )
    if redis_job_id:
        logger.info("Enqueued %s via Redis (arq job_id=%s)", func_name, redis_job_id)
        return redis_job_id

    # Fallback: run synchronously in the background (Fire-and-forget asyncio task)
    # The job_id is the first positional arg by convention in all our workers
    job_id: str = args[0] if args else ""
    logger.info("Running %s in-process (job_id=%s)", func_name, job_id)
    asyncio.create_task(_run_in_process(func_name, *args, **kwargs))  # noqa: RUF006
    return job_id
