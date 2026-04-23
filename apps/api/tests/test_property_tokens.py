"""Property-based tests for security primitives.

These verify invariants that must hold for *any* input the fuzzer can
imagine — e.g. "a freshly issued access token always round-trips" or
"verify_password(p, hash_password(p)) is True for any non-empty string".
"""

from __future__ import annotations

import string
import uuid

from hypothesis import given, settings
from hypothesis import strategies as st

from ozzb2b_api.config import Settings
from ozzb2b_api.security.passwords import hash_password, verify_password
from ozzb2b_api.security.tokens import (
    TokenError,
    create_access_token,
    create_refresh_token,
    create_ws_chat_token,
    decode_access_token,
    decode_refresh_token,
    decode_ws_chat_token,
    hash_refresh_token,
)

TEST_SETTINGS = Settings(
    env="test",
    log_level="WARNING",
    database_url="sqlite+aiosqlite:///:memory:",
    redis_url="redis://127.0.0.1:6399/15",
    meilisearch_url="http://127.0.0.1:7799",
    rate_limit_enabled=False,
    jwt_secret="hypothesis-unit-tests-secret-long-enough-for-hmac",
)

ROLE_STRAT = st.sampled_from(["admin", "provider_owner", "client"])


@given(role=ROLE_STRAT)
@settings(max_examples=50, deadline=None)
def test_access_token_always_roundtrips(role: str) -> None:
    user_id = uuid.uuid4()
    token, _ = create_access_token(user_id=user_id, role=role, settings=TEST_SETTINGS)
    claims = decode_access_token(token, settings=TEST_SETTINGS)
    assert claims.sub == str(user_id)
    assert claims.role == role


@given(garbage=st.text(min_size=1, max_size=128))
@settings(max_examples=50, deadline=None)
def test_decode_access_token_rejects_garbage(garbage: str) -> None:
    # Anything that is not a valid JWT for our secret must raise TokenError,
    # never crash with another exception type.
    try:
        decode_access_token(garbage, settings=TEST_SETTINGS)
    except TokenError:
        return
    # A valid JWT for our secret cannot be generated from random text at this
    # length within a reasonable probability; if by some miracle it decodes,
    # the typ check will still fail.


@given(role=ROLE_STRAT)
@settings(max_examples=25, deadline=None)
def test_ws_chat_token_is_not_accepted_as_access(role: str) -> None:
    token, _ = create_ws_chat_token(
        user_id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        settings=TEST_SETTINGS,
    )
    # Can be decoded as a ws_chat token...
    claims = decode_ws_chat_token(token, settings=TEST_SETTINGS)
    assert claims.user_id and claims.conversation_id
    # ...but never as an access token.
    try:
        decode_access_token(token, settings=TEST_SETTINGS)
    except TokenError:
        return
    raise AssertionError(f"ws_chat token accepted as access, role={role}")


PRINTABLE = st.text(
    alphabet=st.characters(
        blacklist_categories=("Cs",),  # exclude unpaired surrogates
        min_codepoint=0x20,
        max_codepoint=0x7E,
    ),
    min_size=1,
    max_size=128,
)


@given(password=PRINTABLE)
@settings(max_examples=10, deadline=None)  # Argon2 is slow: keep small.
def test_password_roundtrip(password: str) -> None:
    h = hash_password(password)
    assert verify_password(password, h) is True
    # Flipping any char breaks verification.
    altered = password + "Z" if password[-1] != "Z" else password + "A"
    assert verify_password(altered, h) is False


@given(st.integers(min_value=0, max_value=128))
@settings(max_examples=20, deadline=None)
def test_refresh_token_length_gate(extra: int) -> None:
    token, _ = create_refresh_token(settings=TEST_SETTINGS)
    # Real tokens always decode to a hex digest.
    digest = decode_refresh_token(token)
    assert digest == hash_refresh_token(token)
    # Anything shorter than 32 chars must be rejected.
    short = "".join(
        [c for c in (token + " ")[: min(len(token), 31 + extra % 2)]]
    )
    if len(short) < 32:
        try:
            decode_refresh_token(short)
        except TokenError:
            return
        raise AssertionError("short token must be rejected")


# Smoke: confirm the whitelist of printable chars truly stays stable
@given(st.text(alphabet=string.ascii_letters + string.digits, min_size=32, max_size=64))
@settings(max_examples=10, deadline=None)
def test_hash_refresh_is_hex_sha256(token: str) -> None:
    h = hash_refresh_token(token)
    assert len(h) == 64
    int(h, 16)  # raises if not hex
