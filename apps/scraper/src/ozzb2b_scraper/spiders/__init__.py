"""Spiders. Each spider yields ScrapedProvider items; the runner persists them."""

from ozzb2b_scraper.spiders.base import Spider, SpiderContext
from ozzb2b_scraper.spiders.demo_directory import DemoDirectorySpider
from ozzb2b_scraper.spiders.ru_business_services_seed import RuBusinessServicesSeedSpider
from ozzb2b_scraper.spiders.ru_outsourcing_seed import RuOutsourcingSeedSpider

ALL_SPIDERS: tuple[type[Spider], ...] = (
    DemoDirectorySpider,
    RuOutsourcingSeedSpider,
    RuBusinessServicesSeedSpider,
)

__all__ = [
    "ALL_SPIDERS",
    "DemoDirectorySpider",
    "RuBusinessServicesSeedSpider",
    "RuOutsourcingSeedSpider",
    "Spider",
    "SpiderContext",
]
