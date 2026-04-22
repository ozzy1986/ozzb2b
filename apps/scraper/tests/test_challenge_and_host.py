"""Tests for challenge detection and host normalization helpers."""

from __future__ import annotations

from ozzb2b_scraper.http import looks_like_challenge
from ozzb2b_scraper.pipeline import normalize_host


def test_challenge_detects_cloudflare_markup() -> None:
    html = """
    <html><head><title>Just a moment…</title>
      <script src="/cdn-cgi/challenge-platform/h/b/orchestrate/main.js"></script>
    </head><body></body></html>
    """
    assert looks_like_challenge(html) is True


def test_challenge_detects_recaptcha_gate() -> None:
    html = """
    <html><body>
      <div class="g-recaptcha" data-sitekey="x"></div>
    </body></html>
    """
    assert looks_like_challenge(html) is True


def test_challenge_is_false_on_normal_page() -> None:
    html = """
    <html><head>
      <meta property="og:description" content="Normal marketing page for a company">
    </head><body><h1>We build stuff</h1></body></html>
    """
    assert looks_like_challenge(html) is False


def test_challenge_is_false_on_empty_input() -> None:
    assert looks_like_challenge("") is False


def test_normalize_host_strips_www_and_lowercases() -> None:
    assert normalize_host("https://WWW.Example.com/path") == "example.com"
    assert normalize_host("https://example.com/") == "example.com"
    assert normalize_host("http://sub.example.com") == "sub.example.com"


def test_normalize_host_returns_none_for_unparsable() -> None:
    assert normalize_host(None) is None
    assert normalize_host("") is None
    assert normalize_host("not a url") is None
