"""Postgres-only ORM smoke tests.

These guard us against ORM changes that silently work on SQLite but break on
Postgres (JSONB, TSVECTOR, UUID, native enums).
"""

from __future__ import annotations

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ozzb2b_api.db.models import Country, Provider, ProviderStatus

pytestmark = pytest.mark.integration


async def test_create_and_query_provider_with_jsonb(db_session: AsyncSession) -> None:
    country = Country(code="RU", name="Россия")
    db_session.add(country)
    await db_session.flush()

    provider = Provider(
        slug="acme-it",
        legal_name="Acme LLC",
        display_name="Acme",
        description="IT services",
        country_id=country.id,
        status=ProviderStatus.PUBLISHED,
        meta={"rating": 4.8, "tags": ["erp", "crm"]},
    )
    db_session.add(provider)
    await db_session.flush()

    loaded = (
        await db_session.execute(select(Provider).where(Provider.slug == "acme-it"))
    ).scalar_one()
    assert loaded.meta["rating"] == 4.8
    assert "erp" in loaded.meta["tags"]
    # id is a real uuid on Postgres, not a string fallback like on SQLite.
    assert hasattr(loaded.id, "hex")


async def test_tsvector_column_accepts_fts_query(db_session: AsyncSession) -> None:
    country = Country(code="RU", name="Россия")
    db_session.add(country)
    await db_session.flush()

    provider = Provider(
        slug="bytes-llc",
        legal_name="Bytes LLC",
        display_name="Bytes",
        description="разработка ПО",
        country_id=country.id,
        status=ProviderStatus.PUBLISHED,
        meta={},
    )
    db_session.add(provider)
    await db_session.flush()

    # Populate the TSVECTOR column directly; proves the column type is real and
    # that the Russian text-search configuration is available in the test DB.
    await db_session.execute(
        text(
            "UPDATE providers SET search_document = "
            "to_tsvector('russian', coalesce(display_name,'') "
            "|| ' ' || coalesce(description,'')) "
            "WHERE slug = :slug"
        ),
        {"slug": "bytes-llc"},
    )

    row = await db_session.execute(
        text(
            "SELECT count(*) FROM providers "
            "WHERE search_document @@ plainto_tsquery('russian', :q)"
        ),
        {"q": "разработка"},
    )
    assert row.scalar_one() >= 1


async def test_unique_source_source_id_is_enforced(db_session: AsyncSession) -> None:
    country = Country(code="RU", name="Россия")
    db_session.add(country)
    await db_session.flush()

    base = {
        "legal_name": "Source Co",
        "display_name": "Source Co",
        "country_id": country.id,
        "status": ProviderStatus.PUBLISHED,
        "meta": {},
        "source": "crunchy",
        "source_id": "42",
    }
    db_session.add(Provider(slug="src-1", **base))
    await db_session.flush()

    # Same (source, source_id) pair must collide; we rely on that invariant in
    # the scraper upsert path, so the test pins it down.
    db_session.add(Provider(slug="src-2", **base))
    with pytest.raises(IntegrityError):
        await db_session.flush()
