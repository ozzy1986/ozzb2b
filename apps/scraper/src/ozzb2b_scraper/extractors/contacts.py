"""Contact-page extractors used by niche discovery spiders.

A company homepage rarely carries everything we need to reach the company:
the e-mail, INN and city usually live on a separate "Контакты" page or in the
footer. These helpers stay pure (HTML string in, dataclass out) so they are
trivial to unit-test with canned pages.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

from selectolax.parser import HTMLParser

from ozzb2b_scraper.extractors.html_public import extract_public_facts

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}")
# Image names like logo@2x.png look like e-mails to a naive regex.
_EMAIL_JUNK_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".css", ".js")
_EMAIL_JUNK_DOMAINS = ("example.com", "sentry.io", "domain.ru", "mail.example")
_INN_RE = re.compile(r"ИНН\s*[:№]?\s*(\d{12}|\d{10})(?!\d)", re.IGNORECASE)
_CONTACT_HREF_RE = re.compile(r"kontakt|contact|svyaz", re.IGNORECASE)
_CONTACT_TEXT_RE = re.compile(r"^\s*контакты\s*$", re.IGNORECASE)
_GENERIC_TITLES = frozenset({"главная", "главная страница", "home", "контакты", "о компании"})

# Russian city spellings (incl. the locative case used in "в Казани") mapped to
# the English names stored in the catalog's `cities` table.
_CITY_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(pattern, re.IGNORECASE), name)
    for pattern, name in (
        (r"\bмоскв[аеуы]\b", "Moscow"),
        (r"\bсанкт-петербург[ае]?\b|\bспб\b", "Saint Petersburg"),
        (r"\bновосибирск[ае]?\b", "Novosibirsk"),
        (r"\bекатеринбург[ае]?\b", "Yekaterinburg"),
        (r"\bказан[ьи]\b", "Kazan"),
        (r"\bнижн(?:ий|ем) новгород[ае]?\b", "Nizhny Novgorod"),
        (r"\bсамар[аеы]\b", "Samara"),
        (r"\bростов[ае]?-на-дону\b", "Rostov-on-Don"),
        (r"\bкраснодар[ае]?\b", "Krasnodar"),
        (r"\bперм[ьи]\b", "Perm"),
        (r"\bворонеж[ае]?\b", "Voronezh"),
        (r"\bуф[аеы]\b", "Ufa"),
        (r"\bчелябинск[ае]?\b", "Chelyabinsk"),
        (r"\bомск[ае]?\b", "Omsk"),
        (r"\bтюмен[ьи]\b", "Tyumen"),
        (r"\bульяновск[ае]?\b", "Ulyanovsk"),
        (r"\bкиров[ае]?\b", "Kirov"),
    )
)

NICHE_MARKETPLACE_RE = re.compile(
    r"маркетплейс|wildberries|вайлдберриз|\bozon\b|озон|селлер", re.IGNORECASE
)


@dataclass(frozen=True)
class ContactFacts:
    email: str | None = None
    phone: str | None = None
    tax_id: str | None = None
    city_name: str | None = None


@dataclass(frozen=True)
class SiteFacts:
    name: str | None = None
    description: str | None = None
    contact_url: str | None = None


def page_text(html: str) -> str:
    tree = HTMLParser(html)
    for node in tree.css("script, style, noscript"):
        node.decompose()
    body = tree.body or tree.root
    return " ".join((body.text(separator=" ") if body else "").split())


def mentions_marketplaces(html: str) -> bool:
    """True when the page talks about marketplace sellers (WB/Ozon)."""
    return bool(NICHE_MARKETPLACE_RE.search(page_text(html)))


def _clean_email(raw: str) -> str | None:
    email = raw.strip().strip(".").lower()
    if not _EMAIL_RE.fullmatch(email):
        return None
    if email.endswith(_EMAIL_JUNK_SUFFIXES):
        return None
    if email.split("@", 1)[1] in _EMAIL_JUNK_DOMAINS:
        return None
    return email


def _first_text_email(text: str) -> str | None:
    for match in _EMAIL_RE.finditer(text):
        email = _clean_email(match.group(0))
        if email:
            return email
    return None


def _city(text: str) -> str | None:
    for pattern, name in _CITY_PATTERNS:
        if pattern.search(text):
            return name
    return None


def extract_contact_facts(html: str) -> ContactFacts:
    """Pull e-mail, phone, INN and city from a contacts page or footer."""
    links = extract_public_facts(html)
    text = page_text(html)
    email = (_clean_email(links.email) if links.email else None) or _first_text_email(text)
    inn = _INN_RE.search(text)
    return ContactFacts(
        email=email,
        phone=links.phone,
        tax_id=inn.group(1) if inn else None,
        city_name=_city(text),
    )


def _site_name(tree: HTMLParser) -> str | None:
    node = tree.css_first('meta[property="og:site_name"]')
    if node is not None:
        value = (node.attributes.get("content") or "").strip()
        if 2 <= len(value) <= 80:
            return value
    title = tree.css_first("title")
    if title is None:
        return None
    raw = " ".join(title.text().split())
    # "Бухгалтерия для маркетплейсов | Компания" -> keep the shortest segment,
    # which is usually the brand.
    parts = [
        p.strip()
        for p in re.split(r"\s[|—–-]\s", raw)
        if p.strip() and p.strip().lower() not in _GENERIC_TITLES
    ]
    if not parts:
        return None
    best = min(parts, key=len)
    return best if 2 <= len(best) <= 80 else None


def extract_site_facts(html: str, base_url: str) -> SiteFacts:
    """Brand name, description and the same-site contacts-page URL."""
    tree = HTMLParser(html)
    description = extract_public_facts(html).description
    base_host = urlsplit(base_url).hostname
    contact_url = None
    for node in tree.css("a[href]"):
        href = (node.attributes.get("href") or "").strip()
        if not href or href.startswith(("mailto:", "tel:", "#", "javascript:")):
            continue
        if not (_CONTACT_HREF_RE.search(href) or _CONTACT_TEXT_RE.match(node.text() or "")):
            continue
        absolute = urljoin(base_url, href)
        if urlsplit(absolute).hostname == base_host:
            contact_url = absolute
            break
    return SiteFacts(name=_site_name(tree), description=description, contact_url=contact_url)
