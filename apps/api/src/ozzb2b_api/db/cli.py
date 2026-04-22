"""Tiny CLI helpers for migrations and seeding.

Examples:

    python -m ozzb2b_api.db.cli migrate
    python -m ozzb2b_api.db.cli seed
    python -m ozzb2b_api.db.cli claim-provider <provider-slug> <user-email>
    python -m ozzb2b_api.db.cli unclaim-provider <provider-slug>
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


def reindex() -> None:
    from ozzb2b_api.db.session import get_sessionmaker
    from ozzb2b_api.services.indexer import reindex_all

    async def _run() -> None:
        sessionmaker = get_sessionmaker()
        async with sessionmaker() as session:
            await reindex_all(session)

    asyncio.run(_run())


def claim_provider(provider_slug: str, user_email: str) -> int:
    """Link a provider's ownership to an existing user for testing/admin use."""
    from sqlalchemy import select

    from ozzb2b_api.db.models import Provider, User
    from ozzb2b_api.db.session import get_sessionmaker

    async def _run() -> int:
        sessionmaker = get_sessionmaker()
        async with sessionmaker() as session:
            user = (
                await session.execute(select(User).where(User.email == user_email))
            ).scalar_one_or_none()
            if user is None:
                print(f"user not found: {user_email}", file=sys.stderr)
                return 2
            provider = (
                await session.execute(select(Provider).where(Provider.slug == provider_slug))
            ).scalar_one_or_none()
            if provider is None:
                print(f"provider not found: {provider_slug}", file=sys.stderr)
                return 2
            provider.claimed_by_user_id = user.id
            await session.commit()
            print(
                f"provider '{provider.slug}' ({provider.display_name}) "
                f"is now claimed by {user.email} ({user.id})"
            )
            return 0

    return asyncio.run(_run())


def unclaim_provider(provider_slug: str) -> int:
    """Drop the ownership link on a provider."""
    from sqlalchemy import select

    from ozzb2b_api.db.models import Provider
    from ozzb2b_api.db.session import get_sessionmaker

    async def _run() -> int:
        sessionmaker = get_sessionmaker()
        async with sessionmaker() as session:
            provider = (
                await session.execute(select(Provider).where(Provider.slug == provider_slug))
            ).scalar_one_or_none()
            if provider is None:
                print(f"provider not found: {provider_slug}", file=sys.stderr)
                return 2
            provider.claimed_by_user_id = None
            await session.commit()
            print(f"provider '{provider.slug}' is now unclaimed")
            return 0

    return asyncio.run(_run())


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print(
            "usage: python -m ozzb2b_api.db.cli "
            "[migrate|seed|reindex|claim-provider <slug> <email>|unclaim-provider <slug>]",
            file=sys.stderr,
        )
        return 2
    cmd = args[0]
    if cmd == "migrate":
        migrate_up()
        return 0
    if cmd == "seed":
        seed()
        return 0
    if cmd == "reindex":
        reindex()
        return 0
    if cmd == "claim-provider":
        if len(args) != 3:
            print(
                "usage: python -m ozzb2b_api.db.cli claim-provider <slug> <email>",
                file=sys.stderr,
            )
            return 2
        return claim_provider(args[1], args[2])
    if cmd == "unclaim-provider":
        if len(args) != 2:
            print(
                "usage: python -m ozzb2b_api.db.cli unclaim-provider <slug>",
                file=sys.stderr,
            )
            return 2
        return unclaim_provider(args[1])
    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
