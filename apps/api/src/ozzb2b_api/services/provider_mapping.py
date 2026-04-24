"""ORM -> public schema mappers for ``Provider``.

Single source of truth shared by the catalog, search and claims routers so the
public payload shape never drifts between endpoints.
"""

from __future__ import annotations

from ozzb2b_api.db.models import Provider
from ozzb2b_api.schemas.catalog import (
    CategoryPublic,
    CityPublic,
    CountryPublic,
    LegalFormPublic,
    ProviderDetail,
    ProviderSummary,
)


def to_summary(provider: Provider) -> ProviderSummary:
    """Map a ``Provider`` ORM row to the public list/search summary."""
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


def to_detail(provider: Provider) -> ProviderDetail:
    """Map a ``Provider`` ORM row to the public detail payload."""
    summary = to_summary(provider)
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
