"""Tiny CLI helpers for migrations and seeding.

Examples:

    python -m ozzb2b_api.db.cli migrate
    python -m ozzb2b_api.db.cli seed
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config


def _alembic_config() -> Config:
    """Build an Alembic Config that works both from the source tree and inside Docker.

    We point `script_location` at the installed package to avoid relying on where
    `alembic.ini` sits at runtime.
    """
    migrations_dir = Path(__file__).resolve().parent / "migrations"
    # Prefer a local alembic.ini for logger config; fall back to a clean Config().
    candidates = [
        Path.cwd() / "alembic.ini",
        Path(__file__).resolve().parents[3] / "alembic.ini",
        Path("/app/alembic.ini"),
    ]
    ini_path = next((p for p in candidates if p.is_file()), None)
    cfg = Config(str(ini_path)) if ini_path is not None else Config()
    cfg.set_main_option("script_location", str(migrations_dir))
    return cfg


def migrate_up() -> None:
    command.upgrade(_alembic_config(), "head")


def seed() -> None:
    from ozzb2b_api.db.seed import _main

    asyncio.run(_main())


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("usage: python -m ozzb2b_api.db.cli [migrate|seed]", file=sys.stderr)
        return 2
    cmd = args[0]
    if cmd == "migrate":
        migrate_up()
        return 0
    if cmd == "seed":
        seed()
        return 0
    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
