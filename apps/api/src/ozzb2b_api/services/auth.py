"""Auth service: register, authenticate, refresh, logout."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ozzb2b_api.config import Settings, get_settings
from ozzb2b_api.db.models import RefreshToken, User, UserRole
from ozzb2b_api.security.passwords import hash_password, verify_password
from ozzb2b_api.security.tokens import (
    TokenError,
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
)


class AuthError(Exception):
    """Domain error for the auth service."""


class EmailAlreadyRegisteredError(AuthError):
    pass


class InvalidCredentialsError(AuthError):
    pass


class InvalidRefreshTokenError(AuthError):
    pass


@dataclass(frozen=True)
class IssuedTokens:
    access_token: str
    access_expires_at: datetime
    refresh_token: str
    refresh_expires_at: datetime


async def register(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    display_name: str | None,
    settings: Settings | None = None,
) -> User:
    cfg = settings or get_settings()
    email_norm = email.strip().lower()
    existing = (
        await session.execute(select(User).where(User.email == email_norm))
    ).scalar_one_or_none()
    if existing is not None:
        raise EmailAlreadyRegisteredError("email already registered")
    user = User(
        id=uuid.uuid4(),
        email=email_norm,
        password_hash=hash_password(password),
        display_name=display_name,
        role=UserRole.CLIENT,
    )
    session.add(user)
    await session.flush()
    _ = cfg  # reserved for future flags
    return user


async def authenticate(session: AsyncSession, *, email: str, password: str) -> User:
    email_norm = email.strip().lower()
    user = (
        await session.execute(select(User).where(User.email == email_norm))
    ).scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError("invalid email or password")
    await session.execute(
        update(User).where(User.id == user.id).values(last_login_at=datetime.now(tz=UTC))
    )
    return user


async def issue_tokens(
    session: AsyncSession,
    *,
    user: User,
    user_agent: str | None,
    ip_address: str | None,
    family_id: uuid.UUID | None = None,
    settings: Settings | None = None,
) -> IssuedTokens:
    cfg = settings or get_settings()
    access_token, access_exp = create_access_token(user_id=user.id, role=user.role.value, settings=cfg)
    refresh_raw, refresh_exp = create_refresh_token(settings=cfg)
    refresh_hash = hash_refresh_token(refresh_raw)
    record = RefreshToken(
        id=uuid.uuid4(),
        user_id=user.id,
        token_hash=refresh_hash,
        family_id=family_id or uuid.uuid4(),
        expires_at=refresh_exp,
        user_agent=(user_agent or None),
        ip_address=(ip_address or None),
    )
    session.add(record)
    await session.flush()
    return IssuedTokens(
        access_token=access_token,
        access_expires_at=access_exp,
        refresh_token=refresh_raw,
        refresh_expires_at=refresh_exp,
    )


async def _lookup_active_refresh(session: AsyncSession, token_hash: str) -> RefreshToken | None:
    stmt = select(RefreshToken).where(
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked_at.is_(None),
        RefreshToken.expires_at > datetime.now(tz=UTC),
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def rotate_refresh(
    session: AsyncSession,
    *,
    raw_refresh_token: str,
    user_agent: str | None,
    ip_address: str | None,
    settings: Settings | None = None,
) -> tuple[User, IssuedTokens]:
    """Rotate the refresh token (reuse-detection friendly).

    On success: revoke the current token, issue a new pair in the same family.
    On reuse of a revoked token: revoke the entire family as a theft signal.
    """
    try:
        token_hash = hash_refresh_token(raw_refresh_token)
    except TokenError as exc:
        raise InvalidRefreshTokenError(str(exc)) from exc

    existing = (
        await session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
    ).scalar_one_or_none()
    if existing is None:
        raise InvalidRefreshTokenError("refresh token not found")
    if existing.revoked_at is not None:
        # Theft signal: revoke the whole family.
        await session.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == existing.family_id)
            .values(revoked_at=datetime.now(tz=UTC))
        )
        raise InvalidRefreshTokenError("refresh token already used")
    if existing.expires_at <= datetime.now(tz=UTC):
        raise InvalidRefreshTokenError("refresh token expired")

    user = (await session.execute(select(User).where(User.id == existing.user_id))).scalar_one_or_none()
    if user is None:
        raise InvalidRefreshTokenError("user not found")

    # Revoke current and issue a new pair under the same family.
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.id == existing.id)
        .values(revoked_at=datetime.now(tz=UTC))
    )
    tokens = await issue_tokens(
        session,
        user=user,
        user_agent=user_agent,
        ip_address=ip_address,
        family_id=existing.family_id,
        settings=settings,
    )
    return user, tokens


async def revoke_refresh(session: AsyncSession, *, raw_refresh_token: str) -> None:
    token_hash = hash_refresh_token(raw_refresh_token)
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == token_hash, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(tz=UTC))
    )
