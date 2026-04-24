"""Thin wrapper around the Celery client used to enqueue scraper jobs.

Routes call into this module instead of constructing a Celery client inline so
that ``Celery.send_task`` (a synchronous, blocking network call) can be moved
off the FastAPI event loop and so that tests can swap a fake without patching
the route module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import anyio
from celery import Celery

from ozzb2b_api.config import get_settings


@dataclass(frozen=True)
class ScrapeJob:
    task_id: str


_TASK_CRAWL_SOURCE = "ozzb2b.scraper.crawl_source"
_TASK_CRAWL_ALL = "ozzb2b.scraper.crawl_all"


def _build_client() -> Celery:
    cfg = get_settings()
    return Celery("ozzb2b_scraper", broker=cfg.redis_url, backend=cfg.redis_url)


def _send_sync(name: str, args: list[Any]) -> ScrapeJob:
    client = _build_client()
    result = client.send_task(name, args=args)
    return ScrapeJob(task_id=str(result.id))


async def enqueue_crawl_source(source_slug: str, limit: int | None) -> ScrapeJob:
    """Enqueue a ``crawl_source`` Celery task without blocking the event loop."""
    return await anyio.to_thread.run_sync(_send_sync, _TASK_CRAWL_SOURCE, [source_slug, limit])


async def enqueue_crawl_all(limit: int | None) -> ScrapeJob:
    """Enqueue a ``crawl_all`` Celery task without blocking the event loop."""
    return await anyio.to_thread.run_sync(_send_sync, _TASK_CRAWL_ALL, [limit])
