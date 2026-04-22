"""Simple CLI for the scraper.

Examples:
    python -m ozzb2b_scraper.cli list
    python -m ozzb2b_scraper.cli run <source_slug> [--limit N]
    python -m ozzb2b_scraper.cli run-all [--limit N]
"""

from __future__ import annotations

import argparse
import sys

from ozzb2b_scraper.pipeline import IngestionStats, run_spider_sync
from ozzb2b_scraper.spiders import ALL_SPIDERS, DemoDirectorySpider


SPIDERS = {cls.source: cls for cls in ALL_SPIDERS}


def _format_stats(stats: IngestionStats) -> str:
    return (
        "fetched=%d inserted=%d updated=%d merged_by_fuzzy=%d merged_by_domain=%d"
        % (
            stats.fetched,
            stats.inserted,
            stats.updated,
            stats.merged_by_fuzzy,
            stats.merged_by_domain,
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser("ozzb2b-scraper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List registered spider source slugs")

    run = sub.add_parser("run", help="Run a spider by its source slug")
    run.add_argument("source_slug", choices=list(SPIDERS.keys()))
    run.add_argument("--limit", type=int, default=None)

    run_all = sub.add_parser(
        "run-all", help="Run every real (non-demo) spider sequentially"
    )
    run_all.add_argument("--limit", type=int, default=None)

    args = parser.parse_args(argv)

    if args.cmd == "list":
        for slug in sorted(SPIDERS):
            print(slug)
        return 0

    if args.cmd == "run":
        cls = SPIDERS[args.source_slug]
        stats = run_spider_sync(cls(), limit=args.limit)
        print(_format_stats(stats))
        return 0

    if args.cmd == "run-all":
        any_failure = False
        for cls in ALL_SPIDERS:
            if cls is DemoDirectorySpider:
                continue
            try:
                stats = run_spider_sync(cls(), limit=args.limit)
            except Exception as exc:  # noqa: BLE001 - CLI surface; continue across sources
                print(f"{cls.source}: FAILED: {exc}", file=sys.stderr)
                any_failure = True
                continue
            print(f"{cls.source}: {_format_stats(stats)}")
        return 1 if any_failure else 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
