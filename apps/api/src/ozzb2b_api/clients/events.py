"""Product event emitter.

Events are published as JSON entries on a Redis Stream
(`ozzb2b:events:v1` by default). The API side is fire-and-forget: a publish
failure must never break the request. The Go events consumer drains the
stream and persists into ClickHouse.

Design notes (SOLID / KISS):
- `EventEmitter` owns a single async Redis connection, hides the stream name
  and approximate-trim length behind a thin API.
- Every event has the same top-level envelope so consumers don't need to
  know every event type (forward-compatible).
- The emitter is optional (`settings.events_enabled`); when disabled, all
  `emit_*` helpers become no-ops, so instrumenting business code stays safe.
"""

from __future__ import annotations

import asyncio
import json
import secrets
import threading
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

import structlog
from redis.asyncio import Redis

from ozzb2b_api.clients.redis import get_redis
from ozzb2b_api.config import Settings, get_settings
from ozzb2b_api.observability.metrics import events_published_total

log = structlog.get_logger("ozzb2b_api.clients.events")


EVENT_SEARCH_PERFORMED = "search_performed"
EVENT_PROVIDER_VIEWED = "provider_viewed"
EVENT_CHAT_STARTED = "chat_started"
EVENT_CHAT_MESSAGE_SENT = "chat_message_sent"


class EventEmitter:
    """Publishes events to a Redis Stream. Safe to share across coroutines."""

    def __init__(
        self,
        *,
        redis: Redis,
        stream_name: str,
        maxlen: int,
        enabled: bool,
    ) -> None:
        self._redis = redis
        self._stream = stream_name
        self._maxlen = max(1_000, maxlen)
        self._enabled = enabled

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def emit(
        self,
        event_type: str,
        *,
        user_id: uuid.UUID | None = None,
        session_id: str | None = None,
        properties: Mapping[str, Any] | None = None,
    ) -> None:
        """Publish a single event. Failures are logged and swallowed."""
        if not self._enabled:
            return

        envelope: dict[str, Any] = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "occurred_at": datetime.now(UTC).isoformat(),
            "user_id": str(user_id) if user_id else None,
            "session_id": session_id,
            "properties": dict(properties or {}),
        }

        payload = json.dumps(envelope, separators=(",", ":"))
        # Redis xadd is normally fast; brief network blips should not lose
        # an event silently. We retry up to 3 times with exponential backoff
        # and jitter, then give up — analytics is best-effort and must not
        # block the request path forever.
        delay = 0.05
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                # Redis Streams treats fields as a flat map; keep the whole
                # envelope in a single `payload` field so consumers only
                # parse JSON (no per-field type coercion).
                await self._redis.xadd(
                    self._stream,
                    {"payload": payload},
                    maxlen=self._maxlen,
                    approximate=True,
                )
                events_published_total.labels(event_type, "ok").inc()
                return
            except Exception as exc:  # pragma: no cover - best effort
                last_exc = exc
                if attempt == 2:
                    break
                # secrets.SystemRandom for jitter — we don't need cryptographic
                # randomness but it avoids the global random() seed.
                jitter = secrets.SystemRandom().uniform(0, delay)
                await asyncio.sleep(delay + jitter)
                delay *= 2
        events_published_total.labels(event_type, "error").inc()
        log.warning(
            "events.publish_failed",
            err=str(last_exc) if last_exc else "unknown",
            event_type=event_type,
        )


_emitter: EventEmitter | None = None
_emitter_lock = threading.Lock()


def get_event_emitter(settings: Settings | None = None) -> EventEmitter:
    """Process-wide singleton built lazily from `Settings`."""
    global _emitter
    cfg = settings or get_settings()
    with _emitter_lock:
        if _emitter is None:
            _emitter = EventEmitter(
                redis=get_redis(),
                stream_name=cfg.events_stream_name,
                maxlen=cfg.events_stream_maxlen,
                enabled=cfg.events_enabled,
            )
        return _emitter


def reset_event_emitter() -> None:
    """Test helper — drop the cached emitter."""
    global _emitter
    with _emitter_lock:
        _emitter = None
