#!/usr/bin/env python3
"""Phase 4 smoke: exercise /search and /providers/{slug}, then check that the
ClickHouse `events` table sees the produced events.

Run on the VPS (ClickHouse is exposed on 127.0.0.1:8123 there):

    python3 vps_smoke_events.py
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request

API = "https://api.ozzb2b.com"
CH = "http://127.0.0.1:8123"


def hit(url: str) -> int:
    with urllib.request.urlopen(url, timeout=10) as resp:
        return resp.status


def ch(sql: str) -> str:
    req = urllib.request.Request(
        CH + "/?database=ozzb2b",
        data=sql.encode("utf-8"),
        headers={"Content-Type": "text/plain; charset=utf-8"},
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.read().decode("utf-8")


def main() -> int:
    # Drive traffic that should produce events.
    queries = ["разработка", "agima", "веб"]
    for q in queries:
        status = hit(f"{API}/search?q={urllib.parse.quote(q)}")
        print(f"search q={q!r} status={status}")
    for slug in ("agima", "simbirsoft"):
        status = hit(f"{API}/providers/{slug}")
        print(f"provider {slug} status={status}")

    # Events are fire-and-forget; give the consumer a moment to flush.
    time.sleep(2)

    print("--- counts per type (last 1 day) ---")
    print(
        ch(
            "SELECT event_type, count() FROM events "
            "WHERE occurred_at >= now() - INTERVAL 1 DAY "
            "GROUP BY event_type ORDER BY event_type FORMAT JSONEachRow"
        )
    )

    print("--- top searches (last 1 day) ---")
    print(
        ch(
            "SELECT JSONExtractString(properties, 'query') AS q, count() "
            "FROM events WHERE event_type='search_performed' "
            "AND occurred_at >= now() - INTERVAL 1 DAY "
            "GROUP BY q ORDER BY count() DESC LIMIT 10 FORMAT JSONEachRow"
        )
    )

    print("--- top providers (last 1 day) ---")
    print(
        ch(
            "SELECT JSONExtractString(properties, 'slug') AS slug, count() "
            "FROM events WHERE event_type='provider_viewed' "
            "AND occurred_at >= now() - INTERVAL 1 DAY "
            "GROUP BY slug ORDER BY count() DESC LIMIT 10 FORMAT JSONEachRow"
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
