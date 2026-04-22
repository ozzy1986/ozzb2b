"""Tests for the RU outsourcing seed spider.

These tests:
- Validate that the curated seed list is well-formed (sanity checks).
- Verify the spider uses the ctx fetcher (so it stays polite / rate limited)
  and tolerates network failures without dropping items.
- Never touch the real network: we pass a fake fetcher.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest

from ozzb2b_scraper.spiders.ru_outsourcing_seed import (
    SEED_ENTRIES,
    RuOutsourcingSeedSpider,
)


ALLOWED_LEGAL_FORMS = {"OOO", "AO", "PAO", "IP", "UNK"}
ALLOWED_CATEGORY_ROOTS = {"it", "accounting", "legal", "marketing", "hr"}


def test_seed_list_has_expected_size() -> None:
    # Target: 20 curated RU companies.
    assert len(SEED_ENTRIES) == 20


def test_seed_source_ids_are_unique_and_slug_safe() -> None:
    ids = [e.source_id for e in SEED_ENTRIES]
    assert len(ids) == len(set(ids)), "source_id collisions in RU seed"
    for sid in ids:
        assert sid == sid.lower()
        assert all(c.isalnum() or c == "-" for c in sid), sid


def test_seed_websites_are_https() -> None:
    for entry in SEED_ENTRIES:
        assert entry.website.startswith("https://"), entry.source_id


def test_seed_legal_forms_are_known() -> None:
    for entry in SEED_ENTRIES:
        assert entry.legal_form_code in ALLOWED_LEGAL_FORMS, entry.source_id


def test_seed_category_slugs_start_with_known_root() -> None:
    for entry in SEED_ENTRIES:
        assert entry.category_slugs, entry.source_id
        # Every entry must at least be tagged with a top-level category.
        roots = {
            s for s in entry.category_slugs if s in ALLOWED_CATEGORY_ROOTS
        }
        assert roots, f"{entry.source_id} missing a root category"


def test_seed_descriptions_are_meaningful() -> None:
    for entry in SEED_ENTRIES:
        assert len(entry.description) >= 40, entry.source_id
        assert not entry.description.startswith("TODO"), entry.source_id


def test_seed_cities_are_in_ru_reference_list() -> None:
    # Mirrors apps/api/src/ozzb2b_api/db/seed.py CITIES for RU.
    expected_ru_cities = {
        "Moscow",
        "Saint Petersburg",
        "Novosibirsk",
        "Yekaterinburg",
        "Kazan",
        "Nizhny Novgorod",
        "Samara",
        "Ulyanovsk",
        "Voronezh",
        "Omsk",
        "Kirov",
        "Perm",
        "Rostov-on-Don",
        "Krasnodar",
    }
    for entry in SEED_ENTRIES:
        assert entry.city_name in expected_ru_cities, (
            f"{entry.source_id} -> unknown RU city {entry.city_name!r}; "
            "add it to apps/api seed CITIES or fix the spider entry"
        )


def test_seed_has_reasonable_geographic_diversity() -> None:
    counts = Counter(e.city_name for e in SEED_ENTRIES)
    # At least 3 different cities represented.
    assert len(counts) >= 3


# ---------- spider behavior ----------


@dataclass
class _FakeResponse:
    text: str


class _FakeFetcher:
    """In-memory fetcher used to keep tests offline.

    - If `raise_for` contains the URL, the get() call raises.
    - Otherwise it returns a canned response keyed by URL, or a default HTML.
    """

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
    # SpiderContext is frozen and typed; use a duck-typed stand-in for tests.
    return SimpleNamespace(fetcher=fetcher, limit=limit)


@pytest.mark.asyncio
async def test_spider_emits_all_entries_even_when_fetch_fails() -> None:
    fetcher = _FakeFetcher(raise_for={e.website for e in SEED_ENTRIES})
    items = [item async for item in RuOutsourcingSeedSpider().crawl(_ctx(fetcher))]

    assert len(items) == len(SEED_ENTRIES)
    assert len(fetcher.calls) == len(SEED_ENTRIES)

    for item in items:
        assert item.source == "ru-outsourcing-seed"
        assert item.country_code == "RU"
        assert item.display_name
        # With fetch failing we must still have the seeded description.
        assert item.description
        assert item.email is None
        assert item.phone is None


@pytest.mark.asyncio
async def test_spider_respects_limit() -> None:
    fetcher = _FakeFetcher()
    items = [item async for item in RuOutsourcingSeedSpider().crawl(_ctx(fetcher, limit=3))]
    assert len(items) == 3
    assert len(fetcher.calls) == 3


@pytest.mark.asyncio
async def test_spider_enriches_from_html_when_available() -> None:
    # Override response for the first entry only.
    first = SEED_ENTRIES[0]
    fake_html = f"""
    <html><head>
      <meta property="og:description" content="Overridden public description from the company website homepage.">
    </head><body>
      <a href="mailto:contact@{first.source_id}.example">Email</a>
      <a href="tel:+7 812 123 45 67">Call</a>
    </body></html>
    """
    fetcher = _FakeFetcher(responses={first.website: fake_html})
    items = [item async for item in RuOutsourcingSeedSpider().crawl(_ctx(fetcher, limit=1))]

    assert len(items) == 1
    out = items[0]
    assert out.description is not None
    assert out.description.startswith("Overridden public description")
    assert out.email == f"contact@{first.source_id}.example"
    assert out.phone == "+7 812 123 45 67"
    # And the non-enriched fields must stay from the seed.
    assert out.legal_name == first.legal_name
    assert out.city_name == first.city_name
    assert out.legal_form_code == first.legal_form_code
