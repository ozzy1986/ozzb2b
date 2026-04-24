"""Minimal async ClickHouse HTTP client.

Covers only what the API needs — SELECT queries returning JSON — so we don't
pull in an extra dependency. The admin-facing analytics endpoints use this
client; any unavailability is surfaced as `ClickHouseUnavailableError` and
the endpoints must return a friendly degraded response.
"""

from __future__ import annotations

import asyncio
import json
import secrets
from dataclasses import dataclass
from typing import Any

import httpx
import structlog

from ozzb2b_api.config import Settings, get_settings

log = structlog.get_logger("ozzb2b_api.clients.clickhouse")


class ClickHouseError(Exception):
    """Base class for ClickHouse client errors."""


class ClickHouseUnavailableError(ClickHouseError):
    """ClickHouse could not be reached within the configured timeout."""


@dataclass(frozen=True)
class ClickHouseConfig:
    url: str
    user: str
    password: str
    database: str
    timeout_s: float


def _config_from_settings(settings: Settings | None) -> ClickHouseConfig:
    cfg = settings or get_settings()
    return ClickHouseConfig(
        url=cfg.clickhouse_url.rstrip("/"),
        user=cfg.clickhouse_user,
        password=cfg.clickhouse_password,
        database=cfg.clickhouse_database,
        timeout_s=max(0.1, cfg.clickhouse_timeout_ms / 1000.0),
    )


async def query_json(
    sql: str,
    *,
    params: dict[str, Any] | None = None,
    settings: Settings | None = None,
) -> list[dict[str, Any]]:
    """Run a SELECT query and return rows as dicts.

    Uses `FORMAT JSONEachRow` so we never parse the ClickHouse text format.
    Parameters are passed as `param_<name>` query string values which maps to
    `{name:Type}` placeholders in the SQL — keeping us safe from injection.
    """
    cfg = _config_from_settings(settings)
    qparams = {"database": cfg.database}
    for k, v in (params or {}).items():
        qparams[f"param_{k}"] = str(v)

    # Retry transient transport-level failures with capped exponential
    # backoff + jitter (3 attempts: ~100ms, ~200ms, give up). HTTP 5xx
    # responses are not retried here because ClickHouse can return 500 for
    # legitimate query errors — surfacing them is the right behaviour.
    delay = 0.1
    last_exc: Exception | None = None
    resp: httpx.Response | None = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=cfg.timeout_s) as client:
                resp = await client.post(
                    cfg.url,
                    params=qparams,
                    content=sql + "\nFORMAT JSONEachRow",
                    headers={"Content-Type": "text/plain; charset=utf-8"},
                    auth=(cfg.user, cfg.password),
                )
            break
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout) as exc:
            last_exc = exc
            if attempt == 2:
                raise ClickHouseUnavailableError(str(exc)) from exc
            jitter = secrets.SystemRandom().uniform(0, delay)
            await asyncio.sleep(delay + jitter)
            delay *= 2

    if resp is None:
        raise ClickHouseUnavailableError(str(last_exc) if last_exc else "unknown")

    if resp.status_code >= 400:
        raise ClickHouseError(
            f"clickhouse query failed (status={resp.status_code}): {resp.text[:200]}"
        )

    rows: list[dict[str, Any]] = []
    for line in resp.text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            log.warning("clickhouse.bad_row", preview=line[:200])
    return rows
