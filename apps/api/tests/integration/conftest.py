"""Integration test fixtures — require a real Postgres + Redis.

These tests exercise Postgres-specific column types (TSVECTOR, JSONB, UUID)
and Redis semantics that SQLite / fakeredis can't simulate. They are opt-in:
the unit suite ignores this directory (see ``pyproject.toml``) and this
module skips entirely when ``OZZB2B_INTEGRATION_DATABASE_URL`` /
``OZZB2B_INTEGRATION_REDIS_URL`` aren't set, so running ``pytest`` locally
without infra stays green.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from typing import Any

import pytest
import pytest_asyncio
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ozzb2b_api.config import Settings
from ozzb2b_api.db import models  # noqa: F401 — register ORM metadata
from ozzb2b_api.db.base import Base


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        pytest.skip(
            f"{name} not set — skipping integration suite",
            allow_module_level=True,
        )
    return value


@pytest.fixture(scope="session")
def integration_database_url() -> str:
    return _require_env("OZZB2B_INTEGRATION_DATABASE_URL")


@pytest.fixture(scope="session")
def integration_redis_url() -> str:
    return _require_env("OZZB2B_INTEGRATION_REDIS_URL")


@pytest.fixture(scope="session")
def integration_settings(
    integration_database_url: str, integration_redis_url: str
) -> Settings:
    return Settings(
        env="test",
        log_level="WARNING",
        database_url=integration_database_url,
        redis_url=integration_redis_url,
        rate_limit_enabled=False,
        jwt_secret="integration-tests-secret-long-enough-for-hmac",
    )


@pytest_asyncio.fixture(scope="session")
async def integration_engine(
    integration_settings: Settings,
) -> AsyncIterator[AsyncEngine]:
    """Fresh schema per session so tests never observe stale state."""
    engine = create_async_engine(integration_settings.database_url, future=True)
    async with engine.begin() as conn:
        # pg_trgm powers similarity search; the prod migration enables it too,
        # so we mirror that here to keep create_all compatible with any index
        # we later add on top of it.
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture()
async def db_session(integration_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Per-test session; everything rolls back to keep tests independent."""
    sessionmaker: Any = async_sessionmaker(
        bind=integration_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with sessionmaker() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest_asyncio.fixture()
async def redis_client(integration_redis_url: str) -> AsyncIterator[Redis]:
    """Clean Redis DB before/after each test; avoids cross-test leakage."""
    client: Redis = Redis.from_url(integration_redis_url, decode_responses=False)
    try:
        await client.flushdb()
        yield client
    finally:
        await client.flushdb()
        await client.aclose()
