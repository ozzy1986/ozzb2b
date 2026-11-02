"""Accounting firms serving marketplace sellers (Wildberries / Ozon).

First niche of the catalog. Discovery is search-driven: candidate landing
pages were collected from public search results (Yandex, DuckDuckGo) for
queries like «бухгалтерия для селлеров маркетплейсов» across the largest
Russian cities, with media, banks, SaaS products and directories removed.

For every candidate the spider:
- fetches the niche landing page and keeps the company only if the page
  really talks about marketplace sellers;
- fetches the homepage for the brand name and the link to «Контакты»;
- fetches the contacts page for e-mail, phone, INN and city.

Everything stays polite (one request per page, per-host throttling and
robots.txt via `PoliteFetcher`), and fetch failures only drop enrichment.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlsplit

import structlog

from ozzb2b_scraper.extractors import (
    ContactFacts,
    SiteFacts,
    extract_contact_facts,
    extract_site_facts,
    mentions_marketplaces,
)
from ozzb2b_scraper.http import looks_like_challenge
from ozzb2b_scraper.models import ScrapedProvider
from ozzb2b_scraper.spiders.base import Spider, SpiderContext

log = structlog.get_logger("ozzb2b_scraper.spiders.ru_marketplace_accounting")

SOURCE = "ru-marketplace-accounting"
CATEGORY_SLUGS: tuple[str, ...] = ("accounting", "bookkeeping", "marketplace-accounting")


@dataclass(frozen=True)
class Candidate:
    landing_url: str
    city_hint: str | None = None
    # Brand name when the site's <title>/og:site_name is an SEO phrase.
    name: str | None = None


# Longer "names" are page titles ("Бухгалтерские услуги в Тюмени"), not brands.
MAX_NAME_LENGTH = 40


CANDIDATES: tuple[Candidate, ...] = (
    # Nationwide / online and Moscow-based firms.
    Candidate("https://glavbuhok.ru/marketplace/"),
    Candidate("https://fintehplus.ru/industries/marketplaces"),
    Candidate("https://www.buhclear.ru/uslugi/buhgalterskie/marketplaces/", "Moscow", "BuhClear"),
    Candidate("https://proffresh.ru/bukhgalteriya-dlya-marketpleysov/"),
    Candidate("https://xn--80aabihevw3acrwef4a1of.xn--p1ai/buhgalterskie-uslugi-dlya-marketplejsov/"),
    Candidate("https://pbuexpert.ru/marketplaces/"),
    Candidate("https://knopka.com/sellers", name="Кнопка"),
    Candidate("https://xn----etbfcngff4ei8b.xn--p1ai/autsorsing-buhgalterii-dlya-sellerov-na-marketpleysah/"),
    Candidate("https://1cbo.eosfine.ru/buhgalteriya-dlya-marketplejsov", name="ЭосФайн"),
    Candidate("https://buhinfo.pro/"),
    Candidate("https://dbuh.online/"),
    Candidate("https://audston.ru/marketplaces/", "Moscow"),
    Candidate("https://pbu.ru/vedenie-buhgalterii-dlya-marketplejsov/"),
    Candidate("https://i-ias.ru/autsorsing/buhgalteriya/outsourcing-marketplaces/", "Moscow"),
    Candidate("https://www.qb2b.ru/buhgalteriya-dlya-marketpleysov/", "Moscow"),
    Candidate("https://efsol.ru/services/marketplace-accounting/", "Moscow"),
    Candidate("https://fingu.ru/marketplace/", "Moscow", "Фингуру"),
    Candidate("https://chur-buh.ru/buhgalter-marketpleysov/"),
    Candidate("https://binergy.ru/marketplace", name="Бинергика"),
    Candidate("https://cfunalog.ru/buhgalteriya-na-marketpleysah", name="cfunalog.ru"),
    Candidate("https://lad-salon.ru/marketplace/bukhgalterskoe-obsluzhivanie-sellerov"),
    Candidate("https://finexpertgroup.ru/buhuchet/buhgalteriya-dlya-marketpleysov/", "Moscow"),
    Candidate("https://xn--80abgj3a5ames.xn--p1ai/services/postavshchikam-marketpleysov/"),
    Candidate("https://getbuh.com/"),
    Candidate("https://www.buhcontact.ru/accounting-services/buhgalterskoe-obsluzhivanie-marketplejsov/"),
    Candidate("https://tax-smart.pro/services/bukhgalteriya-dlya-marketpleysov"),
    Candidate("https://buh.reg-express.ru/bukhgalterskoe-obsluzhivanie-marketpleysov/"),
    Candidate("https://rarus.ru/buhgalterskie-uslugi/dlya-marketpleisov/", "Moscow", "1С-Рарус"),
    Candidate("https://finabi.ru/industries/marketplace/"),
    Candidate("https://azbuka-ucheta.ru/selleri"),
    Candidate(
        "https://consultexpert.ru/services/buhgalteriya-marketplejsov-dlya-sellerov",
        name="Консалт Эксперт",
    ),
    Candidate("https://megaconsult.ru/bukhgalteriya-dlya-marketpleysov"),
    Candidate("https://uksor.ru/accounting/autsorsing-bukhgalterii-marketplace", "Moscow"),
    Candidate("https://finprofcenter.ru/buhgalteriya-dlya-marketplejsov"),
    Candidate("https://buhtime.pro/services/bukhgalterskie-uslugi/bukhgalteriya-dlya-marketpleysov/", "Moscow"),
    Candidate("https://marketcount.ru/", name="MarketCount"),
    Candidate("https://www.consult-gp.ru/bukhgalterskie-uslugi-dlya-sellerov-marketpleysov.php"),
    # Saint Petersburg.
    Candidate("https://oburo.ru/buhgalteriya-dlya-marketplejsov/", "Saint Petersburg"),
    Candidate("https://sellers.spb.ru/market/", "Saint Petersburg"),
    Candidate("https://finkit.pro/spb", "Saint Petersburg"),
    Candidate("https://saldoria.ru/", "Saint Petersburg"),
    Candidate("https://buhinfospb.ru/", "Saint Petersburg"),
    Candidate("https://poseidon-finance.ru/", "Saint Petersburg"),
    # Regions.
    Candidate("https://buhmmaksimich.ru/", "Kazan", "buhmmaksimich.ru"),
    Candidate("https://buhautsors-kzn.ru/", "Kazan", "ПрофиПрофит"),
    Candidate("https://finexpert-e.ru/buhgalteriya-dlya-marketpleysov/", "Yekaterinburg"),
    Candidate("https://www.bdb-ek.ru/", "Yekaterinburg"),
    Candidate("https://www.atika-grup.ru/uslugi-kompanii/buhgalter/", "Yekaterinburg"),
    Candidate("https://sib-bb.ru/buhgalteria-dlya-marketplasov/", "Novosibirsk"),
    Candidate("https://buhberry.ru/", "Novosibirsk"),
    Candidate("https://polza-buhgalter.ru/", "Krasnodar"),
    Candidate("https://buhkrd.ru/", "Krasnodar"),
    Candidate("https://expert-buhuchet.ru/services/marketplaces/nizhniy-novgorod/", "Nizhny Novgorod"),
    Candidate("https://op-c.ru/industry/marketplace", "Samara"),
    Candidate("https://iqora.ru/", "Samara"),
    Candidate("https://rokass.ru/services/bukhgalteriya-dlya-marketpleysov-/", "Rostov-on-Don"),
    Candidate("https://centrpmb.ru/services/buhgalterskie-uslugi-dlya-marketplejsov", "Perm"),
    Candidate(
        "https://xn--90aad1cjhkq6f.xn--p1ai/services/bukhgalter-dlya-marketpleysakh/",
        "Perm",
        "бухбюросв.рф",
    ),
    Candidate("https://buhkonsalt174.com/uslugi/bukhgalteriya-dlya-it-marketpleysov-uslugi.html", "Chelyabinsk"),
    Candidate("https://agency3.ru/buhgalteriya-dlya-marketplaysov", "Tyumen", "agency3.ru"),
    Candidate("https://tym.my-buhgalter.ru/uslugi/dlya-marketplejsov/", "Tyumen"),
)


def source_id_for(url: str) -> str:
    host = (urlsplit(url).hostname or url).lower()
    return host.removeprefix("www.")


def homepage_for(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}/"


def _brand(name: str | None) -> str | None:
    return name if name and len(name) <= MAX_NAME_LENGTH else None


def _legal_form(tax_id: str | None) -> str:
    if tax_id and len(tax_id) == 12:
        return "IP"
    if tax_id and len(tax_id) == 10:
        return "OOO"
    return "UNK"


def build_provider(
    candidate: Candidate,
    site: SiteFacts,
    landing: SiteFacts,
    contacts: ContactFacts,
    now: datetime,
) -> ScrapedProvider:
    homepage = homepage_for(candidate.landing_url)
    sid = source_id_for(candidate.landing_url)
    return ScrapedProvider(
        source=SOURCE,
        source_id=sid,
        source_url=candidate.landing_url,
        display_name=candidate.name or _brand(site.name) or _brand(landing.name) or sid,
        description=landing.description or site.description,
        country_code="RU",
        city_name=contacts.city_name or candidate.city_hint,
        legal_form_code=_legal_form(contacts.tax_id),
        website=homepage,
        email=contacts.email,
        phone=contacts.phone,
        tax_id=contacts.tax_id,
        category_slugs=CATEGORY_SLUGS,
        meta={"niche": "marketplace-sellers", "landing_url": candidate.landing_url},
        fetched_at=now,
    )


async def _get_html(ctx: SpiderContext, url: str) -> str | None:
    try:
        resp = await ctx.fetcher.get(url)
        html = resp.text
    except Exception as exc:  # noqa: BLE001 - best-effort enrichment
        log.info("ru_marketplace_accounting.fetch.failed", url=url, error=str(exc))
        return None
    if looks_like_challenge(html):
        log.info("ru_marketplace_accounting.challenge.skipped", url=url)
        return None
    return html


def _merge(primary: ContactFacts, fallback: ContactFacts) -> ContactFacts:
    return ContactFacts(
        email=primary.email or fallback.email,
        phone=primary.phone or fallback.phone,
        tax_id=primary.tax_id or fallback.tax_id,
        city_name=primary.city_name or fallback.city_name,
    )


class RuMarketplaceAccountingSpider(Spider):
    """Accounting firms for WB/Ozon sellers, verified by their own landing page."""

    source = SOURCE

    def __init__(self, candidates: tuple[Candidate, ...] = CANDIDATES) -> None:
        self._candidates = candidates

    async def crawl(self, ctx: SpiderContext) -> AsyncIterator[ScrapedProvider]:
        now = datetime.now(tz=UTC)
        yielded = 0
        for candidate in self._candidates:
            if ctx.limit is not None and yielded >= ctx.limit:
                break
            item = await self._crawl_one(ctx, candidate, now)
            if item is not None:
                yield item
                yielded += 1

    async def _crawl_one(
        self, ctx: SpiderContext, candidate: Candidate, now: datetime
    ) -> ScrapedProvider | None:
        landing_html = await _get_html(ctx, candidate.landing_url)
        if landing_html is None or not mentions_marketplaces(landing_html):
            log.info("ru_marketplace_accounting.not_niche", url=candidate.landing_url)
            return None
        landing = extract_site_facts(landing_html, candidate.landing_url)
        contacts = extract_contact_facts(landing_html)

        homepage = homepage_for(candidate.landing_url)
        site = landing
        if homepage.rstrip("/") != candidate.landing_url.rstrip("/"):
            home_html = await _get_html(ctx, homepage)
            if home_html is not None:
                site = extract_site_facts(home_html, homepage)
                contacts = _merge(contacts, extract_contact_facts(home_html))

        contact_url = site.contact_url or landing.contact_url
        if contact_url and not (contacts.email and contacts.tax_id and contacts.city_name):
            contact_html = await _get_html(ctx, contact_url)
            if contact_html is not None:
                contacts = _merge(extract_contact_facts(contact_html), contacts)

        return build_provider(candidate, site, landing, contacts, now)


__all__ = [
    "CANDIDATES",
    "Candidate",
    "RuMarketplaceAccountingSpider",
    "build_provider",
    "homepage_for",
    "source_id_for",
]
