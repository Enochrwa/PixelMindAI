"""User and subscription ORM models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.db.models.job import ProcessingJob


class User(UUIDMixin, TimestampMixin, Base):
    """Application user."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Plan
    plan: Mapped[str] = mapped_column(String(20), default="free", nullable=False)
    credits_remaining: Mapped[int] = mapped_column(Integer, default=30, nullable=False)

    # Auth
    refresh_token_jti: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # OAuth
    google_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    github_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)

    jobs: Mapped[list[ProcessingJob]] = relationship("ProcessingJob", back_populates="user")
