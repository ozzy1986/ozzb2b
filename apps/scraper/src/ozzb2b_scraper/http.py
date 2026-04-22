"""Polite, rate-limited HTTP fetcher.

Features:
- Per-host rate limiting (`OZZB2B_RATE_LIMIT_PER_HOST_RPS`).
- Robots.txt respect: we never request a URL that robots.txt forbids for us.
- Retry with exponential backoff on transport-level errors.
- Optional challenge (CAPTCHA / anti-bot) detection on the response body; the
  caller can treat a challenge response as "no data" without persisting junk.
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict

import httpx
import structlog
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from ozzb2b_scraper.config import get_settings
from ozzb2b_scraper.robots import RobotsCache

log = structlog.get_logger("ozzb2b_scraper.http")


class RobotsDisallowed(RuntimeError):
    """Raised when robots.txt forbids fetching the requested URL."""


class PoliteFetcher:
    """Async HTTP client that respects per-host rate limit, User-Agent and robots.txt.

    We enforce a minimum interval between requests to the same host to stay within
    `rate_limit_per_host_rps`, identify ourselves with a descriptive User-Agent and
    always consult `robots.txt` before a fetch.
    """

    def __init__(self) -> None:
        cfg = get_settings()
        self._min_interval = 1.0 / max(cfg.rate_limit_per_host_rps, 0.01)
        self._last_call: dict[str, float] = defaultdict(lambda: 0.0)
        self._lock = asyncio.Lock()
        self._user_agent = cfg.user_agent
        self._client = httpx.AsyncClient(
            timeout=cfg.request_timeout_s,
            headers={"User-Agent": cfg.user_agent, "Accept": "text/html,application/xhtml+xml"},
            follow_redirects=True,
        )
        self._robots = RobotsCache(self._client, cfg.user_agent)

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
        if not await self._robots.is_allowed(url):
            log.info("http.get.blocked_by_robots", url=url, user_agent=self._user_agent)
            raise RobotsDisallowed(url)
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


_CHALLENGE_MARKERS: tuple[str, ...] = (
    # Cloudflare
    "cf-chl-bypass",
    "cf-browser-verification",
    "__cf_chl_",
    "challenge-platform",
    # Google reCAPTCHA gate pages
    "g-recaptcha",
    "grecaptcha",
    # hCaptcha gate pages
    "h-captcha",
    "hcaptcha.com",
    # Imperva / DataDome
    "_imperva",
    "datadome",
)


def looks_like_challenge(html: str) -> bool:
    """Heuristic check for anti-bot / CAPTCHA interstitial pages.

    We only scan the first few KB to keep this O(n) for huge pages and because
    challenge markers, when present, are always near the top of the document.
    """
    if not html:
        return False
    head = html[:8192].lower()
    return any(marker in head for marker in _CHALLENGE_MARKERS)
