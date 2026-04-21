"""Celery tasks for the ozzb2b scraper.

Phase 0: declares the app, the health task, and placeholder task signatures
that will be implemented in Phase 1 alongside real spiders.
"""

from __future__ import annotations

import os

from celery import Celery

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
    """Simple echo task used in readiness checks."""
    return {"status": "ok", "service": "ozzb2b-scraper"}


@app.task(name="ozzb2b.scraper.crawl_source", bind=True, default_retry_delay=60, max_retries=3)
def crawl_source(self, source_slug: str) -> dict[str, str]:  # noqa: ARG001 (bound task)
    """Placeholder for Phase 1. Will enqueue a Scrapy spider for the given source."""
    return {"status": "planned", "source_slug": source_slug}
