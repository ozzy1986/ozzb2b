"""Meilisearch client wrapper."""

from __future__ import annotations

from functools import lru_cache

import httpx
import meilisearch

from ozzb2b_api.config import get_settings


@lru_cache(maxsize=1)
def get_meilisearch() -> meilisearch.Client:
    """Return a singleton Meilisearch client."""
    settings = get_settings()
    return meilisearch.Client(settings.meilisearch_url, settings.meilisearch_key)


async def ping_meilisearch() -> bool:
    """Return True iff Meilisearch is reachable and healthy."""
    settings = get_settings()
    url = f"{settings.meilisearch_url.rstrip('/')}/health"
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(url)
            return resp.status_code == 200 and resp.json().get("status") == "available"
    except Exception:
        return False
