"""Spiders. Each spider yields ScrapedProvider items; the runner persists them."""

from ozzb2b_scraper.spiders.base import Spider, SpiderContext
from ozzb2b_scraper.spiders.demo_directory import DemoDirectorySpider

__all__ = ["DemoDirectorySpider", "Spider", "SpiderContext"]
