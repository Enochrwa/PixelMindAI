"""Sliding-window rate limiting using Redis."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import redis.asyncio as aioredis
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from app.core.config import settings

if TYPE_CHECKING:
    from fastapi import Request

EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter: X requests per 60-second window."""

    def __init__(self, app: Any) -> None:
        super().__init__(app)
        self._redis: aioredis.Redis | None = None  # type: ignore[type-arg]

    async def _get_redis(self) -> aioredis.Redis:  # type: ignore[type-arg]
        if self._redis is None:
            self._redis = aioredis.from_url(  # type: ignore[no-untyped-call]
                settings.REDIS_URL, decode_responses=True
            )
        return self._redis

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        user_id: str | None = getattr(request.state, "user_id", None)
        identifier = user_id or (request.client.host if request.client else "anonymous")
        limit = (
            settings.RATE_LIMIT_PAID
            if getattr(request.state, "is_paid", False)
            else settings.RATE_LIMIT_FREE
            if user_id
            else settings.RATE_LIMIT_UNAUTHENTICATED
        )

        redis = await self._get_redis()
        key = f"rl:{identifier}:{int(time.time()) // 60}"

        count = await redis.incr(key)
        await redis.expire(key, 120)

        if count > limit:
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": "60"},
                content={"error": "RATE_LIMIT_EXCEEDED", "message": "Rate limit exceeded"},
            )

        return await call_next(request)
