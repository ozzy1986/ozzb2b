"""Fixed-window rate limiter backed by Redis.

We intentionally keep this simple: INCR a counter keyed by endpoint+scope;
EXPIRE the key on first increment. Good enough to stop brute-force attacks
on auth without pulling in Lua or token-buckets. The limiter is resilient to
Redis outages — any exception lets the request through (availability > DoS
protection).
"""

from __future__ import annotations

from dataclasses import dataclass

import structlog
from redis.asyncio import Redis

log = structlog.get_logger("ozzb2b_api.security.rate_limit")


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    remaining: int
    retry_after_seconds: int


class RateLimiter:
    """Fixed-window counter stored as `rl:{endpoint}:{scope}`."""

    def __init__(self, *, redis: Redis, window_seconds: int) -> None:
        self._redis = redis
        self._window = max(1, window_seconds)

    async def hit(
        self,
        *,
        endpoint: str,
        scope: str,
        limit: int,
    ) -> RateLimitResult:
        """Record an attempt and tell the caller if it should be rejected."""
        if limit <= 0:
            return RateLimitResult(allowed=True, remaining=0, retry_after_seconds=0)

        key = f"rl:{endpoint}:{scope}"
        try:
            count = int(await self._redis.incr(key))
            if count == 1:
                await self._redis.expire(key, self._window)
            ttl = int(await self._redis.ttl(key))
            if ttl < 0:
                ttl = self._window
        except Exception as exc:  # pragma: no cover - fail-open by design
            log.warning("rate_limit.redis_error", err=str(exc), endpoint=endpoint)
            return RateLimitResult(allowed=True, remaining=limit, retry_after_seconds=0)

        if count > limit:
            return RateLimitResult(
                allowed=False,
                remaining=0,
                retry_after_seconds=ttl,
            )
        return RateLimitResult(
            allowed=True,
            remaining=max(0, limit - count),
            retry_after_seconds=ttl,
        )


def client_ip(headers: dict[str, str] | None, fallback: str | None) -> str:
    """Derive the client IP from X-Forwarded-For or the raw peer address.

    We trust X-Forwarded-For because the API always sits behind Nginx on
    the VPS; the first element of the list is the real client.
    """
    if headers:
        forwarded = headers.get("x-forwarded-for") or headers.get("X-Forwarded-For")
        if forwarded:
            first = forwarded.split(",")[0].strip()
            if first:
                return first
    return fallback or "unknown"
