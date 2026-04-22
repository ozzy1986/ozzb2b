"""Unit tests for the chat WS-token helpers."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from ozzb2b_api.config import Settings
from ozzb2b_api.security.tokens import (
    TokenError,
    create_access_token,
    create_ws_chat_token,
    decode_access_token,
    decode_ws_chat_token,
)


def _settings() -> Settings:
    return Settings(env="test", jwt_secret="a" * 32)


def test_ws_chat_token_roundtrip() -> None:
    s = _settings()
    user_id = uuid.uuid4()
    conv_id = uuid.uuid4()
    token, expires_at = create_ws_chat_token(
        user_id=user_id, conversation_id=conv_id, settings=s
    )
    claims = decode_ws_chat_token(token, settings=s)
    assert claims.user_id == str(user_id)
    assert claims.conversation_id == str(conv_id)
    assert claims.exp.timestamp() == pytest.approx(expires_at.timestamp(), rel=1e-6)


def test_ws_chat_token_ttl_is_short() -> None:
    s = _settings()
    _, expires_at = create_ws_chat_token(
        user_id=uuid.uuid4(), conversation_id=uuid.uuid4(), settings=s
    )
    now = datetime.now(tz=UTC)
    # handshake-only window: must be short (<= 5 min).
    assert expires_at - now <= timedelta(minutes=5)


def test_ws_chat_token_type_is_enforced() -> None:
    s = _settings()
    access, _ = create_access_token(user_id=uuid.uuid4(), role="client", settings=s)
    # An access token must not be accepted as a WS chat token.
    with pytest.raises(TokenError):
        decode_ws_chat_token(access, settings=s)


def test_ws_chat_token_rejected_as_access() -> None:
    s = _settings()
    ws, _ = create_ws_chat_token(
        user_id=uuid.uuid4(), conversation_id=uuid.uuid4(), settings=s
    )
    with pytest.raises(TokenError):
        decode_access_token(ws, settings=s)


def test_ws_chat_token_tampered_rejected() -> None:
    s = _settings()
    token, _ = create_ws_chat_token(
        user_id=uuid.uuid4(), conversation_id=uuid.uuid4(), settings=s
    )
    tampered = token[:-2] + ("AA" if token[-2:] != "AA" else "BB")
    with pytest.raises(TokenError):
        decode_ws_chat_token(tampered, settings=s)
