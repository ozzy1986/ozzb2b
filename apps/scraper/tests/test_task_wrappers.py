"""Lightweight tests for the scraper Celery task wrappers.

We don't boot a real Celery worker; we drive the tasks as plain Python
callables. The spiders' ``run_spider_sync`` is monkeypatched to avoid any
HTTP / DB calls.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from ozzb2b_scraper import tasks as tasks_module
from ozzb2b_scraper.spiders import (
    DemoDirectorySpider,
    RuBusinessServicesSeedSpider,
    RuFnsSmeRegistrySpider,
    RuOutsourcingSeedSpider,
    RuRegionalItSeedSpider,
)


def _fake_stats(**kw: int) -> Any:
    base = {
        "fetched": 0,
        "inserted": 0,
        "updated": 0,
        "merged_by_fuzzy": 0,
        "merged_by_domain": 0,
    }
    base.update(kw)
    return SimpleNamespace(**base)


def test_health_task_returns_ok_payload() -> None:
    # The inner function is exposed via .run on decorated Celery tasks.
    assert tasks_module.health.run() == {"status": "ok", "service": "ozzb2b-scraper"}


def test_list_sources_hides_demo(monkeypatch: pytest.MonkeyPatch) -> None:
    out = tasks_module.list_sources.run()
    assert out["status"] == "ok"
    assert isinstance(out["sources"], list)
    assert DemoDirectorySpider.source not in out["sources"]
    for cls in (
        RuBusinessServicesSeedSpider,
        RuOutsourcingSeedSpider,
        RuRegionalItSeedSpider,
        RuFnsSmeRegistrySpider,
    ):
        assert cls.source in out["sources"]


def test_crawl_source_unknown_slug_returns_marker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The decorated `crawl_source` binds self; use the underlying `.run`.
    monkeypatch.setattr(tasks_module, "run_spider_sync", lambda *a, **k: _fake_stats())
    out = tasks_module.crawl_source.run("does-not-exist")  # type: ignore[call-arg]
    assert out == {"status": "unknown_source", "source_slug": "does-not-exist"}


def test_crawl_source_returns_stats_for_known_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        tasks_module,
        "run_spider_sync",
        lambda spider, limit=None: _fake_stats(fetched=3, inserted=2, updated=1),
    )
    out = tasks_module.crawl_source.run(  # type: ignore[call-arg]
        RuOutsourcingSeedSpider.source
    )
    assert out["status"] == "ok"
    assert out["fetched"] == 3
    assert out["inserted"] == 2
    assert out["updated"] == 1


def test_crawl_all_skips_demo_and_aggregates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[str] = []

    def fake(spider: Any, limit: int | None = None) -> Any:
        seen.append(spider.__class__.source)
        return _fake_stats(fetched=1, inserted=1)

    monkeypatch.setattr(tasks_module, "run_spider_sync", fake)
    out = tasks_module.crawl_all.run()  # type: ignore[call-arg]
    assert out["status"] == "ok"
    assert DemoDirectorySpider.source not in seen
    assert set(seen) == {
        RuOutsourcingSeedSpider.source,
        RuBusinessServicesSeedSpider.source,
        RuRegionalItSeedSpider.source,
        RuFnsSmeRegistrySpider.source,
    }
