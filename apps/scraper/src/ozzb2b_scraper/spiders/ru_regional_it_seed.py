"""Curated regional Russian IT services providers.

This source complements `ru-outsourcing-seed` by covering strong regional
players outside Moscow/SPB and widening category/city coverage for the catalog.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime

import structlog

from ozzb2b_scraper.extractors import PublicPageFacts, extract_public_facts
from ozzb2b_scraper.http import looks_like_challenge
from ozzb2b_scraper.models import ScrapedProvider
from ozzb2b_scraper.spiders.base import Spider, SpiderContext

log = structlog.get_logger("ozzb2b_scraper.spiders.ru_regional_it_seed")


@dataclass(frozen=True)
class RuRegionalSeedEntry:
    source_id: str
    display_name: str
    legal_name: str
    website: str
    city_name: str
    legal_form_code: str
    description: str
    category_slugs: tuple[str, ...]
    year_founded: int | None = None
    employee_count_range: str | None = None


SEED_ENTRIES: tuple[RuRegionalSeedEntry, ...] = (
    RuRegionalSeedEntry(
        source_id="effective-technologies-kazan",
        display_name="Effective Technologies",
        legal_name="ООО «Эффективные Технологии»",
        website="https://effective.tech/",
        city_name="Kazan",
        legal_form_code="OOO",
        description=(
            "Product software engineering in Kazan: web/mobile platforms, QA, "
            "cloud-native delivery and long-term dedicated teams."
        ),
        category_slugs=("it", "software-development", "quality-assurance", "devops-cloud"),
        year_founded=2014,
        employee_count_range="51-200",
    ),
    RuRegionalSeedEntry(
        source_id="axbit-novosibirsk",
        display_name="Axbit Group",
        legal_name="ООО «Аксбит»",
        website="https://axbit.ru/",
        city_name="Novosibirsk",
        legal_form_code="OOO",
        description=(
            "Custom software vendor from Novosibirsk: enterprise web systems, "
            "mobile apps, integrations and support."
        ),
        category_slugs=("it", "software-development", "ui-ux-design"),
        year_founded=2010,
        employee_count_range="51-200",
    ),
    RuRegionalSeedEntry(
        source_id="krista-samara",
        display_name="NPO Krista",
        legal_name="ООО «НПО Криста»",
        website="https://www.krista.ru/",
        city_name="Samara",
        legal_form_code="OOO",
        description=(
            "Regional IT integrator and software developer: enterprise platforms, "
            "public-sector systems and managed support."
        ),
        category_slugs=("it", "software-development", "data-analytics"),
        year_founded=1992,
        employee_count_range="500-1000",
    ),
    RuRegionalSeedEntry(
        source_id="itrium-perm",
        display_name="Itrium",
        legal_name="ООО «Итриум СПб»",
        website="https://itrium.ru/",
        city_name="Perm",
        legal_form_code="OOO",
        description=(
            "Security software and integration solutions for distributed sites, "
            "video analytics and enterprise monitoring."
        ),
        category_slugs=("it", "cybersecurity", "data-analytics"),
        year_founded=2007,
        employee_count_range="51-200",
    ),
    RuRegionalSeedEntry(
        source_id="itconstruct-yekaterinburg",
        display_name="ITConstruct",
        legal_name="ООО «АйТи Констракт»",
        website="https://itconstruct.ru/",
        city_name="Yekaterinburg",
        legal_form_code="OOO",
        description=(
            "Digital product engineering company in Yekaterinburg: enterprise "
            "portals, e-commerce and process automation."
        ),
        category_slugs=("it", "software-development", "ui-ux-design"),
        year_founded=2012,
        employee_count_range="51-200",
    ),
    RuRegionalSeedEntry(
        source_id="deiteriy-omsk",
        display_name="Deiteriy Lab",
        legal_name="ООО «Дейтерий»",
        website="https://deiteriylab.ru/",
        city_name="Omsk",
        legal_form_code="OOO",
        description=(
            "Design and product engineering studio from Omsk: UX, mobile/web "
            "development and product analytics."
        ),
        category_slugs=("it", "ui-ux-design", "software-development", "data-analytics"),
        year_founded=2013,
        employee_count_range="11-50",
    ),
    RuRegionalSeedEntry(
        source_id="uspek-voronezh",
        display_name="Uspek",
        legal_name="ООО «Успех»",
        website="https://uspek.com/",
        city_name="Voronezh",
        legal_form_code="OOO",
        description=(
            "Regional software and web-product outsourcing company: backend systems, "
            "frontend apps and QA support."
        ),
        category_slugs=("it", "software-development", "quality-assurance"),
        year_founded=2008,
        employee_count_range="51-200",
    ),
    RuRegionalSeedEntry(
        source_id="south-it-krasnodar",
        display_name="South IT Park",
        legal_name="ООО «Юг АйТи Парк»",
        website="https://southitpark.ru/",
        city_name="Krasnodar",
        legal_form_code="OOO",
        description=(
            "IT services ecosystem in Krasnodar: product teams, digital transformation "
            "projects and startup acceleration support."
        ),
        category_slugs=("it", "software-development", "devops-cloud"),
        year_founded=2019,
        employee_count_range="11-50",
    ),
)


def _to_scraped(entry: RuRegionalSeedEntry, facts: PublicPageFacts, now: datetime) -> ScrapedProvider:
    return ScrapedProvider(
        source="ru-regional-it-seed",
        source_id=entry.source_id,
        source_url=entry.website,
        display_name=entry.display_name,
        legal_name=entry.legal_name,
        description=facts.description or entry.description,
        country_code="RU",
        city_name=entry.city_name,
        legal_form_code=entry.legal_form_code,
        website=entry.website,
        email=facts.email,
        phone=facts.phone,
        year_founded=entry.year_founded,
        employee_count_range=entry.employee_count_range,
        category_slugs=entry.category_slugs,
        fetched_at=now,
    )


class RuRegionalItSeedSpider(Spider):
    source = "ru-regional-it-seed"

    async def crawl(self, ctx: SpiderContext) -> AsyncIterator[ScrapedProvider]:
        now = datetime.now(tz=UTC)
        yielded = 0
        for entry in SEED_ENTRIES:
            if ctx.limit is not None and yielded >= ctx.limit:
                break
            facts = await _safe_fetch_facts(ctx, entry)
            yield _to_scraped(entry, facts, now)
            yielded += 1


async def _safe_fetch_facts(ctx: SpiderContext, entry: RuRegionalSeedEntry) -> PublicPageFacts:
    try:
        resp = await ctx.fetcher.get(entry.website)
        html = resp.text
    except Exception as exc:  # noqa: BLE001
        log.warning(
            "ru_regional_it_seed.fetch_or_decode.failed",
            source_id=entry.source_id,
            website=entry.website,
            error=str(exc),
        )
        return PublicPageFacts()

    if looks_like_challenge(html):
        log.info("ru_regional_it_seed.challenge.skipped", source_id=entry.source_id)
        return PublicPageFacts()

    try:
        return extract_public_facts(html)
    except Exception as exc:  # noqa: BLE001
        log.warning("ru_regional_it_seed.extract.failed", source_id=entry.source_id, error=str(exc))
        return PublicPageFacts()


__all__ = ["RuRegionalItSeedSpider", "RuRegionalSeedEntry", "SEED_ENTRIES"]
