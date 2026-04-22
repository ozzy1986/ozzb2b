"""Meilisearch indexer for providers.

Responsibilities:
- Ensure the `providers` index exists and has the right searchable/filterable/sortable attrs.
- Build a denormalized document per provider from Postgres.
- Upsert documents in batches.
"""

from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ozzb2b_api.clients.meilisearch import get_meilisearch
from ozzb2b_api.db.models import Provider, ProviderStatus
from ozzb2b_api.services.search import PROVIDERS_INDEX

log = structlog.get_logger("ozzb2b_api.services.indexer")


SEARCHABLE_ATTRIBUTES = [
    "display_name",
    "legal_name",
    "description",
    "country_name",
    "city_name",
    "address",
    "category_names",
]

FILTERABLE_ATTRIBUTES = [
    "status",
    "country_code",
    "city_slug",
    "legal_form_code",
    "category_slugs",
    "year_founded",
    "employee_count_range",
]

SORTABLE_ATTRIBUTES = ["display_name", "year_founded"]

RANKING_RULES = [
    "words",
    "typo",
    "proximity",
    "attribute",
    "sort",
    "exactness",
]


def ensure_index() -> None:
    client = get_meilisearch()
    client.create_index(PROVIDERS_INDEX, {"primaryKey": "id"})
    index = client.index(PROVIDERS_INDEX)
    index.update_searchable_attributes(SEARCHABLE_ATTRIBUTES)
    index.update_filterable_attributes(FILTERABLE_ATTRIBUTES)
    index.update_sortable_attributes(SORTABLE_ATTRIBUTES)
    index.update_ranking_rules(RANKING_RULES)


def _provider_to_doc(p: Provider) -> dict[str, Any]:
    return {
        "id": str(p.id),
        "slug": p.slug,
        "display_name": p.display_name,
        "legal_name": p.legal_name,
        "description": p.description,
        "address": p.address,
        "country_code": p.country.code if p.country else None,
        "country_name": p.country.name if p.country else None,
        "city_slug": p.city.slug if p.city else None,
        "city_name": p.city.name if p.city else None,
        "legal_form_code": p.legal_form.code if p.legal_form else None,
        "legal_form_name": p.legal_form.name if p.legal_form else None,
        "category_slugs": [c.slug for c in p.categories],
        "category_names": [c.name for c in p.categories],
        "year_founded": p.year_founded,
        "employee_count_range": p.employee_count_range,
        "status": p.status.value,
    }


async def reindex_all(session: AsyncSession, *, batch_size: int = 200) -> int:
    """Full reindex of all published providers. Returns count of documents sent."""
    ensure_index()
    client = get_meilisearch()
    index = client.index(PROVIDERS_INDEX)

    stmt = (
        select(Provider)
        .where(Provider.status == ProviderStatus.PUBLISHED)
        .options(
            selectinload(Provider.country),
            selectinload(Provider.city),
            selectinload(Provider.legal_form),
            selectinload(Provider.categories),
        )
        .order_by(Provider.created_at.asc())
    )

    total = 0
    batch: list[dict[str, Any]] = []
    result = await session.execute(stmt)
    for p in result.scalars().unique():
        batch.append(_provider_to_doc(p))
        if len(batch) >= batch_size:
            index.add_documents(batch, primary_key="id")
            total += len(batch)
            batch = []
    if batch:
        index.add_documents(batch, primary_key="id")
        total += len(batch)

    log.info("indexer.reindex_all.done", docs=total)
    return total


async def upsert_one(p: Provider) -> None:
    ensure_index()
    get_meilisearch().index(PROVIDERS_INDEX).add_documents([_provider_to_doc(p)], primary_key="id")


async def delete_one(provider_id: str) -> None:
    get_meilisearch().index(PROVIDERS_INDEX).delete_document(provider_id)
