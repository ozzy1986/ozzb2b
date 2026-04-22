"""Tests for regional RU IT seed source."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest

from ozzb2b_scraper.spiders.ru_regional_it_seed import SEED_ENTRIES, RuRegionalItSeedSpider


@dataclass
class _FakeResponse:
    text: str


class _FakeFetcher:
    def __init__(self, responses: dict[str, str] | None = None) -> None:
        self.responses = responses or {}
        self.calls: list[str] = []

    async def get(self, url: str) -> _FakeResponse:
        self.calls.append(url)
        return _FakeResponse(text=self.responses.get(url, "<html></html>"))


def _ctx(fetcher: Any, limit: int | None = None) -> Any:
    return SimpleNamespace(fetcher=fetcher, limit=limit)


def test_seed_entries_are_valid() -> None:
    assert len(SEED_ENTRIES) >= 6
    for item in SEED_ENTRIES:
        assert item.website.startswith("https://")
        assert item.city_name
        assert item.source_id == item.source_id.lower()
        assert "it" in item.category_slugs


@pytest.mark.asyncio
async def test_spider_respects_limit() -> None:
    fetcher = _FakeFetcher()
    rows = [row async for row in RuRegionalItSeedSpider().crawl(_ctx(fetcher, limit=2))]
    assert len(rows) == 2
    assert len(fetcher.calls) == 2


@pytest.mark.asyncio
async def test_spider_skips_challenge_markup() -> None:
    first = SEED_ENTRIES[0]
    html = """
    <html><body><script src="/cdn-cgi/challenge-platform/x.js"></script>
    <a href="mailto:bot@bad.example">x</a></body></html>
    """
    fetcher = _FakeFetcher({first.website: html})
    rows = [row async for row in RuRegionalItSeedSpider().crawl(_ctx(fetcher, limit=1))]
    assert len(rows) == 1
    assert rows[0].email is None
    assert rows[0].description == first.description
