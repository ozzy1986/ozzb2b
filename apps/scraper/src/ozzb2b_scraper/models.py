"""Shared dataclasses for scraped provider items.

Only legally usable public info; we never store PII we are not allowed to store.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class ScrapedProvider:
    source: str
    source_id: str
    source_url: str | None
    display_name: str
    legal_name: str | None = None
    description: str | None = None
    country_code: str | None = None
    city_name: str | None = None
    legal_form_code: str | None = None
    website: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    registration_number: str | None = None
    tax_id: str | None = None
    year_founded: int | None = None
    employee_count_range: str | None = None
    category_slugs: tuple[str, ...] = ()
    meta: dict[str, object] = field(default_factory=dict)
    fetched_at: datetime | None = None
