"""Tests for the marketplace-sellers accounting spider and contact extractors."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

from ozzb2b_scraper.extractors import (
    extract_contact_facts,
    extract_site_facts,
    mentions_marketplaces,
)
from ozzb2b_scraper.spiders.ru_marketplace_accounting import (
    CANDIDATES,
    Candidate,
    RuMarketplaceAccountingSpider,
    homepage_for,
    source_id_for,
)

LANDING = "https://buh.example.ru/marketplace/"
HOME = "https://buh.example.ru/"
CONTACTS = "https://buh.example.ru/kontakty/"

LANDING_HTML = """
<html><head>
  <title>Бухгалтерия для маркетплейсов | БухПро</title>
  <meta name="description" content="Ведём учёт селлеров Wildberries и Ozon: УСН, НДС, отчёты площадок.">
</head><body><p>Бухгалтерия для селлеров Wildberries и Ozon.</p></body></html>
"""
HOME_HTML = """
<html><head>
  <meta property="og:site_name" content="БухПро">
  <title>Главная | БухПро</title>
</head><body>
  <a href="/uslugi/">Услуги</a>
  <a href="/kontakty/">Контакты</a>
</body></html>
"""
CONTACTS_HTML = """
<html><body>
  <p>г. Казань, ул. Баумана, 1</p>
  <p>Пишите: info@buhpro.ru, logo@2x.png</p>
  <a href="tel:+7 843 000-00-00">Позвонить</a>
  <p>ООО «БухПро», ИНН 1655000000, ОГРН 1001600000000</p>
  <script>var x = "spam@tracker.example.com";</script>
</body></html>
"""


@dataclass
class _FakeResponse:
    text: str


class _FakeFetcher:
    def __init__(self, responses: dict[str, str], raise_for: set[str] | None = None) -> None:
        self.responses = responses
        self.raise_for = raise_for or set()
        self.calls: list[str] = []

    async def get(self, url: str) -> _FakeResponse:
        self.calls.append(url)
        if url in self.raise_for:
            raise RuntimeError(f"network down for {url}")
        return _FakeResponse(text=self.responses.get(url, "<html></html>"))


def _ctx(fetcher: Any, limit: int | None = None) -> Any:
    return SimpleNamespace(fetcher=fetcher, limit=limit)


async def _collect(spider: RuMarketplaceAccountingSpider, ctx: Any) -> list[Any]:
    return [item async for item in spider.crawl(ctx)]


def test_contact_facts_from_contacts_page() -> None:
    facts = extract_contact_facts(CONTACTS_HTML)
    assert facts.email == "info@buhpro.ru"
    assert facts.phone == "+7 843 000-00-00"
    assert facts.tax_id == "1655000000"
    assert facts.city_name == "Kazan"


def test_contact_facts_prefer_mailto_and_skip_image_names() -> None:
    html = '<a href="mailto:Hello@Firm.ru">mail</a> <img alt="logo@2x.png">'
    assert extract_contact_facts(html).email == "hello@firm.ru"
    assert extract_contact_facts("<p>icon@3x.webp</p>").email is None


def test_contact_facts_twelve_digit_inn() -> None:
    assert extract_contact_facts("<p>ИП Иванов, ИНН: 165500000000</p>").tax_id == "165500000000"


def test_site_facts_name_and_contact_link() -> None:
    facts = extract_site_facts(HOME_HTML, HOME)
    assert facts.name == "БухПро"
    assert facts.contact_url == CONTACTS


def test_site_facts_skip_generic_title_and_foreign_contact_link() -> None:
    html = (
        "<title>Главная | Аудит-Сервис</title>"
        '<a href="https://other.ru/contacts">Контакты</a>'
    )
    facts = extract_site_facts(html, HOME)
    assert facts.name == "Аудит-Сервис"
    assert facts.contact_url is None


def test_mentions_marketplaces() -> None:
    assert mentions_marketplaces(LANDING_HTML)
    assert not mentions_marketplaces("<p>Аудит для банков</p>")


def test_url_helpers() -> None:
    assert source_id_for("https://www.Buh.ru/x/") == "buh.ru"
    assert homepage_for("https://buh.ru/x/y?z=1") == "https://buh.ru/"


async def test_crawl_enriches_from_homepage_and_contacts() -> None:
    fetcher = _FakeFetcher({LANDING: LANDING_HTML, HOME: HOME_HTML, CONTACTS: CONTACTS_HTML})
    spider = RuMarketplaceAccountingSpider((Candidate(LANDING),))
    [item] = await _collect(spider, _ctx(fetcher))
    assert fetcher.calls == [LANDING, HOME, CONTACTS]
    assert item.source == "ru-marketplace-accounting"
    assert item.source_id == "buh.example.ru"
    assert item.display_name == "БухПро"
    assert item.description is not None and "Wildberries" in item.description
    assert item.website == HOME
    assert item.email == "info@buhpro.ru"
    assert item.tax_id == "1655000000"
    assert item.legal_form_code == "OOO"
    assert item.city_name == "Kazan"
    assert "marketplace-accounting" in item.category_slugs


async def test_crawl_skips_pages_outside_the_niche() -> None:
    fetcher = _FakeFetcher({LANDING: "<p>Аудит для банков и страховых</p>"})
    spider = RuMarketplaceAccountingSpider((Candidate(LANDING),))
    assert await _collect(spider, _ctx(fetcher)) == []
    assert fetcher.calls == [LANDING]


async def test_crawl_survives_failed_enrichment_and_uses_city_hint() -> None:
    fetcher = _FakeFetcher({LANDING: LANDING_HTML}, raise_for={HOME})
    spider = RuMarketplaceAccountingSpider((Candidate(LANDING, city_hint="Moscow"),))
    [item] = await _collect(spider, _ctx(fetcher))
    assert item.display_name == "БухПро"
    assert item.city_name == "Moscow"
    assert item.legal_form_code == "UNK"


async def test_crawl_respects_limit() -> None:
    other = "https://other.example.ru/sellers/"
    fetcher = _FakeFetcher({LANDING: LANDING_HTML, other: LANDING_HTML})
    spider = RuMarketplaceAccountingSpider((Candidate(LANDING), Candidate(other)))
    assert len(await _collect(spider, _ctx(fetcher, limit=1))) == 1


def test_candidates_are_unique_https_hosts() -> None:
    hosts = [source_id_for(c.landing_url) for c in CANDIDATES]
    assert len(hosts) == len(set(hosts))
    for candidate in CANDIDATES:
        assert candidate.landing_url.startswith("https://"), candidate.landing_url


async def test_name_override_and_long_titles() -> None:
    long_title = "<title>Бухгалтерские услуги в Тюмени для ИП и ООО недорого</title>"
    page = long_title + "<p>Учёт для селлеров Ozon</p>"
    fetcher = _FakeFetcher({LANDING: page, HOME: long_title})
    spider = RuMarketplaceAccountingSpider(
        (Candidate(LANDING), Candidate("https://named.example.ru/", name="Бренд"))
    )
    fetcher.responses["https://named.example.ru/"] = page
    first, second = await _collect(spider, _ctx(fetcher))
    assert first.display_name == "buh.example.ru"
    assert second.display_name == "Бренд"
