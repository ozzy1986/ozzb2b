"""JWT access tokens + opaque refresh tokens.

Access tokens are short-lived signed JWTs carrying the subject user id and role.
Refresh tokens are opaque random strings; only their SHA-256 hash is stored in the
database (row in `refresh_tokens`), so a DB leak does not yield valid tokens.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt

from ozzb2b_api.config import Settings, get_settings

TOKEN_TYPE_ACCESS = "access"  # nosec B105 - token type label, not a credential
TOKEN_TYPE_REFRESH = "refresh"  # nosec B105 - token type label, not a credential
TOKEN_TYPE_WS_CHAT = "ws_chat"  # nosec B105 - token type label, not a credential
WS_CHAT_TTL_SECONDS = 120  # handshake-only; the live WS connection lives longer


class TokenError(Exception):
    """Raised when a token is invalid/expired/tampered."""


@dataclass(frozen=True)
class AccessTokenClaims:
    sub: str
    role: str
    exp: datetime
    jti: str


@dataclass(frozen=True)
class WsChatClaims:
    """Short-lived claims for the chat WebSocket handshake.

    Bound to a specific `conversation_id` + `user_id` so a leaked token
    cannot be replayed on another conversation.
    """

    user_id: str
    conversation_id: str
    exp: datetime
    jti: str


def _now() -> datetime:
    return datetime.now(tz=UTC)


def create_access_token(
    *,
    user_id: uuid.UUID,
    role: str,
    settings: Settings | None = None,
) -> tuple[str, datetime]:
    """Return a signed access JWT and its expiry."""
    cfg = settings or get_settings()
    expires_at = _now() + timedelta(seconds=cfg.jwt_access_ttl_seconds)
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expires_at,
        "iat": _now(),
        "jti": secrets.token_urlsafe(16),
        "typ": TOKEN_TYPE_ACCESS,
    }
    token = jwt.encode(payload, cfg.jwt_secret, algorithm=cfg.jwt_algorithm)
    return token, expires_at


def decode_access_token(token: str, *, settings: Settings | None = None) -> AccessTokenClaims:
    cfg = settings or get_settings()
    try:
        payload = jwt.decode(token, cfg.jwt_secret, algorithms=[cfg.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise TokenError(str(exc)) from exc
    if payload.get("typ") != TOKEN_TYPE_ACCESS:
        raise TokenError("unexpected token type")
    sub = payload.get("sub")
    role = payload.get("role")
    exp = payload.get("exp")
    jti = payload.get("jti")
    if not isinstance(sub, str) or not isinstance(role, str) or not isinstance(jti, str):
        raise TokenError("malformed token payload")
    return AccessTokenClaims(
        sub=sub,
        role=role,
        exp=datetime.fromtimestamp(exp, tz=UTC) if exp else _now(),
        jti=jti,
    )


def create_ws_chat_token(
    *,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
    settings: Settings | None = None,
) -> tuple[str, datetime]:
    """Issue a short-lived JWT for connecting the chat WebSocket."""
    cfg = settings or get_settings()
    expires_at = _now() + timedelta(seconds=WS_CHAT_TTL_SECONDS)
    payload = {
        "sub": str(user_id),
        "conv": str(conversation_id),
        "exp": expires_at,
        "iat": _now(),
        "jti": secrets.token_urlsafe(12),
        "typ": TOKEN_TYPE_WS_CHAT,
    }
    token = jwt.encode(payload, cfg.jwt_secret, algorithm=cfg.jwt_algorithm)
    return token, expires_at


def decode_ws_chat_token(token: str, *, settings: Settings | None = None) -> WsChatClaims:
    cfg = settings or get_settings()
    try:
        payload = jwt.decode(token, cfg.jwt_secret, algorithms=[cfg.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise TokenError(str(exc)) from exc
    if payload.get("typ") != TOKEN_TYPE_WS_CHAT:
        raise TokenError("unexpected token type")
    sub = payload.get("sub")
    conv = payload.get("conv")
    exp = payload.get("exp")
    jti = payload.get("jti")
    if not isinstance(sub, str) or not isinstance(conv, str) or not isinstance(jti, str):
        raise TokenError("malformed token payload")
    return WsChatClaims(
        user_id=sub,
        conversation_id=conv,
        exp=datetime.fromtimestamp(exp, tz=UTC) if exp else _now(),
        jti=jti,
    )


def create_refresh_token(*, settings: Settings | None = None) -> tuple[str, datetime]:
    """Create an opaque refresh token and its expiry timestamp."""
    cfg = settings or get_settings()
    raw = secrets.token_urlsafe(48)
    expires_at = _now() + timedelta(seconds=cfg.jwt_refresh_ttl_seconds)
    return raw, expires_at


def hash_refresh_token(token: str) -> str:
    """Return a stable hex SHA-256 digest of the raw refresh token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def decode_refresh_token(token: str) -> str:
    """Validate structural integrity of a refresh token and return its hash.

    We only need a minimum length check: the real validation is a DB lookup
    for the hash plus expiry/revocation checks.
    """
    if not token or len(token) < 32:
        raise TokenError("refresh token malformed")
    return hash_refresh_token(token)
