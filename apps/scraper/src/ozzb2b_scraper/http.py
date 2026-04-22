"""Polite, rate-limited HTTP fetcher."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict

import httpx
import structlog
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from ozzb2b_scraper.config import get_settings

log = structlog.get_logger("ozzb2b_scraper.http")


class PoliteFetcher:
    """Async HTTP client that respects a per-host rate limit and honors robots.txt-like policy.

    We enforce a minimum interval between requests to the same host to stay within
    `rate_limit_per_host_rps` and we set a descriptive User-Agent.
    """

    def __init__(self) -> None:
        cfg = get_settings()
        self._min_interval = 1.0 / max(cfg.rate_limit_per_host_rps, 0.01)
        self._last_call: dict[str, float] = defaultdict(lambda: 0.0)
        self._lock = asyncio.Lock()
        self._client = httpx.AsyncClient(
            timeout=cfg.request_timeout_s,
            headers={"User-Agent": cfg.user_agent, "Accept": "text/html,application/xhtml+xml"},
            follow_redirects=True,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _throttle(self, host: str) -> None:
        async with self._lock:
            last = self._last_call[host]
            now = time.monotonic()
            wait = self._min_interval - (now - last)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_call[host] = time.monotonic()

    async def get(self, url: str) -> httpx.Response:
        host = httpx.URL(url).host
        await self._throttle(host)
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception_type((httpx.TransportError, httpx.ReadTimeout)),
            reraise=True,
        ):
            with attempt:
                resp = await self._client.get(url)
                resp.raise_for_status()
                log.debug("http.get.ok", url=url, status=resp.status_code)
                return resp
        raise RuntimeError("unreachable")
