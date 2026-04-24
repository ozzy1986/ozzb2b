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
from fastapi import HTTPException, Request, Response, status
from redis.asyncio import Redis

from ozzb2b_api.clients.redis import get_redis
from ozzb2b_api.config import get_settings
from ozzb2b_api.observability.metrics import auth_rate_limit_blocked_total

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


async def enforce_rate_limit(
    *,
    request: Request,
    response: Response,
    endpoint: str,
    limit: int,
    user_scope: str | None = None,
) -> None:
    """Reject the request with 429 when the IP+scope budget is exhausted.

    Always throttles by client IP; additionally throttles by `user_scope`
    (e.g. ``user.id`` or normalised email) so a single attacker can't roll
    addresses to burn through accounts.
    """
    cfg = get_settings()
    if not cfg.rate_limit_enabled or limit <= 0:
        return
    limiter = RateLimiter(redis=get_redis(), window_seconds=cfg.rate_limit_window_seconds)
    headers = {k.lower(): v for k, v in request.headers.items()}
    ip = client_ip(
        headers,
        request.client.host if request.client else None,
        trusted_proxy_count=cfg.trusted_proxy_count,
    )
    for scope_name, scope_value in (("ip", ip), ("user", user_scope)):
        if not scope_value:
            continue
        outcome = await limiter.hit(
            endpoint=endpoint,
            scope=f"{scope_name}:{scope_value}",
            limit=limit,
        )
        if not outcome.allowed:
            auth_rate_limit_blocked_total.labels(endpoint, scope_name).inc()
            response.headers["Retry-After"] = str(outcome.retry_after_seconds)
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "слишком много попыток, попробуйте позже",
            )


def client_ip(
    headers: dict[str, str] | None,
    fallback: str | None,
    *,
    trusted_proxy_count: int = 0,
) -> str:
    """Derive the client IP, honouring `trusted_proxy_count` for X-Forwarded-For.

    The header is a chain ``client, proxy1, proxy2, ...`` where each rightward
    entry is a hop closer to us. An attacker on the public internet can
    append arbitrary entries to the LEFT, so we MUST skip ``trusted_proxy_count``
    rightmost entries (the hops we control) and pick the next one back as
    the real client. With ``trusted_proxy_count=0`` we ignore the header
    entirely and use the socket peer; the caller opts in by passing the
    number of trusted hops at the perimeter (e.g. 1 for a single nginx in
    front of the API).
    """
    if headers and trusted_proxy_count > 0:
        forwarded = headers.get("x-forwarded-for") or headers.get("X-Forwarded-For")
        if forwarded:
            chain = [p.strip() for p in forwarded.split(",") if p.strip()]
            if chain:
                # `chain[-trusted_proxy_count]` is the first non-trusted IP
                # (counting from the right). Clamp to leftmost when fewer
                # entries than trusted hops are present.
                idx = max(0, len(chain) - trusted_proxy_count - 1)
                candidate = chain[idx]
                if candidate:
                    return candidate
    return fallback or "unknown"
