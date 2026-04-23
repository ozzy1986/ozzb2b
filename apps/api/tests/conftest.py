"""Pytest fixtures shared across the API test suite."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

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
def settings() -> Settings:
    """Minimal, hermetic test settings (no external deps required)."""
    return Settings(
        env="test",
        log_level="WARNING",
        database_url="sqlite+aiosqlite:///:memory:",
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
def client(settings: Settings) -> Iterator[TestClient]:
    """TestClient with an isolated in-memory SQLite DB wired as get_db()."""
    engine = create_async_engine(settings.database_url, future=True)
    sessionmaker: Any = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    import asyncio

    async def _prepare() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(_create_portable_tables)

    asyncio.get_event_loop().run_until_complete(_prepare())

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

    async def _dispose() -> None:
        await engine.dispose()

    asyncio.get_event_loop().run_until_complete(_dispose())


@pytest_asyncio.fixture()
async def db_session(settings: Settings) -> AsyncIterator[AsyncSession]:
    """Standalone session for service-layer tests (no FastAPI wiring)."""
    engine = create_async_engine(settings.database_url, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(_create_portable_tables)
    sessionmaker: Any = async_sessionmaker(
        bind=engine, expire_on_commit=False, class_=AsyncSession
    )
    async with sessionmaker() as session:
        yield session
    await engine.dispose()
