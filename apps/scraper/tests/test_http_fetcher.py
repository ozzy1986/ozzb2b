"""PoliteFetcher body handling against a mocked transport."""

from __future__ import annotations

import gzip

import httpx

from ozzb2b_scraper.http import PoliteFetcher

PAGE = "<html><body>Бухгалтерия для селлеров</body></html>"


def _gzip_handler(request: httpx.Request) -> httpx.Response:
    body = gzip.compress(PAGE.encode("utf-8"))
    return httpx.Response(
        200,
        headers={
            "Content-Encoding": "gzip",
            "Content-Length": str(len(body)),
            "Content-Type": "text/html; charset=utf-8",
        },
        content=body,
    )


async def test_compressed_page_is_decoded_once() -> None:
    fetcher = PoliteFetcher()
    await fetcher.close()
    fetcher._client = httpx.AsyncClient(transport=httpx.MockTransport(_gzip_handler))
    try:
        resp = await fetcher._stream_capped("https://buh.example.ru/")
        assert resp.text == PAGE
        assert "content-encoding" not in resp.headers
    finally:
        await fetcher.close()
