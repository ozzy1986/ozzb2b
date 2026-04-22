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
    # alembic.ini sits at the repo/app root (/app in the container).
    ini = Path(__file__).resolve().parents[3] / "alembic.ini"
    cfg = Config(str(ini))
    cfg.set_main_option("script_location", str(Path(__file__).resolve().parent / "migrations"))
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
