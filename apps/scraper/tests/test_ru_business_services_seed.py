"""Tests for the RU business-services seed spider (accounting/legal/marketing/HR)."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest

from ozzb2b_scraper.spiders.ru_business_services_seed import (
    SEED_ENTRIES,
    RuBusinessServicesSeedSpider,
)

ALLOWED_LEGAL_FORMS = {"OOO", "AO", "PAO", "IP", "UNK"}
ALLOWED_CATEGORY_ROOTS = {"accounting", "legal", "marketing", "hr"}


def test_seed_source_ids_are_unique_and_slug_safe() -> None:
    ids = [e.source_id for e in SEED_ENTRIES]
    assert len(ids) == len(set(ids))
    for sid in ids:
        assert sid == sid.lower()
        assert all(c.isalnum() or c == "-" for c in sid), sid


def test_seed_websites_are_https() -> None:
    for entry in SEED_ENTRIES:
        assert entry.website.startswith("https://"), entry.source_id


def test_seed_legal_forms_are_known() -> None:
    for entry in SEED_ENTRIES:
        assert entry.legal_form_code in ALLOWED_LEGAL_FORMS, entry.source_id


def test_seed_every_entry_has_a_non_it_root_category() -> None:
    for entry in SEED_ENTRIES:
        roots = {s for s in entry.category_slugs if s in ALLOWED_CATEGORY_ROOTS}
        assert roots, (
            f"{entry.source_id}: business-services seed must pick at least one of "
            f"{ALLOWED_CATEGORY_ROOTS}"
        )


def test_seed_has_multiple_service_verticals() -> None:
    covered_roots = {
        s
        for entry in SEED_ENTRIES
        for s in entry.category_slugs
        if s in ALLOWED_CATEGORY_ROOTS
    }
    # At least 3 of the 4 non-IT verticals represented to make the seed useful.
    assert len(covered_roots) >= 3, covered_roots


@dataclass
class _FakeResponse:
    text: str


class _FakeFetcher:
    def __init__(
        self,
        responses: dict[str, str] | None = None,
        raise_for: set[str] | None = None,
    ) -> None:
        self.responses = responses or {}
        self.raise_for = raise_for or set()
        self.calls: list[str] = []

    async def get(self, url: str) -> _FakeResponse:
        self.calls.append(url)
        if url in self.raise_for:
            raise RuntimeError(f"network down for {url}")
        return _FakeResponse(text=self.responses.get(url, "<html></html>"))


def _ctx(fetcher: Any, limit: int | None = None) -> Any:
    return SimpleNamespace(fetcher=fetcher, limit=limit)


@pytest.mark.asyncio
async def test_spider_emits_all_entries_even_when_fetch_fails() -> None:
    fetcher = _FakeFetcher(raise_for={e.website for e in SEED_ENTRIES})
    items = [item async for item in RuBusinessServicesSeedSpider().crawl(_ctx(fetcher))]
    assert len(items) == len(SEED_ENTRIES)
    for item in items:
        assert item.source == "ru-business-services-seed"
        assert item.country_code == "RU"
        assert item.description


@pytest.mark.asyncio
async def test_spider_respects_limit() -> None:
    fetcher = _FakeFetcher()
    items = [
        item
        async for item in RuBusinessServicesSeedSpider().crawl(_ctx(fetcher, limit=2))
    ]
    assert len(items) == 2


@pytest.mark.asyncio
async def test_spider_skips_enrichment_on_challenge_page() -> None:
    first = SEED_ENTRIES[0]
    challenge_html = """
    <html><head><title>Just a moment…</title></head>
    <body><script src="/cdn-cgi/challenge-platform/x.js"></script>
      <a href="mailto:leak@bot.example">leak</a>
      <a href="tel:+0000000">bot</a>
    </body></html>
    """
    fetcher = _FakeFetcher(responses={first.website: challenge_html})
    items = [
        item
        async for item in RuBusinessServicesSeedSpider().crawl(_ctx(fetcher, limit=1))
    ]
    assert len(items) == 1
    out = items[0]
    # Seed data preserved, challenge markup never harvested.
    assert out.description == first.description
    assert out.email is None
    assert out.phone is None
