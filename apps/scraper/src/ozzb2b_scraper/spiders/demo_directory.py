"""Demo spider that yields a handful of additional providers deterministically.

This is intentionally offline-safe so we can run the pipeline end-to-end without
touching third-party sites until real sources are picked. Real spiders can be
added later by subclassing `Spider` and replacing the hard-coded items with
HTTP fetches via `ctx.fetcher`.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime

from ozzb2b_scraper.models import ScrapedProvider
from ozzb2b_scraper.spiders.base import Spider, SpiderContext

_DEMO_ITEMS: tuple[ScrapedProvider, ...] = (
    ScrapedProvider(
        source="demo-directory",
        source_id="nimbus-cloud-systems",
        source_url="https://example.com/demo/nimbus-cloud-systems",
        display_name="Nimbus Cloud Systems",
        legal_name="Nimbus Cloud Systems Sp. z o.o.",
        description=(
            "Managed AWS and GCP infrastructure for B2B SaaS. Kubernetes operators, "
            "incident response, cost optimization, and 24/7 SRE on call."
        ),
        country_code="PL",
        city_name="Krakow",
        legal_form_code="SP_Z_O_O",
        website="https://example.com/nimbus-cloud-systems",
        email="hello@nimbuscloud.example",
        phone="+48 12 000 0007",
        address="Rynek Glowny 10, Krakow",
        year_founded=2016,
        employee_count_range="50-200",
        category_slugs=("it", "devops-cloud", "cybersecurity"),
    ),
    ScrapedProvider(
        source="demo-directory",
        source_id="medusa-design-studio",
        source_url="https://example.com/demo/medusa-design-studio",
        display_name="Medusa Design Studio",
        legal_name="Medusa Design Studio GmbH",
        description="Product design studio for B2B SaaS: research, UI systems, prototyping, and user testing.",
        country_code="DE",
        city_name="Munich",
        legal_form_code="GMBH",
        website="https://example.com/medusa-design-studio",
        email="studio@medusadesign.example",
        phone="+49 89 000 0008",
        address="Maximilianstr. 20, Munich",
        year_founded=2018,
        employee_count_range="11-50",
        category_slugs=("it", "ui-ux-design"),
    ),
    ScrapedProvider(
        source="demo-directory",
        source_id="prague-tax-advisors",
        source_url="https://example.com/demo/prague-tax-advisors",
        display_name="Prague Tax Advisors",
        legal_name="Prague Tax Advisors s.r.o.",
        description=(
            "Cross-border tax advisory for EU tech companies. VAT OSS, transfer pricing, "
            "and dual-country payroll setups."
        ),
        country_code="CZ",
        city_name="Prague",
        legal_form_code="UNK",
        website="https://example.com/prague-tax-advisors",
        email="team@praguetax.example",
        phone="+420 000 0009",
        address="Wenceslas Square 5, Prague",
        year_founded=2011,
        employee_count_range="11-50",
        category_slugs=("accounting", "tax-advisory", "financial-reporting"),
    ),
)


class DemoDirectorySpider(Spider):
    source = "demo-directory"

    async def crawl(self, ctx: SpiderContext) -> AsyncIterator[ScrapedProvider]:
        now = datetime.now(tz=UTC)
        yielded = 0
        for item in _DEMO_ITEMS:
            if ctx.limit is not None and yielded >= ctx.limit:
                break
            yield ScrapedProvider(
                **{**item.__dict__, "fetched_at": now},
            )
            yielded += 1
