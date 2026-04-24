"""HTTP-level tests for the /search route.

We stub the search service so the test exercises serialisation, rate
limiting and the response envelope without standing up Meilisearch.
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from ozzb2b_api.services import search as search_service


def _hit(provider_id: uuid.UUID) -> search_service.SearchHit:
    return search_service.SearchHit(provider_id=provider_id, score=0.5)


def _provider(provider_id: uuid.UUID, slug: str) -> Any:
    return SimpleNamespace(
        id=provider_id,
        slug=slug,
        display_name=slug.title(),
        description=None,
        country=SimpleNamespace(id=1, code="RU", name="Россия", slug="ru"),
        city=None,
        legal_form=None,
        year_founded=None,
        employee_count_range=None,
        logo_url=None,
        categories=[],
        last_scraped_at=None,
    )


@pytest.fixture()
def stub_search(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Replace `services.search.{search,hydrate_providers,maybe_rerank}` with stubs."""
    pid_a = uuid.uuid4()
    pid_b = uuid.uuid4()
    seen: dict[str, Any] = {}

    async def fake_search(_db: Any, q: search_service.SearchQuery) -> search_service.SearchResult:
        seen["query"] = q
        return search_service.SearchResult(
            total=2,
            hits=[_hit(pid_a), _hit(pid_b)],
            engine="meilisearch",
        )

    async def fake_hydrate(_db: Any, ids: list[uuid.UUID]) -> list[Any]:
        m = {pid_a: _provider(pid_a, "alpha"), pid_b: _provider(pid_b, "beta")}
        return [m[i] for i in ids if i in m]

    async def fake_maybe_rerank(
        _q: Any,
        result: search_service.SearchResult,
        _providers: Any,
        **_: Any,
    ) -> search_service.SearchResult:
        return result

    monkeypatch.setattr(search_service, "search", fake_search)
    monkeypatch.setattr(search_service, "hydrate_providers", fake_hydrate)
    monkeypatch.setattr(search_service, "maybe_rerank", fake_maybe_rerank)
    return seen


def test_search_returns_summary_envelope(client: TestClient, stub_search: dict[str, Any]) -> None:
    resp = client.get("/search", params={"q": "test", "limit": 10, "offset": 0})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 2
    assert body["limit"] == 10
    assert body["offset"] == 0
    assert body["engine"] == "meilisearch"
    slugs = [item["slug"] for item in body["items"]]
    assert sorted(slugs) == ["alpha", "beta"]
    # Filters reach the service unchanged.
    assert stub_search["query"].q == "test"


def test_search_validates_required_query(client: TestClient) -> None:
    resp = client.get("/search")
    assert resp.status_code == 422


def test_search_caps_limit(client: TestClient, stub_search: dict[str, Any]) -> None:
    resp = client.get("/search", params={"q": "x", "limit": 9999})
    assert resp.status_code == 422


def test_search_passes_filters_to_service(
    client: TestClient, stub_search: dict[str, Any]
) -> None:
    resp = client.get(
        "/search",
        params={
            "q": "x",
            "category": ["it", "legal"],
            "country": ["RU"],
            "city": ["moscow"],
            "legal_form": ["OOO"],
        },
    )
    assert resp.status_code == 200
    sent = stub_search["query"]
    assert sent.category_slugs == ("it", "legal")
    assert sent.country_codes == ("RU",)
    assert sent.city_slugs == ("moscow",)
    assert sent.legal_form_codes == ("OOO",)
