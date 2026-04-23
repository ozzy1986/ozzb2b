"""Rate limiter behaviour against a real Redis instance."""

from __future__ import annotations

import pytest
from redis.asyncio import Redis

from ozzb2b_api.security.rate_limit import RateLimiter

pytestmark = pytest.mark.integration


async def test_real_redis_enforces_limit(redis_client: Redis) -> None:
    rl = RateLimiter(redis=redis_client, window_seconds=5)

    for _ in range(3):
        outcome = await rl.hit(endpoint="login", scope="ip:10.0.0.1", limit=3)
        assert outcome.allowed

    blocked = await rl.hit(endpoint="login", scope="ip:10.0.0.1", limit=3)
    assert not blocked.allowed
    assert blocked.retry_after_seconds > 0


async def test_real_redis_isolates_scopes(redis_client: Redis) -> None:
    rl = RateLimiter(redis=redis_client, window_seconds=5)

    for scope in ("ip:1.1.1.1", "ip:2.2.2.2"):
        assert (
            await rl.hit(endpoint="register", scope=scope, limit=1)
        ).allowed

    # One scope is exhausted; the other must still be throttled independently.
    assert not (
        await rl.hit(endpoint="register", scope="ip:1.1.1.1", limit=1)
    ).allowed
