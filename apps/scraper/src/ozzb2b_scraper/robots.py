"""robots.txt support for the polite HTTP fetcher.

Before fetching any URL we:
- look up the per-host robots.txt (cached for the process lifetime),
- honour User-Agent based Allow / Disallow rules.

If robots.txt cannot be fetched (non-2xx, timeout, DNS) we fail open — the
original curated seed lists are trusted public homepages, and we prefer
availability over strict enforcement when the site itself is broken.
The public API is deliberately tiny: `RobotsCache.is_allowed(url)`.
"""

from __future__ import annotations

from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx
import structlog

from ozzb2b_scraper.config import get_settings

log = structlog.get_logger("ozzb2b_scraper.robots")


class RobotsCache:
    """Process-wide robots.txt cache keyed by scheme+host.

    The cache is intentionally simple (no TTL). Spiders run as short-lived
    Celery tasks, so a per-task cache is the right unit of reuse.
    """

    def __init__(self, client: httpx.AsyncClient, user_agent: str) -> None:
        self._client = client
        self._user_agent = user_agent
        self._parsers: dict[str, RobotFileParser] = {}

    async def is_allowed(self, url: str) -> bool:
        parser = await self._parser_for(url)
        if parser is None:
            return True
        return parser.can_fetch(self._user_agent, url)

    def _on_fetch_failure(self, key: str, *, error: str) -> RobotFileParser:
        """Pick the strict-vs-permissive policy based on settings.

        ``robots_strict=True`` makes a missing/broken robots.txt deny every
        URL on the host (safer for production crawling); the default keeps
        the historical fail-open behaviour for resilience.
        """
        if get_settings().robots_strict:
            log.warning("robots.fetch.failed_deny", host=key, error=error)
            self._parsers[key] = _DenyAll()
        else:
            log.debug("robots.fetch.failed", host=key, error=error)
            self._parsers[key] = _AllowAll()
        return self._parsers[key]

    async def _parser_for(self, url: str) -> RobotFileParser | None:
        split = urlsplit(url)
        if not split.scheme or not split.netloc:
            return None
        key = f"{split.scheme}://{split.netloc}"
        cached = self._parsers.get(key)
        if cached is not None:
            return cached
        parser = RobotFileParser()
        robots_url = f"{key}/robots.txt"
        parser.set_url(robots_url)
        try:
            resp = await self._client.get(robots_url)
        except httpx.HTTPError as exc:
            return self._on_fetch_failure(key, error=str(exc))
        if resp.status_code >= 400:
            # Many small sites just return 404 for /robots.txt — treat as
            # allow unless strict mode is on.
            return self._on_fetch_failure(key, error=f"http {resp.status_code}")
        try:
            parser.parse(resp.text.splitlines())
        except Exception as exc:  # noqa: BLE001 - be robust against malformed content
            return self._on_fetch_failure(key, error=f"parse: {exc}")
        self._parsers[key] = parser
        return parser


class _AllowAll(RobotFileParser):
    """A parser replacement that allows everything.

    Returning a plain `RobotFileParser()` with no data also allows everything,
    but naming it explicitly makes intent obvious at the call site.
    """

    def can_fetch(self, useragent: str, url: str) -> bool:  # noqa: ARG002 - interface parity
        return True


class _DenyAll(RobotFileParser):
    """A parser replacement that blocks every URL.

    Used when ``robots_strict`` is on and we couldn't fetch/parse robots.txt.
    """

    def can_fetch(self, useragent: str, url: str) -> bool:  # noqa: ARG002 - interface parity
        return False
