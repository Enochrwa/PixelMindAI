"""Health check endpoint — used by UptimeRobot to keep Fly.io + Neon warm."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends
from sqlalchemy import text

from app.core.config import settings
from app.db.session import get_db

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/health", tags=["System"])
async def health_check(db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    """Health check: verifies app is alive and warms Neon PostgreSQL."""
    await db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(UTC).isoformat(),
    }
