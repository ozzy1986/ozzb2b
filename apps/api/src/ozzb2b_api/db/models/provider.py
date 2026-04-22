"""Provider (B2B company) and the M2M link to categories."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ozzb2b_api.db.base import Base
from ozzb2b_api.db.models._mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from ozzb2b_api.db.models.category import Category
    from ozzb2b_api.db.models.geo import City, Country
    from ozzb2b_api.db.models.legal_form import LegalForm
    from ozzb2b_api.db.models.user import User


class ProviderStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Provider(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A company that offers B2B outsourcing services."""

    __tablename__ = "providers"

    slug: Mapped[str] = mapped_column(String(160), nullable=False, unique=True, index=True)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    country_id: Mapped[int | None] = mapped_column(
        ForeignKey("countries.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    city_id: Mapped[int | None] = mapped_column(
        ForeignKey("cities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    legal_form_id: Mapped[int | None] = mapped_column(
        ForeignKey("legal_forms.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)

    registration_number: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    tax_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    year_founded: Mapped[int | None] = mapped_column(Integer, nullable=True)
    employee_count_range: Mapped[str | None] = mapped_column(String(32), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    source: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    source_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_scraped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[ProviderStatus] = mapped_column(
        Enum(
            ProviderStatus,
            name="provider_status",
            native_enum=False,
            validate_strings=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=ProviderStatus.PUBLISHED,
        index=True,
    )
    is_claimed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    claimed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Free-form, per-source data (rating, certifications, tech stack, etc.)
    meta: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    # Full-text search document maintained by a DB trigger (see migration).
    search_document: Mapped[str | None] = mapped_column(TSVECTOR, nullable=True)

    country: Mapped["Country | None"] = relationship(back_populates="providers")
    city: Mapped["City | None"] = relationship(back_populates="providers")
    legal_form: Mapped["LegalForm | None"] = relationship(back_populates="providers")
    claimed_by: Mapped["User | None"] = relationship()
    categories: Mapped[list["Category"]] = relationship(
        secondary="provider_categories",
        back_populates="providers",
    )

    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_providers_source_source_id"),
    )


class ProviderCategory(Base):
    """Many-to-many link between providers and categories."""

    __tablename__ = "provider_categories"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("providers.id", ondelete="CASCADE"),
        primary_key=True,
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        primary_key=True,
    )
