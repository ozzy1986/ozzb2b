"""Read-side analytics queries over ClickHouse.

All functions degrade gracefully: when ClickHouse is unreachable we return
empty results so the admin UI can still render.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog

from ozzb2b_api.clients.clickhouse import (
    ClickHouseUnavailableError,
    query_json,
)

log = structlog.get_logger("ozzb2b_api.services.analytics")


@dataclass(frozen=True)
class EventTypeCount:
    event_type: str
    count: int


@dataclass(frozen=True)
class TopQuery:
    query: str
    count: int


@dataclass(frozen=True)
class TopProvider:
    provider_id: str
    display_name: str
    slug: str
    count: int


def _window_clause(days: int) -> str:
    """Produce an inlined, safe WHERE clause for the last N days."""
    d = max(1, min(days, 365))
    return f"occurred_at >= now() - INTERVAL {d} DAY"


async def event_type_counts(days: int) -> list[EventTypeCount]:
    # nosec B608 - the only interpolated value is produced by _window_clause,
    # which clamps an int to [1, 365]; there is no user-controlled string here.
    sql = f"""
        SELECT
            event_type AS event_type,
            count() AS cnt
        FROM events
        WHERE {_window_clause(days)}
        GROUP BY event_type
        ORDER BY cnt DESC
    """  # nosec B608
    try:
        rows = await query_json(sql)
    except ClickHouseUnavailableError as exc:
        log.warning("analytics.clickhouse_unavailable", err=str(exc))
        return []
    return [
        EventTypeCount(event_type=str(r.get("event_type") or ""), count=int(r.get("cnt") or 0))
        for r in rows
    ]


async def top_searches(days: int, limit: int) -> list[TopQuery]:
    # nosec B608 - interpolated values are int-only (_window_clause + clamped
    # LIMIT via max/min); no user string reaches the query.
    sql = f"""
        SELECT
            JSONExtractString(properties, 'query') AS query,
            count() AS cnt
        FROM events
        WHERE event_type = 'search_performed' AND {_window_clause(days)}
        GROUP BY query
        HAVING length(query) > 0
        ORDER BY cnt DESC
        LIMIT {max(1, min(limit, 200))}
    """  # nosec B608
    try:
        rows = await query_json(sql)
    except ClickHouseUnavailableError as exc:
        log.warning("analytics.clickhouse_unavailable", err=str(exc))
        return []
    return [
        TopQuery(query=str(r.get("query") or ""), count=int(r.get("cnt") or 0))
        for r in rows
    ]


async def top_providers(days: int, limit: int) -> list[TopProvider]:
    # nosec B608 - same rationale as top_searches: interpolated values are
    # strictly int-bounded and never carry user-provided strings.
    sql = f"""
        SELECT
            JSONExtractString(properties, 'provider_id') AS provider_id,
            any(JSONExtractString(properties, 'display_name')) AS display_name,
            any(JSONExtractString(properties, 'slug')) AS slug,
            count() AS cnt
        FROM events
        WHERE event_type = 'provider_viewed' AND {_window_clause(days)}
        GROUP BY provider_id
        HAVING length(provider_id) > 0
        ORDER BY cnt DESC
        LIMIT {max(1, min(limit, 200))}
    """  # nosec B608
    try:
        rows: list[dict[str, Any]] = await query_json(sql)
    except ClickHouseUnavailableError as exc:
        log.warning("analytics.clickhouse_unavailable", err=str(exc))
        return []
    return [
        TopProvider(
            provider_id=str(r.get("provider_id") or ""),
            display_name=str(r.get("display_name") or ""),
            slug=str(r.get("slug") or ""),
            count=int(r.get("cnt") or 0),
        )
        for r in rows
    ]
