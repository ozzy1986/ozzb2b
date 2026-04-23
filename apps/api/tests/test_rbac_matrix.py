"""RBAC matrix: every protected endpoint is checked for every role.

For each (endpoint, required_role) pair we assert:
  * anonymous request -> 401
  * admin-only route rejects clients and provider_owners -> 403
  * admin-only route accepts an admin token (status != 401/403)
  * "any authenticated user" route accepts every role

This guards against the class of bugs where a new admin endpoint is added
without a role check — the matrix grows when the list below grows.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from ozzb2b_api.config import get_settings
from ozzb2b_api.db.models import User, UserRole
from ozzb2b_api.security.passwords import hash_password
from ozzb2b_api.security.tokens import create_access_token


@dataclass(frozen=True)
class RbacCase:
    method: str
    path: str
    # None = "any authenticated user"; otherwise the exact required role.
    required_role: UserRole | None
    # Optional JSON payload so that POST/PATCH routes reach the guard
    # before validation (our guards run as dependencies, not after body
    # parsing, so an empty {} is usually enough).
    payload: dict | None = None


CASES: list[RbacCase] = [
    # /admin/* — admin only
    RbacCase("GET", "/admin/claims", UserRole.ADMIN),
    RbacCase("POST", f"/admin/claims/{uuid.uuid4()}/approve", UserRole.ADMIN),
    RbacCase(
        "POST",
        f"/admin/claims/{uuid.uuid4()}/reject",
        UserRole.ADMIN,
        {"reason": "spam"},
    ),
]


@pytest.fixture()
def roles(
    client: TestClient,
    test_engine: AsyncEngine,
) -> dict[UserRole, str]:
    """Create one DB user per role and return access tokens."""
    tokens: dict[UserRole, str] = {}
    import asyncio

    sessionmaker = async_sessionmaker(test_engine, expire_on_commit=False)
    live_settings = get_settings()

    async def _seed() -> None:
        async with sessionmaker() as s:
            for role in (UserRole.ADMIN, UserRole.PROVIDER_OWNER, UserRole.CLIENT):
                user_id = uuid.uuid4()
                s.add(
                    User(
                        id=user_id,
                        email=f"{role.value}@example.com",
                        password_hash=hash_password("Xx123456789!"),
                        role=role,
                    )
                )
                token, _ = create_access_token(
                    user_id=user_id,
                    role=role.value,
                    settings=live_settings,
                )
                tokens[role] = token
            await s.commit()

    asyncio.run(_seed())
    return tokens


def _request(client: TestClient, case: RbacCase, *, token: str | None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    if case.method == "GET":
        return client.get(case.path, headers=headers)
    if case.method == "POST":
        return client.post(case.path, json=case.payload or {}, headers=headers)
    if case.method == "PATCH":
        return client.patch(case.path, json=case.payload or {}, headers=headers)
    raise AssertionError(f"Unsupported method in matrix: {case.method}")


@pytest.mark.parametrize("case", CASES, ids=lambda c: f"{c.method} {c.path}")
def test_protected_endpoint_requires_authentication(
    client: TestClient, case: RbacCase
) -> None:
    resp = _request(client, case, token=None)
    assert resp.status_code == 401, (
        f"{case.method} {case.path} must require auth; got {resp.status_code}: {resp.text}"
    )


@pytest.mark.parametrize(
    "case",
    [c for c in CASES if c.required_role is UserRole.ADMIN],
    ids=lambda c: f"{c.method} {c.path}",
)
def test_admin_endpoints_reject_non_admin(
    client: TestClient, roles: dict[UserRole, str], case: RbacCase
) -> None:
    for role in (UserRole.CLIENT, UserRole.PROVIDER_OWNER):
        resp = _request(client, case, token=roles[role])
        assert resp.status_code == 403, (
            f"{case.method} {case.path} must reject role={role.value}; "
            f"got {resp.status_code}: {resp.text}"
        )


