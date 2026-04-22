"""Tests for the robots.txt cache."""

from __future__ import annotations

from dataclasses import dataclass

import httpx
import pytest

from ozzb2b_scraper.robots import RobotsCache


@dataclass
class _FakeResponse:
    status_code: int
    text: str


class _FakeHttpxClient:
    def __init__(self, responses: dict[str, _FakeResponse]) -> None:
        self._responses = responses
        self.calls: list[str] = []

    async def get(self, url: str) -> _FakeResponse:
        self.calls.append(url)
        if url in self._responses:
            return self._responses[url]
        return _FakeResponse(status_code=404, text="")


@pytest.mark.asyncio
async def test_allows_when_robots_disallow_does_not_cover_path() -> None:
    client = _FakeHttpxClient(
        {
            "https://example.com/robots.txt": _FakeResponse(
                status_code=200,
                text="User-agent: *\nDisallow: /private/\n",
            )
        }
    )
    cache = RobotsCache(client, user_agent="ozzb2b-scraper/test")  # type: ignore[arg-type]
    assert await cache.is_allowed("https://example.com/") is True
    assert await cache.is_allowed("https://example.com/public/page") is True


@pytest.mark.asyncio
async def test_blocks_when_robots_disallows_matching_path() -> None:
    client = _FakeHttpxClient(
        {
            "https://example.com/robots.txt": _FakeResponse(
                status_code=200,
                text="User-agent: *\nDisallow: /private/\n",
            )
        }
    )
    cache = RobotsCache(client, user_agent="ozzb2b-scraper/test")  # type: ignore[arg-type]
    assert await cache.is_allowed("https://example.com/private/thing") is False


@pytest.mark.asyncio
async def test_caches_robots_per_host() -> None:
    client = _FakeHttpxClient(
        {
            "https://example.com/robots.txt": _FakeResponse(
                status_code=200, text="User-agent: *\nAllow: /\n"
            )
        }
    )
    cache = RobotsCache(client, user_agent="ozzb2b-scraper/test")  # type: ignore[arg-type]
    await cache.is_allowed("https://example.com/a")
    await cache.is_allowed("https://example.com/b")
    await cache.is_allowed("https://example.com/c")
    assert client.calls.count("https://example.com/robots.txt") == 1


@pytest.mark.asyncio
async def test_allow_on_404_or_transport_error() -> None:
    class _ErroringClient:
        async def get(self, url: str) -> _FakeResponse:
            raise httpx.ConnectError("dns down")

    cache = RobotsCache(_ErroringClient(), user_agent="ozzb2b-scraper/test")  # type: ignore[arg-type]
    assert await cache.is_allowed("https://down.example/anywhere") is True

    client = _FakeHttpxClient({})  # Any robots.txt -> 404
    cache2 = RobotsCache(client, user_agent="ozzb2b-scraper/test")  # type: ignore[arg-type]
    assert await cache2.is_allowed("https://missing.example/page") is True


@pytest.mark.asyncio
async def test_allow_when_url_is_not_parsable() -> None:
    client = _FakeHttpxClient({})
    cache = RobotsCache(client, user_agent="ozzb2b-scraper/test")  # type: ignore[arg-type]
    # Relative URL -> no scheme/host -> can't enforce robots, must allow.
    assert await cache.is_allowed("/relative/path") is True
