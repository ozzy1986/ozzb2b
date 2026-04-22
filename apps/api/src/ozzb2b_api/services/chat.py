"""Chat domain logic: conversations, messages, authorization, fan-out.

Access rules:
- A conversation is viewed/modified by its client (`user_id`) or by the user
  that owns the linked provider via `providers.claimed_by_user_id`.
- Admins can see everything.
- A message is sent by a participant; `sender_user_id` is recorded.

Fan-out:
- Every persisted message is published to Redis channel `chat:conv:{id}`
  so the Go WebSocket gateway can forward it to subscribers in real time.
- Publishing failures never break the write path — they're logged and skipped.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ozzb2b_api.clients.redis import get_redis
from ozzb2b_api.db.models import (
    Conversation,
    Message,
    Provider,
    ProviderStatus,
    User,
    UserRole,
)

log = structlog.get_logger("ozzb2b_api.services.chat")


class ChatError(Exception):
    """Base error for chat service."""


class ProviderNotFoundError(ChatError):
    pass


class ConversationNotFoundError(ChatError):
    pass


class ChatForbiddenError(ChatError):
    pass


@dataclass(frozen=True)
class ConversationWithPeer:
    conversation: Conversation
    provider: Provider


def _can_access(conv: Conversation, user: User, provider: Provider) -> bool:
    """A user can access a conversation if any of these is true.

    - They are the conversation's client (`user_id`).
    - They have claimed the conversation's provider.
    - They are an admin.
    """
    if user.role == UserRole.ADMIN:
        return True
    if conv.user_id == user.id:
        return True
    return (
        provider.claimed_by_user_id is not None
        and provider.claimed_by_user_id == user.id
    )


async def _load_provider_by_slug(session: AsyncSession, slug: str) -> Provider:
    stmt = select(Provider).where(
        Provider.slug == slug,
        Provider.status == ProviderStatus.PUBLISHED,
    )
    provider = (await session.execute(stmt)).scalar_one_or_none()
    if provider is None:
        raise ProviderNotFoundError("provider not found")
    return provider


async def _load_provider_by_id(session: AsyncSession, provider_id: uuid.UUID) -> Provider:
    provider = (
        await session.execute(select(Provider).where(Provider.id == provider_id))
    ).scalar_one_or_none()
    if provider is None:
        raise ProviderNotFoundError("provider not found")
    return provider


async def start_or_get_conversation(
    session: AsyncSession, *, client_user: User, provider_slug: str
) -> Conversation:
    """Create (or return the existing) conversation between the client and provider.

    The client is always the `user_id` side of the conversation. A provider owner
    opens conversations initiated by others via `list_conversations`.
    """
    provider = await _load_provider_by_slug(session, provider_slug)
    stmt = select(Conversation).where(
        Conversation.user_id == client_user.id,
        Conversation.provider_id == provider.id,
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing is not None:
        return existing
    conv = Conversation(
        id=uuid.uuid4(),
        user_id=client_user.id,
        provider_id=provider.id,
        is_active=True,
    )
    session.add(conv)
    await session.flush()
    return conv


async def list_conversations(
    session: AsyncSession, *, viewer: User
) -> list[ConversationWithPeer]:
    """List all conversations the viewer can access, newest activity first."""
    stmt = select(Conversation).options(selectinload(Conversation.provider))
    if viewer.role != UserRole.ADMIN:
        stmt = stmt.where(
            (Conversation.user_id == viewer.id)
            | (
                Conversation.provider_id.in_(
                    select(Provider.id).where(Provider.claimed_by_user_id == viewer.id)
                )
            )
        )
    stmt = stmt.order_by(
        Conversation.last_message_at.desc().nullslast(),
        Conversation.created_at.desc(),
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [ConversationWithPeer(conversation=c, provider=c.provider) for c in rows]


async def get_conversation(
    session: AsyncSession, *, viewer: User, conversation_id: uuid.UUID
) -> ConversationWithPeer:
    conv = (
        await session.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.provider))
        )
    ).scalar_one_or_none()
    if conv is None:
        raise ConversationNotFoundError("conversation not found")
    if not _can_access(conv, viewer, conv.provider):
        raise ChatForbiddenError("access denied")
    return ConversationWithPeer(conversation=conv, provider=conv.provider)


async def list_messages(
    session: AsyncSession,
    *,
    viewer: User,
    conversation_id: uuid.UUID,
    limit: int = 100,
    before: uuid.UUID | None = None,
) -> tuple[int, list[Message]]:
    """Return the most recent messages for the conversation.

    `before` lets the client page backwards by the id of the oldest message
    they already have. Messages are returned in ascending `created_at` order.
    """
    await get_conversation(session, viewer=viewer, conversation_id=conversation_id)

    total_stmt = select(func.count(Message.id)).where(
        Message.conversation_id == conversation_id
    )
    total = int((await session.execute(total_stmt)).scalar_one())

    stmt = select(Message).where(Message.conversation_id == conversation_id)
    if before is not None:
        anchor = (
            await session.execute(select(Message).where(Message.id == before))
        ).scalar_one_or_none()
        if anchor is not None:
            stmt = stmt.where(Message.created_at < anchor.created_at)
    stmt = stmt.order_by(Message.created_at.desc()).limit(limit)

    rows = list((await session.execute(stmt)).scalars().all())
    rows.reverse()
    return total, rows


async def send_message(
    session: AsyncSession,
    *,
    sender: User,
    conversation_id: uuid.UUID,
    body: str,
) -> Message:
    """Persist a message and publish it to Redis for live fan-out."""
    cleaned = body.strip()
    if not cleaned:
        raise ChatError("message body must not be empty")

    peer = await get_conversation(
        session, viewer=sender, conversation_id=conversation_id
    )
    conv = peer.conversation

    message = Message(
        id=uuid.uuid4(),
        conversation_id=conv.id,
        sender_user_id=sender.id,
        body=cleaned,
    )
    session.add(message)
    await session.flush()

    conv.last_message_at = message.created_at
    await session.flush()

    await _publish_message(conv.id, message)
    return message


async def _publish_message(conversation_id: uuid.UUID, message: Message) -> None:
    """Publish a fan-out event to Redis. Never breaks the caller on failure."""
    event = {
        "id": str(message.id),
        "conversation_id": str(conversation_id),
        "sender_user_id": str(message.sender_user_id) if message.sender_user_id else None,
        "body": message.body,
        "created_at": message.created_at.isoformat(),
    }
    try:
        redis = get_redis()
        await redis.publish(f"chat:conv:{conversation_id}", json.dumps(event))
    except Exception as exc:  # pragma: no cover - best effort fan-out
        log.warning("chat.publish_failed", err=str(exc), conversation_id=str(conversation_id))


async def ensure_conversation_access(
    session: AsyncSession,
    *,
    viewer: User,
    conversation_id: uuid.UUID,
) -> ConversationWithPeer:
    """Thin wrapper used by the WS-token endpoint."""
    return await get_conversation(
        session, viewer=viewer, conversation_id=conversation_id
    )
