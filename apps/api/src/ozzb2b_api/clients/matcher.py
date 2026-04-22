"""Thin async wrapper around the matcher gRPC service.

Design notes:
- The wrapper owns a single `grpc.aio.Channel` created lazily, reused across
  calls. It's safe to share across coroutines.
- All public methods return plain Python types so the rest of the codebase
  never imports the generated protobuf symbols directly.
- Any RPC failure (timeout, UNAVAILABLE, etc.) is surfaced as
  `MatcherUnavailableError`; callers must fall back to the un-re-ranked
  result in that case — the matcher is strictly optional.
"""

from __future__ import annotations

import asyncio
import threading
import uuid
from dataclasses import dataclass
from typing import Any

import grpc
import structlog

from ozzb2b_api.config import Settings, get_settings
from ozzb2b_api.grpc_gen.ozzb2b.matcher.v1 import (
    matcher_pb2 as _matcher_pb2,
)
from ozzb2b_api.grpc_gen.ozzb2b.matcher.v1 import (
    matcher_pb2_grpc as _matcher_pb2_grpc,
)

log = structlog.get_logger("ozzb2b_api.clients.matcher")

# protoc emits dynamic attributes that mypy can't resolve; wrap the modules
# as Any so the rest of this file stays fully typed.
matcher_pb2: Any = _matcher_pb2
matcher_pb2_grpc: Any = _matcher_pb2_grpc


class MatcherError(Exception):
    """Base error for matcher client."""


class MatcherUnavailableError(MatcherError):
    """The matcher service could not be reached in time."""


@dataclass(frozen=True)
class MatcherCandidate:
    provider_id: uuid.UUID
    display_name: str
    description: str
    category_slugs: tuple[str, ...]
    country_code: str
    city_slug: str
    legal_form_code: str
    retrieval_score: float


@dataclass(frozen=True)
class MatcherScore:
    provider_id: uuid.UUID
    score: float
    matcher_score: float


class MatcherClient:
    """Async gRPC client for `MatcherService.Rank`.

    The instance caches a single channel; call `close()` on shutdown if you
    want a clean release of file descriptors (FastAPI lifecycle hook).
    """

    def __init__(self, *, addr: str, timeout_ms: int) -> None:
        self._addr = addr
        self._timeout = timeout_ms / 1000.0
        self._channel: grpc.aio.Channel | None = None
        self._stub: Any = None
        self._lock = threading.Lock()

    def _ensure_stub(self) -> Any:
        with self._lock:
            if self._stub is None:
                self._channel = grpc.aio.insecure_channel(self._addr)
                self._stub = matcher_pb2_grpc.MatcherServiceStub(self._channel)
            return self._stub

    async def close(self) -> None:
        if self._channel is not None:
            await self._channel.close()
            self._channel = None
            self._stub = None

    async def rank(
        self,
        *,
        query: str,
        category_slugs: tuple[str, ...],
        country_codes: tuple[str, ...],
        city_slugs: tuple[str, ...],
        legal_form_codes: tuple[str, ...],
        limit: int,
        offset: int,
        candidates: list[MatcherCandidate],
    ) -> list[MatcherScore]:
        if not candidates:
            return []

        stub = self._ensure_stub()
        req = matcher_pb2.RankRequest(
            query=query,
            category_slugs=list(category_slugs),
            country_codes=list(country_codes),
            city_slugs=list(city_slugs),
            legal_form_codes=list(legal_form_codes),
            limit=limit,
            offset=offset,
            candidates=[
                matcher_pb2.Candidate(
                    provider_id=str(c.provider_id),
                    display_name=c.display_name,
                    description=c.description,
                    category_slugs=list(c.category_slugs),
                    country_code=c.country_code,
                    city_slug=c.city_slug,
                    legal_form_code=c.legal_form_code,
                    retrieval_score=c.retrieval_score,
                )
                for c in candidates
            ],
        )
        try:
            resp = await asyncio.wait_for(stub.Rank(req), timeout=self._timeout)
        except (grpc.aio.AioRpcError, TimeoutError, OSError) as exc:
            raise MatcherUnavailableError(str(exc)) from exc

        out: list[MatcherScore] = []
        for p in resp.providers:
            try:
                pid = uuid.UUID(p.provider_id)
            except (ValueError, AttributeError):
                log.warning("matcher.invalid_provider_id", id=p.provider_id)
                continue
            out.append(
                MatcherScore(
                    provider_id=pid,
                    score=float(p.score),
                    matcher_score=float(p.matcher_score),
                )
            )
        return out


_client: MatcherClient | None = None
_client_lock = threading.Lock()


def get_matcher_client(settings: Settings | None = None) -> MatcherClient:
    """Process-wide singleton, built lazily from `Settings`."""
    global _client
    cfg = settings or get_settings()
    with _client_lock:
        if _client is None:
            _client = MatcherClient(
                addr=cfg.matcher_grpc_addr,
                timeout_ms=cfg.matcher_timeout_ms,
            )
        return _client


def reset_matcher_client() -> None:
    """Test/utility helper — drop the cached client."""
    global _client
    with _client_lock:
        _client = None
