"""Catalog endpoints: providers + reference data."""

from __future__ import annotations

from typing import Annotated, cast

from fastapi import APIRouter, HTTPException, Query, status

from ozzb2b_api.clients.cache import get_or_set
from ozzb2b_api.clients.events import EVENT_PROVIDER_VIEWED, get_event_emitter
from ozzb2b_api.routes.deps import DbSession
from ozzb2b_api.schemas.catalog import (
    CategoryPublic,
    CategoryTreeNode,
    CityPublic,
    CountryPublic,
    LegalFormPublic,
    ProviderDetail,
    ProviderFacets,
    ProviderFacetValue,
    ProviderListResponse,
)
from ozzb2b_api.services import catalog as catalog_service
from ozzb2b_api.services.provider_mapping import to_detail, to_summary

# Reference data changes at most once per deploy; a 5-minute cache is more
# than enough freshness while removing a chunk of repetitive DB hits during
# catalog navigation.
_REFERENCE_TTL_SECONDS = 5 * 60

router = APIRouter(tags=["catalog"])


@router.get("/providers", response_model=ProviderListResponse)
async def list_providers_endpoint(
    db: DbSession,
    q: Annotated[str | None, Query(description="Free-text query")] = None,
    categories: Annotated[list[str] | None, Query(alias="category")] = None,
    countries: Annotated[list[str] | None, Query(alias="country")] = None,
    cities: Annotated[list[str] | None, Query(alias="city")] = None,
    legal_forms: Annotated[list[str] | None, Query(alias="legal_form")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 24,
    offset: Annotated[int, Query(ge=0)] = 0,
    with_facets: Annotated[bool, Query(alias="facets")] = False,
) -> ProviderListResponse:
    f = catalog_service.ProviderFilter(
        query=q,
        category_slugs=tuple(categories or ()),
        country_codes=tuple(countries or []),
        city_slugs=tuple(cities or ()),
        legal_form_codes=tuple(legal_forms or ()),
        limit=limit,
        offset=offset,
    )
    total, rows = await catalog_service.list_providers(db, f)
    items = [to_summary(p) for p in rows]
    facets: ProviderFacets | None = None
    if with_facets:
        counts = await catalog_service.facet_counts(db, f)
        facets = ProviderFacets(
            categories=[
                ProviderFacetValue(value=v, label=lbl, count=c)
                for v, lbl, c in counts["categories"]
            ],
            countries=[
                ProviderFacetValue(value=v, label=lbl, count=c)
                for v, lbl, c in counts["countries"]
            ],
            cities=[
                ProviderFacetValue(value=v, label=lbl, count=c)
                for v, lbl, c in counts["cities"]
            ],
            legal_forms=[
                ProviderFacetValue(value=v, label=lbl, count=c)
                for v, lbl, c in counts["legal_forms"]
            ],
        )
    return ProviderListResponse(
        total=total, limit=limit, offset=offset, items=items, facets=facets
    )


@router.get("/providers/{slug}", response_model=ProviderDetail)
async def get_provider_endpoint(slug: str, db: DbSession) -> ProviderDetail:
    provider = await catalog_service.get_provider_by_slug(db, slug)
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "provider not found")
    await get_event_emitter().emit(
        EVENT_PROVIDER_VIEWED,
        properties={
            "provider_id": str(provider.id),
            "slug": provider.slug,
            "display_name": provider.display_name,
            "country_code": provider.country.code if provider.country else None,
            "city_slug": provider.city.slug if provider.city else None,
            "category_slugs": [c.slug for c in provider.categories],
        },
    )
    return to_detail(provider)


@router.get("/categories", response_model=list[CategoryPublic])
async def list_categories_endpoint(db: DbSession) -> list[CategoryPublic]:
    async def _load() -> list[CategoryPublic]:
        rows = await catalog_service.list_categories(db)
        return [CategoryPublic.model_validate(c) for c in rows]

    return await get_or_set(
        "ref:categories:v1",
        ttl_seconds=_REFERENCE_TTL_SECONDS,
        loader=_load,
        encode=lambda items: [c.model_dump(mode="json") for c in items],
        decode=lambda raw: [
            CategoryPublic.model_validate(c)
            for c in cast(list[dict[str, object]], raw)
        ],
    )


@router.get("/categories/tree", response_model=list[CategoryTreeNode])
async def categories_tree_endpoint(db: DbSession) -> list[CategoryTreeNode]:
    flat = await catalog_service.list_categories(db)
    by_id: dict[int, CategoryTreeNode] = {
        c.id: CategoryTreeNode(
            id=c.id,
            parent_id=c.parent_id,
            slug=c.slug,
            name=c.name,
            description=c.description,
            position=c.position,
            children=[],
        )
        for c in flat
    }
    roots: list[CategoryTreeNode] = []
    for c in flat:
        node = by_id[c.id]
        if c.parent_id is None:
            roots.append(node)
        else:
            parent = by_id.get(c.parent_id)
            if parent is not None:
                parent.children.append(node)
    return roots


@router.get("/countries", response_model=list[CountryPublic])
async def list_countries_endpoint(db: DbSession) -> list[CountryPublic]:
    async def _load() -> list[CountryPublic]:
        rows = await catalog_service.list_countries(db)
        return [CountryPublic.model_validate(c) for c in rows]

    return await get_or_set(
        "ref:countries:v1",
        ttl_seconds=_REFERENCE_TTL_SECONDS,
        loader=_load,
        encode=lambda items: [c.model_dump(mode="json") for c in items],
        decode=lambda raw: [
            CountryPublic.model_validate(c)
            for c in cast(list[dict[str, object]], raw)
        ],
    )


@router.get("/cities", response_model=list[CityPublic])
async def list_cities_endpoint(
    db: DbSession,
    country: Annotated[str | None, Query(description="ISO country code")] = None,
) -> list[CityPublic]:
    async def _load() -> list[CityPublic]:
        rows = await catalog_service.list_cities(db, country)
        return [CityPublic.model_validate(c) for c in rows]

    return await get_or_set(
        f"ref:cities:v1:{country or '*'}",
        ttl_seconds=_REFERENCE_TTL_SECONDS,
        loader=_load,
        encode=lambda items: [c.model_dump(mode="json") for c in items],
        decode=lambda raw: [
            CityPublic.model_validate(c)
            for c in cast(list[dict[str, object]], raw)
        ],
    )


@router.get("/legal-forms", response_model=list[LegalFormPublic])
async def list_legal_forms_endpoint(
    db: DbSession,
    country: Annotated[str | None, Query(description="ISO country code")] = None,
) -> list[LegalFormPublic]:
    async def _load() -> list[LegalFormPublic]:
        rows = await catalog_service.list_legal_forms(db, country)
        return [LegalFormPublic.model_validate(lf) for lf in rows]

    return await get_or_set(
        f"ref:legal-forms:v1:{country or '*'}",
        ttl_seconds=_REFERENCE_TTL_SECONDS,
        loader=_load,
        encode=lambda items: [c.model_dump(mode="json") for c in items],
        decode=lambda raw: [
            LegalFormPublic.model_validate(c)
            for c in cast(list[dict[str, object]], raw)
        ],
    )
