"""Public-HTML extractors used to enrich curated seed entries.

Pulls only publicly displayed metadata:
- og:description / meta[name=description] -> description
- first reasonable mailto: -> email
- first reasonable tel: -> phone

Kept intentionally tiny and pure so it is easy to unit-test with canned HTML.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from selectolax.parser import HTMLParser

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_PHONE_CLEAN_RE = re.compile(r"[^\d+]+")


@dataclass(frozen=True)
class PublicPageFacts:
    description: str | None = None
    email: str | None = None
    phone: str | None = None


def _attr(tree: HTMLParser, selector: str, attr: str) -> str | None:
    node = tree.css_first(selector)
    if node is None:
        return None
    value = node.attributes.get(attr)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _meta_content(tree: HTMLParser, *selectors: str) -> str | None:
    for selector in selectors:
        value = _attr(tree, selector, "content")
        if value:
            return value
    return None


def _first_mailto(tree: HTMLParser) -> str | None:
    for node in tree.css('a[href^="mailto:"]'):
        href = (node.attributes.get("href") or "").strip()
        candidate = href.removeprefix("mailto:").split("?", 1)[0].strip()
        if _EMAIL_RE.fullmatch(candidate):
            return candidate.lower()
    return None


def _first_tel(tree: HTMLParser) -> str | None:
    for node in tree.css('a[href^="tel:"]'):
        href = (node.attributes.get("href") or "").strip()
        candidate = href.removeprefix("tel:").strip()
        digits = _PHONE_CLEAN_RE.sub("", candidate)
        # At least an international-looking phone number.
        if len(digits) >= 7:
            return candidate
    return None


def _normalize_description(raw: str | None) -> str | None:
    if not raw:
        return None
    collapsed = " ".join(raw.split())
    if len(collapsed) < 20:
        return None
    return collapsed[:1000]


def extract_public_facts(html: str) -> PublicPageFacts:
    """Extract safe, publicly-visible facts from a company homepage HTML."""
    tree = HTMLParser(html)
    description = _normalize_description(
        _meta_content(
            tree,
            'meta[property="og:description"]',
            'meta[name="description"]',
            'meta[name="Description"]',
        )
    )
    email = _first_mailto(tree)
    phone = _first_tel(tree)
    return PublicPageFacts(description=description, email=email, phone=phone)
