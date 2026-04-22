"""Async Redis client."""

from __future__ import annotations

from functools import lru_cache

from redis.asyncio import Redis

from ozzb2b_api.config import get_settings


@lru_cache(maxsize=1)
def get_redis() -> Redis:
    """Return the application-wide Redis client."""
    settings = get_settings()
    return Redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )


async def ping_redis() -> bool:
    """Return True iff Redis is reachable."""
    try:
        return bool(await get_redis().ping())
    except Exception:
        return False
