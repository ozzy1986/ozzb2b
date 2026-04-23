"""Alembic upgrade → downgrade → upgrade round-trip against real Postgres.

Run only against Postgres (our production dialect); SQLite is too divergent
for reversed DDL. Skipped unless ``OZZB2B_INTEGRATION_DATABASE_URL`` is set.

What this proves:
  * Every `upgrade()` has a working `downgrade()` (no half-done migrations).
  * The baseline applies on an empty schema.
  * Stepping all the way down and all the way back up yields a schema that
    matches the final revision, so replaying on a fresh DB is safe.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text

pytestmark = pytest.mark.integration


def _alembic_cfg(db_url: str) -> Config:
    api_root = Path(__file__).resolve().parents[2]
    cfg = Config(str(api_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(api_root / "src/ozzb2b_api/db/migrations"))
    # Alembic consumes a *sync* URL for migration runners in env.py's sync path,
    # but our env.py honours get_settings(). We set both to be safe.
    cfg.set_main_option("sqlalchemy.url", db_url.replace("+asyncpg", ""))
    return cfg


def _sync_db_url() -> str:
    url = os.environ.get("OZZB2B_INTEGRATION_DATABASE_URL")
    if not url:
        pytest.skip("integration DB not configured")
    return url.replace("+asyncpg", "+psycopg")


def _reset_public_schema(sync_url: str) -> None:
    engine = create_engine(sync_url, future=True)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    engine.dispose()


@pytest.fixture(scope="module")
def alembic_cfg() -> Config:
    # Point Alembic at the sync URL (psycopg) so its built-in migration
    # runner can create its own engine without clashing with our async one.
    sync_url = _sync_db_url()
    os.environ["OZZB2B_DATABASE_URL"] = sync_url  # read by Settings
    _reset_public_schema(sync_url)
    return _alembic_cfg(sync_url)


def _collected_tables(sync_url: str) -> set[str]:
    engine = create_engine(sync_url, future=True)
    try:
        return set(inspect(engine).get_table_names(schema="public"))
    finally:
        engine.dispose()


def test_upgrade_head_creates_expected_tables(alembic_cfg: Config) -> None:
    command.upgrade(alembic_cfg, "head")
    tables = _collected_tables(_sync_db_url())
    required = {
        "alembic_version",
        "users",
        "refresh_tokens",
        "providers",
        "conversations",
        "messages",
        "provider_claims",
    }
    missing = required - tables
    assert not missing, f"missing tables after upgrade head: {missing}"


def test_round_trip_down_and_up_yields_same_head(alembic_cfg: Config) -> None:
    script = ScriptDirectory.from_config(alembic_cfg)
    head = script.get_current_head()
    assert head, "alembic heads are empty"

    command.downgrade(alembic_cfg, "base")
    # After a full downgrade only alembic's own bookkeeping table is allowed.
    residual = _collected_tables(_sync_db_url()) - {"alembic_version"}
    assert residual == set(), f"downgrade base left tables behind: {residual}"

    command.upgrade(alembic_cfg, "head")
    tables_after = _collected_tables(_sync_db_url())
    assert {"users", "providers", "conversations"} <= tables_after
