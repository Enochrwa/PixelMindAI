"""Pytest configuration and fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

from httpx import ASGITransport, AsyncClient
import pytest_asyncio

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async test client for the FastAPI app with DB dependency overridden."""
    from app.db.session import get_db
    from main import app

    # Override DB dependency so tests don't require a real PostgreSQL connection.
    # Tests that need a real DB should create their own engine fixture.
    async def mock_get_db() -> AsyncGenerator:
        session = AsyncMock()
        # Make execute return a mock result that supports scalar_one_or_none, etc.
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.refresh = AsyncMock()
        session.add = MagicMock()
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = mock_get_db

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield c
    finally:
        app.dependency_overrides.clear()
