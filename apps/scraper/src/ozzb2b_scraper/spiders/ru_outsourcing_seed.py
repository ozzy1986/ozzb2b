"""Curated Russian IT-outsourcing companies + public-homepage enrichment.

Strategy:
- A hand-picked list of 20 well-known, publicly operating Russian software / IT
  services companies. Each entry carries everything we need to publish a useful
  profile even when the network fetch fails.
- For each entry the spider politely fetches the company's own homepage (a
  single request per domain, throttled by `PoliteFetcher`) and enriches the
  profile with publicly-visible metadata (description, email, phone).
- Fetch failures are swallowed: we still emit the entry with seed-only data.

This keeps the spider:
- Safe: only public marketing homepages, one GET each, clear User-Agent.
- Robust: offline-tolerant so a bad site never breaks the pipeline.
- Deterministic: rerunning the spider is idempotent thanks to dedupe upstream.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime

import structlog

from ozzb2b_scraper.extractors import extract_public_facts
from ozzb2b_scraper.http import looks_like_challenge
from ozzb2b_scraper.models import ScrapedProvider
from ozzb2b_scraper.spiders.base import Spider, SpiderContext

log = structlog.get_logger("ozzb2b_scraper.spiders.ru_outsourcing_seed")


@dataclass(frozen=True)
class RuSeedEntry:
    """Static seed data for one RU company."""

    source_id: str
    display_name: str
    legal_name: str
    website: str
    city_name: str
    legal_form_code: str  # one of: OOO, AO, PAO, IP, UNK
    description: str
    category_slugs: tuple[str, ...]
    year_founded: int | None = None
    employee_count_range: str | None = None


# Curated list of 20 publicly-operating Russian IT-services / outsourcing companies.
# All fields are derived from each company's own public website.
SEED_ENTRIES: tuple[RuSeedEntry, ...] = (
    RuSeedEntry(
        source_id="reksoft",
        display_name="Reksoft",
        legal_name="ООО «Рексофт»",
        website="https://www.reksoft.ru/",
        city_name="Saint Petersburg",
        legal_form_code="OOO",
        description=(
            "Custom software development and digital transformation services for "
            "enterprises: system integration, product engineering, cloud, data and AI."
        ),
        category_slugs=("it", "software-development", "data-analytics", "ai-ml"),
        year_founded=1991,
        employee_count_range="500-1000",
    ),
    RuSeedEntry(
        source_id="auriga",
        display_name="Auriga",
        legal_name="ООО «Аурига»",
        website="https://www.auriga.com/",
        city_name="Moscow",
        legal_form_code="OOO",
        description=(
            "Global outsourcing partner for product R&D and engineering: embedded, "
            "medical, and enterprise software development services."
        ),
        category_slugs=("it", "software-development", "quality-assurance"),
        year_founded=1990,
        employee_count_range="500-1000",
    ),
    RuSeedEntry(
        source_id="first-line-software",
        display_name="First Line Software",
        legal_name="ООО «Ферст Лайн Софтвер»",
        website="https://firstlinesoftware.com/",
        city_name="Saint Petersburg",
        legal_form_code="OOO",
        description=(
            "Custom software development, digital transformation, data platforms and "
            "cloud migration for enterprises in Europe and North America."
        ),
        category_slugs=("it", "software-development", "devops-cloud", "data-analytics"),
        year_founded=2009,
        employee_count_range="500-1000",
    ),
    RuSeedEntry(
        source_id="digital-design",
        display_name="Digital Design",
        legal_name="АО «Диджитал Дизайн»",
        website="https://digdes.com/",
        city_name="Saint Petersburg",
        legal_form_code="AO",
        description=(
            "Enterprise IT integrator specializing in document management, business "
            "process automation, mobile and identity platforms for large customers."
        ),
        category_slugs=("it", "software-development"),
        year_founded=1992,
        employee_count_range="200-500",
    ),
    RuSeedEntry(
        source_id="cinimex",
        display_name="Cinimex",
        legal_name="ООО «Синимекс-Информатика»",
        website="https://cinimex.ru/",
        city_name="Moscow",
        legal_form_code="OOO",
        description=(
            "Systems integrator and custom software developer for banks, telecoms "
            "and retail: integration platforms, distributed systems, cloud-native."
        ),
        category_slugs=("it", "software-development", "devops-cloud"),
        year_founded=1997,
        employee_count_range="500-1000",
    ),
    RuSeedEntry(
        source_id="lanit",
        display_name="LANIT",
        legal_name="АО «ЛАНИТ»",
        website="https://www.lanit.ru/",
        city_name="Moscow",
        legal_form_code="AO",
        description=(
            "One of the largest Russian IT holdings: systems integration, consulting, "
            "custom software, infrastructure, cybersecurity and managed services."
        ),
        category_slugs=("it", "software-development", "cybersecurity"),
        year_founded=1989,
        employee_count_range="1000+",
    ),
    RuSeedEntry(
        source_id="ibs",
        display_name="IBS",
        legal_name="АО «ИБС Экспертиза»",
        website="https://www.ibs.ru/",
        city_name="Moscow",
        legal_form_code="AO",
        description=(
            "Consulting and systems integration company delivering digital "
            "transformation, enterprise software, data, and managed IT services."
        ),
        category_slugs=("it", "software-development", "data-analytics"),
        year_founded=1992,
        employee_count_range="1000+",
    ),
    RuSeedEntry(
        source_id="croc",
        display_name="CROC",
        legal_name="АО «КРОК инкорпорейтед»",
        website="https://www.croc.ru/",
        city_name="Moscow",
        legal_form_code="AO",
        description=(
            "IT integrator delivering cloud, data centers, cybersecurity, custom "
            "software and managed services for large Russian and international clients."
        ),
        category_slugs=("it", "devops-cloud", "cybersecurity"),
        year_founded=1992,
        employee_count_range="1000+",
    ),
    RuSeedEntry(
        source_id="softline",
        display_name="Softline",
        legal_name="ООО «Софтлайн Проекты»",
        website="https://softline.ru/",
        city_name="Moscow",
        legal_form_code="OOO",
        description=(
            "Global IT solutions and services provider: software licensing, cloud, "
            "cybersecurity, custom development and managed services."
        ),
        category_slugs=("it", "software-development", "cybersecurity", "devops-cloud"),
        year_founded=1993,
        employee_count_range="1000+",
    ),
    RuSeedEntry(
        source_id="simbirsoft",
        display_name="SimbirSoft",
        legal_name="ООО «СимбирСофт»",
        website="https://www.simbirsoft.com/",
        city_name="Ulyanovsk",
        legal_form_code="OOO",
        description=(
            "Custom software development company: web, mobile, enterprise systems "
            "and dedicated engineering teams with strong QA practices."
        ),
        category_slugs=("it", "software-development", "quality-assurance"),
        year_founded=2001,
        employee_count_range="500-1000",
    ),
    RuSeedEntry(
        source_id="agima",
        display_name="AGIMA",
        legal_name="ООО «АГИМА»",
        website="https://agima.ru/",
        city_name="Moscow",
        legal_form_code="OOO",
        description=(
            "Digital production company: high-load web platforms, mobile apps, "
            "e-commerce, UX/UI design and long-running product teams."
        ),
        category_slugs=("it", "software-development", "ui-ux-design"),
        year_founded=2007,
        employee_count_range="200-500",
    ),
    RuSeedEntry(
        source_id="redmadrobot",
        display_name="Redmadrobot",
        legal_name="ООО «Редмэдробот»",
        website="https://redmadrobot.ru/",
        city_name="Moscow",
        legal_form_code="OOO",
        description=(
            "Digital product studio: mobile and web products for banks, telecoms "
            "and retail; strategy, product design and engineering."
        ),
        category_slugs=("it", "software-development", "ui-ux-design"),
        year_founded=2008,
        employee_count_range="200-500",
    ),
    RuSeedEntry(
        source_id="red-collar",
        display_name="Red Collar",
        legal_name="ООО «Ред Коллар»",
        website="https://redcollar.studio/",
        city_name="Voronezh",
        legal_form_code="OOO",
        description=(
            "Award-winning digital agency specializing in complex websites, branding "
            "and digital experiences for international and Russian clients."
        ),
        category_slugs=("it", "ui-ux-design", "software-development"),
        year_founded=2011,
        employee_count_range="51-200",
    ),
    RuSeedEntry(
        source_id="mobileup",
        display_name="MobileUp",
        legal_name="ООО «МобайлАп»",
        website="https://mobileup.ru/",
        city_name="Moscow",
        legal_form_code="OOO",
        description=(
            "Mobile-first product studio: iOS, Android and cross-platform apps, "
            "backend services and product design for enterprises and startups."
        ),
        category_slugs=("it", "software-development", "ui-ux-design"),
        year_founded=2009,
        employee_count_range="51-200",
    ),
    RuSeedEntry(
        source_id="live-typing",
        display_name="Live Typing",
        legal_name="ООО «Лайв Тайпинг»",
        website="https://livetyping.com/",
        city_name="Omsk",
        legal_form_code="OOO",
        description=(
            "Product development agency building web and mobile products: design, "
            "engineering and growth for founders and enterprise innovation teams."
        ),
        category_slugs=("it", "software-development", "ui-ux-design"),
        year_founded=2010,
        employee_count_range="51-200",
    ),
    RuSeedEntry(
        source_id="surf",
        display_name="Surf",
        legal_name="ООО «Сёрф»",
        website="https://surf.dev/",
        city_name="Kirov",
        legal_form_code="OOO",
        description=(
            "Mobile and web development studio: iOS, Android, Flutter, complex "
            "product engineering for enterprises and fast-growing companies."
        ),
        category_slugs=("it", "software-development"),
        year_founded=2011,
        employee_count_range="51-200",
    ),
    RuSeedEntry(
        source_id="naumen",
        display_name="Naumen",
        legal_name="ООО «Наумен Консалтинг»",
        website="https://www.naumen.ru/",
        city_name="Yekaterinburg",
        legal_form_code="OOO",
        description=(
            "Russian vendor of enterprise software: service management, contact "
            "centers, HR and document management. Custom development and support."
        ),
        category_slugs=("it", "software-development"),
        year_founded=2001,
        employee_count_range="500-1000",
    ),
    RuSeedEntry(
        source_id="otr",
        display_name="OTR",
        legal_name="АО «Организационно-технологические решения 2000»",
        website="https://www.otr.ru/",
        city_name="Moscow",
        legal_form_code="AO",
        description=(
            "IT systems integrator building large-scale state and commercial "
            "information systems: enterprise applications, integration, operations."
        ),
        category_slugs=("it", "software-development"),
        year_founded=2000,
        employee_count_range="500-1000",
    ),
    RuSeedEntry(
        source_id="t1",
        display_name="T1 Group",
        legal_name="ООО «Холдинговая компания Т1»",
        website="https://t1.ru/",
        city_name="Moscow",
        legal_form_code="OOO",
        description=(
            "Technology holding delivering custom software, systems integration, "
            "cloud, cybersecurity and digital products for large Russian enterprises."
        ),
        category_slugs=("it", "software-development", "cybersecurity", "devops-cloud"),
        year_founded=2020,
        employee_count_range="1000+",
    ),
    RuSeedEntry(
        source_id="arcadia",
        display_name="Arcadia",
        legal_name="ООО «Аркадия»",
        website="https://arcadia.spb.ru/",
        city_name="Saint Petersburg",
        legal_form_code="OOO",
        description=(
            "Custom software development and outsourcing: web, mobile, enterprise "
            "platforms and long-running dedicated teams for international clients."
        ),
        category_slugs=("it", "software-development", "quality-assurance"),
        year_founded=1996,
        employee_count_range="51-200",
    ),
)


def _to_scraped(entry: RuSeedEntry, facts, now: datetime) -> ScrapedProvider:
    """Merge static seed data with publicly-extracted HTML facts."""
    return ScrapedProvider(
        source="ru-outsourcing-seed",
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


class RuOutsourcingSeedSpider(Spider):
    """Emit the curated RU list, enriched from each company's own homepage."""

    source = "ru-outsourcing-seed"

    async def crawl(self, ctx: SpiderContext) -> AsyncIterator[ScrapedProvider]:
        now = datetime.now(tz=UTC)
        yielded = 0
        for entry in SEED_ENTRIES:
            if ctx.limit is not None and yielded >= ctx.limit:
                break
            facts = await _safe_fetch_facts(ctx, entry)
            yield _to_scraped(entry, facts, now)
            yielded += 1


