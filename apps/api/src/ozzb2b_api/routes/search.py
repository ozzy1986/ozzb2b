"""Search endpoint."""

from __future__ import annotations

import time
from typing import Annotated

from fastapi import APIRouter, Query, Request, Response
from pydantic import BaseModel

from ozzb2b_api.clients.events import EVENT_SEARCH_PERFORMED, get_event_emitter
from ozzb2b_api.config import get_settings
from ozzb2b_api.routes.deps import DbSession
from ozzb2b_api.schemas.catalog import ProviderSummary
from ozzb2b_api.security.rate_limit import enforce_rate_limit
from ozzb2b_api.services import search as search_service
from ozzb2b_api.services.provider_mapping import to_summary

router = APIRouter(tags=["search"])


class SearchResponse(BaseModel):
    total: int
    limit: int
    offset: int
    engine: str
    items: list[ProviderSummary]


class SearchSuggestionPublic(BaseModel):
    slug: str
    display_name: str
    description: str | None = None
    city_name: str | None = None
    country_code: str | None = None


class SearchSuggestResponse(BaseModel):
    items: list[SearchSuggestionPublic]


@router.get("/search", response_model=SearchResponse)
async def search_endpoint(
    db: DbSession,
    request: Request,
    response: Response,
    q: Annotated[str, Query(min_length=1, max_length=200)],
    categories: Annotated[list[str] | None, Query(alias="category")] = None,
    countries: Annotated[list[str] | None, Query(alias="country")] = None,
    cities: Annotated[list[str] | None, Query(alias="city")] = None,
    legal_forms: Annotated[list[str] | None, Query(alias="legal_form")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 24,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> SearchResponse:
    # Public endpoint, so we throttle by IP only — anonymous users have no
    # identity beyond their socket peer (or trusted XFF hop, see config).
    cfg = get_settings()
    await enforce_rate_limit(
        request=request,
        response=response,
        endpoint="search",
        limit=cfg.rate_limit_search_max,
    )
    query = search_service.SearchQuery(
        q=q,
        category_slugs=tuple(categories or ()),
        country_codes=tuple(countries or ()),
        city_slugs=tuple(cities or ()),
        legal_form_codes=tuple(legal_forms or ()),
        limit=limit,
        offset=offset,
    )
    started = time.perf_counter()
    result = await search_service.search(db, query)
    providers = await search_service.hydrate_providers(
        db, [h.provider_id for h in result.hits]
    )
    result = await search_service.maybe_rerank(query, result, providers)
    provider_by_id = {p.id: p for p in providers}
    ordered_providers = [
        provider_by_id[h.provider_id]
        for h in result.hits
        if h.provider_id in provider_by_id
    ]
    latency_ms = int((time.perf_counter() - started) * 1000)

    await get_event_emitter().emit(
        EVENT_SEARCH_PERFORMED,
        properties={
            "query": q,
            "engine": result.engine,
            "result_count": result.total,
            "latency_ms": latency_ms,
            "category_slugs": list(query.category_slugs),
            "country_codes": list(query.country_codes),
            "city_slugs": list(query.city_slugs),
            "legal_form_codes": list(query.legal_form_codes),
            "limit": limit,
            "offset": offset,
        },
    )

    return SearchResponse(
        total=result.total,
        limit=limit,
        offset=offset,
        engine=result.engine,
        items=[to_summary(p) for p in ordered_providers],
    )


@router.get("/search/suggest", response_model=SearchSuggestResponse)
async def search_suggest_endpoint(
    request: Request,
    response: Response,
    q: Annotated[str, Query(min_length=2, max_length=120)],
    categories: Annotated[list[str] | None, Query(alias="category")] = None,
    countries: Annotated[list[str] | None, Query(alias="country")] = None,
    cities: Annotated[list[str] | None, Query(alias="city")] = None,
    legal_forms: Annotated[list[str] | None, Query(alias="legal_form")] = None,
    limit: Annotated[int, Query(ge=1, le=10)] = 6,
) -> SearchSuggestResponse:
    cfg = get_settings()
    await enforce_rate_limit(
        request=request,
        response=response,
        endpoint="search-suggest",
        limit=cfg.rate_limit_search_max,
    )
    query = search_service.SearchQuery(
        q=q,
        category_slugs=tuple(categories or ()),
        country_codes=tuple(countries or ()),
        city_slugs=tuple(cities or ()),
        legal_form_codes=tuple(legal_forms or ()),
        limit=limit,
        offset=0,
    )
    suggestions = await search_service.suggest(query)
    return SearchSuggestResponse(
        items=[SearchSuggestionPublic(**s.__dict__) for s in suggestions]
    )
