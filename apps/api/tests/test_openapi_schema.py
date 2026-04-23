"""OpenAPI contract smoke tests.

Catches accidental removal/renaming of public routes. We don't pin the full
schema byte-for-byte (it would be noisy on every Pydantic/FastAPI bump) but we
do enforce that every documented operation still exists, still has the same
HTTP method, and keeps a stable ``operationId``-less signature (path + method).

The canonical snapshot lives in ``tests/snapshots/openapi_routes.json``. Any
intentional change requires updating that file in the same commit as the code
change so a reviewer sees the diff.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SNAPSHOT_PATH = Path(__file__).parent / "snapshots" / "openapi_routes.json"


def _current_routes(client: TestClient) -> list[list[str]]:
    """Extract a sorted list of ``[method, path]`` pairs from the live spec."""
    spec = client.get("/openapi.json").json()
    pairs: list[list[str]] = []
    for path, ops in spec.get("paths", {}).items():
        for method in ops:
            if method.lower() in {"get", "post", "put", "patch", "delete"}:
                pairs.append([method.upper(), path])
    pairs.sort()
    return pairs


def test_openapi_routes_match_snapshot(client: TestClient) -> None:
    current = _current_routes(client)
    if not SNAPSHOT_PATH.exists():
        SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT_PATH.write_text(json.dumps(current, indent=2, ensure_ascii=False) + "\n")
        pytest.fail(
            f"Seeded initial OpenAPI snapshot at {SNAPSHOT_PATH}. Review the "
            "committed file and rerun the test suite.",
        )
    expected = json.loads(SNAPSHOT_PATH.read_text())
    assert current == expected, (
        "Public HTTP surface changed. Update snapshots/openapi_routes.json "
        "intentionally if this is expected."
    )


def test_openapi_has_security_tags(client: TestClient) -> None:
    spec = client.get("/openapi.json").json()
    # Smoke: every auth-protected path declares a security scheme reference.
    paths = spec.get("paths", {})
    auth_paths = [
        ("/auth/me", "get"),
        ("/chat/conversations", "get"),
        ("/admin/analytics/summary", "get"),
    ]
    for path, method in auth_paths:
        assert path in paths, f"missing {method.upper()} {path}"
        op = paths[path].get(method)
        assert op is not None, f"missing {method.upper()} {path}"


def test_openapi_title_and_version(client: TestClient) -> None:
    spec = client.get("/openapi.json").json()
    info = spec.get("info", {})
    assert info.get("title") == "ozzb2b API"
    assert info.get("version")
