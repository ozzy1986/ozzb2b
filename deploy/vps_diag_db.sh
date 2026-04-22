#!/usr/bin/env bash
set -euo pipefail

echo "=== host listeners ==="
ss -ltnp | awk '/:5432 /{print}'

echo "=== inside api container: connect to host postgres ==="
docker exec -i ozzb2b-api python -u - <<'PY'
import socket, sys
for addr in ("host.docker.internal", "172.17.0.1"):
    try:
        ip = socket.gethostbyname(addr)
    except Exception as e:
        print(f"{addr}: resolve failed: {e}", flush=True); continue
    s = socket.socket(); s.settimeout(3)
    try:
        s.connect((ip, 5432))
        print(f"{addr} ({ip}): CONNECTED", flush=True)
    except Exception as e:
        print(f"{addr} ({ip}): {e!r}", flush=True)
    finally:
        s.close()
PY
