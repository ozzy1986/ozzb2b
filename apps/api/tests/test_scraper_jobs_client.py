"""Unit tests for the Celery wrapper used by /admin/scrape* endpoints.

The wrapper exists so the synchronous Celery client never blocks the FastAPI
event loop. We don't talk to a real broker: the Celery class is replaced with
a stub that records the invocation arguments.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from ozzb2b_api.clients import scraper_jobs


class _FakeAsyncResult:
    def __init__(self, task_id: str) -> None:
        self.id = task_id


class _RecordingCelery:
    last_task: tuple[str, list[Any]] | None = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Constructor args are ignored by the test double.
        pass

    def send_task(self, name: str, args: list[Any]) -> _FakeAsyncResult:
        type(self).last_task = (name, args)
        return _FakeAsyncResult("task-123")


@pytest.fixture(autouse=True)
def _reset_recorder() -> None:
    _RecordingCelery.last_task = None


@pytest.mark.asyncio
async def test_enqueue_crawl_source_dispatches_correct_task() -> None:
    with patch.object(scraper_jobs, "Celery", _RecordingCelery):
        job = await scraper_jobs.enqueue_crawl_source("ru-it", 25)
    assert job.task_id == "task-123"
    assert _RecordingCelery.last_task == ("ozzb2b.scraper.crawl_source", ["ru-it", 25])


@pytest.mark.asyncio
async def test_enqueue_crawl_all_dispatches_correct_task() -> None:
    with patch.object(scraper_jobs, "Celery", _RecordingCelery):
        job = await scraper_jobs.enqueue_crawl_all(None)
    assert job.task_id == "task-123"
    assert _RecordingCelery.last_task == ("ozzb2b.scraper.crawl_all", [None])
