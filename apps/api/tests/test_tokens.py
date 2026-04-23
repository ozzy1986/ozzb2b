"""Unit tests for JWT access + refresh + ws-chat token helpers."""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from ozzb2b_api.config import Settings
from ozzb2b_api.security.tokens import (
    TOKEN_TYPE_ACCESS,
    TokenError,
    create_access_token,
    create_refresh_token,
    create_ws_chat_token,
    decode_access_token,
    decode_refresh_token,
    decode_ws_chat_token,
    hash_refresh_token,
)


@pytest.fixture()
def cfg() -> Settings:
    return Settings(jwt_secret="unit-tests-secret", jwt_access_ttl_seconds=60)


def test_access_token_roundtrip(cfg: Settings) -> None:
    uid = uuid.uuid4()
    token, exp = create_access_token(user_id=uid, role="client", settings=cfg)
    claims = decode_access_token(token, settings=cfg)
    assert claims.sub == str(uid)
    assert claims.role == "client"
    assert claims.jti
    assert exp > datetime.now(tz=UTC)


def test_access_token_rejects_wrong_signature(cfg: Settings) -> None:
    token, _ = create_access_token(user_id=uuid.uuid4(), role="client", settings=cfg)
    other = Settings(jwt_secret="another-secret")
    with pytest.raises(TokenError):
        decode_access_token(token, settings=other)


def test_access_token_rejects_expired(cfg: Settings) -> None:
    past = datetime.now(tz=UTC) - timedelta(seconds=10)
    payload = {
        "sub": str(uuid.uuid4()),
        "role": "client",
        "exp": past,
        "iat": past - timedelta(seconds=1),
        "jti": "x",
        "typ": TOKEN_TYPE_ACCESS,
    }
    token = jwt.encode(payload, cfg.jwt_secret, algorithm=cfg.jwt_algorithm)
    with pytest.raises(TokenError):
        decode_access_token(token, settings=cfg)


def test_access_token_rejects_wrong_type(cfg: Settings) -> None:
    token, _ = create_ws_chat_token(
        user_id=uuid.uuid4(), conversation_id=uuid.uuid4(), settings=cfg
    )
    with pytest.raises(TokenError):
        decode_access_token(token, settings=cfg)


def test_ws_chat_token_roundtrip(cfg: Settings) -> None:
    uid = uuid.uuid4()
    cid = uuid.uuid4()
    token, exp = create_ws_chat_token(user_id=uid, conversation_id=cid, settings=cfg)
    claims = decode_ws_chat_token(token, settings=cfg)
    assert claims.user_id == str(uid)
    assert claims.conversation_id == str(cid)
    assert exp > datetime.now(tz=UTC)


def test_ws_chat_token_rejects_access_token(cfg: Settings) -> None:
    token, _ = create_access_token(user_id=uuid.uuid4(), role="client", settings=cfg)
    with pytest.raises(TokenError):
        decode_ws_chat_token(token, settings=cfg)


def test_ws_chat_token_typ_guard(cfg: Settings) -> None:
    payload = {
        "sub": str(uuid.uuid4()),
        "conv": str(uuid.uuid4()),
        "exp": datetime.now(tz=UTC) + timedelta(seconds=60),
        "iat": datetime.now(tz=UTC),
        "jti": "x",
        "typ": "other",
    }
    token = jwt.encode(payload, cfg.jwt_secret, algorithm=cfg.jwt_algorithm)
    with pytest.raises(TokenError):
        decode_ws_chat_token(token, settings=cfg)


def test_refresh_token_is_opaque_and_hashable(cfg: Settings) -> None:
    raw, exp = create_refresh_token(settings=cfg)
    # Opaque: not a JWT (no dots).
    assert "." not in raw
    assert len(raw) >= 48
    assert hash_refresh_token(raw) == decode_refresh_token(raw)
    assert exp > datetime.now(tz=UTC)


def test_refresh_token_malformed_is_rejected() -> None:
    with pytest.raises(TokenError):
        decode_refresh_token("")
    with pytest.raises(TokenError):
        decode_refresh_token("tiny")


def test_access_tokens_are_unique_each_call(cfg: Settings) -> None:
    uid = uuid.uuid4()
    a, _ = create_access_token(user_id=uid, role="client", settings=cfg)
    time.sleep(0.001)
    b, _ = create_access_token(user_id=uid, role="client", settings=cfg)
    assert a != b  # jti differs
