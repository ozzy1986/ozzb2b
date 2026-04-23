"""Unit tests for indexer document shape (pure — no Meilisearch needed)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

from ozzb2b_api.db.models import ProviderStatus
from ozzb2b_api.services.indexer import _provider_to_doc


def _fake_provider() -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        slug="acme",
        display_name="Acme",
        legal_name="Acme LLC",
        description="desc",
        address="Moscow",
        country=SimpleNamespace(code="RU", name="Россия"),
        city=SimpleNamespace(slug="moscow", name="Москва"),
        legal_form=SimpleNamespace(code="OOO", name="ООО"),  # noqa: RUF001
        categories=[
            SimpleNamespace(slug="it", name="ИТ"),
            SimpleNamespace(slug="seo", name="SEO"),
        ],
        year_founded=2020,
        employee_count_range="10-50",
        status=ProviderStatus.PUBLISHED,
        created_at=datetime.now(tz=UTC),
    )


def test_doc_has_expected_top_level_keys() -> None:
    doc = _provider_to_doc(_fake_provider())
    for key in (
        "id",
        "slug",
        "display_name",
        "legal_name",
        "description",
        "address",
        "country_code",
        "country_name",
        "city_slug",
        "city_name",
        "legal_form_code",
        "legal_form_name",
        "category_slugs",
        "category_names",
        "year_founded",
        "employee_count_range",
        "status",
    ):
        assert key in doc, f"missing '{key}'"


def test_doc_denormalizes_categories_into_lists() -> None:
    doc = _provider_to_doc(_fake_provider())
    assert doc["category_slugs"] == ["it", "seo"]
    assert doc["category_names"] == ["ИТ", "SEO"]


def test_doc_handles_missing_optional_relations() -> None:
    p = _fake_provider()
    p.country = None
    p.city = None
    p.legal_form = None
    doc = _provider_to_doc(p)
    assert doc["country_code"] is None
    assert doc["city_slug"] is None
    assert doc["legal_form_code"] is None


def test_doc_ids_are_stringified() -> None:
    doc = _provider_to_doc(_fake_provider())
    assert isinstance(doc["id"], str)
    assert uuid.UUID(doc["id"])
