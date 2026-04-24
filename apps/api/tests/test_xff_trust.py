"""Trusted-proxy handling for X-Forwarded-For."""

from __future__ import annotations

from ozzb2b_api.security.rate_limit import client_ip


def test_xff_ignored_by_default() -> None:
    headers = {"x-forwarded-for": "1.2.3.4, 5.6.7.8"}
    assert client_ip(headers, "10.0.0.1") == "10.0.0.1"


def test_single_trusted_hop_picks_entry_before_trusted_proxy() -> None:
    # Chain: <client>, <our-nginx>. With 1 trusted hop, the real client is
    # the entry to the LEFT of the rightmost (trusted) one.
    headers = {"x-forwarded-for": "1.2.3.4, 10.0.0.1"}
    assert client_ip(headers, "127.0.0.1", trusted_proxy_count=1) == "1.2.3.4"


def test_two_trusted_hops_walk_back_two_from_right() -> None:
    # Chain: <client>, <edge-proxy>, <our-nginx>. With 2 trusted hops we
    # skip the two rightmost and the real client is the leftmost entry.
    headers = {"x-forwarded-for": "client.real, edge.proxy, our.nginx"}
    assert (
        client_ip(headers, "10.0.0.1", trusted_proxy_count=2) == "client.real"
    )


def test_trust_more_hops_than_chain_falls_back_to_leftmost() -> None:
    headers = {"x-forwarded-for": "1.2.3.4"}
    # If we say we trust 5 proxies but only one IP is in the chain, the
    # leftmost (only) entry is what we have to use.
    assert (
        client_ip(headers, "10.0.0.1", trusted_proxy_count=5) == "1.2.3.4"
    )


def test_falls_back_to_socket_peer_when_header_absent() -> None:
    assert client_ip({}, "10.0.0.1", trusted_proxy_count=1) == "10.0.0.1"
    assert client_ip(None, "10.0.0.1", trusted_proxy_count=1) == "10.0.0.1"


def test_unknown_when_neither_header_nor_peer_available() -> None:
    assert client_ip(None, None) == "unknown"
