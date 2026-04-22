"""Simple CLI for the scraper:

    python -m ozzb2b_scraper.cli run <source_slug> [--limit N]
"""

from __future__ import annotations

import argparse
import sys

from ozzb2b_scraper.pipeline import run_spider_sync
from ozzb2b_scraper.spiders import DemoDirectorySpider, RuOutsourcingSeedSpider


SPIDERS = {
    DemoDirectorySpider.source: DemoDirectorySpider,
    RuOutsourcingSeedSpider.source: RuOutsourcingSeedSpider,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser("ozzb2b-scraper")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="Run a spider by its source slug")
    run.add_argument("source_slug", choices=list(SPIDERS.keys()))
    run.add_argument("--limit", type=int, default=None)
    args = parser.parse_args(argv)
    if args.cmd == "run":
        cls = SPIDERS[args.source_slug]
        stats = run_spider_sync(cls(), limit=args.limit)
        print(
            "fetched=%d inserted=%d updated=%d merged_by_fuzzy=%d"
            % (stats.fetched, stats.inserted, stats.updated, stats.merged_by_fuzzy)
        )
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
