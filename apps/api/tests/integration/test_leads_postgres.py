"""Lead → outreach drafts on real Postgres (matching query, unsubscribe)."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ozzb2b_api.config import Settings
from ozzb2b_api.db.models import (
    Category,
    City,
    Country,
    EmailSuppression,
    OutreachMessage,
    Provider,
    ProviderStatus,
)
from ozzb2b_api.services import leads as leads_service

pytestmark = pytest.mark.integration


async def _seed(db: AsyncSession) -> tuple[Category, City]:
    country = Country(code="RU", name="Россия", slug="ru")
    db.add(country)
    await db.flush()
    kazan = City(country_id=country.id, name="Kazan", slug="kazan")
    moscow = City(country_id=country.id, name="Moscow", slug="moscow")
    root = Category(slug="accounting", name="Accounting", position=10)
    db.add_all([kazan, moscow, root])
    await db.flush()
    niche = Category(slug="marketplace-accounting", name="Sellers", parent_id=root.id)
    db.add(niche)
    await db.flush()

    def provider(slug: str, email: str | None, city: City, cats: list[Category]) -> Provider:
        return Provider(
            slug=slug,
            legal_name=slug,
            display_name=slug,
            country_id=country.id,
            city_id=city.id,
            email=email,
            website=f"https://{slug}.ru/",
            status=ProviderStatus.PUBLISHED,
            meta={},
            categories=cats,
        )

    db.add_all(
        [
            # In both the niche and its parent: must still get exactly one draft.
            provider("b-moscow", "info@b-moscow.ru", moscow, [root, niche]),
            provider("a-kazan", "info@a-kazan.ru", kazan, [niche]),
            provider("no-email", None, kazan, [niche]),
            provider("gone", "Hello@Gone.ru", kazan, [niche]),
        ]
    )
    db.add(EmailSuppression(email="hello@gone.ru", reason="unsubscribe_link"))
    await db.flush()
    return root, kazan


async def test_lead_drafts_match_city_first_and_skip_unreachable(
    db_session: AsyncSession, integration_settings: Settings
) -> None:
    _, kazan = await _seed(db_session)
    lead, drafts = await leads_service.create_lead(
        db_session,
        leads_service.LeadInput(
            category_slug="accounting",
            city_id=kazan.id,
            description="Нужен бухгалтер для селлера на Ozon",
            budget=None,
            contact_name="Иван",
            contact_email="Ivan@Client.ru",
            contact_phone=None,
            company_name=None,
            source_ip="203.0.113.5",
            user_agent="pytest",
        ),
        integration_settings,
    )
    assert drafts == 2
    assert lead.contact_email == "ivan@client.ru"

    rows = (
        await db_session.execute(
            select(OutreachMessage).where(OutreachMessage.lead_id == lead.id)
        )
    ).scalars().all()
    assert sorted(m.to_email for m in rows) == ["info@a-kazan.ru", "info@b-moscow.ru"]

    matched = await leads_service.match_providers(db_session, lead, limit=5)
    assert [p.slug for p in matched] == ["a-kazan", "b-moscow"]


async def test_unsubscribe_is_idempotent(
    db_session: AsyncSession, integration_settings: Settings
) -> None:
    token = leads_service.unsubscribe_token("info@buh.ru", integration_settings)
    await leads_service.unsubscribe(db_session, "Info@Buh.ru", token, integration_settings)
    await leads_service.unsubscribe(db_session, "info@buh.ru", token, integration_settings)
    rows = (
        await db_session.execute(
            select(EmailSuppression).where(EmailSuppression.email == "info@buh.ru")
        )
    ).scalars().all()
    assert len(rows) == 1
