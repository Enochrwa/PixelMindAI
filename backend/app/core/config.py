"""Application configuration via Pydantic Settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """PixelMind AI application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # === App ===
    APP_NAME: str = "PixelMind AI"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = Field(default="change-me-in-production-min-32-chars!!")

    # === Server ===
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    # NOTE: stored as a raw string and exposed as a list via the
    # `ALLOWED_ORIGINS` property below. pydantic-settings tries to JSON-decode
    # any field typed as list[...] when reading from .env/the environment,
    # which breaks on a plain comma-separated string like
    # "http://localhost:5173,https://pixelmind.vercel.app". Keeping the raw
    # field as `str` avoids that, while the property keeps call sites
    # (e.g. main.py's `allow_origins=settings.ALLOWED_ORIGINS`) unchanged.
    ALLOWED_ORIGINS_RAW: str = Field(
        default="http://localhost:5173,https://pixelmind.vercel.app",
        alias="ALLOWED_ORIGINS",
    )

    # === Auth ===
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # === Database (Aiven PostgreSQL) ===
    DATABASE_URL: str = Field(default="postgresql+asyncpg://user:pass@localhost/pixelmind")
    DATABASE_URL_POOLED: str = Field(
        default="postgresql+asyncpg://user:pass@localhost/pixelmind?pgbouncer=true"
    )
    DB_ECHO: bool = False

    # === Redis (Upstash) ===
    # REDIS_URL must be the Redis/TCP protocol URL (redis:// or rediss://),
    # used by arq and redis.asyncio. Get it from the Upstash console "Redis" tab.
    REDIS_URL: str = Field(default="redis://localhost:6379")
    # Optional: Upstash REST API credentials, kept for any future HTTP-based
    # usage. Not used by the current arq / redis.asyncio code paths.
    UPSTASH_REDIS_REST_URL: str = ""
    UPSTASH_REDIS_REST_TOKEN: str = ""

    # === Cloudflare R2 Storage ===
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "pixelmind-uploads"
    R2_PUBLIC_URL: str = "https://pub-placeholder.r2.dev"

    # === Groq AI (Free LLM) ===
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    GROQ_MAX_TOKENS: int = 1024
    # Language AI provider selection: "groq" | "together" | "fireworks"
    LANGUAGE_AI_PROVIDER: str = "groq"
    LANGUAGE_AI_API_KEY: str = ""
    LANGUAGE_AI_MODEL: str = "mistralai/Mixtral-8x7B-Instruct-v0.1"

    # === Email ===
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "noreply@pixelmind.ai"
    RESEND_DAILY_CAP: int = 90
    BREVO_API_KEY: str = ""
    BREVO_SMTP_HOST: str = "smtp-relay.brevo.com"
    BREVO_SMTP_PORT: int = 587

    # === File Upload ===
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_MIME_TYPES: list[str] = [
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/heic",
        "application/pdf",
    ]

    # === Free User Defaults ===
    FREE_USER_CREDITS: int = 30
    FREE_FILE_RETENTION_HOURS: int = 24

    # === Rate Limits ===
    RATE_LIMIT_UNAUTHENTICATED: int = 60
    RATE_LIMIT_FREE: int = 200
    RATE_LIMIT_PAID: int = 1000

    @property
    def ALLOWED_ORIGINS(self) -> list[str]:  # noqa: N802 (kept upper-case to match prior public API)
        """CORS origins, parsed from the comma-separated ALLOWED_ORIGINS env var."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS_RAW.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings: Settings = get_settings()
