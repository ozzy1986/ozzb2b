"""Unit tests for the product event emitter."""

from __future__ import annotations

import json
import uuid
from typing import Any

import pytest

from ozzb2b_api.clients.events import (
    EVENT_SEARCH_PERFORMED,
    EventEmitter,
)


class _FakeRedis:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def xadd(
        self,
        name: str,
        fields: dict[str, str],
        *,
        maxlen: int,
        approximate: bool,
    ) -> str:
        self.calls.append(
            {
                "name": name,
                "fields": fields,
                "maxlen": maxlen,
                "approximate": approximate,
            }
        )
        return "1-0"


class _BrokenRedis:
    async def xadd(self, *_args: Any, **_kwargs: Any) -> str:
        raise RuntimeError("redis down")


async def test_disabled_emitter_is_noop() -> None:
    redis = _FakeRedis()
    emitter = EventEmitter(redis=redis, stream_name="s", maxlen=1000, enabled=False)
    await emitter.emit(EVENT_SEARCH_PERFORMED, properties={"query": "x"})
    assert redis.calls == []


async def test_enabled_emitter_writes_envelope() -> None:
    redis = _FakeRedis()
    emitter = EventEmitter(redis=redis, stream_name="ozzb2b:events:v1", maxlen=5000, enabled=True)
    user_id = uuid.uuid4()
    await emitter.emit(
        EVENT_SEARCH_PERFORMED,
        user_id=user_id,
        session_id="sid-123",
        properties={"query": "разработка", "engine": "meilisearch"},
    )
    assert len(redis.calls) == 1
    call = redis.calls[0]
    assert call["name"] == "ozzb2b:events:v1"
    assert call["approximate"] is True
    assert call["maxlen"] == 5000

    envelope = json.loads(call["fields"]["payload"])
    assert envelope["event_type"] == EVENT_SEARCH_PERFORMED
    assert envelope["user_id"] == str(user_id)
    assert envelope["session_id"] == "sid-123"
    assert envelope["properties"]["query"] == "разработка"
    assert envelope["properties"]["engine"] == "meilisearch"
    # sanity: envelope timestamp is ISO-8601 UTC.
    assert envelope["occurred_at"].endswith("+00:00")
    uuid.UUID(envelope["event_id"])  # raises on bad format


async def test_emitter_swallows_redis_errors() -> None:
    emitter = EventEmitter(
        redis=_BrokenRedis(),  # type: ignore[arg-type]
        stream_name="s",
        maxlen=1000,
        enabled=True,
    )
    # Must not raise — failures are logged and discarded.
    await emitter.emit(EVENT_SEARCH_PERFORMED, properties={})


async def test_maxlen_floor_guards_against_zero() -> None:
    redis = _FakeRedis()
    emitter = EventEmitter(redis=redis, stream_name="s", maxlen=0, enabled=True)
    await emitter.emit(EVENT_SEARCH_PERFORMED, properties={})
    assert redis.calls[0]["maxlen"] >= 1000


@pytest.fixture(autouse=True)
def _no_env_leak(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OZZB2B_EVENTS_ENABLED", raising=False)
