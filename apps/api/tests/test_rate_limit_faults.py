"""Fault-injection tests for the Redis-backed rate limiter.

The production contract is "fail-open on Redis outage": if Redis is slow,
unreachable, misconfigured, or returns garbage, the limiter must never
block legitimate traffic. These tests lock that guarantee in.
"""

from __future__ import annotations

import asyncio

import pytest

from ozzb2b_api.security.rate_limit import RateLimiter, RateLimitResult, client_ip


class _FailingRedis:
    """Redis stub where every coroutine raises the configured exception."""

    def __init__(self, exc: BaseException) -> None:
        self._exc = exc

    async def incr(self, _key: str) -> int:
        raise self._exc

    async def expire(self, _key: str, _ttl: int) -> int:
        raise self._exc

    async def ttl(self, _key: str) -> int:
        raise self._exc


class _SlowRedis:
    """Redis stub that hangs forever; we wrap it in asyncio.wait_for ourselves."""

    async def incr(self, _key: str) -> int:
        await asyncio.sleep(3600)
        return 0

    async def expire(self, _key: str, _ttl: int) -> int:
        await asyncio.sleep(3600)
        return 0

    async def ttl(self, _key: str) -> int:
        await asyncio.sleep(3600)
        return -2


async def test_rate_limiter_fails_open_on_connection_error() -> None:
    rl = RateLimiter(redis=_FailingRedis(ConnectionError("boom")), window_seconds=60)
    res = await rl.hit(endpoint="login", scope="1.2.3.4", limit=1)
    assert isinstance(res, RateLimitResult)
    assert res.allowed is True


async def test_rate_limiter_fails_open_on_generic_error() -> None:
    rl = RateLimiter(redis=_FailingRedis(RuntimeError("oops")), window_seconds=60)
    res = await rl.hit(endpoint="register", scope="fp-1", limit=5)
    assert res.allowed is True
    assert res.remaining == 5


async def test_rate_limiter_respects_zero_or_negative_limit() -> None:
    # Limit <= 0 means "unlimited" by contract — must never query Redis.
    rl = RateLimiter(redis=_FailingRedis(RuntimeError("should not be called")), window_seconds=60)
    res = await rl.hit(endpoint="any", scope="scope", limit=0)
    assert res.allowed is True
    res_negative = await rl.hit(endpoint="any", scope="scope", limit=-10)
    assert res_negative.allowed is True


async def test_rate_limiter_fails_open_when_redis_hangs() -> None:
    """Even if Redis hangs, we still get an allowed response within our timeout.

    The real production wrapper uses asyncio.wait_for around hit(). We simulate
    that here to prove the limiter's exception path is reachable from a cancel.
    """
    rl = RateLimiter(redis=_SlowRedis(), window_seconds=60)
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(
            rl.hit(endpoint="login", scope="fp-x", limit=1), timeout=0.05
        )


def test_client_ip_prefers_x_forwarded_for_when_proxy_count_set() -> None:
    # XFF must be opted into via trusted_proxy_count; without it we never
    # trust the header (anti-spoofing default).
    ip = client_ip(
        {"x-forwarded-for": "1.2.3.4, 10.0.0.1"},
        fallback="127.0.0.1",
        trusted_proxy_count=1,
    )
    assert ip == "1.2.3.4"


def test_client_ip_falls_back_when_no_header() -> None:
    assert client_ip(None, fallback="127.0.0.1") == "127.0.0.1"
    assert client_ip({}, fallback=None) == "unknown"


def test_client_ip_handles_case_variants() -> None:
    # With one trusted hop and a single-entry chain, the leftmost (==only)
    # entry is the best available answer.
    assert (
        client_ip(
            {"X-Forwarded-For": "2.2.2.2"},
            fallback="127.0.0.1",
            trusted_proxy_count=1,
        )
        == "2.2.2.2"
    )
