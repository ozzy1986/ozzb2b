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
from sqlalchemy.pool import NullPool

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


def _prepare_schema(integration_database_url: str) -> None:
    """Drop + recreate the full schema in a dedicated short-lived loop.

    asyncpg connections bind to the asyncio event loop they're created in,
    so any engine opened inside pytest-asyncio's per-test loop would later
    leak a dead connection into a different loop. Running setup via
    ``asyncio.run`` gives us an isolated loop that fully closes before the
    test session hands control to pytest-asyncio.
    """
    import asyncio

    async def _run() -> None:
        engine = create_async_engine(
            integration_database_url, future=True, poolclass=NullPool
        )
        try:
            async with engine.begin() as conn:
                # pg_trgm powers similarity search; mirror the prod migration
                # so create_all stays compatible with any index we add later.
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
                await conn.run_sync(Base.metadata.drop_all)
                await conn.run_sync(Base.metadata.create_all)
        finally:
            await engine.dispose()

    asyncio.run(_run())


@pytest.fixture(scope="session")
def _schema_ready(integration_database_url: str) -> None:
    """Create the schema exactly once per session, outside any async loop."""
    _prepare_schema(integration_database_url)


@pytest_asyncio.fixture()
async def integration_engine(
    integration_settings: Settings, _schema_ready: None
) -> AsyncIterator[AsyncEngine]:
    """Fresh async engine per test.

    We use ``NullPool`` so no connection outlives the test's event loop,
    which is what triggered the earlier "another operation is in progress"
    / "attached to a different loop" asyncpg failures when the engine was
    session-scoped.
    """
    engine = create_async_engine(
        integration_settings.database_url, future=True, poolclass=NullPool
    )
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
