"""Pytest fixtures shared across the API test suite."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ozzb2b_api.app import create_app
from ozzb2b_api.config import Settings
from ozzb2b_api.db.base import Base
from ozzb2b_api.db import models  # noqa: F401  # register models in metadata


@pytest.fixture()
def settings() -> Settings:
    # In-memory SQLite for unit-level tests that don't exercise Postgres-only features.
    return Settings(
        env="test",
        log_level="WARNING",
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://127.0.0.1:6399/15",  # unused unless mocked
        meilisearch_url="http://127.0.0.1:7799",
    )


@pytest.fixture()
def client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(settings=settings)) as c:
        yield c


@pytest_asyncio.fixture()
async def db_session(settings: Settings) -> AsyncIterator[AsyncSession]:
    """A SQLite-backed DB session with the schema created (no pg-specific features)."""
    engine = create_async_engine(settings.database_url, future=True)
    # Build a PG-free metadata subset (skip TSVECTOR/JSONB columns via column_visible=False).
    # For our unit tests this isolated runtime is enough for basic constraint checks.
    async with engine.begin() as conn:
        await conn.run_sync(_create_portable_tables)
    sessionmaker: Any = async_sessionmaker(
        bind=engine, expire_on_commit=False, class_=AsyncSession
    )
    async with sessionmaker() as session:
        yield session
    await engine.dispose()


def _create_portable_tables(sync_conn: Any) -> None:
    """Create only the portable tables we need for unit tests on SQLite."""
    from sqlalchemy import inspect

    portable = [
        Base.metadata.tables[n]
        for n in (
            "countries",
            "cities",
            "legal_forms",
            "categories",
        )
    ]
    for t in portable:
        if not inspect(sync_conn).has_table(t.name):
            t.create(sync_conn)
