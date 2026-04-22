"""Search service: Meilisearch-first with a Postgres FTS fallback.

Design notes (SOLID):
- `SearchGateway` is the abstract port.
- `MeilisearchGateway` and `PostgresFtsGateway` are interchangeable adapters.
- `search()` tries Meili first; on any failure it falls back to Postgres so the
  site stays functional while indexing catches up.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass

import structlog
from sqlalchemy import func, literal, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ozzb2b_api.clients.meilisearch import get_meilisearch
from ozzb2b_api.db.models import (
    Category,
    City,
    Country,
    LegalForm,
    Provider,
    ProviderCategory,
    ProviderStatus,
)

log = structlog.get_logger("ozzb2b_api.services.search")

PROVIDERS_INDEX = "providers"


@dataclass(frozen=True)
class SearchQuery:
    q: str
    category_slugs: tuple[str, ...] = ()
    country_codes: tuple[str, ...] = ()
    city_slugs: tuple[str, ...] = ()
    legal_form_codes: tuple[str, ...] = ()
    limit: int = 24
    offset: int = 0


@dataclass(frozen=True)
class SearchHit:
    provider_id: uuid.UUID
    score: float


@dataclass(frozen=True)
class SearchResult:
    total: int
    hits: list[SearchHit]
    engine: str


class SearchGateway(ABC):
    @abstractmethod
    async def search(self, session: AsyncSession, q: SearchQuery) -> SearchResult:
        ...


def _meili_filter_expression(q: SearchQuery) -> list[str]:
    parts: list[str] = ["status = 'published'"]
    if q.category_slugs:
        ors = " OR ".join(f"category_slugs = '{s}'" for s in q.category_slugs)
        parts.append(f"({ors})")
    if q.country_codes:
        ors = " OR ".join(f"country_code = '{s}'" for s in q.country_codes)
        parts.append(f"({ors})")
    if q.city_slugs:
        ors = " OR ".join(f"city_slug = '{s}'" for s in q.city_slugs)
        parts.append(f"({ors})")
    if q.legal_form_codes:
        ors = " OR ".join(f"legal_form_code = '{s}'" for s in q.legal_form_codes)
        parts.append(f"({ors})")
    return parts


class MeilisearchGateway(SearchGateway):
    async def search(self, session: AsyncSession, q: SearchQuery) -> SearchResult:
        client = get_meilisearch()
        index = client.index(PROVIDERS_INDEX)
        filter_exprs = _meili_filter_expression(q)
        response = index.search(
            q.q,
            {
                "limit": q.limit,
                "offset": q.offset,
                "filter": filter_exprs,
                "attributesToRetrieve": ["id"],
            },
        )
        hits_raw = response.get("hits", [])
        total = response.get("estimatedTotalHits", response.get("totalHits", len(hits_raw)))
        hits = [
            SearchHit(provider_id=uuid.UUID(str(h["id"])), score=1.0)
            for h in hits_raw
            if "id" in h
        ]
        return SearchResult(total=int(total), hits=hits, engine="meilisearch")


class PostgresFtsGateway(SearchGateway):
    async def search(self, session: AsyncSession, q: SearchQuery) -> SearchResult:
        stmt = select(Provider.id).where(Provider.status == ProviderStatus.PUBLISHED)
        if q.country_codes:
            stmt = stmt.join(Provider.country).where(Country.code.in_(q.country_codes))
        if q.city_slugs:
            stmt = stmt.join(Provider.city).where(City.slug.in_(q.city_slugs))
        if q.legal_form_codes:
            stmt = stmt.join(Provider.legal_form).where(LegalForm.code.in_(q.legal_form_codes))
        if q.category_slugs:
            stmt = (
                stmt.join(ProviderCategory, ProviderCategory.provider_id == Provider.id)
                .join(Category, Category.id == ProviderCategory.category_id)
                .where(Category.slug.in_(q.category_slugs))
            )
        text = q.q.strip()
        if text:
            ts = func.plainto_tsquery("simple", func.unaccent(text))
            stmt = stmt.where(Provider.search_document.op("@@")(ts))
            rank = func.ts_rank_cd(Provider.search_document, ts)
            stmt = stmt.add_columns(rank).order_by(rank.desc())
        else:
            stmt = stmt.add_columns(literal(1.0)).order_by(Provider.display_name.asc())

        stmt = stmt.distinct()
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = int((await session.execute(total_stmt)).scalar_one())
        rows = (await session.execute(stmt.limit(q.limit).offset(q.offset))).all()
        hits = [SearchHit(provider_id=r[0], score=float(r[1]) if len(r) > 1 else 1.0) for r in rows]
        return SearchResult(total=total, hits=hits, engine="postgres-fts")


async def search(session: AsyncSession, q: SearchQuery) -> SearchResult:
    """Meili-first with Postgres FTS fallback."""
    try:
        return await MeilisearchGateway().search(session, q)
    except Exception as exc:  # pragma: no cover - fallback path
        log.warning("search.meilisearch_fail", err=str(exc))
        return await PostgresFtsGateway().search(session, q)


async def hydrate_providers(session: AsyncSession, ids: list[uuid.UUID]) -> list[Provider]:
    """Fetch full Provider rows for hit ids, preserving the input order."""
    if not ids:
        return []
    stmt = (
        select(Provider)
        .where(Provider.id.in_(ids))
        .options(
            selectinload(Provider.country),
            selectinload(Provider.city),
            selectinload(Provider.legal_form),
            selectinload(Provider.categories),
        )
    )
    rows = {p.id: p for p in (await session.execute(stmt)).unique().scalars().all()}
    return [rows[i] for i in ids if i in rows]
