"""Direct tests for the shared provider -> public schema mapper.

The mapper is the single source of truth used by the catalog, search and
claims routes. We test it in isolation here so a regression that
silently drops fields (e.g. last_scraped_at) shows up immediately.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

from ozzb2b_api.services.provider_mapping import to_detail, to_summary


def _provider_stub() -> SimpleNamespace:
    """Minimal duck-typed Provider stand-in matching what the mapper reads."""
    return SimpleNamespace(
        id=uuid.uuid4(),
        slug="acme",
        display_name="ACME",
        description="Best provider",
        country=SimpleNamespace(id=1, code="RU", name="Россия", slug="ru"),
        city=SimpleNamespace(
            id=10,
            country_id=1,
            name="Москва",
            slug="moscow",
            region=None,
        ),
        legal_form=SimpleNamespace(
            id=2,
            country_id=1,
            code="OOO",
            name="ООО",
            slug="ooo",
        ),
        year_founded=2010,
        employee_count_range="11-50",
        logo_url="https://cdn.example/acme.png",
        categories=[
            SimpleNamespace(
                id=99,
                parent_id=None,
                slug="it",
                name="ИТ",
                description=None,
                position=1,
            ),
        ],
        last_scraped_at=datetime(2026, 4, 1, 12, 0, tzinfo=UTC),
        legal_name="ООО ACME",
        website="https://acme.example",
        email="hi@acme.example",
        phone="+7 495 000-00-00",
        address="Москва, ул. Примерная, 1",
        registration_number="1234567890",
        tax_id="9876543210",
        source="manual",
        source_url=None,
        status=SimpleNamespace(value="published"),
        is_claimed=False,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        updated_at=datetime(2026, 4, 1, tzinfo=UTC),
    )


def test_to_summary_preserves_last_scraped_at() -> None:
    summary = to_summary(_provider_stub())  # type: ignore[arg-type]
    assert summary.last_scraped_at is not None
    assert summary.display_name == "ACME"
    assert summary.country is not None and summary.country.code == "RU"
    assert summary.legal_form is not None and summary.legal_form.code == "OOO"
    assert [c.slug for c in summary.categories] == ["it"]


def test_to_detail_extends_summary_with_contact_fields() -> None:
    detail = to_detail(_provider_stub())  # type: ignore[arg-type]
    # Summary fields must be carried through unchanged.
    assert detail.display_name == "ACME"
    assert detail.last_scraped_at is not None
    # Detail-only fields.
    assert detail.legal_name == "ООО ACME"
    assert detail.website == "https://acme.example"
    assert detail.email == "hi@acme.example"
    assert detail.phone == "+7 495 000-00-00"
    assert detail.status == "published"
    assert detail.is_claimed is False


def test_to_summary_handles_missing_relations() -> None:
    bare = _provider_stub()
    bare.country = None
    bare.city = None
    bare.legal_form = None
    bare.categories = []
    bare.last_scraped_at = None

    summary = to_summary(bare)  # type: ignore[arg-type]
    assert summary.country is None
    assert summary.city is None
    assert summary.legal_form is None
    assert summary.categories == []
    assert summary.last_scraped_at is None
