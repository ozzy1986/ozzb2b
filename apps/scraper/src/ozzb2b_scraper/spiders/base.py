"""Abstract spider contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass

from ozzb2b_scraper.http import PoliteFetcher
from ozzb2b_scraper.models import ScrapedProvider


@dataclass(frozen=True)
class SpiderContext:
    """Runtime context passed to each spider (fetcher, run-specific opts)."""

    fetcher: PoliteFetcher
    limit: int | None = None


class Spider(ABC):
    """A spider yields ScrapedProvider items. Subclasses must be idempotent."""

    source: str = "unknown"

    @abstractmethod
    def crawl(self, ctx: SpiderContext) -> AsyncIterator[ScrapedProvider]:
        ...
