"""Service category (IT, accounting, legal, ...)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ozzb2b_api.db.base import Base
from ozzb2b_api.db.models._mixins import IntPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from ozzb2b_api.db.models.provider import Provider


class Category(IntPrimaryKeyMixin, TimestampMixin, Base):
    """Hierarchical service category."""

    __tablename__ = "categories"

    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    slug: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    parent: Mapped["Category | None"] = relationship(
        remote_side="Category.id",
        back_populates="children",
    )
    children: Mapped[list["Category"]] = relationship(back_populates="parent")
    providers: Mapped[list["Provider"]] = relationship(
        secondary="provider_categories",
        back_populates="categories",
    )
