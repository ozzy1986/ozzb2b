"""Unit tests for search filter construction."""

from __future__ import annotations

from ozzb2b_api.services.search import SearchQuery, _meili_filter_expression


def test_meili_filter_minimal() -> None:
    q = SearchQuery(q="data")
    expr = _meili_filter_expression(q)
    assert expr == ["status = 'published'"]


def test_meili_filter_combines_axes() -> None:
    q = SearchQuery(
        q="data",
        category_slugs=("it", "data-analytics"),
        country_codes=("PL",),
        city_slugs=("warsaw",),
        legal_form_codes=("SP_Z_O_O",),
    )
    expr = _meili_filter_expression(q)
    assert expr[0] == "status = 'published'"
    combined = " AND ".join(expr)
    assert "category_slugs = 'it'" in combined
    assert "category_slugs = 'data-analytics'" in combined
    assert "country_code = 'PL'" in combined
    assert "city_slug = 'warsaw'" in combined
    assert "legal_form_code = 'SP_Z_O_O'" in combined
