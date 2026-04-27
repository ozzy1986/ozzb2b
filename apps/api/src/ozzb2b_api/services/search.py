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
from typing import Any

import anyio
import structlog
from sqlalchemy import func, literal, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ozzb2b_api.clients.matcher import (
    MatcherCandidate,
    MatcherClient,
    MatcherUnavailableError,
    get_matcher_client,
)
from ozzb2b_api.clients.meilisearch import get_meilisearch
from ozzb2b_api.config import get_settings
from ozzb2b_api.db.models import (
    Category,
    City,
    Country,
    LegalForm,
    Provider,
    ProviderCategory,
    ProviderStatus,
)
from ozzb2b_api.observability.metrics import matcher_calls_total

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


@dataclass(frozen=True)
class SearchSuggestion:
    slug: str
    display_name: str
    description: str | None
    city_name: str | None
    country_code: str | None


class SearchGateway(ABC):
    @abstractmethod
    async def search(self, session: AsyncSession, q: SearchQuery) -> SearchResult:
        ...


def _escape_meili_value(value: str) -> str:
    """Escape a single quoted-string value for Meilisearch's filter DSL.

    Meilisearch parses filter strings like ``field = 'value'`` and the only
    metacharacter inside the quoted segment is the single quote. Doubling it
    is the documented escape, so a value of ``it's`` becomes ``'it''s'``.
    Inputs containing CR/LF or NUL are rejected outright — they have no
    legitimate place in a slug/code coming from our schemas and would only
    show up as a malicious crafting attempt.
    """
    if any(ch in value for ch in ("\r", "\n", "\x00")):
        raise ValueError(f"invalid filter value: {value!r}")
    return value.replace("'", "''")


def _switch_keyboard_layout(value: str) -> str:
    en = "`qwertyuiop[]asdfghjkl;'zxcvbnm,./"
    ru = "ёйцукенгшщзхъфывапролджэячсмитьбю."
    to_ru = {en[i]: ru[i] for i in range(len(en))}
    to_en = {ru[i]: en[i] for i in range(len(ru))}
    lower = value.lower()
    has_ru = any(ch in to_en for ch in lower)
    has_en = any(ch in to_ru for ch in lower)
    mapping = to_en if has_ru and not has_en else to_ru
    return "".join(mapping.get(ch, ch) for ch in lower)


def _query_variants(value: str) -> list[str]:
    base = value.strip().lower()
    if not base:
        return []
    switched = _switch_keyboard_layout(base)
    return [base, switched] if switched != base else [base]


def _meili_filter_expression(q: SearchQuery) -> list[str]:
    parts: list[str] = ["status = 'published'"]

    def _ors(field: str, values: tuple[str, ...]) -> str:
        return " OR ".join(f"{field} = '{_escape_meili_value(v)}'" for v in values)

    if q.category_slugs:
        parts.append(f"({_ors('category_slugs', q.category_slugs)})")
    if q.country_codes:
        parts.append(f"({_ors('country_code', q.country_codes)})")
    if q.city_slugs:
        parts.append(f"({_ors('city_slug', q.city_slugs)})")
    if q.legal_form_codes:
        parts.append(f"({_ors('legal_form_code', q.legal_form_codes)})")
    return parts


class MeilisearchGateway(SearchGateway):
    async def search(self, session: AsyncSession, q: SearchQuery) -> SearchResult:
        client = get_meilisearch()
        index = client.index(PROVIDERS_INDEX)
        filter_exprs = _meili_filter_expression(q)
        params = {
            "limit": q.limit,
            "offset": q.offset,
            "filter": filter_exprs,
            "attributesToRetrieve": ["id"],
        }

        # The official Meilisearch SDK uses requests under the hood, which is
        # synchronous. Calling it from an async route would block the event
        # loop and tank concurrent throughput, so we hop to a worker thread.
        variants = _query_variants(q.q) or [q.q]
        response: dict[str, Any] = {"hits": [], "estimatedTotalHits": 0}
        for variant in variants:
            def _call(v: str = variant) -> dict[str, Any]:
                return index.search(v, params)

            response = await anyio.to_thread.run_sync(_call)
            if response.get("hits"):
                break
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


