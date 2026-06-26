"""Application configuration via Pydantic Settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
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
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "https://pixelmind.vercel.app"]

    # === Auth ===
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # === Database (Neon PostgreSQL) ===
    DATABASE_URL: str = Field(default="postgresql+asyncpg://user:pass@localhost/pixelmind")
    DATABASE_URL_POOLED: str = Field(
        default="postgresql+asyncpg://user:pass@localhost/pixelmind?pgbouncer=true"
    )
    DB_ECHO: bool = False

    # === Redis (Upstash) ===
    REDIS_URL: str = Field(default="redis://localhost:6379")

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

    # === Email ===
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "noreply@pixelmind.ai"
    RESEND_DAILY_CAP: int = 90
    BREVO_API_KEY: str = ""
    BREVO_SMTP_HOST: str = "smtp-relay.brevo.com"
    BREVO_SMTP_PORT: int = 587

    # === Sentry ===
    SENTRY_DSN: str = ""

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

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings: Settings = get_settings()
