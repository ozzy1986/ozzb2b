"""Unit tests for scraper Celery tasks that don't require a broker."""

from __future__ import annotations

from ozzb2b_scraper.tasks import crawl_source, health


def test_health_returns_ok() -> None:
    result = health.run()
    assert result == {"status": "ok", "service": "ozzb2b-scraper"}


def test_crawl_source_placeholder_returns_planned() -> None:
    result = crawl_source.run("example-registry")
    assert result == {"status": "planned", "source_slug": "example-registry"}
