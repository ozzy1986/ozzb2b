"""Catalog endpoints: providers + reference data."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from ozzb2b_api.clients.events import EVENT_PROVIDER_VIEWED, get_event_emitter
from ozzb2b_api.db.models import Provider
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
    ProviderSummary,
)
from ozzb2b_api.services import catalog as catalog_service

router = APIRouter(tags=["catalog"])


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
        last_scraped_at=provider.last_scraped_at,
    )


def _to_detail(provider: Provider) -> ProviderDetail:
    summary = _to_summary(provider)
    return ProviderDetail(
        **summary.model_dump(),
        legal_name=provider.legal_name,
        website=provider.website,
        email=provider.email,
        phone=provider.phone,
        address=provider.address,
        registration_number=provider.registration_number,
        tax_id=provider.tax_id,
        source=provider.source,
        source_url=provider.source_url,
        status=provider.status.value,
        is_claimed=bool(provider.is_claimed),
        created_at=provider.created_at,
        updated_at=provider.updated_at,
    )


def to_provider_detail(provider: Provider) -> ProviderDetail:
    """Public alias for the internal detail mapper so other routers can reuse it."""
    return _to_detail(provider)


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
    items = [_to_summary(p) for p in rows]
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
    return _to_detail(provider)


@router.get("/categories", response_model=list[CategoryPublic])
async def list_categories_endpoint(db: DbSession) -> list[CategoryPublic]:
    rows = await catalog_service.list_categories(db)
    return [CategoryPublic.model_validate(c) for c in rows]


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
    rows = await catalog_service.list_countries(db)
    return [CountryPublic.model_validate(c) for c in rows]


@router.get("/cities", response_model=list[CityPublic])
async def list_cities_endpoint(
    db: DbSession,
    country: Annotated[str | None, Query(description="ISO country code")] = None,
) -> list[CityPublic]:
    rows = await catalog_service.list_cities(db, country)
    return [CityPublic.model_validate(c) for c in rows]


@router.get("/legal-forms", response_model=list[LegalFormPublic])
async def list_legal_forms_endpoint(
    db: DbSession,
    country: Annotated[str | None, Query(description="ISO country code")] = None,
) -> list[LegalFormPublic]:
    rows = await catalog_service.list_legal_forms(db, country)
    return [LegalFormPublic.model_validate(lf) for lf in rows]
