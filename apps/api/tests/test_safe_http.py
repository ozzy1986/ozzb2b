"""SSRF defenses for outbound HTTP fetches."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from ozzb2b_api.security.safe_http import (
    SafeHttpPolicy,
    UnsafeUrlError,
    _is_safe_ip,
    _registered_domain,
    _validate_url,
)


@pytest.mark.parametrize(
    "addr",
    [
        "127.0.0.1",
        "10.0.0.1",
        "192.168.1.1",
        "172.16.0.1",
        "169.254.169.254",
        "::1",
        "fe80::1",
        "fd00::1",
        "0.0.0.0",
        "224.0.0.1",
    ],
)
def test_is_safe_ip_rejects_internal_ranges(addr: str) -> None:
    assert _is_safe_ip(addr) is False


@pytest.mark.parametrize("addr", ["8.8.8.8", "1.1.1.1", "2606:4700:4700::1111"])
def test_is_safe_ip_accepts_public_addresses(addr: str) -> None:
    assert _is_safe_ip(addr) is True


def test_validate_rejects_non_https_in_strict_mode() -> None:
    policy = SafeHttpPolicy(allow_http=False)
    with pytest.raises(UnsafeUrlError):
        _validate_url("http://example.com", policy=policy, expected_domain=None)


def test_validate_rejects_other_schemes() -> None:
    policy = SafeHttpPolicy(allow_http=True)
    for url in ("ftp://example.com", "file:///etc/passwd", "gopher://example.com"):
        with pytest.raises(UnsafeUrlError):
            _validate_url(url, policy=policy, expected_domain=None)


def test_validate_rejects_url_without_host() -> None:
    policy = SafeHttpPolicy(allow_http=True)
    with pytest.raises(UnsafeUrlError):
        _validate_url("https:///path", policy=policy, expected_domain=None)


def test_validate_rejects_when_dns_resolves_to_private_ip() -> None:
    policy = SafeHttpPolicy()
    fake = [(0, 0, 0, "", ("10.0.0.5", 0))]
    with (
        patch("ozzb2b_api.security.safe_http.socket.getaddrinfo", return_value=fake),
        pytest.raises(UnsafeUrlError, match="forbidden address"),
    ):
        _validate_url("https://internal.bad", policy=policy, expected_domain=None)


def test_validate_pins_redirect_to_registered_domain() -> None:
    policy = SafeHttpPolicy()
    fake = [(0, 0, 0, "", ("8.8.8.8", 0))]
    with (
        patch("ozzb2b_api.security.safe_http.socket.getaddrinfo", return_value=fake),
        pytest.raises(UnsafeUrlError, match="leaves the original domain"),
    ):
        _validate_url(
            "https://attacker.example",
            policy=policy,
            expected_domain="legit.example",
        )


def test_registered_domain_returns_etld_plus_one() -> None:
    assert _registered_domain("www.example.com") == "example.com"
    assert _registered_domain("a.b.example.org") == "example.org"
    # Single-label hosts (e.g. localhost) collapse to themselves.
    assert _registered_domain("localhost") == "localhost"
