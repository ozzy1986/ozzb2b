"""Ingestion pipeline: dedup + upsert scraped providers into Postgres.

We avoid taking a hard dependency on the api package's SQLAlchemy models to keep
the scraper independently deployable. Instead we emit raw SQL via asyncpg.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass
from urllib.parse import urlsplit

import asyncpg
import structlog
from slugify import slugify

from ozzb2b_scraper.config import get_settings
from ozzb2b_scraper.models import ScrapedProvider
from ozzb2b_scraper.spiders.base import Spider, SpiderContext

log = structlog.get_logger("ozzb2b_scraper.pipeline")

# A similarity score of 0.85 on display_name is a strong fuzzy match; below 0.7 we treat it as different.
FUZZY_THRESHOLD = 0.85


@dataclass
class IngestionStats:
    fetched: int = 0
    inserted: int = 0
    updated: int = 0
    merged_by_fuzzy: int = 0
    merged_by_domain: int = 0


def normalize_host(url: str | None) -> str | None:
    """Return a lowercase host without `www.` prefix, or None if not parsable.

    Used as a dedup key: two providers with the same canonical homepage host
    are almost certainly the same company even if display names differ slightly.
    """
    if not url:
        return None
    try:
        host = urlsplit(url).hostname
    except (ValueError, TypeError):
        return None
    if not host:
        return None
    host = host.lower()
    return host.removeprefix("www.")


def _to_asyncpg_dsn(url: str) -> str:
    """Convert SQLAlchemy-style DSN to asyncpg-style DSN."""
    return url.replace("postgresql+asyncpg://", "postgresql://")


async def _ensure_reference(conn: asyncpg.Connection, item: ScrapedProvider) -> tuple[int | None, int | None, int | None]:
    country_id = None
    city_id = None
    legal_form_id = None
    if item.country_code:
        row = await conn.fetchrow("SELECT id FROM countries WHERE code = $1", item.country_code)
        country_id = row["id"] if row else None
    if item.city_name and country_id is not None:
        city_slug = slugify(item.city_name)
        row = await conn.fetchrow(
            "SELECT id FROM cities WHERE country_id = $1 AND slug = $2", country_id, city_slug
        )
        if row is None:
            row = await conn.fetchrow(
                "INSERT INTO cities (country_id, name, slug, created_at, updated_at) "
                "VALUES ($1, $2, $3, now(), now()) RETURNING id",
                country_id,
                item.city_name,
                city_slug,
            )
        city_id = row["id"]
    if item.legal_form_code:
        row = await conn.fetchrow(
            """
            SELECT id FROM legal_forms
            WHERE code = $1 AND (country_id = $2 OR country_id IS NULL)
            ORDER BY country_id NULLS LAST LIMIT 1
            """,
            item.legal_form_code,
            country_id,
        )
        legal_form_id = row["id"] if row else None
    return country_id, city_id, legal_form_id


async def _find_existing_by_source(conn: asyncpg.Connection, source: str, source_id: str):
    return await conn.fetchrow(
        "SELECT id, slug FROM providers WHERE source = $1 AND source_id = $2",
        source,
        source_id,
    )


async def _find_existing_by_domain(
    conn: asyncpg.Connection, website: str | None
) -> asyncpg.Record | None:
    """Match providers whose stored `website` resolves to the same host.

    Strong, safe dedup signal: a shared homepage host is the single best
    indicator that two scraped items describe the same company, across sources.
    """
    host = normalize_host(website)
    if not host:
        return None
    return await conn.fetchrow(
        """
        SELECT id, slug FROM providers
        WHERE website IS NOT NULL
          AND (
                website ILIKE $1
             OR website ILIKE $2
          )
        ORDER BY last_scraped_at DESC NULLS LAST
        LIMIT 1
        """,
        f"%://{host}/%",
        f"%://www.{host}/%",
    )


async def _find_existing_by_public_id(
    conn: asyncpg.Connection, tax_id: str | None, registration_number: str | None
) -> asyncpg.Record | None:
    """Match official registry records by strong public identifiers."""

    if tax_id:
        row = await conn.fetchrow(
            "SELECT id, slug FROM providers WHERE tax_id = $1 LIMIT 1",
            tax_id,
        )
        if row is not None:
            return row
    if registration_number:
        return await conn.fetchrow(
            "SELECT id, slug FROM providers WHERE registration_number = $1 LIMIT 1",
            registration_number,
        )
    return None


async def _find_existing_by_fuzzy(
    conn: asyncpg.Connection, display_name: str, country_id: int | None
) -> asyncpg.Record | None:
    if country_id is None:
        return None
    return await conn.fetchrow(
        """
        SELECT id, slug, similarity(display_name, $1) AS score
        FROM providers
        WHERE country_id = $2
        ORDER BY similarity(display_name, $1) DESC
        LIMIT 1
        """,
        display_name,
        country_id,
    )


async def _make_unique_slug(conn: asyncpg.Connection, base: str) -> str:
    slug = slugify(base)[:140] or uuid.uuid4().hex[:12]
    if not await conn.fetchrow("SELECT 1 FROM providers WHERE slug = $1", slug):
        return slug
    i = 2
    while True:
        candidate = f"{slug}-{i}"
        if not await conn.fetchrow("SELECT 1 FROM providers WHERE slug = $1", candidate):
            return candidate
        i += 1


async def _link_categories(conn: asyncpg.Connection, provider_id: uuid.UUID, slugs: tuple[str, ...]) -> None:
    if not slugs:
        return
    rows = await conn.fetch(
        "SELECT id FROM categories WHERE slug = ANY($1::text[])", list(slugs)
    )
    if not rows:
        return
    await conn.executemany(
        "INSERT INTO provider_categories (provider_id, category_id) VALUES ($1, $2) "
        "ON CONFLICT DO NOTHING",
        [(provider_id, r["id"]) for r in rows],
    )


async def _upsert_one(conn: asyncpg.Connection, item: ScrapedProvider) -> tuple[str, uuid.UUID]:
    """Upsert a single scraped provider. Returns (action, id)."""
    country_id, city_id, legal_form_id = await _ensure_reference(conn, item)

    existing = await _find_existing_by_source(conn, item.source, item.source_id)
    action = "updated"
    if existing is None:
        by_public_id = await _find_existing_by_public_id(
            conn,
            item.tax_id,
            item.registration_number,
        )
        if by_public_id is not None:
            existing = by_public_id
            action = "merged_by_domain"
    if existing is None:
        by_domain = await _find_existing_by_domain(conn, item.website)
        if by_domain is not None:
            existing = by_domain
            action = "merged_by_domain"
    # Official registries with INN/OGRN should not fuzzy-merge into unrelated
    # similarly named companies; the indexed identifiers are the authority.
    has_public_id = bool(item.tax_id or item.registration_number)
    if existing is None and not has_public_id:
        fuzzy = await _find_existing_by_fuzzy(conn, item.display_name, country_id)
        if fuzzy and float(fuzzy["score"]) >= FUZZY_THRESHOLD:
            existing = fuzzy
            action = "merged_by_fuzzy"

    if existing is None:
        pid = uuid.uuid4()
        slug = await _make_unique_slug(conn, item.display_name)
        await conn.execute(
            """
            INSERT INTO providers (
                id, slug, legal_name, display_name, description,
                country_id, city_id, legal_form_id,
                website, email, phone, address,
                registration_number, tax_id, year_founded, employee_count_range,
                source, source_id, source_url, last_scraped_at,
                status, is_claimed, meta, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5,
                $6, $7, $8,
                $9, $10, $11, $12,
                $13, $14, $15, $16,
                $17, $18, $19, now(),
                'published', false, $20::jsonb, now(), now()
            )
            """,
            pid,
            slug,
            item.legal_name or item.display_name,
            item.display_name,
            item.description,
            country_id,
            city_id,
            legal_form_id,
            item.website,
            item.email,
            item.phone,
            item.address,
            item.registration_number,
            item.tax_id,
            item.year_founded,
            item.employee_count_range,
            item.source,
            item.source_id,
            item.source_url,
            json.dumps(item.meta, ensure_ascii=False),
        )
        await _link_categories(conn, pid, item.category_slugs)
        return "inserted", pid

    pid = existing["id"]
    await conn.execute(
        """
        UPDATE providers
        SET display_name = COALESCE(NULLIF($2,''), display_name),
            legal_name   = COALESCE(NULLIF($3,''), legal_name),
            description  = COALESCE(NULLIF($4,''), description),
            country_id   = COALESCE($5, country_id),
            city_id      = COALESCE($6, city_id),
            legal_form_id= COALESCE($7, legal_form_id),
            website      = COALESCE(NULLIF($8,''), website),
            email        = COALESCE(NULLIF($9,''), email),
            phone        = COALESCE(NULLIF($10,''), phone),
            address      = COALESCE(NULLIF($11,''), address),
            registration_number = COALESCE(NULLIF($12,''), registration_number),
            tax_id       = COALESCE(NULLIF($13,''), tax_id),
            year_founded = COALESCE($14, year_founded),
            employee_count_range = COALESCE(NULLIF($15,''), employee_count_range),
            source       = COALESCE(source, $16),
            source_id    = COALESCE(source_id, $17),
            source_url   = COALESCE(source_url, $18),
            meta         = CASE
                              WHEN $19::jsonb = '{}'::jsonb THEN meta
                              ELSE COALESCE(meta, '{}'::jsonb) || $19::jsonb
                           END,
            last_scraped_at = now(),
            updated_at   = now()
        WHERE id = $1
        """,
        pid,
        item.display_name,
        item.legal_name or "",
        item.description or "",
        country_id,
        city_id,
        legal_form_id,
        item.website or "",
        item.email or "",
        item.phone or "",
        item.address or "",
        item.registration_number or "",
        item.tax_id or "",
        item.year_founded,
        item.employee_count_range or "",
        item.source,
        item.source_id,
        item.source_url or "",
        json.dumps(item.meta, ensure_ascii=False),
    )
    await _link_categories(conn, pid, item.category_slugs)
    return action, pid


async def run_spider(spider: Spider, *, limit: int | None = None) -> IngestionStats:
    """Run a spider end-to-end: fetch, dedup, and upsert."""
    from ozzb2b_scraper.http import PoliteFetcher

    cfg = get_settings()
    fetcher = PoliteFetcher()
    stats = IngestionStats()
    dsn = _to_asyncpg_dsn(cfg.database_url)
    conn = await asyncpg.connect(dsn)
    try:
        ctx = SpiderContext(fetcher=fetcher, limit=limit)
        async for item in spider.crawl(ctx):
            stats.fetched += 1
            action, _ = await _upsert_one(conn, item)
            if action == "inserted":
                stats.inserted += 1
            elif action == "updated":
                stats.updated += 1
            elif action == "merged_by_fuzzy":
                stats.merged_by_fuzzy += 1
            elif action == "merged_by_domain":
                stats.merged_by_domain += 1
    finally:
        await fetcher.close()
        await conn.close()
    log.info(
        "scraper.run.done",
        source=spider.source,
        **{
            k: getattr(stats, k)
            for k in (
                "fetched",
                "inserted",
                "updated",
                "merged_by_fuzzy",
                "merged_by_domain",
            )
        },
    )
    return stats


def run_spider_sync(spider: Spider, *, limit: int | None = None) -> IngestionStats:
    return asyncio.run(run_spider(spider, limit=limit))
