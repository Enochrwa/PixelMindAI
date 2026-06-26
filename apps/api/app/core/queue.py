"""ARQ job queue helpers for async CV processing."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from app.core.config import settings

if TYPE_CHECKING:
    from collections.abc import Callable


def _redis_settings() -> RedisSettings:
    url = settings.REDIS_URL
    # Parse redis://[:password@]host[:port][/db]
    return RedisSettings.from_dsn(url)


async def get_redis_pool() -> ArqRedis:
    """Create and return an ARQ Redis connection pool."""
    return await create_pool(_redis_settings())


async def enqueue_job(
    func: str | Callable[..., Any],
    *args: Any,
    _queue_name: str = "pixelmind:jobs",
    **kwargs: Any,
) -> str:
    """Enqueue a job and return the job ID."""
    pool = await get_redis_pool()
    func_name = func if isinstance(func, str) else func.__name__
    job = await pool.enqueue_job(func_name, *args, _queue_name=_queue_name, **kwargs)
    return job.job_id if job else ""
