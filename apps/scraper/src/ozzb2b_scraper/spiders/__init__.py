"""Spiders. Each spider yields ScrapedProvider items; the runner persists them."""

from ozzb2b_scraper.spiders.base import Spider, SpiderContext
from ozzb2b_scraper.spiders.demo_directory import DemoDirectorySpider
from ozzb2b_scraper.spiders.ru_business_services_seed import RuBusinessServicesSeedSpider
from ozzb2b_scraper.spiders.ru_outsourcing_seed import RuOutsourcingSeedSpider
from ozzb2b_scraper.spiders.ru_regional_it_seed import RuRegionalItSeedSpider

ALL_SPIDERS: tuple[type[Spider], ...] = (
    DemoDirectorySpider,
    RuOutsourcingSeedSpider,
    RuBusinessServicesSeedSpider,
    RuRegionalItSeedSpider,
)

__all__ = [
    "ALL_SPIDERS",
    "DemoDirectorySpider",
    "RuBusinessServicesSeedSpider",
    "RuOutsourcingSeedSpider",
    "RuRegionalItSeedSpider",
    "Spider",
    "SpiderContext",
]
