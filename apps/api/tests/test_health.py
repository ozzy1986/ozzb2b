"""Health and readiness endpoint contract tests."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "ozzb2b-api"
    assert body["version"]


def test_ready_reports_dependency_statuses(client: TestClient) -> None:
    with (
        patch("ozzb2b_api.routes.health._ping_database", return_value=True),
        patch("ozzb2b_api.routes.health.ping_redis", return_value=True),
        patch("ozzb2b_api.routes.health.ping_meilisearch", return_value=True),
    ):
        response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    dep_names = {d["name"] for d in body["dependencies"]}
    assert dep_names == {"database", "redis", "meilisearch"}
    assert all(d["ok"] for d in body["dependencies"])


def test_ready_returns_503_when_any_dependency_fails(client: TestClient) -> None:
    with (
        patch("ozzb2b_api.routes.health._ping_database", return_value=True),
        patch("ozzb2b_api.routes.health.ping_redis", return_value=False),
        patch("ozzb2b_api.routes.health.ping_meilisearch", return_value=True),
    ):
        response = client.get("/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    by_name = {d["name"]: d["ok"] for d in body["dependencies"]}
    assert by_name["redis"] is False
