"""Tool catalog ORM model."""

from __future__ import annotations

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, TimestampMixin, UUIDMixin


class ToolCatalog(UUIDMixin, TimestampMixin, Base):
    """All 43 CV tools available on the platform."""

    __tablename__ = "tool_catalog"

    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    module: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "ocr", "photo"
    credits_cost: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    min_plan: Mapped[str] = mapped_column(String(20), default="free", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_novel: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    icon: Mapped[str | None] = mapped_column(String(100), nullable=True)
