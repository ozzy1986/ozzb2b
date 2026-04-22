"""Security response-headers middleware.

Sets a conservative set of headers on every API response. The API serves
JSON only, so the CSP is extremely restrictive (`default-src 'none'`): a
compromised response shouldn't execute anything, even when viewed directly
in a browser.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ozzb2b_api.config import Settings, get_settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Callable[..., Awaitable[Response]], settings: Settings | None = None):
        super().__init__(app)
        self._settings = settings or get_settings()

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        self._apply(response)
        return response

    def _apply(self, response: Response) -> None:
        headers = response.headers
        headers.setdefault("X-Content-Type-Options", "nosniff")
        headers.setdefault("X-Frame-Options", "DENY")
        headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        headers.setdefault(
            "Content-Security-Policy",
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
        )
        if self._settings.is_production:
            max_age = max(0, self._settings.hsts_max_age_seconds)
            headers.setdefault(
                "Strict-Transport-Security",
                f"max-age={max_age}; includeSubDomains",
            )
