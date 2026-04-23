"""Smoke / contract tests for unauthenticated public endpoints.

These guard against regressions where a route is silently removed, renamed or
changed from list to envelope. We deliberately hit an empty in-process DB so
any response body that depends on seed data is asserted as "empty-list-shape".
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    ("path", "expected_type"),
    [
        ("/countries", list),
        ("/categories", list),
        ("/categories/tree", list),
        ("/cities", list),
        ("/legal-forms", list),
    ],
)
def test_public_list_endpoints_return_list(
    client: TestClient, path: str, expected_type: type
) -> None:
    resp = client.get(path)
    assert resp.status_code == 200, resp.text
    assert isinstance(resp.json(), expected_type)


# /providers uses Postgres-only types (TSVECTOR, JSONB), so it is covered by
# the Postgres-backed integration tests (not runnable on SQLite). We keep only
# envelope shape testing via the OpenAPI snapshot here.


def test_auth_me_requires_authentication(client: TestClient) -> None:
    resp = client.get("/auth/me")
    assert resp.status_code == 401
    assert "detail" in resp.json()


def test_chat_requires_authentication(client: TestClient) -> None:
    resp = client.get("/chat/conversations")
    assert resp.status_code == 401


def test_admin_endpoints_require_authentication(client: TestClient) -> None:
    for path in (
        "/admin/analytics/summary",
        "/admin/analytics/top-searches",
        "/admin/analytics/top-providers",
        "/admin/claims",
    ):
        resp = client.get(path)
        assert resp.status_code in {401, 403}, f"{path}: {resp.status_code} {resp.text}"


def test_docs_not_exposed_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    from ozzb2b_api.app import create_app
    from ozzb2b_api.config import Settings

    app = create_app(
        Settings(
            env="production",
            log_level="WARNING",
            database_url="sqlite+aiosqlite:///:memory:",
        )
    )
    with TestClient(app) as c:
        assert c.get("/docs").status_code == 404


def test_openapi_json_always_available(client: TestClient) -> None:
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/json")


def test_metrics_are_available(client: TestClient) -> None:
    resp = client.get("/metrics")
    assert resp.status_code == 200
