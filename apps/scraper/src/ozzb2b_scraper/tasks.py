"""Celery tasks for the ozzb2b scraper.

Also defines a default `beat_schedule` so a Celery Beat container can drive
periodic crawls without extra wiring. Workers still respond to ad-hoc calls.
"""

from __future__ import annotations

import os
from datetime import timedelta

from celery import Celery

from ozzb2b_scraper.pipeline import run_spider_sync
from ozzb2b_scraper.spiders import (
    ALL_SPIDERS,
    DemoDirectorySpider,
    RuBusinessServicesSeedSpider,
    RuOutsourcingSeedSpider,
)

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
    beat_schedule={
        "refresh-ru-outsourcing-daily": {
            "task": "ozzb2b.scraper.crawl_source",
            "schedule": timedelta(hours=24),
            "args": (RuOutsourcingSeedSpider.source,),
            "options": {"queue": "scraper"},
        },
        "refresh-ru-business-services-daily": {
            "task": "ozzb2b.scraper.crawl_source",
            "schedule": timedelta(hours=24),
            "args": (RuBusinessServicesSeedSpider.source,),
            "options": {"queue": "scraper"},
        },
    },
)


_SPIDER_MAP = {cls.source: cls for cls in ALL_SPIDERS}


@app.task(name="ozzb2b.scraper.health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ozzb2b-scraper"}


@app.task(name="ozzb2b.scraper.crawl_source", bind=True, default_retry_delay=60, max_retries=3)
def crawl_source(self, source_slug: str, limit: int | None = None) -> dict[str, int | str]:
    """Run a registered spider by its source slug."""
    cls = _SPIDER_MAP.get(source_slug)
    if cls is None:
        return {"status": "unknown_source", "source_slug": source_slug}
    stats = run_spider_sync(cls(), limit=limit)
    return {
        "status": "ok",
        "source_slug": source_slug,
        "fetched": stats.fetched,
        "inserted": stats.inserted,
        "updated": stats.updated,
        "merged_by_fuzzy": stats.merged_by_fuzzy,
        "merged_by_domain": stats.merged_by_domain,
    }


@app.task(name="ozzb2b.scraper.crawl_all")
def crawl_all(limit: int | None = None) -> dict[str, object]:
    """Run every registered real-source spider once. Skips the demo spider."""
    results: dict[str, object] = {"status": "ok", "sources": []}
    for cls in ALL_SPIDERS:
        if cls is DemoDirectorySpider:
            continue
        stats = run_spider_sync(cls(), limit=limit)
        results["sources"].append(  # type: ignore[union-attr]
            {
                "source_slug": cls.source,
                "fetched": stats.fetched,
                "inserted": stats.inserted,
                "updated": stats.updated,
                "merged_by_fuzzy": stats.merged_by_fuzzy,
                "merged_by_domain": stats.merged_by_domain,
            }
        )
    return results
