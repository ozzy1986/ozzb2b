"""Client leads and the outreach e-mails drafted for matching providers.

A lead is a client's request ("need an accountant for my WB store"). For
each lead we draft one e-mail per matching provider; drafts are only sent
after the admin reviews and edits them — nothing goes out automatically.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ozzb2b_api.db.base import Base
from ozzb2b_api.db.models._mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from ozzb2b_api.db.models.category import Category
    from ozzb2b_api.db.models.geo import City
    from ozzb2b_api.db.models.provider import Provider


class LeadStatus(enum.StrEnum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
    SPAM = "spam"


class OutreachStatus(enum.StrEnum):
    DRAFT = "draft"
    SENT = "sent"
    SKIPPED = "skipped"
    FAILED = "failed"


def _enum(cls: type[enum.StrEnum], name: str) -> Enum:
    return Enum(
        cls,
        name=name,
        native_enum=False,
        validate_strings=True,
        values_callable=lambda e: [m.value for m in e],
    )


class Lead(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A client's request for a provider."""

    __tablename__ = "leads"

    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    city_id: Mapped[int | None] = mapped_column(
        ForeignKey("cities.id", ondelete="SET NULL"), nullable=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    budget: Mapped[str | None] = mapped_column(String(120), nullable=True)
    contact_name: Mapped[str] = mapped_column(String(120), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[LeadStatus] = mapped_column(
        _enum(LeadStatus, "lead_status"),
        nullable=False,
        default=LeadStatus.NEW,
        index=True,
    )
    source_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    category: Mapped["Category | None"] = relationship()
    city: Mapped["City | None"] = relationship()
    outreach: Mapped[list["OutreachMessage"]] = relationship(
        back_populates="lead",
        order_by="OutreachMessage.created_at",
        cascade="all, delete-orphan",
    )


class OutreachMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One e-mail to one provider about one lead."""

    __tablename__ = "outreach_messages"

    lead_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("providers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    to_email: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[OutreachStatus] = mapped_column(
        _enum(OutreachStatus, "outreach_status"),
        nullable=False,
        default=OutreachStatus.DRAFT,
        index=True,
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    lead: Mapped["Lead"] = relationship(back_populates="outreach")
    provider: Mapped["Provider"] = relationship()

    __table_args__ = (
        UniqueConstraint("lead_id", "provider_id", name="uq_outreach_lead_provider"),
    )


class EmailSuppression(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Addresses that asked not to be contacted again. Checked before every send."""

    __tablename__ = "email_suppressions"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
