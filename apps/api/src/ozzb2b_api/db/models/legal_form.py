"""Legal form reference data (LLC, Ltd, OOO, SARL, ...)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ozzb2b_api.db.base import Base
from ozzb2b_api.db.models._mixins import IntPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from ozzb2b_api.db.models.geo import Country
    from ozzb2b_api.db.models.provider import Provider


class LegalForm(IntPrimaryKeyMixin, TimestampMixin, Base):
    """Legal form: e.g. LLC, Ltd, OOO. Optionally scoped to a country."""

    __tablename__ = "legal_forms"

    country_id: Mapped[int | None] = mapped_column(
        ForeignKey("countries.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), nullable=False)

    country: Mapped["Country | None"] = relationship()
    providers: Mapped[list["Provider"]] = relationship(back_populates="legal_form")

    __table_args__ = (
        UniqueConstraint("country_id", "code", name="uq_legal_forms_country_id_code"),
        UniqueConstraint("country_id", "slug", name="uq_legal_forms_country_id_slug"),
    )
