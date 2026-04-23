"""Pytest fixtures shared across the API test suite."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from ozzb2b_api.app import create_app
from ozzb2b_api.config import Settings
from ozzb2b_api.db import models  # noqa: F401 — register models in metadata
from ozzb2b_api.db.base import Base
from ozzb2b_api.db.session import get_db

PORTABLE_TABLES = (
    "countries",
    "cities",
    "legal_forms",
    "categories",
    "users",
    "refresh_tokens",
)


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    """Minimal, hermetic test settings (no external deps required).

    We back SQLite with a tmp-file so that every Session opened from the
    same engine sees the same database — a shared ``:memory:`` DB would
    otherwise need StaticPool + thread-pinning, which breaks when the
    FastAPI TestClient spawns its own event loop in a worker thread.
    """
    db_path = tmp_path / "ozzb2b-test.db"
    return Settings(
        env="test",
        log_level="WARNING",
        database_url=f"sqlite+aiosqlite:///{db_path.as_posix()}",
        redis_url="redis://127.0.0.1:6399/15",
        meilisearch_url="http://127.0.0.1:7799",
        rate_limit_enabled=False,
        jwt_secret="unit-tests-secret-long-enough-for-hmac",
    )


def _create_portable_tables(sync_conn: Any) -> None:
    """Create only the SQLite-compatible subset of our schema."""
    for name in PORTABLE_TABLES:
        t = Base.metadata.tables[name]
        if not inspect(sync_conn).has_table(t.name):
            t.create(sync_conn)


@pytest.fixture()
def test_engine(settings: Settings) -> Iterator[AsyncEngine]:
    """A pre-populated SQLite engine shared with ``client``.

    Exposing the engine explicitly lets tests insert fixture rows (users,
    providers, etc.) without going through FastAPI, while still sharing
    state with whatever the route-handlers read from ``get_db``.
    """
    # NullPool: every new session opens its own aiosqlite connection and
    # closes it on release, so connections never cross the event-loop
    # boundary between the main thread and the TestClient worker loop.
    engine = create_async_engine(
        settings.database_url, future=True, poolclass=NullPool
    )

    async def _prepare() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(_create_portable_tables)

    asyncio.run(_prepare())
    try:
        yield engine
    finally:

        async def _dispose() -> None:
            await engine.dispose()

        asyncio.run(_dispose())


@pytest.fixture()
def client(settings: Settings, test_engine: AsyncEngine) -> Iterator[TestClient]:
    """TestClient wired to the shared in-memory SQLite engine."""
    sessionmaker: Any = async_sessionmaker(
        test_engine, expire_on_commit=False, class_=AsyncSession
    )

    async def override_db() -> AsyncIterator[AsyncSession]:
        async with sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app = create_app(settings=settings)
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as c:
        yield c


@pytest_asyncio.fixture()
async def db_session(settings: Settings) -> AsyncIterator[AsyncSession]:
    """Standalone session for service-layer tests (no FastAPI wiring)."""
    engine = create_async_engine(
        settings.database_url, future=True, poolclass=NullPool
    )
    async with engine.begin() as conn:
        await conn.run_sync(_create_portable_tables)
    sessionmaker: Any = async_sessionmaker(
        bind=engine, expire_on_commit=False, class_=AsyncSession
    )
    async with sessionmaker() as session:
        yield session
    await engine.dispose()
