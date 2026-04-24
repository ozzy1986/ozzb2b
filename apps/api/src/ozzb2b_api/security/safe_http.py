"""Outbound HTTP client hardened against SSRF.

Used for any user-driven fetch (claim verification, future webhooks, etc.).
The implementation is intentionally narrow: a single ``fetch_text`` helper
that returns a UTF-8 string body capped at ``max_bytes``.

Defenses applied:

- Scheme allowlist: only ``https://`` is accepted in production. ``http://``
  is permitted in dev so test fixtures and ``httpbin``-style stubs work,
  but production clients MUST set ``allow_http=False`` (default).
- DNS resolution before connecting: every candidate URL is resolved via
  ``socket.getaddrinfo`` and rejected if any returned IP is private,
  loopback, link-local, the cloud-metadata address (169.254.169.254) or a
  multicast/broadcast/reserved range.
- Bounded redirects: ``max_redirects`` (default 2) and the redirect target
  must pass the same DNS check. Cross-eTLD+1 redirects are rejected so a
  helpful 302 cannot be used to pivot off the original domain.
- Bounded body: ``max_bytes`` is enforced by streaming the response and
  abandoning the read once the cap is exceeded.
- Bounded time: separate ``connect_timeout`` and ``total_timeout``.

Failures raise :class:`UnsafeUrlError` so the caller can return a generic
"homepage unreachable" message without leaking the underlying reason.
"""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlsplit

import httpx
import structlog

log = structlog.get_logger("ozzb2b_api.security.safe_http")


class UnsafeUrlError(RuntimeError):
    """The requested URL is not safe to fetch (scheme/host/redirect/body)."""


@dataclass(frozen=True)
class SafeHttpPolicy:
    allow_http: bool = False
    max_redirects: int = 2
    max_bytes: int = 512 * 1024
    connect_timeout: float = 2.0
    total_timeout: float = 5.0


def _is_safe_ip(addr: str) -> bool:
    try:
        ip = ipaddress.ip_address(addr)
    except ValueError:
        return False
    if ip.is_loopback or ip.is_private or ip.is_link_local:
        return False
    # 169.254.169.254 is link-local already, but cloud metadata aliases
    # (e.g. fd00:ec2::254 in IMDSv2 IPv6) live in fd00::/8 which our
    # `is_private` check covers.
    return not (ip.is_multicast or ip.is_reserved or ip.is_unspecified)


def _resolve(host: str) -> list[str]:
    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UnsafeUrlError(f"could not resolve host {host!r}: {exc}") from exc
    # getaddrinfo returns IPv4 and IPv6 records whose sockaddr tuples have
    # different shapes; the address is always the first element.
    return [str(info[4][0]) for info in infos]


def _registered_domain(host: str) -> str:
    """Return the eTLD+1 used to pin a redirect to the original site.

    We deliberately avoid pulling in a Public Suffix List dependency for this
    simple policy: a stricter domain-pin is fine for our use case (claim
    verification only follows redirects within the literal registered name).
    """
    parts = host.lower().rstrip(".").split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host.lower()


def _validate_url(url: str, *, policy: SafeHttpPolicy, expected_domain: str | None) -> str:
    """Return the host of ``url`` after running every static + DNS check."""
    parts = urlsplit(url)
    scheme = parts.scheme.lower()
    if scheme not in {"http", "https"}:
        raise UnsafeUrlError(f"only http(s) URLs are allowed (got {scheme!r})")
    if scheme == "http" and not policy.allow_http:
        raise UnsafeUrlError("https is required for outbound fetches")
    host = parts.hostname or ""
    if not host:
        raise UnsafeUrlError("URL has no hostname")
    if expected_domain and _registered_domain(host) != expected_domain:
        raise UnsafeUrlError(
            f"redirect leaves the original domain {expected_domain!r}",
        )
    for addr in _resolve(host):
        if not _is_safe_ip(addr):
            raise UnsafeUrlError(
                f"hostname {host!r} resolves to a forbidden address {addr!r}",
            )
    return host


async def fetch_text(
    url: str,
    *,
    policy: SafeHttpPolicy | None = None,
    user_agent: str = "ozzb2b/1.0 (+https://ozzb2b.com)",
) -> str:
    """Fetch ``url`` and return its UTF-8 body, capped at ``policy.max_bytes``.

    The body is streamed and decoding stops once the cap is reached, so an
    attacker cannot keep us reading forever.
    """
    cfg = policy or SafeHttpPolicy()
    initial_host = _validate_url(url, policy=cfg, expected_domain=None)
    expected_domain = _registered_domain(initial_host)

    # Manual redirect handling: validate every hop. httpx follow_redirects
    # would silently bypass our DNS / scheme allowlist.
    timeout = httpx.Timeout(cfg.total_timeout, connect=cfg.connect_timeout)
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml",
    }
    current = url
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        for _hop in range(cfg.max_redirects + 1):
            try:
                async with client.stream("GET", current, headers=headers) as resp:
                    if resp.is_redirect:
                        location = resp.headers.get("location")
                        if not location:
                            raise UnsafeUrlError("redirect with no Location header")
                        nxt = str(httpx.URL(current).join(location))
                        _validate_url(nxt, policy=cfg, expected_domain=expected_domain)
                        current = nxt
                        continue
                    resp.raise_for_status()
                    chunks: list[bytes] = []
                    received = 0
                    async for chunk in resp.aiter_bytes(chunk_size=8 * 1024):
                        received += len(chunk)
                        if received > cfg.max_bytes:
                            raise UnsafeUrlError(
                                f"response body exceeded {cfg.max_bytes} bytes",
                            )
                        chunks.append(chunk)
                    body = b"".join(chunks)
                    return body.decode("utf-8", errors="replace")
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                raise UnsafeUrlError(f"transport error fetching {current!r}: {exc}") from exc
            except httpx.HTTPStatusError as exc:
                raise UnsafeUrlError(
                    f"upstream {current!r} returned {exc.response.status_code}",
                ) from exc
    raise UnsafeUrlError("too many redirects")
