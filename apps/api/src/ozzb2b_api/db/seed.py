"""Idempotent seed data for categories, countries, legal forms, and demo providers.

Run via:

    python -m ozzb2b_api.db.seed
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass

import structlog
from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ozzb2b_api.db.models import (
    Category,
    City,
    Country,
    LegalForm,
    Provider,
    ProviderStatus,
)
from ozzb2b_api.db.session import get_sessionmaker

log = structlog.get_logger("ozzb2b_api.db.seed")


@dataclass(frozen=True)
class CategorySeed:
    slug: str
    name: str
    description: str
    position: int
    children: tuple[tuple[str, str], ...] = ()


CATEGORIES: tuple[CategorySeed, ...] = (
    CategorySeed(
        slug="it",
        name="IT",
        description="Software engineering, DevOps, QA, data, AI/ML, cybersecurity, design.",
        position=10,
        children=(
            ("software-development", "Software development"),
            ("devops-cloud", "DevOps & cloud"),
            ("quality-assurance", "Quality assurance"),
            ("data-analytics", "Data & analytics"),
            ("ai-ml", "AI / ML"),
            ("cybersecurity", "Cybersecurity"),
            ("ui-ux-design", "UI / UX design"),
        ),
    ),
    CategorySeed(
        slug="accounting",
        name="Accounting",
        description="Bookkeeping, tax, payroll, audit, and financial reporting services.",
        position=20,
        children=(
            ("bookkeeping", "Bookkeeping"),
            ("tax-advisory", "Tax advisory"),
            ("payroll", "Payroll"),
            ("audit-assurance", "Audit & assurance"),
            ("financial-reporting", "Financial reporting"),
        ),
    ),
    CategorySeed(
        slug="legal",
        name="Legal",
        description="Corporate law, contracts, IP, compliance, dispute resolution.",
        position=30,
        children=(
            ("corporate-law", "Corporate law"),
            ("contracts", "Contracts & commercial"),
            ("intellectual-property", "Intellectual property"),
            ("compliance-regulatory", "Compliance & regulatory"),
            ("dispute-resolution", "Dispute resolution"),
            ("labor-law", "Labor & employment"),
        ),
    ),
    CategorySeed(
        slug="marketing",
        name="Marketing",
        description="Digital marketing, SEO, content, PR, branding, performance ads.",
        position=40,
        children=(
            ("seo", "SEO"),
            ("content", "Content marketing"),
            ("paid-media", "Paid media"),
            ("branding", "Branding"),
            ("pr", "PR & communications"),
        ),
    ),
    CategorySeed(
        slug="hr",
        name="HR",
        description="Recruiting, staffing, EOR, training, employer branding.",
        position=50,
        children=(
            ("recruiting", "Recruiting"),
            ("staffing", "Staffing"),
            ("eor-peo", "EOR / PEO"),
            ("training", "Training & development"),
        ),
    ),
)


COUNTRIES: tuple[tuple[str, str], ...] = (
    ("PL", "Poland"),
    ("DE", "Germany"),
    ("UA", "Ukraine"),
    ("US", "United States"),
    ("GB", "United Kingdom"),
    ("NL", "Netherlands"),
    ("EE", "Estonia"),
    ("CZ", "Czechia"),
    ("RO", "Romania"),
    ("LT", "Lithuania"),
)


@dataclass(frozen=True)
class LegalFormSeed:
    country_code: str | None
    code: str
    name: str


LEGAL_FORMS: tuple[LegalFormSeed, ...] = (
    # Universal
    LegalFormSeed(None, "UNK", "Unknown / other"),
    LegalFormSeed(None, "SELF_EMPLOYED", "Self-employed"),
    # Poland
    LegalFormSeed("PL", "SP_Z_O_O", "sp. z o.o."),
    LegalFormSeed("PL", "SA", "S.A."),
    LegalFormSeed("PL", "JDG", "JDG (sole proprietorship)"),
    # Germany
    LegalFormSeed("DE", "GMBH", "GmbH"),
    LegalFormSeed("DE", "UG", "UG (haftungsbeschränkt)"),
    LegalFormSeed("DE", "AG", "AG"),
    # Ukraine
    LegalFormSeed("UA", "TOV", "ТОВ (LLC)"),
    LegalFormSeed("UA", "FOP", "ФОП (sole proprietor)"),
    # US
    LegalFormSeed("US", "LLC", "LLC"),
    LegalFormSeed("US", "INC", "Inc."),
    LegalFormSeed("US", "CORP", "Corp."),
    # UK
    LegalFormSeed("GB", "LTD", "Ltd"),
    LegalFormSeed("GB", "PLC", "PLC"),
    LegalFormSeed("GB", "LLP", "LLP"),
)


@dataclass(frozen=True)
class CitySeed:
    country_code: str
    name: str


CITIES: tuple[CitySeed, ...] = (
    CitySeed("PL", "Warsaw"),
    CitySeed("PL", "Krakow"),
    CitySeed("PL", "Wroclaw"),
    CitySeed("PL", "Gdansk"),
    CitySeed("DE", "Berlin"),
    CitySeed("DE", "Munich"),
    CitySeed("DE", "Hamburg"),
    CitySeed("UA", "Kyiv"),
    CitySeed("UA", "Lviv"),
    CitySeed("UA", "Kharkiv"),
    CitySeed("US", "New York"),
    CitySeed("US", "San Francisco"),
    CitySeed("US", "Austin"),
    CitySeed("GB", "London"),
    CitySeed("GB", "Manchester"),
    CitySeed("NL", "Amsterdam"),
    CitySeed("EE", "Tallinn"),
    CitySeed("CZ", "Prague"),
    CitySeed("RO", "Bucharest"),
    CitySeed("LT", "Vilnius"),
)


@dataclass(frozen=True)
class ProviderSeed:
    slug: str
    legal_name: str
    display_name: str
    description: str
    country_code: str
    city_name: str
    legal_form_code: str
    website: str
    email: str
    phone: str
    address: str
    year_founded: int
    employee_count_range: str
    category_slugs: tuple[str, ...]


PROVIDERS: tuple[ProviderSeed, ...] = (
    ProviderSeed(
        slug="northwind-software-labs",
        legal_name="Northwind Software Labs sp. z o.o.",
        display_name="Northwind Software Labs",
        description=(
            "Custom software development studio specializing in Python backends, "
            "TypeScript/React frontends, and scalable AWS/GCP infrastructure. "
            "We ship MVPs in 8 weeks and operate long-running product teams for SaaS scale-ups."
        ),
        country_code="PL",
        city_name="Warsaw",
        legal_form_code="SP_Z_O_O",
        website="https://example.com/northwind-software-labs",
        email="hello@northwindlabs.example",
        phone="+48 22 000 0001",
        address="Aleje Jerozolimskie 100, Warsaw",
        year_founded=2017,
        employee_count_range="50-200",
        category_slugs=("it", "software-development", "devops-cloud"),
    ),
    ProviderSeed(
        slug="lindgren-data",
        legal_name="Lindgren Data GmbH",
        display_name="Lindgren Data",
        description=(
            "Data engineering and analytics consultancy. We design modern data platforms "
            "(dbt, Snowflake, BigQuery) and build internal BI for mid-market companies."
        ),
        country_code="DE",
        city_name="Berlin",
        legal_form_code="GMBH",
        website="https://example.com/lindgren-data",
        email="contact@lindgrendata.example",
        phone="+49 30 000 0002",
        address="Friedrichstr. 200, Berlin",
        year_founded=2019,
        employee_count_range="11-50",
        category_slugs=("it", "data-analytics", "ai-ml"),
    ),
    ProviderSeed(
        slug="kalynivka-legal-tov",
        legal_name="ТОВ Kalynivka Legal",
        display_name="Kalynivka Legal",
        description=(
            "Ukrainian corporate lawyers helping foreign companies enter the EU market. "
            "Contracts, IP, compliance, GDPR. EN/UA/PL."
        ),
        country_code="UA",
        city_name="Lviv",
        legal_form_code="TOV",
        website="https://example.com/kalynivka-legal",
        email="office@kalynivka-legal.example",
        phone="+380 32 000 0003",
        address="vul. Svobody 15, Lviv",
        year_founded=2014,
        employee_count_range="11-50",
        category_slugs=("legal", "contracts", "corporate-law", "intellectual-property"),
    ),
    ProviderSeed(
        slug="aurora-bookkeeping",
        legal_name="Aurora Bookkeeping Ltd",
        display_name="Aurora Bookkeeping",
        description=(
            "UK-registered bookkeeping and payroll service for SMEs across Europe. "
            "Xero and QuickBooks specialists."
        ),
        country_code="GB",
        city_name="London",
        legal_form_code="LTD",
        website="https://example.com/aurora-bookkeeping",
        email="hello@aurorabooks.example",
        phone="+44 20 0000 0004",
        address="1 Poultry, London",
        year_founded=2015,
        employee_count_range="11-50",
        category_slugs=("accounting", "bookkeeping", "payroll"),
    ),
    ProviderSeed(
        slug="paloma-growth",
        legal_name="Paloma Growth LLC",
        display_name="Paloma Growth",
        description=(
            "Performance marketing studio for B2B SaaS. Paid search, paid social, "
            "LinkedIn ABM, analytics, and lifecycle automation."
        ),
        country_code="US",
        city_name="Austin",
        legal_form_code="LLC",
        website="https://example.com/paloma-growth",
        email="team@palomagrowth.example",
        phone="+1 512 000 0005",
        address="Congress Ave 500, Austin",
        year_founded=2020,
        employee_count_range="11-50",
        category_slugs=("marketing", "paid-media", "seo"),
    ),
    ProviderSeed(
        slug="tallinn-staffing-ou",
        legal_name="Tallinn Staffing OÜ",
        display_name="Tallinn Staffing",
        description=(
            "Recruiting and EOR services for Baltic and Nordic tech companies. "
            "We hire and manage distributed engineers end to end."
        ),
        country_code="EE",
        city_name="Tallinn",
        legal_form_code="UNK",
        website="https://example.com/tallinn-staffing",
        email="recruit@tallinnstaffing.example",
        phone="+372 600 0006",
        address="Pirita tee 20, Tallinn",
        year_founded=2018,
        employee_count_range="11-50",
        category_slugs=("hr", "recruiting", "eor-peo"),
    ),
)


async def _upsert_categories(session: AsyncSession) -> dict[str, Category]:
    by_slug: dict[str, Category] = {}
    for seed in CATEGORIES:
        parent = (await session.execute(select(Category).where(Category.slug == seed.slug))).scalar_one_or_none()
        if parent is None:
            parent = Category(
                slug=seed.slug, name=seed.name, description=seed.description, position=seed.position
            )
            session.add(parent)
            await session.flush()
        by_slug[seed.slug] = parent
        for idx, (child_slug, child_name) in enumerate(seed.children):
            child = (
                await session.execute(select(Category).where(Category.slug == child_slug))
            ).scalar_one_or_none()
            if child is None:
                child = Category(
                    slug=child_slug,
                    name=child_name,
                    parent_id=parent.id,
                    position=(idx + 1) * 10,
                )
                session.add(child)
                await session.flush()
            else:
                child.parent_id = parent.id
            by_slug[child_slug] = child
    return by_slug


async def _upsert_countries(session: AsyncSession) -> dict[str, Country]:
    by_code: dict[str, Country] = {}
    for code, name in COUNTRIES:
        country = (await session.execute(select(Country).where(Country.code == code))).scalar_one_or_none()
        if country is None:
            country = Country(code=code, name=name, slug=slugify(name))
            session.add(country)
            await session.flush()
        by_code[code] = country
    return by_code


async def _upsert_cities(
    session: AsyncSession, countries: dict[str, Country]
) -> dict[tuple[str, str], City]:
    index: dict[tuple[str, str], City] = {}
    for seed in CITIES:
        country = countries[seed.country_code]
        slug = slugify(seed.name)
        city = (
            await session.execute(
                select(City).where(City.country_id == country.id, City.slug == slug)
            )
        ).scalar_one_or_none()
        if city is None:
            city = City(country_id=country.id, name=seed.name, slug=slug)
            session.add(city)
            await session.flush()
        index[(seed.country_code, seed.name)] = city
    return index


async def _upsert_legal_forms(
    session: AsyncSession, countries: dict[str, Country]
) -> dict[tuple[str | None, str], LegalForm]:
    index: dict[tuple[str | None, str], LegalForm] = {}
    for seed in LEGAL_FORMS:
        country_id = countries[seed.country_code].id if seed.country_code else None
        lf = (
            await session.execute(
                select(LegalForm).where(
                    LegalForm.country_id.is_(country_id)
                    if country_id is None
                    else LegalForm.country_id == country_id,
                    LegalForm.code == seed.code,
                )
            )
        ).scalar_one_or_none()
        if lf is None:
            lf = LegalForm(
                country_id=country_id,
                code=seed.code,
                name=seed.name,
                slug=slugify(seed.code).replace("-", "_"),
            )
            session.add(lf)
            await session.flush()
        index[(seed.country_code, seed.code)] = lf
    return index


async def _upsert_providers(
    session: AsyncSession,
    *,
    categories: dict[str, Category],
    countries: dict[str, Country],
    cities: dict[tuple[str, str], City],
    legal_forms: dict[tuple[str | None, str], LegalForm],
) -> int:
    """Upsert demo providers and their category links idempotently."""
    from sqlalchemy import delete, insert

    from ozzb2b_api.db.models import ProviderCategory

    inserted = 0
    for seed in PROVIDERS:
        provider = (
            await session.execute(select(Provider).where(Provider.slug == seed.slug))
        ).scalar_one_or_none()
        country = countries[seed.country_code]
        city = cities[(seed.country_code, seed.city_name)]
        legal_form = legal_forms.get((seed.country_code, seed.legal_form_code)) or legal_forms.get(
            (None, seed.legal_form_code)
        )
        if provider is None:
            provider = Provider(
                id=uuid.uuid4(),
                slug=seed.slug,
                legal_name=seed.legal_name,
                display_name=seed.display_name,
                description=seed.description,
                country_id=country.id,
                city_id=city.id,
                legal_form_id=legal_form.id if legal_form else None,
                website=seed.website,
                email=seed.email,
                phone=seed.phone,
                address=seed.address,
                year_founded=seed.year_founded,
                employee_count_range=seed.employee_count_range,
                source="seed",
                source_id=seed.slug,
                status=ProviderStatus.PUBLISHED,
            )
            session.add(provider)
            await session.flush()
            inserted += 1
        # Sync categories explicitly via the link table to avoid async lazy-loading.
        desired_ids = [categories[s].id for s in seed.category_slugs if s in categories]
        await session.execute(
            delete(ProviderCategory).where(ProviderCategory.provider_id == provider.id)
        )
        if desired_ids:
            await session.execute(
                insert(ProviderCategory),
                [{"provider_id": provider.id, "category_id": cid} for cid in desired_ids],
            )
        await session.flush()
    return inserted


async def seed(session: AsyncSession) -> dict[str, int]:
    """Seed reference data and demo providers. Idempotent."""
    categories = await _upsert_categories(session)
    countries = await _upsert_countries(session)
    cities = await _upsert_cities(session, countries)
    legal_forms = await _upsert_legal_forms(session, countries)
    inserted_providers = await _upsert_providers(
        session,
        categories=categories,
        countries=countries,
        cities=cities,
        legal_forms=legal_forms,
    )
    await session.commit()
    return {
        "categories": len(categories),
        "countries": len(countries),
        "cities": len(cities),
        "legal_forms": len(legal_forms),
        "providers_inserted": inserted_providers,
    }


async def _main() -> None:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        stats = await seed(session)
    log.info("seed.done", **stats)


if __name__ == "__main__":
    asyncio.run(_main())
