"""Simple CLI for the scraper.

Examples:
    python -m ozzb2b_scraper.cli list
    python -m ozzb2b_scraper.cli run <source_slug> [--limit N]
    python -m ozzb2b_scraper.cli run-all [--limit N]
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from ozzb2b_scraper.pipeline import IngestionStats, run_spider_sync
from ozzb2b_scraper.spiders import ALL_SPIDERS, DemoDirectorySpider
from ozzb2b_scraper.spiders.ru_fns_sme_registry import iter_records


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
    run_all.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first failed source instead of continuing.",
    )

    prepare_fns = sub.add_parser(
        "prepare-fns-sme",
        help="Convert the official FNS SME XML/ZIP dump into import-ready JSONL batches.",
    )
    prepare_fns.add_argument("input_path", type=Path)
    prepare_fns.add_argument("output_dir", type=Path)
    prepare_fns.add_argument("--limit", type=int, default=10_000)
    prepare_fns.add_argument("--batch-size", type=int, default=1_000)

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
                if args.fail_fast:
                    return 1
                continue
            print(f"{cls.source}: {_format_stats(stats)}")
        return 1 if any_failure else 0

    if args.cmd == "prepare-fns-sme":
        return _prepare_fns_sme(args.input_path, args.output_dir, args.limit, args.batch_size)

    return 2


def _prepare_fns_sme(input_path: Path, output_dir: Path, limit: int, batch_size: int) -> int:
    if limit <= 0:
        raise SystemExit("--limit must be positive")
    if batch_size <= 0:
        raise SystemExit("--batch-size must be positive")

    output_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    batch_no = 0
    current = None
    try:
        for record in iter_records(input_path):
            if written >= limit:
                break
            if written % batch_size == 0:
                if current is not None:
                    current.close()
                batch_no += 1
                current = (output_dir / f"batch-{batch_no:04d}.jsonl").open(
                    "w", encoding="utf-8"
                )
            if current is None:
                raise RuntimeError("FNS SME batch output file was not opened")
            current.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
            written += 1
    finally:
        if current is not None:
            current.close()

    print(f"prepared={written} batches={batch_no} output_dir={output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
