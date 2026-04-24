"""Chat REST endpoints.

See `services.chat` for all the business logic; this module only does
HTTP translation + dependency wiring.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from ozzb2b_api.clients.events import (
    EVENT_CHAT_MESSAGE_SENT,
    EVENT_CHAT_STARTED,
    get_event_emitter,
)
from ozzb2b_api.config import Settings, get_settings
from ozzb2b_api.db.models import Provider, User
from ozzb2b_api.routes.deps import DbSession, get_current_user
from ozzb2b_api.schemas.chat import (
    ConversationList,
    ConversationPeer,
    ConversationPublic,
    MessageList,
    MessagePublic,
    SendMessageRequest,
    StartConversationRequest,
    WsToken,
)
from ozzb2b_api.security.rate_limit import enforce_rate_limit
from ozzb2b_api.security.tokens import create_ws_chat_token
from ozzb2b_api.services import chat as chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


def _peer(provider: Provider | None) -> ConversationPeer | None:
    if provider is None:
        return None
    return ConversationPeer(
        provider_id=provider.id,
        provider_slug=provider.slug,
        provider_display_name=provider.display_name,
    )


@router.post(
    "/conversations",
    response_model=ConversationPublic,
    status_code=status.HTTP_201_CREATED,
)
async def start_conversation(
    payload: StartConversationRequest,
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> ConversationPublic:
    try:
        conv = await chat_service.start_or_get_conversation(
            db,
            client_user=current_user,
            provider_slug=payload.provider_slug,
        )
    except chat_service.ProviderNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    peer = await chat_service.get_conversation(
        db, viewer=current_user, conversation_id=conv.id
    )
    await get_event_emitter().emit(
        EVENT_CHAT_STARTED,
        user_id=current_user.id,
        properties={
            "conversation_id": str(peer.conversation.id),
            "provider_id": str(peer.provider.id) if peer.provider else None,
            "provider_slug": peer.provider.slug if peer.provider else None,
        },
    )
    return ConversationPublic(
        id=peer.conversation.id,
        user_id=peer.conversation.user_id,
        provider_id=peer.conversation.provider_id,
        last_message_at=peer.conversation.last_message_at,
        is_active=peer.conversation.is_active,
        created_at=peer.conversation.created_at,
        updated_at=peer.conversation.updated_at,
        peer=_peer(peer.provider),
    )


@router.get("/conversations", response_model=ConversationList)
async def list_conversations_endpoint(
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> ConversationList:
    rows = await chat_service.list_conversations(db, viewer=current_user)
    items = [
        ConversationPublic(
            id=r.conversation.id,
            user_id=r.conversation.user_id,
            provider_id=r.conversation.provider_id,
            last_message_at=r.conversation.last_message_at,
            is_active=r.conversation.is_active,
            created_at=r.conversation.created_at,
            updated_at=r.conversation.updated_at,
            peer=_peer(r.provider),
        )
        for r in rows
    ]
    return ConversationList(total=len(items), items=items)


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationPublic,
)
async def get_conversation_endpoint(
    conversation_id: uuid.UUID,
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> ConversationPublic:
    try:
        row = await chat_service.get_conversation(
            db, viewer=current_user, conversation_id=conversation_id
        )
    except chat_service.ConversationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except chat_service.ChatForbiddenError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc
    return ConversationPublic(
        id=row.conversation.id,
        user_id=row.conversation.user_id,
        provider_id=row.conversation.provider_id,
        last_message_at=row.conversation.last_message_at,
        is_active=row.conversation.is_active,
        created_at=row.conversation.created_at,
        updated_at=row.conversation.updated_at,
        peer=_peer(row.provider),
    )


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=MessageList,
)
async def list_messages_endpoint(
    conversation_id: uuid.UUID,
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    before: Annotated[uuid.UUID | None, Query()] = None,
) -> MessageList:
    try:
        total, rows = await chat_service.list_messages(
            db,
            viewer=current_user,
            conversation_id=conversation_id,
            limit=limit,
            before=before,
        )
    except chat_service.ConversationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except chat_service.ChatForbiddenError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc
    items = [MessagePublic.model_validate(m) for m in rows]
    return MessageList(total=total, items=items)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessagePublic,
    status_code=status.HTTP_201_CREATED,
)
async def send_message_endpoint(
    conversation_id: uuid.UUID,
    payload: SendMessageRequest,
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> MessagePublic:
    try:
        message = await chat_service.send_message(
            db,
            sender=current_user,
            conversation_id=conversation_id,
            body=payload.body,
        )
    except chat_service.ConversationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except chat_service.ChatForbiddenError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc
    except chat_service.ChatError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    await get_event_emitter().emit(
        EVENT_CHAT_MESSAGE_SENT,
        user_id=current_user.id,
        properties={
            "conversation_id": str(conversation_id),
            "message_id": str(message.id),
            "body_length": len(message.body),
        },
    )
    return MessagePublic.model_validate(message)


@router.post(
    "/conversations/{conversation_id}/ws-token",
    response_model=WsToken,
)
async def issue_ws_token(
    conversation_id: uuid.UUID,
    request: Request,
    response: Response,
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> WsToken:
    # WS handshake tokens are short-lived but cheap to mint, so we cap how
    # often a single user can grind them out to dampen abuse.
    await enforce_rate_limit(
        request=request,
        response=response,
        endpoint="ws_token",
        limit=settings.rate_limit_ws_token_max,
        user_scope=str(current_user.id),
    )
    try:
        await chat_service.ensure_conversation_access(
            db, viewer=current_user, conversation_id=conversation_id
        )
    except chat_service.ConversationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except chat_service.ChatForbiddenError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc
    token, expires_at = create_ws_chat_token(
        user_id=current_user.id,
        conversation_id=conversation_id,
        settings=settings,
    )
    ws_url = _ws_url_for(settings, token)
    return WsToken(token=token, expires_at=expires_at, ws_url=ws_url)


def _ws_url_for(settings: Settings, token: str) -> str:
    """Build the URL the browser should hit to connect to the chat WS gateway.

    In production we expose it as `wss://api.ozzb2b.com/chat/ws`; in dev we
    point at the Go container on the compose network.
    """
    if settings.is_production:
        return f"wss://api.ozzb2b.com/chat/ws?token={token}"
    return f"ws://localhost:8090/ws?token={token}"
