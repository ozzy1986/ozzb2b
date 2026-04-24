"""Tiny JSON-over-Redis cache used for reference-data endpoints.

Reference data (countries, categories, cities, legal forms) changes once per
deployment at most, so caching it for a few minutes removes repeat DB hits
during catalog navigation while staying simple.

The cache is fail-open: any Redis error returns a miss so the caller falls
through to the DB query. Availability beats freshness for static data.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import TypeVar

import structlog

from ozzb2b_api.clients.redis import get_redis

T = TypeVar("T")

log = structlog.get_logger("ozzb2b_api.clients.cache")

# In-memory lock map per key prevents a thundering herd: when many workers
# call ``get_or_set`` for the same cold key, only the first opens the DB
# query, the rest await the resulting cached value. The lock is process-local
# (one per uvicorn worker) which is good enough for our scale; cross-worker
# coordination would require Redis SETNX semantics that are overkill here.
_locks: dict[str, asyncio.Lock] = {}


def _lock_for(key: str) -> asyncio.Lock:
    lock = _locks.get(key)
    if lock is None:
        lock = asyncio.Lock()
        _locks[key] = lock
    return lock


async def get_or_set(
    key: str,
    *,
    ttl_seconds: int,
    loader: Callable[[], Awaitable[T]],
    encode: Callable[[T], object],
    decode: Callable[[object], T],
) -> T:
    """Return the cached value for ``key`` or compute it via ``loader``.

    ``encode`` / ``decode`` adapt arbitrary types to/from JSON-safe objects
    so the function works for lists of Pydantic models, plain dicts, etc.
    """
    redis = get_redis()
    try:
        cached = await redis.get(key)
    except Exception as exc:  # pragma: no cover - fail-open
        log.warning("cache.get.error", key=key, err=str(exc))
        return await loader()
    if cached is not None:
        try:
            return decode(json.loads(cached))
        except Exception as exc:  # pragma: no cover - cache poison, recompute
            log.warning("cache.decode.error", key=key, err=str(exc))

    async with _lock_for(key):
        # Double-check after acquiring the lock so concurrent waiters skip
        # the DB query that the first task is about to perform.
        try:
            cached = await redis.get(key)
        except Exception:  # pragma: no cover - fail-open
            cached = None
        if cached is not None:
            try:
                return decode(json.loads(cached))
            except Exception:  # pragma: no cover
                pass

        value = await loader()
        try:
            await redis.set(key, json.dumps(encode(value)), ex=max(1, ttl_seconds))
        except Exception as exc:  # pragma: no cover - fail-open
            log.warning("cache.set.error", key=key, err=str(exc))
        return value
