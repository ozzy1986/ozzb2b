"""Unit tests for the public-HTML extractor.

The extractor must:
- Pull description from og:description or meta[name=description].
- Pick up the first valid mailto: / tel: links.
- Never crash on malformed input.
- Refuse obviously-short / junk descriptions.
"""

from __future__ import annotations

from ozzb2b_scraper.extractors import extract_public_facts


def test_extract_from_og_and_contacts() -> None:
    html = """
    <html><head>
      <meta property="og:description" content="  Custom software   development   studio.   ">
      <meta name="description" content="shorter meta">
    </head><body>
      <a href="mailto:hello@example.com">Write us</a>
      <a href="tel:+7 495 000 00 00">Call</a>
    </body></html>
    """
    facts = extract_public_facts(html)
    assert facts.description == "Custom software development studio."
    assert facts.email == "hello@example.com"
    assert facts.phone == "+7 495 000 00 00"


def test_extract_prefers_og_over_meta() -> None:
    html = """
    <html><head>
      <meta name="description" content="This meta description is long enough to be kept by extractor">
      <meta property="og:description" content="This OG description is long enough and preferred over meta">
    </head></html>
    """
    facts = extract_public_facts(html)
    assert facts.description is not None
    assert facts.description.startswith("This OG description")


def test_extract_falls_back_to_meta_when_no_og() -> None:
    html = """
    <html><head>
      <meta name="description" content="We are a company that builds enterprise systems">
    </head></html>
    """
    facts = extract_public_facts(html)
    assert facts.description == "We are a company that builds enterprise systems"


def test_extract_rejects_too_short_description() -> None:
    html = '<html><head><meta name="description" content="Hi"></head></html>'
    facts = extract_public_facts(html)
    assert facts.description is None


def test_extract_ignores_invalid_mailto_and_short_tel() -> None:
    html = """
    <html><body>
      <a href="mailto:not-an-email">bad</a>
      <a href="mailto:ok@site.org">ok</a>
      <a href="tel:123">too short</a>
      <a href="tel:+7 812 000 00 00">good</a>
    </body></html>
    """
    facts = extract_public_facts(html)
    assert facts.email == "ok@site.org"
    assert facts.phone == "+7 812 000 00 00"


def test_extract_is_safe_on_empty_html() -> None:
    facts = extract_public_facts("")
    assert facts.description is None
    assert facts.email is None
    assert facts.phone is None


def test_extract_is_safe_on_broken_html() -> None:
    facts = extract_public_facts("<html><head><meta ")
    # Should not raise and should not fabricate data.
    assert facts.email is None
    assert facts.phone is None
