"""Tests for the matcher-backed re-rank path in `services/search.maybe_rerank`.

These tests stub the gRPC client with an in-process fake so they exercise the
wiring (score extraction, ordering, invariants) without any network.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

import pytest

from ozzb2b_api.clients.matcher import (
    MatcherCandidate,
    MatcherScore,
    MatcherUnavailableError,
)
from ozzb2b_api.config import get_settings
from ozzb2b_api.services.search import (
    SearchHit,
    SearchQuery,
    SearchResult,
    maybe_rerank,
)


@dataclass
class _FakeCategory:
    slug: str


@dataclass
class _FakeCountry:
    code: str


@dataclass
class _FakeCity:
    slug: str


@dataclass
class _FakeLegalForm:
    code: str


@dataclass
class _FakeProvider:
    id: uuid.UUID
    display_name: str
    description: str
    categories: list[_FakeCategory] = field(default_factory=list)
    country: _FakeCountry | None = None
    city: _FakeCity | None = None
    legal_form: _FakeLegalForm | None = None


class _FakeMatcherClient:
    def __init__(self, scores: list[MatcherScore]) -> None:
        self.scores = scores
        self.calls: list[dict[str, Any]] = []

    async def rank(self, **kwargs: Any) -> list[MatcherScore]:
        self.calls.append(kwargs)
        return self.scores


class _FailingMatcherClient:
    async def rank(self, **_: Any) -> list[MatcherScore]:
        raise MatcherUnavailableError("boom")


@pytest.fixture(autouse=True)
def _enable_matcher(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("OZZB2B_MATCHER_ENABLED", "true")
    yield
    get_settings.cache_clear()


def _providers() -> tuple[list[_FakeProvider], list[SearchHit]]:
    ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]
    providers = [
        _FakeProvider(
            id=ids[0],
            display_name="Alpha IT",
            description="Software",
            categories=[_FakeCategory("it")],
            country=_FakeCountry("RU"),
            city=_FakeCity("moscow"),
            legal_form=_FakeLegalForm("OOO"),
        ),
        _FakeProvider(
            id=ids[1],
            display_name="Beta Legal",
            description="Law",
            categories=[_FakeCategory("legal")],
            country=_FakeCountry("RU"),
        ),
        _FakeProvider(
            id=ids[2],
            display_name="Gamma IT",
            description="Dev shop",
            categories=[_FakeCategory("it")],
            country=_FakeCountry("RU"),
        ),
    ]
    hits = [SearchHit(provider_id=p.id, score=0.9 - i * 0.1) for i, p in enumerate(providers)]
    return providers, hits


async def test_maybe_rerank_reorders_using_matcher_scores() -> None:
    providers, hits = _providers()
    scores_in_matcher_order = [
        MatcherScore(provider_id=providers[2].id, score=9.0, matcher_score=9.0),
        MatcherScore(provider_id=providers[0].id, score=5.0, matcher_score=5.0),
        MatcherScore(provider_id=providers[1].id, score=1.0, matcher_score=1.0),
    ]
    fake = _FakeMatcherClient(scores_in_matcher_order)

    query = SearchQuery(q="it", category_slugs=("it",))
    result = SearchResult(total=3, hits=hits, engine="meilisearch")

    out = await maybe_rerank(query, result, providers, client=fake)  # type: ignore[arg-type]
    assert [h.provider_id for h in out.hits] == [
        providers[2].id,
        providers[0].id,
        providers[1].id,
    ]
    assert out.engine == "meilisearch+matcher"
    assert out.total == 3
    # The client got populated candidates with the right feature set.
    assert fake.calls
    passed = fake.calls[0]
    assert passed["query"] == "it"
    assert passed["category_slugs"] == ("it",)
    sent_ids = {c.provider_id for c in passed["candidates"]}
    assert sent_ids == {p.id for p in providers}
    it_candidates = [c for c in passed["candidates"] if c.display_name == "Alpha IT"]
    assert it_candidates and it_candidates[0].category_slugs == ("it",)
    assert isinstance(it_candidates[0], MatcherCandidate)


async def test_maybe_rerank_keeps_original_on_matcher_failure() -> None:
    providers, hits = _providers()
    query = SearchQuery(q="anything")
    result = SearchResult(total=3, hits=hits, engine="meilisearch")
    out = await maybe_rerank(query, result, providers, client=_FailingMatcherClient())  # type: ignore[arg-type]
    assert out is result


async def test_maybe_rerank_disabled_when_flag_off(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("OZZB2B_MATCHER_ENABLED", "false")
    get_settings.cache_clear()

    providers, hits = _providers()
    fake = _FakeMatcherClient([])
    query = SearchQuery(q="anything")
    result = SearchResult(total=3, hits=hits, engine="meilisearch")
    out = await maybe_rerank(query, result, providers, client=fake)  # type: ignore[arg-type]
    assert out is result
    assert fake.calls == []
