"""HTTP-level tests for /admin routes (analytics + scrape trigger).

ClickHouse and Celery are stubbed so the tests stay hermetic.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from ozzb2b_api.config import get_settings
from ozzb2b_api.db.models import User, UserRole
from ozzb2b_api.security.passwords import hash_password
from ozzb2b_api.security.tokens import create_access_token


@pytest.fixture()
def admin_token(test_engine: AsyncEngine) -> str:
    """Seed an admin user and return a fresh access token for it."""
    import asyncio

    sm = async_sessionmaker(test_engine, expire_on_commit=False)
    user_id = uuid.uuid4()

    async def _seed() -> None:
        async with sm() as s:
            s.add(
                User(
                    id=user_id,
                    email="admin-tests@example.com",
                    password_hash=hash_password("Xx12345678!"),
                    role=UserRole.ADMIN,
                )
            )
            await s.commit()

    asyncio.run(_seed())
    cfg = get_settings()
    token, _ = create_access_token(user_id=user_id, role=UserRole.ADMIN.value, settings=cfg)
    return token


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_analytics_summary_returns_envelope(
    client: TestClient,
    admin_token: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ozzb2b_api.services import analytics as svc

    async def fake_counts(*, days: int) -> list[Any]:
        assert days == 7
        return [
            type("Row", (), {"event_type": "search_performed", "count": 3})(),
            type("Row", (), {"event_type": "provider_viewed", "count": 5})(),
        ]

    monkeypatch.setattr(svc, "event_type_counts", fake_counts)

    resp = client.get("/admin/analytics/summary", headers=_auth(admin_token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["days"] == 7
    assert {item["event_type"] for item in body["items"]} == {
        "search_performed",
        "provider_viewed",
    }


def test_scrape_trigger_calls_celery_wrapper(
    client: TestClient,
    admin_token: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ozzb2b_api.clients import scraper_jobs

    fake = AsyncMock(return_value=scraper_jobs.ScrapeJob(task_id="abc-123"))
    monkeypatch.setattr(scraper_jobs, "enqueue_crawl_source", fake)

    resp = client.post(
        "/admin/scrape",
        headers=_auth(admin_token),
        json={"source_slug": "ru-it", "limit": 5},
    )
    assert resp.status_code == 202, resp.text
    assert resp.json() == {"task_id": "abc-123", "source_slug": "ru-it"}
    fake.assert_awaited_once_with("ru-it", 5)


def test_scrape_all_calls_celery_wrapper(
    client: TestClient,
    admin_token: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ozzb2b_api.clients import scraper_jobs

    fake = AsyncMock(return_value=scraper_jobs.ScrapeJob(task_id="xyz-9"))
    monkeypatch.setattr(scraper_jobs, "enqueue_crawl_all", fake)

    resp = client.post(
        "/admin/scrape/all",
        headers=_auth(admin_token),
        json={"limit": 100},
    )
    assert resp.status_code == 202
    assert resp.json() == {"task_id": "xyz-9"}
    fake.assert_awaited_once_with(100)
