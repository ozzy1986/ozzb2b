"""Verifies the iss/aud/leeway hardening on access + ws_chat tokens."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
import pytest

from ozzb2b_api.config import Settings
from ozzb2b_api.security.tokens import (
    TOKEN_TYPE_ACCESS,
    TokenError,
    create_access_token,
    create_ws_chat_token,
    decode_access_token,
    decode_ws_chat_token,
)


def _settings(**overrides: object) -> Settings:
    base = {
        "env": "test",
        "log_level": "WARNING",
        "database_url": "sqlite+aiosqlite:///:memory:",
        "rate_limit_enabled": False,
        "jwt_secret": "x" * 32,
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


def test_access_token_round_trip_with_aud_and_iss() -> None:
    cfg = _settings()
    user_id = uuid.uuid4()
    token, _ = create_access_token(user_id=user_id, role="client", settings=cfg)
    claims = decode_access_token(token, settings=cfg)
    assert claims.sub == str(user_id)
    assert claims.role == "client"


def test_access_token_rejected_when_aud_mismatches() -> None:
    cfg = _settings()
    token, _ = create_access_token(user_id=uuid.uuid4(), role="client", settings=cfg)
    other = _settings(jwt_audience_api="someone-else")
    with pytest.raises(TokenError):
        decode_access_token(token, settings=other)


def test_access_token_rejected_when_iss_mismatches() -> None:
    cfg = _settings()
    token, _ = create_access_token(user_id=uuid.uuid4(), role="client", settings=cfg)
    other = _settings(jwt_issuer="evil")
    with pytest.raises(TokenError):
        decode_access_token(token, settings=other)


def test_access_token_within_leeway_is_accepted() -> None:
    cfg = _settings(jwt_leeway_seconds=10)
    user_id = uuid.uuid4()
    expires_at = datetime.now(tz=UTC) - timedelta(seconds=2)
    payload = {
        "sub": str(user_id),
        "role": "client",
        "exp": expires_at,
        "iat": datetime.now(tz=UTC) - timedelta(minutes=1),
        "jti": "leeway-test",
        "typ": TOKEN_TYPE_ACCESS,
        "iss": cfg.jwt_issuer,
        "aud": cfg.jwt_audience_api,
    }
    token = pyjwt.encode(payload, cfg.jwt_secret, algorithm=cfg.jwt_algorithm)
    claims = decode_access_token(token, settings=cfg)
    assert claims.sub == str(user_id)


def test_access_token_rejected_after_leeway() -> None:
    cfg = _settings(jwt_leeway_seconds=1)
    payload = {
        "sub": str(uuid.uuid4()),
        "role": "client",
        "exp": datetime.now(tz=UTC) - timedelta(minutes=5),
        "iat": datetime.now(tz=UTC) - timedelta(minutes=10),
        "jti": "expired",
        "typ": TOKEN_TYPE_ACCESS,
        "iss": cfg.jwt_issuer,
        "aud": cfg.jwt_audience_api,
    }
    token = pyjwt.encode(payload, cfg.jwt_secret, algorithm=cfg.jwt_algorithm)
    with pytest.raises(TokenError):
        decode_access_token(token, settings=cfg)


def test_legacy_token_without_aud_iss_is_still_accepted() -> None:
    """Backwards-compat shim: tokens minted before the iss/aud upgrade keep working."""
    cfg = _settings()
    user_id = uuid.uuid4()
    payload = {
        "sub": str(user_id),
        "role": "client",
        "exp": datetime.now(tz=UTC) + timedelta(minutes=5),
        "iat": datetime.now(tz=UTC),
        "jti": "legacy",
        "typ": TOKEN_TYPE_ACCESS,
    }
    token = pyjwt.encode(payload, cfg.jwt_secret, algorithm=cfg.jwt_algorithm)
    claims = decode_access_token(token, settings=cfg)
    assert claims.sub == str(user_id)


def test_ws_chat_token_uses_separate_audience() -> None:
    cfg = _settings()
    user_id = uuid.uuid4()
    conv_id = uuid.uuid4()
    token, _ = create_ws_chat_token(user_id=user_id, conversation_id=conv_id, settings=cfg)
    claims = decode_ws_chat_token(token, settings=cfg)
    assert claims.user_id == str(user_id)
    assert claims.conversation_id == str(conv_id)


def test_access_token_cannot_be_replayed_as_ws_chat() -> None:
    cfg = _settings()
    token, _ = create_access_token(user_id=uuid.uuid4(), role="client", settings=cfg)
    with pytest.raises(TokenError):
        decode_ws_chat_token(token, settings=cfg)


def test_ws_chat_token_rejected_when_audience_swapped() -> None:
    cfg = _settings()
    token, _ = create_ws_chat_token(
        user_id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        settings=cfg,
    )
    other = _settings(jwt_audience_ws_chat="someone-else")
    with pytest.raises(TokenError):
        decode_ws_chat_token(token, settings=other)


def test_ws_chat_token_typ_mismatch_rejected() -> None:
    cfg = _settings()
    payload = {
        "sub": str(uuid.uuid4()),
        "conv": str(uuid.uuid4()),
        "exp": datetime.now(tz=UTC) + timedelta(minutes=1),
        "iat": datetime.now(tz=UTC),
        "jti": "wrong-typ",
        "typ": TOKEN_TYPE_ACCESS,
        "iss": cfg.jwt_issuer,
        "aud": cfg.jwt_audience_ws_chat,
    }
    token = pyjwt.encode(payload, cfg.jwt_secret, algorithm=cfg.jwt_algorithm)
    with pytest.raises(TokenError, match="unexpected token type"):
        decode_ws_chat_token(token, settings=cfg)
