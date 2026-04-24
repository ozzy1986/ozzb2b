"""Pure-logic tests for the JSON-over-Redis reference-data cache."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from ozzb2b_api.clients import cache as cache_module


class _FakeRedis:
    def __init__(self, fail_get: bool = False, fail_set: bool = False) -> None:
        self.store: dict[str, str] = {}
        self.get_calls = 0
        self.set_calls = 0
        self.fail_get = fail_get
        self.fail_set = fail_set

    async def get(self, key: str) -> str | None:
        self.get_calls += 1
        if self.fail_get:
            raise RuntimeError("redis unavailable")
        return self.store.get(key)

    async def set(self, key: str, value: str, *, ex: int | None = None) -> None:
        self.set_calls += 1
        if self.fail_set:
            raise RuntimeError("redis unavailable")
        self.store[key] = value


@pytest.fixture(autouse=True)
def _reset_locks() -> None:
    cache_module._locks.clear()


@pytest.mark.asyncio
async def test_cache_miss_populates_value() -> None:
    fake = _FakeRedis()
    loader = AsyncMock(return_value=[1, 2, 3])
    with patch.object(cache_module, "get_redis", return_value=fake):
        result = await cache_module.get_or_set(
            "k:1",
            ttl_seconds=10,
            loader=loader,
            encode=list,
            decode=list,
        )
    assert result == [1, 2, 3]
    assert loader.await_count == 1
    assert fake.set_calls == 1
    assert "k:1" in fake.store


@pytest.mark.asyncio
async def test_cache_hit_skips_loader() -> None:
    fake = _FakeRedis()
    fake.store["k:2"] = '[1,2,3]'
    loader = AsyncMock(return_value=[9])
    with patch.object(cache_module, "get_redis", return_value=fake):
        result = await cache_module.get_or_set(
            "k:2",
            ttl_seconds=10,
            loader=loader,
            encode=list,
            decode=list,
        )
    assert result == [1, 2, 3]
    assert loader.await_count == 0
    # Cache hit -> no SET roundtrip.
    assert fake.set_calls == 0


@pytest.mark.asyncio
async def test_redis_get_failure_falls_through_to_loader() -> None:
    fake = _FakeRedis(fail_get=True)
    loader = AsyncMock(return_value="ok")
    with patch.object(cache_module, "get_redis", return_value=fake):
        result = await cache_module.get_or_set(
            "k:fail",
            ttl_seconds=10,
            loader=loader,
            encode=lambda v: v,
            decode=lambda v: v,  # type: ignore[arg-type]
        )
    assert result == "ok"
    assert loader.await_count == 1


@pytest.mark.asyncio
async def test_redis_set_failure_does_not_break_caller() -> None:
    fake = _FakeRedis(fail_set=True)
    loader = AsyncMock(return_value=[1])
    with patch.object(cache_module, "get_redis", return_value=fake):
        result = await cache_module.get_or_set(
            "k:set-fail",
            ttl_seconds=10,
            loader=loader,
            encode=list,
            decode=list,
        )
    assert result == [1]
    # Loader still ran; SET attempted (and failed silently).
    assert loader.await_count == 1


@pytest.mark.asyncio
async def test_concurrent_requests_only_load_once_per_key() -> None:
    """Single-flight: when several tasks race on a cold key, loader runs once."""
    fake = _FakeRedis()
    calls = 0

    async def loader() -> list[int]:
        nonlocal calls
        calls += 1
        return [calls]

    import asyncio

    with patch.object(cache_module, "get_redis", return_value=fake):
        results: list[Any] = await asyncio.gather(
            *(
                cache_module.get_or_set(
                    "k:race",
                    ttl_seconds=10,
                    loader=loader,
                    encode=list,
                    decode=list,
                )
                for _ in range(5)
            ),
        )
    assert calls == 1
    assert all(r == [1] for r in results)
