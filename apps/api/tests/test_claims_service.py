"""Pure-logic tests for the claim service helpers.

We keep these tests Postgres-free by exercising the in-memory helpers
(extract_token_from_html, user_may_edit_provider, _hash_token_equivalence).
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from typing import cast

from ozzb2b_api.db.models import User, UserRole
from ozzb2b_api.services.claims import (
    META_TAG_NAME,
    _hash_token,
    extract_token_from_html,
    user_may_edit_provider,
)


def _user(role: UserRole = UserRole.CLIENT) -> User:
    return User(
        id=uuid.uuid4(),
        email=f"u-{uuid.uuid4().hex[:6]}@example.com",
        password_hash="x",
        role=role,
    )


def _provider(*, claimed_by: uuid.UUID | None = None, is_claimed: bool = False) -> object:
    return SimpleNamespace(
        id=uuid.uuid4(),
        is_claimed=is_claimed,
        claimed_by_user_id=claimed_by,
    )


def test_extracts_token_when_name_before_content() -> None:
    html = f"""
    <html><head>
      <meta name="{META_TAG_NAME}" content="ozzb2b-abc123">
    </head></html>
    """
    assert extract_token_from_html(html) == "ozzb2b-abc123"


def test_extracts_token_when_content_before_name() -> None:
    html = f"""
    <html><head>
      <meta content="ozzb2b-xyz789" name="{META_TAG_NAME}"/>
    </head></html>
    """
    assert extract_token_from_html(html) == "ozzb2b-xyz789"


def test_extract_is_case_insensitive_for_meta_attribute_order() -> None:
    html = f'<META NAME="{META_TAG_NAME.upper()}" CONTENT="ozzb2b-UP">'
    assert extract_token_from_html(html) == "ozzb2b-UP"


def test_extract_returns_none_without_tag() -> None:
    assert extract_token_from_html("<html><body>no tag</body></html>") is None
    assert extract_token_from_html("") is None


def test_hash_token_is_deterministic_and_differs_by_input() -> None:
    assert _hash_token("abc") == _hash_token("abc")
    assert _hash_token("abc") != _hash_token("abd")


def test_owner_may_edit_when_claim_matches_user() -> None:
    user = _user()
    provider = _provider(claimed_by=user.id, is_claimed=True)
    assert user_may_edit_provider(user, cast(object, provider)) is True  # type: ignore[arg-type]


def test_non_owner_may_not_edit_claimed_provider() -> None:
    owner = _user()
    other = _user()
    provider = _provider(claimed_by=owner.id, is_claimed=True)
    assert user_may_edit_provider(other, cast(object, provider)) is False  # type: ignore[arg-type]


def test_admin_may_edit_any_provider() -> None:
    admin = _user(role=UserRole.ADMIN)
    # Provider not even claimed yet; admin still allowed.
    provider = _provider(is_claimed=False)
    assert user_may_edit_provider(admin, cast(object, provider)) is True  # type: ignore[arg-type]


def test_user_may_not_edit_unclaimed_provider() -> None:
    user = _user()
    provider = _provider(is_claimed=False)
    assert user_may_edit_provider(user, cast(object, provider)) is False  # type: ignore[arg-type]
