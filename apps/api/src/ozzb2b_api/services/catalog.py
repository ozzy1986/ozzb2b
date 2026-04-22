"""Catalog queries: providers listing with filters, detail, facet counts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ozzb2b_api.db.models import (
    Category,
    City,
    Country,
    LegalForm,
    Provider,
    ProviderCategory,
    ProviderStatus,
)


@dataclass(frozen=True)
class ProviderFilter:
    query: str | None = None
    category_slugs: tuple[str, ...] = ()
    country_codes: tuple[str, ...] = ()
    city_slugs: tuple[str, ...] = ()
    legal_form_codes: tuple[str, ...] = ()
    limit: int = 24
    offset: int = 0


def _apply_filter(stmt: Select[tuple[Provider]], f: ProviderFilter) -> Select[Any]:
    stmt = stmt.where(Provider.status == ProviderStatus.PUBLISHED)
    if f.country_codes:
        stmt = stmt.join(Provider.country).where(Country.code.in_(f.country_codes))
    if f.city_slugs:
        stmt = stmt.join(Provider.city).where(City.slug.in_(f.city_slugs))
    if f.legal_form_codes:
        stmt = stmt.join(Provider.legal_form).where(LegalForm.code.in_(f.legal_form_codes))
    if f.category_slugs:
        # Provider must be linked to ANY of the given category slugs (OR semantics).
        stmt = stmt.join(Provider.categories).where(Category.slug.in_(f.category_slugs))
    if f.query:
        q = f.query.strip()
        if q:
            like = f"%{q.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Provider.display_name).like(like),
                    func.lower(Provider.legal_name).like(like),
                    func.lower(Provider.description).like(like),
                )
            )
    return stmt


async def list_providers(session: AsyncSession, f: ProviderFilter) -> tuple[int, list[Provider]]:
    base = select(Provider)
    filtered = _apply_filter(base, f).distinct()
    total_stmt = select(func.count()).select_from(filtered.subquery())
    total = (await session.execute(total_stmt)).scalar_one()

    data_stmt = (
        filtered.options(
            selectinload(Provider.country),
            selectinload(Provider.city),
            selectinload(Provider.legal_form),
            selectinload(Provider.categories),
        )
        .order_by(Provider.display_name.asc())
        .limit(f.limit)
        .offset(f.offset)
    )
    rows = (await session.execute(data_stmt)).unique().scalars().all()
    return int(total), list(rows)


async def get_provider_by_slug(session: AsyncSession, slug: str) -> Provider | None:
    stmt = (
        select(Provider)
        .where(Provider.slug == slug, Provider.status == ProviderStatus.PUBLISHED)
        .options(
            selectinload(Provider.country),
            selectinload(Provider.city),
            selectinload(Provider.legal_form),
            selectinload(Provider.categories),
        )
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def list_categories(session: AsyncSession) -> list[Category]:
    stmt = select(Category).order_by(Category.position.asc(), Category.name.asc())
    return list((await session.execute(stmt)).scalars().all())


async def list_countries(session: AsyncSession) -> list[Country]:
    stmt = select(Country).order_by(Country.name.asc())
    return list((await session.execute(stmt)).scalars().all())


async def list_cities(session: AsyncSession, country_code: str | None) -> list[City]:
    stmt = select(City).order_by(City.name.asc())
    if country_code:
        stmt = stmt.join(Country).where(Country.code == country_code)
    return list((await session.execute(stmt)).scalars().all())


async def list_legal_forms(session: AsyncSession, country_code: str | None) -> list[LegalForm]:
    stmt = select(LegalForm).order_by(LegalForm.name.asc())
    if country_code:
        stmt = stmt.join(Country, LegalForm.country_id == Country.id, isouter=True).where(
            or_(Country.code == country_code, LegalForm.country_id.is_(None))
        )
    return list((await session.execute(stmt)).scalars().all())


async def facet_counts(
    session: AsyncSession, f: ProviderFilter
) -> dict[str, list[tuple[str, str, int]]]:
    """Compute facet counts for the current filter set, ignoring the facet's own axis."""
    async def count_axis(axis: str) -> list[tuple[str, str, int]]:
        flt = ProviderFilter(
            query=f.query,
            category_slugs=() if axis == "categories" else f.category_slugs,
            country_codes=() if axis == "countries" else f.country_codes,
            city_slugs=() if axis == "cities" else f.city_slugs,
            legal_form_codes=() if axis == "legal_forms" else f.legal_form_codes,
        )
        base = select(Provider)
        filtered = _apply_filter(base, flt).distinct().subquery()
        if axis == "countries":
            stmt = (
                select(Country.code, Country.name, func.count(filtered.c.id))
                .join(filtered, filtered.c.country_id == Country.id)
                .group_by(Country.code, Country.name)
                .order_by(func.count(filtered.c.id).desc(), Country.name.asc())
            )
        elif axis == "cities":
            stmt = (
                select(City.slug, City.name, func.count(filtered.c.id))
                .join(filtered, filtered.c.city_id == City.id)
                .group_by(City.slug, City.name)
                .order_by(func.count(filtered.c.id).desc(), City.name.asc())
            )
        elif axis == "legal_forms":
            stmt = (
                select(LegalForm.code, LegalForm.name, func.count(filtered.c.id))
                .join(filtered, filtered.c.legal_form_id == LegalForm.id)
                .group_by(LegalForm.code, LegalForm.name)
                .order_by(func.count(filtered.c.id).desc(), LegalForm.name.asc())
            )
        elif axis == "categories":
            stmt = (
                select(Category.slug, Category.name, func.count(func.distinct(filtered.c.id)))
                .join(ProviderCategory, ProviderCategory.category_id == Category.id)
                .join(filtered, filtered.c.id == ProviderCategory.provider_id)
                .group_by(Category.slug, Category.name)
                .order_by(func.count(func.distinct(filtered.c.id)).desc(), Category.name.asc())
            )
        else:
            return []
        rows = (await session.execute(stmt)).all()
        return [(str(r[0]), str(r[1]), int(r[2])) for r in rows]

    return {
        "categories": await count_axis("categories"),
        "countries": await count_axis("countries"),
        "cities": await count_axis("cities"),
        "legal_forms": await count_axis("legal_forms"),
    }
