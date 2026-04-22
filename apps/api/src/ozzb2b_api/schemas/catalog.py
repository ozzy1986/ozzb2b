"""Catalog (providers / categories / geo) response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    parent_id: int | None
    slug: str
    name: str
    description: str | None
    position: int


class CategoryTreeNode(CategoryPublic):
    children: list["CategoryTreeNode"] = Field(default_factory=list)


class CountryPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    slug: str


class CityPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    country_id: int
    name: str
    slug: str
    region: str | None


class LegalFormPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    country_id: int | None
    code: str
    name: str
    slug: str


class ProviderSummary(BaseModel):
    id: uuid.UUID
    slug: str
    display_name: str
    description: str | None
    country: CountryPublic | None
    city: CityPublic | None
    legal_form: LegalFormPublic | None
    year_founded: int | None
    employee_count_range: str | None
    logo_url: str | None
    categories: list[CategoryPublic]
    last_scraped_at: datetime | None = None


class ProviderDetail(ProviderSummary):
    legal_name: str
    website: str | None
    email: str | None
    phone: str | None
    address: str | None
    registration_number: str | None
    tax_id: str | None
    source: str | None
    source_url: str | None
    status: str
    last_scraped_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ProviderFacetValue(BaseModel):
    value: str
    label: str
    count: int


class ProviderFacets(BaseModel):
    categories: list[ProviderFacetValue] = Field(default_factory=list)
    countries: list[ProviderFacetValue] = Field(default_factory=list)
    cities: list[ProviderFacetValue] = Field(default_factory=list)
    legal_forms: list[ProviderFacetValue] = Field(default_factory=list)


class ProviderListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[ProviderSummary]
    facets: ProviderFacets | None = None


CategoryTreeNode.model_rebuild()
