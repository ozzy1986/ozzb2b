"""Pure HTML extraction helpers used by spiders."""

from ozzb2b_scraper.extractors.contacts import (
    ContactFacts,
    SiteFacts,
    extract_contact_facts,
    extract_site_facts,
    mentions_marketplaces,
)
from ozzb2b_scraper.extractors.html_public import PublicPageFacts, extract_public_facts

__all__ = [
    "ContactFacts",
    "PublicPageFacts",
    "SiteFacts",
    "extract_contact_facts",
    "extract_public_facts",
    "extract_site_facts",
    "mentions_marketplaces",
]
