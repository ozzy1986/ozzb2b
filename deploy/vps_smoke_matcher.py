#!/usr/bin/env python3
"""Phase 3 smoke: probe /search and print engine + top items per query.

Run on the VPS (or anywhere with outbound HTTPS to api.ozzb2b.com):

    python3 vps_smoke_matcher.py
"""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request

API = "https://api.ozzb2b.com"
QUERIES = ("разработка", "agima", "веб")


def run_query(q: str) -> None:
    url = f"{API}/search?q={urllib.parse.quote(q)}"
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.load(resp)
    print(f"engine={data.get('engine')} total={data.get('total')}")
    for i, item in enumerate(data.get("items", [])[:5], 1):
        print(f"  {i:>2}. {item.get('display_name')}")


def main() -> int:
    for q in QUERIES:
        print(f"=== q={q} ===")
        try:
            run_query(q)
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR: {exc}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
