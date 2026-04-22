"""Phase 4 admin analytics smoke.

Runs the exact service functions the /admin/analytics/* endpoints use, so we
validate both the ClickHouse schema and the Python query layer on prod data
without needing an admin session.
"""

from __future__ import annotations

import asyncio

from ozzb2b_api.services import analytics


async def main() -> None:
    summary = await analytics.event_type_counts(days=7)
    print("summary (7d):")
    for item in summary:
        print(f"  {item.event_type:>20}  {item.count}")

    top_q = await analytics.top_searches(days=7, limit=10)
    print("top searches (7d):")
    for q in top_q:
        print(f"  {q.count:>4}  {q.query!r}")

    top_p = await analytics.top_providers(days=7, limit=10)
    print("top providers (7d):")
    for p in top_p:
        print(f"  {p.count:>4}  {p.slug}  ({p.display_name})")


if __name__ == "__main__":
    asyncio.run(main())
