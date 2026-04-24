"""Unit tests for the Redis-backed rate limiter."""

from __future__ import annotations

from typing import Any

import pytest

from ozzb2b_api.security.rate_limit import RateLimiter, client_ip


class _FakeRedis:
    """Minimal async fake mimicking INCR/EXPIRE/TTL semantics."""

    def __init__(self) -> None:
        self.counters: dict[str, int] = {}
        self.ttls: dict[str, int] = {}
        self.fail = False

    async def incr(self, key: str) -> int:
        if self.fail:
            raise RuntimeError("redis down")
        self.counters[key] = self.counters.get(key, 0) + 1
        return self.counters[key]

    async def expire(self, key: str, seconds: int) -> bool:
        self.ttls[key] = seconds
        return True

    async def ttl(self, key: str) -> int:
        return self.ttls.get(key, 0)


async def test_allows_first_hits_and_blocks_after_limit() -> None:
    redis = _FakeRedis()
    rl = RateLimiter(redis=redis, window_seconds=60)  # type: ignore[arg-type]

    for i in range(3):
        outcome = await rl.hit(endpoint="login", scope="ip:1.2.3.4", limit=3)
        assert outcome.allowed, f"hit {i} should pass"
        assert outcome.remaining == 3 - (i + 1)

    blocked = await rl.hit(endpoint="login", scope="ip:1.2.3.4", limit=3)
    assert not blocked.allowed
    assert blocked.retry_after_seconds > 0


async def test_limit_zero_always_allows() -> None:
    redis = _FakeRedis()
    rl = RateLimiter(redis=redis, window_seconds=60)  # type: ignore[arg-type]
    outcome = await rl.hit(endpoint="refresh", scope="ip:1.2.3.4", limit=0)
    assert outcome.allowed
    assert redis.counters == {}


async def test_fail_open_on_redis_error() -> None:
    redis = _FakeRedis()
    redis.fail = True
    rl = RateLimiter(redis=redis, window_seconds=60)  # type: ignore[arg-type]
    outcome = await rl.hit(endpoint="login", scope="ip:1.2.3.4", limit=3)
    assert outcome.allowed
    assert outcome.remaining == 3


def test_client_ip_uses_xff_when_proxy_count_set() -> None:
    # Chain layout: ``<original-client>, <trusted-nginx>``. With one trusted
    # hop we skip the rightmost entry (our nginx) and pick the one to its
    # left as the real client.
    headers: dict[str, str] = {
        "x-forwarded-for": "203.0.113.1, 10.0.0.1",
    }
    assert (
        client_ip(headers, "192.168.0.1", trusted_proxy_count=1) == "203.0.113.1"
    )


def test_client_ip_ignores_xff_by_default() -> None:
    """Without trusted_proxy_count we never trust XFF — see test_xff_trust.py."""
    headers: dict[str, str] = {
        "x-forwarded-for": "203.0.113.1, 10.0.0.1",
    }
    assert client_ip(headers, "192.168.0.1") == "192.168.0.1"


def test_client_ip_falls_back_to_peer() -> None:
    assert client_ip(None, "192.168.0.1") == "192.168.0.1"
    assert client_ip({}, None) == "unknown"


@pytest.fixture(autouse=True)
def _reset(monkeypatch: pytest.MonkeyPatch) -> Any:
    yield
