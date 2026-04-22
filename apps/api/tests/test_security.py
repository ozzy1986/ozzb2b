"""Unit tests for password hashing + token helpers."""

from __future__ import annotations

import uuid
from datetime import timedelta

import pytest

from ozzb2b_api.config import Settings
from ozzb2b_api.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


def test_password_hash_roundtrip() -> None:
    pw = "correct-horse-battery-staple"
    h = hash_password(pw)
    assert h != pw
    assert verify_password(pw, h)
    assert not verify_password("wrong", h)


def test_password_hashes_are_unique_per_call() -> None:
    pw = "correct-horse-battery-staple"
    assert hash_password(pw) != hash_password(pw)


def test_access_token_decode_roundtrip() -> None:
    s = Settings(env="test", jwt_secret="a" * 32)
    user_id = uuid.uuid4()
    token, expires_at = create_access_token(user_id=user_id, role="client", settings=s)
    claims = decode_access_token(token, settings=s)
    assert claims.sub == str(user_id)
    assert claims.role == "client"
    assert claims.exp.timestamp() == pytest.approx(expires_at.timestamp(), rel=1e-6)


def test_access_token_tampered_rejected() -> None:
    s = Settings(env="test", jwt_secret="a" * 32)
    token, _ = create_access_token(user_id=uuid.uuid4(), role="client", settings=s)
    tampered = token[:-2] + ("AA" if token[-2:] != "AA" else "BB")
    with pytest.raises(TokenError):
        decode_access_token(tampered, settings=s)


def test_access_token_wrong_secret_rejected() -> None:
    a = Settings(env="test", jwt_secret="a" * 32)
    b = Settings(env="test", jwt_secret="b" * 32)
    token, _ = create_access_token(user_id=uuid.uuid4(), role="client", settings=a)
    with pytest.raises(TokenError):
        decode_access_token(token, settings=b)


def test_refresh_token_hash_is_stable() -> None:
    raw, _ = create_refresh_token()
    assert hash_refresh_token(raw) == hash_refresh_token(raw)
    assert decode_refresh_token(raw) == hash_refresh_token(raw)


def test_refresh_token_malformed_rejected() -> None:
    with pytest.raises(TokenError):
        decode_refresh_token("")
    with pytest.raises(TokenError):
        decode_refresh_token("short")


def test_access_token_ttl_respected() -> None:
    s = Settings(env="test", jwt_secret="a" * 32, jwt_access_ttl_seconds=5)
    _, exp = create_access_token(user_id=uuid.uuid4(), role="client", settings=s)
    # Expiry should be roughly "now + 5s"; we allow a generous window.
    assert timedelta(seconds=1) < (exp - _now_utc()) <= timedelta(seconds=10)


def _now_utc():
    from datetime import UTC, datetime

    return datetime.now(tz=UTC)
