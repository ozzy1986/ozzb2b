"""ProviderClaim model: lets users claim ownership of a provider profile.

Ownership verification is done by asking the user to publish a short meta tag on
their company homepage. The token is stored hashed at rest; the raw value is
only returned once to the user when they initiate the claim.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ozzb2b_api.db.base import Base
from ozzb2b_api.db.models._mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from ozzb2b_api.db.models.provider import Provider
    from ozzb2b_api.db.models.user import User


class ClaimStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class ClaimMethod(str, enum.Enum):
    META_TAG = "meta_tag"
    ADMIN_MANUAL = "admin_manual"


class ProviderClaim(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Single claim attempt by a user for a specific provider profile."""

    __tablename__ = "provider_claims"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("providers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[ClaimStatus] = mapped_column(
        Enum(
            ClaimStatus,
            name="claim_status",
            native_enum=False,
            validate_strings=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=ClaimStatus.PENDING,
        index=True,
    )
    method: Mapped[ClaimMethod] = mapped_column(
        Enum(
            ClaimMethod,
            name="claim_method",
            native_enum=False,
            validate_strings=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=ClaimMethod.META_TAG,
    )
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    provider: Mapped["Provider"] = relationship()
    user: Mapped["User"] = relationship()
