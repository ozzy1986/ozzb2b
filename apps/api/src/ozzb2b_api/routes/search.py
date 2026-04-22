"""Search endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import BaseModel

from ozzb2b_api.db.models import Provider
from ozzb2b_api.routes.deps import DbSession
from ozzb2b_api.schemas.catalog import (
    CategoryPublic,
    CityPublic,
    CountryPublic,
    LegalFormPublic,
    ProviderSummary,
)
from ozzb2b_api.services import search as search_service

router = APIRouter(tags=["search"])


class SearchResponse(BaseModel):
    total: int
    limit: int
    offset: int
    engine: str
    items: list[ProviderSummary]


def _to_summary(provider: Provider) -> ProviderSummary:
    return ProviderSummary(
        id=provider.id,
        slug=provider.slug,
        display_name=provider.display_name,
        description=provider.description,
        country=CountryPublic.model_validate(provider.country) if provider.country else None,
        city=CityPublic.model_validate(provider.city) if provider.city else None,
        legal_form=LegalFormPublic.model_validate(provider.legal_form)
        if provider.legal_form
        else None,
        year_founded=provider.year_founded,
        employee_count_range=provider.employee_count_range,
        logo_url=provider.logo_url,
        categories=[CategoryPublic.model_validate(c) for c in provider.categories],
    )


@router.get("/search", response_model=SearchResponse)
async def search_endpoint(
    db: DbSession,
    q: Annotated[str, Query(min_length=1, max_length=200)],
    categories: Annotated[list[str] | None, Query(alias="category")] = None,
    countries: Annotated[list[str] | None, Query(alias="country")] = None,
    cities: Annotated[list[str] | None, Query(alias="city")] = None,
    legal_forms: Annotated[list[str] | None, Query(alias="legal_form")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 24,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> SearchResponse:
    query = search_service.SearchQuery(
        q=q,
        category_slugs=tuple(categories or ()),
        country_codes=tuple(countries or ()),
        city_slugs=tuple(cities or ()),
        legal_form_codes=tuple(legal_forms or ()),
        limit=limit,
        offset=offset,
    )
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
    return SearchResponse(
        total=result.total,
        limit=limit,
        offset=offset,
        engine=result.engine,
        items=[_to_summary(p) for p in ordered_providers],
    )
