"""PixelMind AI — FastAPI application entry point."""

from __future__ import annotations

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.middleware.rate_limit import RateLimitMiddleware
from app.api.v1.endpoints import health, auth, files, jobs

# === Sentry (noop if DSN is empty) ===
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=0.1,
    )


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="The World's First Unified Visual Intelligence Operating System",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
    )

    # === Middleware ===
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware)

    # === Error handlers ===
    register_exception_handlers(app)

    # === Routers ===
    app.include_router(health.router)
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(files.router, prefix="/api/v1")
    app.include_router(jobs.router, prefix="/api/v1")

    return app


app = create_app()
