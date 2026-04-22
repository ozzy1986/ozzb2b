#!/usr/bin/env python3
"""End-to-end smoke test for the Phase 2 chat stack.

- Registers a fresh client user against api.ozzb2b.com.
- Opens a conversation with a published RU provider.
- Fetches a short-lived WS token.
- Opens the WebSocket via wss://api.ozzb2b.com/chat/ws and waits for a
  fan-out frame after POST-ing a new message.
- Fails loudly on any bad status / timeout.
"""

from __future__ import annotations

import asyncio
import json
import os
import secrets
import sys
import time
from urllib.parse import urlparse

import requests
import websockets

API = os.environ.get("OZZB2B_SMOKE_API", "https://api.ozzb2b.com")
PROVIDER_SLUG = os.environ.get("OZZB2B_SMOKE_PROVIDER_SLUG", "reksoft")


def die(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def main() -> None:
    session = requests.Session()
    email = f"smoke-{secrets.token_hex(4)}@example.com"
    password = "sm0kePass-" + secrets.token_hex(4)

    print("register", email)
    r = session.post(
        f"{API}/auth/register",
        json={"email": email, "password": password, "display_name": "Smoke"},
        timeout=15,
    )
    if r.status_code != 201:
        die(f"register status={r.status_code}: {r.text[:200]}")

    print("start conversation with", PROVIDER_SLUG)
    r = session.post(
        f"{API}/chat/conversations",
        json={"provider_slug": PROVIDER_SLUG},
        timeout=15,
    )
    if r.status_code != 201:
        die(f"start conv status={r.status_code}: {r.text[:200]}")
    conv = r.json()
    conv_id = conv["id"]
    print("conversation id:", conv_id)

    print("issue ws-token")
    r = session.post(f"{API}/chat/conversations/{conv_id}/ws-token", timeout=15)
    if r.status_code != 200:
        die(f"ws-token status={r.status_code}: {r.text[:200]}")
    ws_url = r.json()["ws_url"]
    print("ws url:", ws_url)

    asyncio.run(_exercise_ws(ws_url, session, conv_id))
    print("OK: end-to-end chat works")


async def _exercise_ws(
    ws_url: str, session: requests.Session, conv_id: str
) -> None:
    # Convert the wss:// URL to use the same hostname the API uses (the URL
    # returned by the API should already be correct).
    parsed = urlparse(ws_url)
    if parsed.scheme not in ("ws", "wss"):
        die(f"bad ws scheme: {parsed.scheme}")

    expected = f"hello-{secrets.token_hex(3)}"
    async with websockets.connect(ws_url, open_timeout=10, ping_interval=None) as ws:
        # Give the gateway a moment to finish subscribing to Redis.
        await asyncio.sleep(0.3)

        # Publish a message via the REST API — the gateway should fan it out.
        r = session.post(
            f"{API}/chat/conversations/{conv_id}/messages",
            json={"body": expected},
            timeout=15,
        )
        if r.status_code != 201:
            die(f"send message status={r.status_code}: {r.text[:200]}")

        deadline = time.time() + 10
        while time.time() < deadline:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=deadline - time.time())
            except asyncio.TimeoutError:
                die("timeout waiting for fan-out frame")
            payload = json.loads(raw)
            if payload.get("body") == expected:
                return
        die("expected body never arrived on the socket")


if __name__ == "__main__":
    main()
