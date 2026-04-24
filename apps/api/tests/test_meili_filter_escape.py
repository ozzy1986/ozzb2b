"""Meilisearch filter DSL escape — defends against filter injection."""

from __future__ import annotations

import pytest

from ozzb2b_api.services.search import (
    SearchQuery,
    _escape_meili_value,
    _meili_filter_expression,
)


def test_escape_doubles_single_quotes() -> None:
    assert _escape_meili_value("plain") == "plain"
    assert _escape_meili_value("it's") == "it''s"
    assert _escape_meili_value("a' OR 1=1 --") == "a'' OR 1=1 --"


def test_escape_rejects_control_characters() -> None:
    for value in ("foo\x00bar", "foo\rbar", "foo\nbar"):
        with pytest.raises(ValueError):
            _escape_meili_value(value)


def test_filter_expression_quotes_each_value() -> None:
    q = SearchQuery(
        q="any",
        category_slugs=("it",),
        country_codes=("RU", "BY"),
        city_slugs=("moscow",),
        legal_form_codes=("OOO",),
    )
    parts = _meili_filter_expression(q)
    assert "status = 'published'" == parts[0]
    assert any("category_slugs = 'it'" in p for p in parts)
    assert any("country_code = 'RU'" in p and "country_code = 'BY'" in p for p in parts)


def test_filter_expression_handles_quoted_user_input_safely() -> None:
    q = SearchQuery(q="anything", category_slugs=("foo' OR '1'='1",))
    parts = _meili_filter_expression(q)
    cat_part = next(p for p in parts if "category_slugs" in p)
    # The injected single quote must have been doubled, not interpreted.
    assert "''" in cat_part
    assert "'1'='1'" not in cat_part
