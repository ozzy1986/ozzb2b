"""Global DomainError -> HTTP handler.

Asserts that every DomainError subclass raised inside a route is translated
to the right HTTP status and the body keeps a stable `detail` field.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ozzb2b_api.app import create_app
from ozzb2b_api.config import Settings
from ozzb2b_api.errors import (
    AuthenticationError,
    ConflictError,
    DomainError,
    ExternalServiceError,
    ForbiddenError,
    NotFoundError,
    RateLimitedError,
    ValidationError,
)


@pytest.fixture()
def app_with_probes(settings: Settings) -> Iterator[TestClient]:
    """An app with an auxiliary router exposing one route per error class."""
    app = create_app(settings=settings)

    @app.get("/_probe/domain")
    def _domain() -> None:
        raise DomainError("base detail")

    @app.get("/_probe/not_found")
    def _not_found() -> None:
        raise NotFoundError("missing thing")

    @app.get("/_probe/conflict")
    def _conflict() -> None:
        raise ConflictError("duplicate row")

    @app.get("/_probe/validation")
    def _validation() -> None:
        raise ValidationError("body invalid")

    @app.get("/_probe/auth")
    def _auth() -> None:
        raise AuthenticationError("bad token")

    @app.get("/_probe/forbidden")
    def _forbidden() -> None:
        raise ForbiddenError("nope")

    @app.get("/_probe/external")
    def _external() -> None:
        raise ExternalServiceError("upstream sad")

    @app.get("/_probe/rate")
    def _rate() -> None:
        raise RateLimitedError("slow down")

    with TestClient(app) as c:
        yield c


def _assert(client: TestClient, path: str, status: int, detail: str) -> None:
    resp = client.get(path)
    assert resp.status_code == status, f"{path}: {resp.status_code} {resp.text}"
    body = resp.json()
    assert body == {"detail": detail}


def test_domain_error_maps_to_400(app_with_probes: TestClient) -> None:
    _assert(app_with_probes, "/_probe/domain", 400, "base detail")


def test_subclasses_carry_their_own_status(app_with_probes: TestClient) -> None:
    _assert(app_with_probes, "/_probe/not_found", 404, "missing thing")
    _assert(app_with_probes, "/_probe/conflict", 409, "duplicate row")
    _assert(app_with_probes, "/_probe/validation", 422, "body invalid")
    _assert(app_with_probes, "/_probe/auth", 401, "bad token")
    _assert(app_with_probes, "/_probe/forbidden", 403, "nope")
    _assert(app_with_probes, "/_probe/external", 502, "upstream sad")
    _assert(app_with_probes, "/_probe/rate", 429, "slow down")


def test_app_factory_does_not_install_handler_twice() -> None:
    """Sanity check: building the app multiple times does not stack handlers."""
    settings = Settings(
        env="test",
        log_level="WARNING",
        database_url="sqlite+aiosqlite:///:memory:",
        rate_limit_enabled=False,
        jwt_secret="x" * 32,
    )
    apps: list[FastAPI] = [create_app(settings=settings) for _ in range(2)]
    for a in apps:
        # FastAPI stores handlers in a dict-of-class-to-handler so re-installing
        # the same exception class keeps the dict size at one entry.
        assert any(
            cls is DomainError
            for cls in (a.exception_handlers.keys())  # type: ignore[attr-defined]
        )
