from __future__ import annotations

from ozzb2b_scraper.tasks import app


def test_beat_schedule_contains_all_real_sources() -> None:
    schedule = app.conf.beat_schedule
    assert "refresh-ru-outsourcing-daily" in schedule
    assert "refresh-ru-business-services-daily" in schedule
    assert "refresh-ru-regional-it-daily" in schedule