async def suggest(q: SearchQuery) -> list[SearchSuggestion]:
    """Return lightweight provider suggestions directly from Meilisearch."""
    text = q.q.strip()
    if not text:
        return []
    index = get_meilisearch().index(PROVIDERS_INDEX)
    params = {
        "limit": q.limit,
        "offset": 0,
        "filter": _meili_filter_expression(q),
        "attributesToRetrieve": [
            "slug",
            "display_name",
            "description",
            "city_name",
            "country_code",
        ],
        "attributesToCrop": ["description"],
        "cropLength": 18,
    }

    variants = _query_variants(text) or [text]
    response: dict[str, Any] = {"hits": []}
    for variant in variants:
        def _call(v: str = variant) -> dict[str, Any]:
            return index.search(v, params)

        response = await anyio.to_thread.run_sync(_call)
        if response.get("hits"):
            break
    suggestions: list[SearchSuggestion] = []
    for hit in response.get("hits", []):
        slug = str(hit.get("slug") or "")
        display_name = str(hit.get("display_name") or "")
        if not slug or not display_name:
            continue
        suggestions.append(
            SearchSuggestion(
                slug=slug,
                display_name=display_name,
                description=hit.get("description"),
                city_name=hit.get("city_name"),
                country_code=hit.get("country_code"),
            )
        )
    return suggestions


async def maybe_rerank(
    q: SearchQuery,
    result: SearchResult,
    providers: list[Provider],
    *,
    client: MatcherClient | None = None,
) -> SearchResult:
    """Optionally re-rank `result.hits` using the matcher gRPC service.

    The matcher is strictly optional: any failure leaves `result` untouched
    and is logged at WARNING. Invariants preserved:
    - Output `hits` is a permutation of a subset of input `hits`: no new ids
      are introduced, so hydration keys stay valid upstream.
    - `total` and `engine` semantics stay consistent; on success we annotate
      `engine` with `+matcher` so the client can see the re-rank fired.
    """
    settings = get_settings()
    if not settings.matcher_enabled:
        return result
    if not result.hits or not providers:
        return result

    current_scores = {h.provider_id: h.score for h in result.hits}
    provider_by_id = {p.id: p for p in providers}
    candidates: list[MatcherCandidate] = []
    for hit in result.hits:
        provider = provider_by_id.get(hit.provider_id)
        if provider is None:
            continue
        candidates.append(
            MatcherCandidate(
                provider_id=provider.id,
                display_name=provider.display_name or "",
                description=provider.description or "",
                category_slugs=tuple(c.slug for c in provider.categories),
                country_code=provider.country.code if provider.country else "",
                city_slug=provider.city.slug if provider.city else "",
                legal_form_code=provider.legal_form.code if provider.legal_form else "",
                retrieval_score=current_scores.get(provider.id, 0.0),
            )
        )
    if not candidates:
        return result

    try:
        scores = await (client or get_matcher_client()).rank(
            query=q.q,
            category_slugs=q.category_slugs,
            country_codes=q.country_codes,
            city_slugs=q.city_slugs,
            legal_form_codes=q.legal_form_codes,
            limit=len(candidates),
            offset=0,
            candidates=candidates,
        )
    except MatcherUnavailableError as exc:
        matcher_calls_total.labels("unavailable").inc()
        log.warning("search.matcher_unavailable", err=str(exc))
        return result
    matcher_calls_total.labels("ok").inc()

    ranked_ids = [s.provider_id for s in scores]
    score_by_id = {s.provider_id: s.score for s in scores}
    hits_by_id = {h.provider_id: h for h in result.hits}
    new_hits: list[SearchHit] = []
    for pid in ranked_ids:
        if pid not in hits_by_id:
            continue
        new_hits.append(SearchHit(provider_id=pid, score=float(score_by_id.get(pid, 0.0))))
    # Append any hits the matcher dropped (defensive), preserving original order.
    for hit in result.hits:
        if hit.provider_id not in score_by_id:
            new_hits.append(hit)

    return SearchResult(
        total=result.total,
        hits=new_hits,
        engine=f"{result.engine}+matcher",
    )


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
