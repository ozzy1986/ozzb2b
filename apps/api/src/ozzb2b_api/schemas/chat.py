"""Pydantic schemas for the chat domain."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StartConversationRequest(BaseModel):
    """Client-side request to open (or fetch) a conversation with a provider."""

    provider_slug: str = Field(min_length=1, max_length=160)


class ConversationPeer(BaseModel):
    """Summary of the "other side" rendered in the conversation list."""

    provider_id: uuid.UUID
    provider_slug: str
    provider_display_name: str


class ConversationPublic(BaseModel):
    """Conversation as exposed to clients of our API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    provider_id: uuid.UUID
    last_message_at: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    peer: ConversationPeer | None = None


class ConversationList(BaseModel):
    total: int
    items: list[ConversationPublic]


class MessagePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_user_id: uuid.UUID | None
    body: str
    created_at: datetime


class MessageList(BaseModel):
    total: int
    items: list[MessagePublic]


class SendMessageRequest(BaseModel):
    body: str = Field(min_length=1, max_length=8000)


class WsToken(BaseModel):
    """Short-lived JWT used by the browser to connect to the chat WS gateway."""

    token: str
    expires_at: datetime
    ws_url: str
