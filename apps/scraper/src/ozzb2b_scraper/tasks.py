"""Celery tasks for the ozzb2b scraper."""

from __future__ import annotations

import os

from celery import Celery

from ozzb2b_scraper.pipeline import run_spider_sync
from ozzb2b_scraper.spiders import DemoDirectorySpider

REDIS_URL = os.environ.get("OZZB2B_REDIS_URL", "redis://localhost:6380/0")

app = Celery(
    "ozzb2b_scraper",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    timezone="UTC",
    enable_utc=True,
)


@app.task(name="ozzb2b.scraper.health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ozzb2b-scraper"}


@app.task(name="ozzb2b.scraper.crawl_source", bind=True, default_retry_delay=60, max_retries=3)
def crawl_source(self, source_slug: str, limit: int | None = None) -> dict[str, int | str]:
    """Run a registered spider by its source slug."""
    spider_map = {DemoDirectorySpider.source: DemoDirectorySpider()}
    spider = spider_map.get(source_slug)
    if spider is None:
        return {"status": "unknown_source", "source_slug": source_slug}
    stats = run_spider_sync(spider, limit=limit)
    return {
        "status": "ok",
        "source_slug": source_slug,
        "fetched": stats.fetched,
        "inserted": stats.inserted,
        "updated": stats.updated,
        "merged_by_fuzzy": stats.merged_by_fuzzy,
    }
