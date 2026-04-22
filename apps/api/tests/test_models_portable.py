"""Basic model sanity tests on the portable subset (SQLite-compatible)."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from ozzb2b_api.db.models import Category, City, Country, LegalForm


@pytest.mark.asyncio
async def test_country_city_roundtrip(db_session) -> None:
    pl = Country(code="PL", name="Poland", slug="poland")
    db_session.add(pl)
    await db_session.flush()
    warsaw = City(country_id=pl.id, name="Warsaw", slug="warsaw")
    db_session.add(warsaw)
    await db_session.flush()

    fetched = (
        await db_session.execute(select(City).where(City.slug == "warsaw"))
    ).scalar_one()
    assert fetched.country_id == pl.id
    assert fetched.name == "Warsaw"


@pytest.mark.asyncio
async def test_category_hierarchy(db_session) -> None:
    root = Category(slug="it", name="IT")
    db_session.add(root)
    await db_session.flush()
    child = Category(slug="software-development", name="Software development", parent_id=root.id)
    db_session.add(child)
    await db_session.flush()
    fetched = (
        await db_session.execute(select(Category).where(Category.slug == "software-development"))
    ).scalar_one()
    assert fetched.parent_id == root.id


@pytest.mark.asyncio
async def test_legal_form_country_scoped(db_session) -> None:
    de = Country(code="DE", name="Germany", slug="germany")
    db_session.add(de)
    await db_session.flush()
    lf = LegalForm(country_id=de.id, code="GMBH", name="GmbH", slug="gmbh")
    db_session.add(lf)
    await db_session.flush()
    fetched = (
        await db_session.execute(select(LegalForm).where(LegalForm.code == "GMBH"))
    ).scalar_one()
    assert fetched.country_id == de.id
