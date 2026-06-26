"""Async SQLAlchemy engine and session factory."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

# Strip the ?pgbouncer=true query param from the URL (it's an asyncpg connect_arg,
# not a URL parameter). Pass it via connect_args instead.
import re as _re

# asyncpg does not accept pgbouncer as a URL query param or connect_arg.
# Strip it from the URL; PgBouncer mode is handled by SQLAlchemy pool settings.
_db_url = _re.sub(r"[?&]pgbouncer=[^&]*", "", settings.DATABASE_URL_POOLED)
# Remove trailing ? if it was the only param
_db_url = _db_url.rstrip("?")

engine = create_async_engine(
    _db_url,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
