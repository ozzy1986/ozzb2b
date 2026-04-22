"""Liveness and readiness endpoints."""

from __future__ import annotations

import asyncio

import structlog
from fastapi import APIRouter, Response, status
from pydantic import BaseModel
from sqlalchemy import text

from ozzb2b_api import __version__
from ozzb2b_api.clients.meilisearch import ping_meilisearch
from ozzb2b_api.clients.redis import ping_redis
from ozzb2b_api.db.session import get_engine

router = APIRouter(tags=["health"])
log = structlog.get_logger("ozzb2b_api.health")


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ReadyDependency(BaseModel):
    name: str
    ok: bool


class ReadyResponse(BaseModel):
    status: str
    service: str
    version: str
    dependencies: list[ReadyDependency]


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness probe: 200 as long as the process is running."""
    return HealthResponse(status="ok", service="ozzb2b-api", version=__version__)


async def _ping_database() -> bool:
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # pragma: no cover - exercised only when DB is down
        log.warning("ready.database_fail", err=str(exc))
        return False


@router.get("/ready", response_model=ReadyResponse)
async def ready(response: Response) -> ReadyResponse:
    """Readiness probe: check that DB, Redis, and Meilisearch are reachable."""
    db_ok, redis_ok, meili_ok = await asyncio.gather(
        _ping_database(),
        ping_redis(),
        ping_meilisearch(),
    )
    deps = [
        ReadyDependency(name="database", ok=db_ok),
        ReadyDependency(name="redis", ok=redis_ok),
        ReadyDependency(name="meilisearch", ok=meili_ok),
    ]
    overall_ok = all(d.ok for d in deps)
    if not overall_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadyResponse(
        status="ok" if overall_ok else "degraded",
        service="ozzb2b-api",
        version=__version__,
        dependencies=deps,
    )
