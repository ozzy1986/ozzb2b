"""Unit tests for the catalog filter parsing / provider filter construction."""

from __future__ import annotations

from ozzb2b_api.services.catalog import ProviderFilter


def test_provider_filter_defaults() -> None:
    f = ProviderFilter()
    assert f.query is None
    assert f.category_slugs == ()
    assert f.limit == 24
    assert f.offset == 0


def test_provider_filter_is_frozen() -> None:
    f = ProviderFilter(limit=10)
    try:
        f.limit = 20  # type: ignore[misc]
    except Exception:
        return
    raise AssertionError("ProviderFilter should be immutable")
