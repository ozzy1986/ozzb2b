"""Unit tests for chat-service access rules and business logic.

We exercise the pure logic of `_can_access` against hand-built objects to
avoid pulling in Postgres-only types (TSVECTOR / JSONB in Provider).
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from typing import Any, cast

from ozzb2b_api.db.models import User, UserRole
from ozzb2b_api.services.chat import _can_access


def _user(role: UserRole = UserRole.CLIENT) -> User:
    u = User(
        id=uuid.uuid4(),
        email=f"u-{uuid.uuid4().hex[:6]}@example.com",
        password_hash="x",
        role=role,
    )
    return u


def _conversation(*, user_id: uuid.UUID, provider_id: uuid.UUID) -> Any:
    return SimpleNamespace(user_id=user_id, provider_id=provider_id)


def _provider(claimed_by: uuid.UUID | None = None) -> Any:
    return SimpleNamespace(id=uuid.uuid4(), claimed_by_user_id=claimed_by)


def test_client_can_access_own_conversation() -> None:
    client = _user()
    provider = _provider()
    conv = _conversation(user_id=client.id, provider_id=provider.id)
    assert _can_access(cast(Any, conv), client, cast(Any, provider)) is True


def test_stranger_cannot_access_conversation() -> None:
    owner = _user()
    stranger = _user()
    provider = _provider()
    conv = _conversation(user_id=owner.id, provider_id=provider.id)
    assert _can_access(cast(Any, conv), stranger, cast(Any, provider)) is False


def test_provider_owner_can_access_conversation() -> None:
    client = _user()
    provider_owner = _user(role=UserRole.PROVIDER_OWNER)
    provider = _provider(claimed_by=provider_owner.id)
    conv = _conversation(user_id=client.id, provider_id=provider.id)
    assert _can_access(cast(Any, conv), provider_owner, cast(Any, provider)) is True


def test_admin_can_access_any_conversation() -> None:
    admin = _user(role=UserRole.ADMIN)
    provider = _provider()
    conv = _conversation(user_id=uuid.uuid4(), provider_id=provider.id)
    assert _can_access(cast(Any, conv), admin, cast(Any, provider)) is True


def test_provider_owner_of_other_provider_cannot_access() -> None:
    client = _user()
    some_owner = _user(role=UserRole.PROVIDER_OWNER)
    this_provider = _provider(claimed_by=uuid.uuid4())  # owned by someone else
    conv = _conversation(user_id=client.id, provider_id=this_provider.id)
    assert _can_access(cast(Any, conv), some_owner, cast(Any, this_provider)) is False
