"""Country and City lookup tables."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ozzb2b_api.db.base import Base
from ozzb2b_api.db.models._mixins import IntPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from ozzb2b_api.db.models.provider import Provider


class Country(IntPrimaryKeyMixin, TimestampMixin, Base):
    """ISO country entry."""

    __tablename__ = "countries"

    code: Mapped[str] = mapped_column(String(2), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    cities: Mapped[list["City"]] = relationship(
        back_populates="country",
        cascade="all, delete-orphan",
    )
    providers: Mapped[list["Provider"]] = relationship(back_populates="country")


class City(IntPrimaryKeyMixin, TimestampMixin, Base):
    """City entry scoped to a country."""

    __tablename__ = "cities"

    country_id: Mapped[int] = mapped_column(
        ForeignKey("countries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    region: Mapped[str | None] = mapped_column(String(128), nullable=True)

    country: Mapped["Country"] = relationship(back_populates="cities")
    providers: Mapped[list["Provider"]] = relationship(back_populates="city")

    __table_args__ = (
        # Slugs are unique within a country (Paris/FR vs Paris/TX).
        UniqueConstraint("country_id", "slug", name="uq_cities_country_id_slug"),
    )
