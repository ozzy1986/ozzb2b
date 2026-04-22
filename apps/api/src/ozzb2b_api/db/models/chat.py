"""Chat domain: `conversations` and `messages`.

Design:
- Each `Conversation` is a 1-to-1 channel between a client (`user_id`) and a
  `provider`. The (user_id, provider_id) pair is unique so a user cannot open
  more than one conversation per provider.
- Messages store the original raw body. The provider-side "owner" is resolved
  via `providers.claimed_by_user_id` when present, otherwise only the client
  can access the conversation until the provider is claimed.
- `last_message_at` and `is_active` let us cheaply sort inbox and archive.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ozzb2b_api.db.base import Base
from ozzb2b_api.db.models._mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from ozzb2b_api.db.models.provider import Provider
    from ozzb2b_api.db.models.user import User


class Conversation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """1-to-1 channel between a client and a provider."""

    __tablename__ = "conversations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("providers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped["User"] = relationship()
    provider: Mapped["Provider"] = relationship()
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at.asc()",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "provider_id", name="uq_conversations_user_provider"),
    )


class Message(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single chat message within a `Conversation`."""

    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    sender: Mapped["User | None"] = relationship()
