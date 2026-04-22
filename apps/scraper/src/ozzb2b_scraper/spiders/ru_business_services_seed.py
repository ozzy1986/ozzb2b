"""Curated Russian B2B services companies (accounting, legal, marketing, HR).

Same philosophy as the IT outsourcing seed spider: a hand-picked list of
publicly-operating Russian service providers, enriched with facts extracted
from each company's own homepage. Widens the catalog beyond IT so the
marketplace is useful for finance/legal/marketing/HR buyers too.
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

log = structlog.get_logger("ozzb2b_scraper.spiders.ru_business_services_seed")


@dataclass(frozen=True)
class RuBizSeedEntry:
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


SEED_ENTRIES: tuple[RuBizSeedEntry, ...] = (
    RuBizSeedEntry(
        source_id="b1-consulting",
        display_name="Б1",
        legal_name="ООО «Би1 Консалт»",
        website="https://b1.ru/",
        city_name="Moscow",
        legal_form_code="OOO",
        description=(
            "Аудит, налоговое и юридическое консультирование, финансовый консалтинг "
            "и управленческий консалтинг для крупного и среднего бизнеса."
        ),
        category_slugs=("accounting", "audit-assurance", "tax-advisory", "financial-reporting"),
        year_founded=2022,
        employee_count_range="1000+",
    ),
    RuBizSeedEntry(
        source_id="kept",
        display_name="Kept",
        legal_name="АО «Кэпт»",
        website="https://kept.ru/",
        city_name="Moscow",
        legal_form_code="AO",
        description=(
            "Аудит, налоговое и юридическое консультирование, сделки M&A и "
            "стратегический консалтинг для российских и международных компаний."
        ),
        category_slugs=("accounting", "audit-assurance", "tax-advisory", "legal"),
        year_founded=2022,
        employee_count_range="1000+",
    ),
    RuBizSeedEntry(
        source_id="delovoy-profil",
        display_name="Деловой профиль",
        legal_name="АО «Деловой Профиль»",
        website="https://delprof.ru/",
        city_name="Moscow",
        legal_form_code="AO",
        description=(
            "Аудиторско-консалтинговая группа: аудит, налоговое и юридическое "
            "консультирование, оценка, due diligence, финансовый консалтинг."
        ),
        category_slugs=("accounting", "audit-assurance", "tax-advisory"),
        year_founded=1995,
        employee_count_range="200-500",
    ),
    RuBizSeedEntry(
        source_id="fbk",
        display_name="ФБК",
        legal_name="АО «ФБК»",
        website="https://www.fbk.ru/",
        city_name="Moscow",
        legal_form_code="AO",
        description=(
            "Одна из крупнейших российских аудиторско-консалтинговых групп: аудит, "
            "налоговый и управленческий консалтинг, оценка, IT-консалтинг."
        ),
        category_slugs=("accounting", "audit-assurance", "tax-advisory"),
        year_founded=1990,
        employee_count_range="500-1000",
    ),
    RuBizSeedEntry(
        source_id="nalog-expert",
        display_name="Главбух Ассистент",
        legal_name="ООО «Главбух Ассистент»",
        website="https://glavbuh-assistent.ru/",
        city_name="Moscow",
        legal_form_code="OOO",
        description=(
            "Онлайн-сервис бухгалтерского обслуживания для малого и среднего бизнеса: "
            "ведение учета, зарплата, налоги, отчетность, юридическая поддержка."
        ),
        category_slugs=("accounting", "bookkeeping", "payroll", "tax-advisory"),
        year_founded=2016,
        employee_count_range="200-500",
    ),
    RuBizSeedEntry(
        source_id="pepeliaev",
        display_name="Пепеляев Групп",
        legal_name="ООО «Пепеляев Групп»",
        website="https://www.pgplaw.ru/",
        city_name="Moscow",
        legal_form_code="OOO",
        description=(
            "Одна из ведущих российских юридических фирм: налоговое и корпоративное "
            "право, комплаенс, трудовое право, разрешение споров, ИС."
        ),
        category_slugs=(
            "legal",
            "tax-advisory",
            "corporate-law",
            "dispute-resolution",
            "intellectual-property",
        ),
        year_founded=2002,
        employee_count_range="200-500",
    ),
    RuBizSeedEntry(
        source_id="egorov-puginsky",
        display_name="ЕПАМ",
        legal_name="Адвокатское бюро «Егоров, Пугинский, Афанасьев и партнеры»",
        website="https://epam.ru/",
        city_name="Moscow",
        legal_form_code="UNK",
        description=(
            "Крупная российская юридическая фирма: M&A, банкротство, международный "
            "арбитраж, налоговое и уголовное право, комплаенс."
        ),
        category_slugs=("legal", "corporate-law", "dispute-resolution", "compliance-regulatory"),
        year_founded=1993,
        employee_count_range="200-500",
    ),
    RuBizSeedEntry(
        source_id="gorodissky",
        display_name="Городисский и Партнёры",
        legal_name="ООО «Городисский и Партнёры»",
        website="https://gorodissky.ru/",
        city_name="Moscow",
        legal_form_code="OOO",
        description=(
            "Одна из крупнейших российских IP-фирм: регистрация, защита и коммерциализация "
            "интеллектуальной собственности, товарные знаки, патенты, судебные споры."
        ),
        category_slugs=("legal", "intellectual-property", "dispute-resolution"),
        year_founded=1959,
        employee_count_range="200-500",
    ),
    RuBizSeedEntry(
        source_id="ashmanov",
        display_name="Ашманов и партнеры",
        legal_name="ООО «Ашманов и партнеры»",
        website="https://www.ashmanov.com/",
        city_name="Moscow",
        legal_form_code="OOO",
        description=(
            "SEO и поисковый маркетинг, контекстная реклама, аналитика, "
            "репутационный и контент-маркетинг для российских компаний."
        ),
        category_slugs=("marketing", "seo", "paid-media", "content"),
        year_founded=2001,
        employee_count_range="51-200",
    ),
    RuBizSeedEntry(
        source_id="inagency",
        display_name="iKRA",
        legal_name="ООО «АйКРА»",
        website="https://ikra.agency/",
        city_name="Moscow",
        legal_form_code="OOO",
        description=(
            "Креативное и инновационное агентство: брендинг, стратегия, "
            "digital-коммуникации и трансформация брендов."
        ),
        category_slugs=("marketing", "branding", "pr", "content"),
        year_founded=2009,
        employee_count_range="11-50",
    ),
    RuBizSeedEntry(
        source_id="ancor",
        display_name="ANCOR",
        legal_name="АО «Холдинг Анкор»",
        website="https://ancor.ru/",
        city_name="Moscow",
        legal_form_code="AO",
        description=(
            "Одно из крупнейших кадровых агентств России: подбор персонала всех уровней, "
            "аутстаффинг, массовый подбор, консалтинг в HR."
        ),
        category_slugs=("hr", "recruiting", "staffing"),
        year_founded=1990,
        employee_count_range="1000+",
    ),
    RuBizSeedEntry(
        source_id="kelly-services-ru",
        display_name="Coleman Services",
        legal_name="ООО «Коулман Сервисиз»",
        website="https://colemanservices.ru/",
        city_name="Saint Petersburg",
        legal_form_code="OOO",
        description=(
            "Международное кадровое агентство: подбор персонала, аутстаффинг, "
            "расчет зарплаты и HR-аутсорсинг для крупных и средних компаний."
        ),
        category_slugs=("hr", "recruiting", "staffing", "payroll"),
        year_founded=1994,
        employee_count_range="200-500",
    ),
)


def _to_scraped(entry: RuBizSeedEntry, facts: PublicPageFacts, now: datetime) -> ScrapedProvider:
    return ScrapedProvider(
        source="ru-business-services-seed",
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


class RuBusinessServicesSeedSpider(Spider):
    """Curated RU accounting/legal/marketing/HR list with public-page enrichment."""

    source = "ru-business-services-seed"

    async def crawl(self, ctx: SpiderContext) -> AsyncIterator[ScrapedProvider]:
        now = datetime.now(tz=UTC)
        yielded = 0
        for entry in SEED_ENTRIES:
            if ctx.limit is not None and yielded >= ctx.limit:
                break
            facts = await _safe_fetch_facts(ctx, entry)
            yield _to_scraped(entry, facts, now)
            yielded += 1


async def _safe_fetch_facts(ctx: SpiderContext, entry: RuBizSeedEntry) -> PublicPageFacts:
    try:
        resp = await ctx.fetcher.get(entry.website)
    except Exception as exc:  # noqa: BLE001 - best-effort enrichment
        log.warning(
            "ru_business_services_seed.fetch.failed",
            source_id=entry.source_id,
            website=entry.website,
            error=str(exc),
        )
        return PublicPageFacts()

    try:
        html = resp.text
    except Exception as exc:  # noqa: BLE001
        log.warning(
            "ru_business_services_seed.decode.failed",
            source_id=entry.source_id,
            error=str(exc),
        )
        return PublicPageFacts()

    if looks_like_challenge(html):
        log.info(
            "ru_business_services_seed.challenge.skipped",
            source_id=entry.source_id,
            website=entry.website,
        )
        return PublicPageFacts()

    try:
        return extract_public_facts(html)
    except Exception as exc:  # noqa: BLE001
        log.warning(
            "ru_business_services_seed.extract.failed",
            source_id=entry.source_id,
            error=str(exc),
        )
        return PublicPageFacts()


__all__ = ["RuBizSeedEntry", "RuBusinessServicesSeedSpider", "SEED_ENTRIES"]
