"""Service-layer tests for auth (pure SQLite roundtrip, no FastAPI)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from ozzb2b_api.config import Settings
from ozzb2b_api.db.models import RefreshToken, User
from ozzb2b_api.services import auth as auth_service


@pytest.fixture()
def cfg() -> Settings:
    return Settings(
        env="test",
        jwt_secret="unit-tests-secret-long-enough-for-hmac",
        jwt_access_ttl_seconds=30,
        jwt_refresh_ttl_seconds=300,
    )


async def _make_user(db: AsyncSession) -> User:
    return await auth_service.register(
        db, email="svc@example.com", password="SuperSecret123!", display_name="svc"
    )


async def test_register_and_authenticate(db_session: AsyncSession, cfg: Settings) -> None:
    user = await _make_user(db_session)
    assert user.email == "svc@example.com"
    got = await auth_service.authenticate(
        db_session, email="svc@example.com", password="SuperSecret123!"
    )
    assert got.id == user.id


async def test_authenticate_wrong_password_raises(db_session: AsyncSession) -> None:
    await _make_user(db_session)
    with pytest.raises(auth_service.InvalidCredentialsError):
        await auth_service.authenticate(
            db_session, email="svc@example.com", password="NOPE"
        )


async def test_register_duplicate_email_raises(db_session: AsyncSession) -> None:
    await _make_user(db_session)
    with pytest.raises(auth_service.EmailAlreadyRegisteredError):
        await _make_user(db_session)


async def test_issue_and_rotate_refresh_token(db_session: AsyncSession, cfg: Settings) -> None:
    user = await _make_user(db_session)
    first = await auth_service.issue_tokens(
        db_session, user=user, user_agent="ua", ip_address="1.2.3.4", settings=cfg
    )
    # The initial refresh record must exist and be active.
    _, rotated = await auth_service.rotate_refresh(
        db_session,
        raw_refresh_token=first.refresh_token,
        user_agent="ua",
        ip_address="1.2.3.4",
        settings=cfg,
    )
    assert rotated.refresh_token != first.refresh_token
    # Reusing the old (now revoked) token triggers a family-wide revoke.
    with pytest.raises(auth_service.InvalidRefreshTokenError):
        await auth_service.rotate_refresh(
            db_session,
            raw_refresh_token=first.refresh_token,
            user_agent="ua",
            ip_address="1.2.3.4",
            settings=cfg,
        )
    # Now the freshly issued one is also considered compromised.
    with pytest.raises(auth_service.InvalidRefreshTokenError):
        await auth_service.rotate_refresh(
            db_session,
            raw_refresh_token=rotated.refresh_token,
            user_agent="ua",
            ip_address="1.2.3.4",
            settings=cfg,
        )


async def test_rotate_refresh_rejects_unknown_token(
    db_session: AsyncSession, cfg: Settings
) -> None:
    with pytest.raises(auth_service.InvalidRefreshTokenError):
        await auth_service.rotate_refresh(
            db_session,
            raw_refresh_token="x" * 48,
            user_agent=None,
            ip_address=None,
            settings=cfg,
        )


async def test_rotate_refresh_rejects_expired(
    db_session: AsyncSession, cfg: Settings
) -> None:
    user = await _make_user(db_session)
    issued = await auth_service.issue_tokens(
        db_session, user=user, user_agent=None, ip_address=None, settings=cfg
    )
    # Force-expire the stored record.
    await db_session.execute(
        update(RefreshToken).values(expires_at=datetime.now(tz=UTC) - timedelta(seconds=1))
    )
    with pytest.raises(auth_service.InvalidRefreshTokenError):
        await auth_service.rotate_refresh(
            db_session,
            raw_refresh_token=issued.refresh_token,
            user_agent=None,
            ip_address=None,
            settings=cfg,
        )


async def test_revoke_refresh_is_idempotent(
    db_session: AsyncSession, cfg: Settings
) -> None:
    user = await _make_user(db_session)
    issued = await auth_service.issue_tokens(
        db_session, user=user, user_agent=None, ip_address=None, settings=cfg
    )
    await auth_service.revoke_refresh(db_session, raw_refresh_token=issued.refresh_token)
    await auth_service.revoke_refresh(db_session, raw_refresh_token=issued.refresh_token)
    # Malformed is also safely rejected at rotate_refresh.
    with pytest.raises(auth_service.InvalidRefreshTokenError):
        await auth_service.rotate_refresh(
            db_session,
            raw_refresh_token="short",
            user_agent=None,
            ip_address=None,
            settings=cfg,
        )
    _ = uuid.uuid4()
