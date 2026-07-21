"""End-to-end tests for /auth/* endpoints via TestClient + SQLite."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ozzb2b_api.config import Settings
from ozzb2b_api.routes import auth as auth_routes


def _register(
    client: TestClient, email: str = "user@example.com", password: str = "SuperSecret123!"
) -> dict[str, object]:
    resp = client.post(
        "/auth/register",
        json={"email": email, "password": password, "display_name": "U"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_register_issues_tokens_and_sets_cookies(client: TestClient) -> None:
    body = _register(client)
    assert "access_token" in body
    assert body["user"]["email"] == "user@example.com"
    assert body["user"]["role"] == "client"
    # TestClient exposes set-cookies via .cookies
    assert any(c for c in client.cookies.jar)


def test_production_auth_cookies_are_shared_with_web_origin(
    client: TestClient,
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    production = settings.model_copy(
        update={"env": "production", "auth_cookie_domain": ".ozzb2b.com"},
    )
    monkeypatch.setattr(auth_routes, "get_settings", lambda: production)

    response = client.post(
        "/auth/register",
        json={
            "email": "shared-cookie@example.com",
            "password": "SuperSecret123!",
            "display_name": "U",
        },
    )

    assert response.status_code == 201
    cookies = response.headers.get_list("set-cookie")
    shared_cookies = [cookie for cookie in cookies if "Domain=.ozzb2b.com" in cookie]
    assert len(shared_cookies) == 2
    assert all("HttpOnly" in cookie and "Secure" in cookie for cookie in shared_cookies)
    assert all("SameSite=lax" in cookie for cookie in shared_cookies)


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    _register(client)
    resp = client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "AnotherPass123!"},
    )
    assert resp.status_code == 409


def test_register_rejects_short_password(client: TestClient) -> None:
    resp = client.post(
        "/auth/register",
        json={"email": "x@example.com", "password": "short"},
    )
    assert resp.status_code == 422


def test_login_returns_401_on_wrong_password(client: TestClient) -> None:
    _register(client)
    resp = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "WRONG"},
    )
    assert resp.status_code == 401


def test_login_returns_200_with_correct_password(client: TestClient) -> None:
    _register(client)
    resp = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "SuperSecret123!"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_me_returns_current_user(client: TestClient) -> None:
    body = _register(client)
    token = body["access_token"]
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "user@example.com"


def test_me_rejects_missing_token(client: TestClient) -> None:
    assert client.get("/auth/me").status_code == 401


def test_me_rejects_bad_token(client: TestClient) -> None:
    resp = client.get("/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401


def test_session_returns_null_for_anonymous_user(client: TestClient) -> None:
    response = client.get("/auth/session")

    assert response.status_code == 200
    assert response.json() is None


def test_session_returns_authenticated_user(client: TestClient) -> None:
    body = _register(client)
    response = client.get(
        "/auth/session",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"


def test_logout_returns_204(client: TestClient) -> None:
    _register(client)
    resp = client.post("/auth/logout")
    assert resp.status_code == 204
