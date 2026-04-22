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
            log.debug("robots.fetch.failed", host=key, error=str(exc))
            # Fail-open: no parser means "is_allowed() -> True".
            self._parsers[key] = _AllowAll()
            return self._parsers[key]
        if resp.status_code >= 400:
            # Many small sites just return 404 for /robots.txt — treat as allow.
            self._parsers[key] = _AllowAll()
            return self._parsers[key]
        try:
            parser.parse(resp.text.splitlines())
        except Exception as exc:  # noqa: BLE001 - be robust against malformed content
            log.debug("robots.parse.failed", host=key, error=str(exc))
            self._parsers[key] = _AllowAll()
            return self._parsers[key]
        self._parsers[key] = parser
        return parser


class _AllowAll(RobotFileParser):
    """A parser replacement that allows everything.

    Returning a plain `RobotFileParser()` with no data also allows everything,
    but naming it explicitly makes intent obvious at the call site.
    """

    def can_fetch(self, useragent: str, url: str) -> bool:  # noqa: ARG002 - interface parity
        return True
