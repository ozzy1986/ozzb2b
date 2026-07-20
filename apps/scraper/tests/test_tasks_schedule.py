from __future__ import annotations

from ozzb2b_scraper.spiders import (
    RuBusinessServicesSeedSpider,
    RuOutsourcingSeedSpider,
    RuRegionalItSeedSpider,
)
from ozzb2b_scraper.tasks import SCRAPER_QUEUE, app


def test_beat_schedule_contains_all_periodic_sources() -> None:
    schedule = app.conf.beat_schedule
    expected = {
        "refresh-ru-outsourcing-daily": RuOutsourcingSeedSpider.source,
        "refresh-ru-business-services-daily": RuBusinessServicesSeedSpider.source,
        "refresh-ru-regional-it-daily": RuRegionalItSeedSpider.source,
    }

    assert set(schedule) == set(expected)
    assert app.conf.task_default_queue == SCRAPER_QUEUE
    for name, source in expected.items():
        assert schedule[name]["task"] == "ozzb2b.scraper.crawl_source"
        assert schedule[name]["args"] == (source,)