async def _safe_fetch_facts(ctx: SpiderContext, entry: RuSeedEntry):
    """Fetch the homepage and extract enrichment facts; tolerate failures."""
    try:
        resp = await ctx.fetcher.get(entry.website)
    except Exception as exc:  # noqa: BLE001  # best-effort: never break ingest on one bad site
        log.warning(
            "ru_outsourcing_seed.fetch.failed",
            source_id=entry.source_id,
            website=entry.website,
            error=str(exc),
        )
        return _empty_facts()

    try:
        html = resp.text
    except Exception as exc:  # noqa: BLE001
        log.warning(
            "ru_outsourcing_seed.decode.failed",
            source_id=entry.source_id,
            error=str(exc),
        )
        return _empty_facts()

    # Anti-bot interstitial pages contain no meaningful facts; drop them instead of
    # scraping captcha markup into the `description` / `email` fields.
    if looks_like_challenge(html):
        log.info(
            "ru_outsourcing_seed.challenge.skipped",
            source_id=entry.source_id,
            website=entry.website,
        )
        return _empty_facts()

    try:
        return extract_public_facts(html)
    except Exception as exc:  # noqa: BLE001
        log.warning(
            "ru_outsourcing_seed.extract.failed",
            source_id=entry.source_id,
            error=str(exc),
        )
        return _empty_facts()


def _empty_facts():
    # Imported lazily to keep a single source of truth for the dataclass.
    from ozzb2b_scraper.extractors import PublicPageFacts

    return PublicPageFacts()


__all__ = ["RuOutsourcingSeedSpider", "RuSeedEntry", "SEED_ENTRIES"]
