"""Async Redis client."""

from __future__ import annotations

from functools import lru_cache
from typing import cast

from redis.asyncio import Redis

from ozzb2b_api.config import get_settings


@lru_cache(maxsize=1)
def get_redis() -> Redis:
    """Return the application-wide Redis client.

    The connection pool size is env-driven so the API can absorb traffic
    bursts (auth + chat + events all hammer Redis) without exhausting the
    library default of 50 sockets per process.
    """
    settings = get_settings()
    return cast(
        Redis,
        Redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=max(8, settings.redis_max_connections),
        ),
    )


async def ping_redis() -> bool:
    """Return True iff Redis is reachable."""
    try:
        return bool(await get_redis().ping())
    except Exception:
        return False
