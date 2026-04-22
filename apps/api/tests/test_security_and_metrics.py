"""Integration-style tests over `create_app` wiring.

We cover:
- `/metrics` endpoint returns Prometheus text exposition.
- Every response carries the security headers our middleware installs.
- Non-`/metrics` requests bump the `http_requests_total` counter.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from ozzb2b_api.app import create_app
from ozzb2b_api.config import Settings
from ozzb2b_api.observability.metrics import http_requests_total


@pytest.fixture()
def client(settings: Settings) -> Iterator[TestClient]:
    app = create_app(settings)
    with TestClient(app) as c:
        yield c


def test_metrics_endpoint_exposes_counters(client: TestClient) -> None:
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers.get("content-type", "")
    body = resp.text
    # HELP lines for our own counters must be present even before any traffic.
    assert "ozzb2b_api_http_requests_total" in body
    assert "ozzb2b_api_auth_rate_limit_blocked_total" in body


def test_security_headers_present_on_every_response(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    headers = {k.lower(): v for k, v in resp.headers.items()}
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert "referrer-policy" in headers
    assert "content-security-policy" in headers


def test_requests_counter_increments(client: TestClient) -> None:
    before = _count("GET", "/health")
    client.get("/health")
    client.get("/health")
    after = _count("GET", "/health")
    assert after - before >= 2


def _count(method: str, path: str) -> int:
    for metric in http_requests_total.collect():
        for sample in metric.samples:
            if sample.name != "ozzb2b_api_http_requests_total":
                continue
            labels = sample.labels
            if labels.get("method") == method and labels.get("path") == path:
                return int(sample.value)
    return 0
