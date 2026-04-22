"""Spider-level tests that don't need Postgres."""

from __future__ import annotations

import pytest

from ozzb2b_scraper.http import PoliteFetcher
from ozzb2b_scraper.spiders import DemoDirectorySpider, SpiderContext


@pytest.mark.asyncio
async def test_demo_spider_yields_expected_items() -> None:
    spider = DemoDirectorySpider()
    fetcher = PoliteFetcher()
    try:
        ctx = SpiderContext(fetcher=fetcher)
        items = [item async for item in spider.crawl(ctx)]
    finally:
        await fetcher.close()
    assert len(items) == 3
    assert {i.source for i in items} == {"demo-directory"}
    for i in items:
        assert i.display_name
        assert i.country_code
        assert i.category_slugs


@pytest.mark.asyncio
async def test_demo_spider_respects_limit() -> None:
    spider = DemoDirectorySpider()
    fetcher = PoliteFetcher()
    try:
        ctx = SpiderContext(fetcher=fetcher, limit=1)
        items = [item async for item in spider.crawl(ctx)]
    finally:
        await fetcher.close()
    assert len(items) == 1
