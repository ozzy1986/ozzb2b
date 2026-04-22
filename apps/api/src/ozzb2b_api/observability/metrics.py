"""Prometheus metrics registry + HTTP middleware.

Design notes:
- A single `CollectorRegistry` is shared across the process so every module
  imports the counters from here rather than redefining them; double
  registration raises in `prometheus_client` so this keeps boot-time safe.
- The middleware measures every HTTP request (path template, method, status)
  and exposes latency via a histogram. The path template is the FastAPI
  route pattern (e.g. `/providers/{slug}`) so high-cardinality IDs don't
  explode the metric.
- `/metrics` itself is always unmetered to avoid infinite loops and to keep
  exporter traffic out of the latency histogram.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

REGISTRY: CollectorRegistry = CollectorRegistry(auto_describe=True)

http_requests_total = Counter(
    "ozzb2b_api_http_requests_total",
    "HTTP requests handled by the API, labelled by method/path/status.",
    labelnames=("method", "path", "status"),
    registry=REGISTRY,
)

http_request_duration_seconds = Histogram(
    "ozzb2b_api_http_request_duration_seconds",
    "Latency of API responses, per route template and method.",
    labelnames=("method", "path"),
    registry=REGISTRY,
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)

events_published_total = Counter(
    "ozzb2b_api_events_published_total",
    "Product events published to Redis Streams by the API.",
    labelnames=("event_type", "outcome"),
    registry=REGISTRY,
)

matcher_calls_total = Counter(
    "ozzb2b_api_matcher_calls_total",
    "Matcher gRPC calls made by the API.",
    labelnames=("outcome",),
    registry=REGISTRY,
)

auth_rate_limit_blocked_total = Counter(
    "ozzb2b_api_auth_rate_limit_blocked_total",
    "Auth attempts rejected by the rate limiter.",
    labelnames=("endpoint", "scope"),
    registry=REGISTRY,
)


def metrics_response() -> Response:
    return StarletteResponse(
        generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST,
    )


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Records latency + count per resolved route template.

    We deliberately use the `route.path` (e.g. `/providers/{slug}`) rather
    than the raw `request.url.path` so path parameters don't blow out
    cardinality (one series per provider id is poison).
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path == "/metrics":
            return await call_next(request)

        started = time.perf_counter()
        response: Response
        try:
            response = await call_next(request)
        except Exception:
            # Let errors propagate; we still want one datapoint for them.
            elapsed = time.perf_counter() - started
            route = _route_template(request)
            http_requests_total.labels(request.method, route, "500").inc()
            http_request_duration_seconds.labels(request.method, route).observe(elapsed)
            raise

        elapsed = time.perf_counter() - started
        route = _route_template(request)
        http_requests_total.labels(
            request.method, route, str(response.status_code)
        ).inc()
        http_request_duration_seconds.labels(request.method, route).observe(elapsed)
        return response


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    if route is not None:
        path = getattr(route, "path", None)
        if isinstance(path, str) and path:
            return path
    # Fallback: use the raw path but truncate long parameters so we
    # don't create unbounded series. This should rarely trigger.
    raw = request.url.path
    return raw[:120] if len(raw) > 120 else raw
