#!/usr/bin/env bash
# Phase 5 smoke: metrics endpoints, security headers, auth rate limit.
set -u

echo "--- /metrics endpoints ---"
for svc in "api:http://127.0.0.1:8001" "chat:http://127.0.0.1:8090" \
           "events:http://127.0.0.1:8095" "matcher:http://127.0.0.1:8090/../"; do
  :
done

api_metrics_first=$(curl -sS http://127.0.0.1:8001/metrics | grep -m1 '^ozzb2b_api_http_requests_total' || true)
echo "api: ${api_metrics_first:-<none>}"

chat_metrics_first=$(curl -sS http://127.0.0.1:8090/metrics | grep -m1 '^ozzb2b_chat_ws_connections_total' || true)
echo "chat: ${chat_metrics_first:-<none>}"

events_metrics_first=$(curl -sS http://127.0.0.1:8095/metrics | grep -m1 '^ozzb2b_events_' || true)
echo "events: ${events_metrics_first:-<none>}"

# Matcher runs the http server on 8090 inside its container; find its ip
matcher_ip=$(docker inspect ozzb2b-matcher --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' | head -1)
matcher_metrics_first=$(docker exec ozzb2b-matcher wget -qO- http://127.0.0.1:8090/metrics 2>/dev/null | grep -m1 '^ozzb2b_matcher_' || true)
echo "matcher (ip=$matcher_ip): ${matcher_metrics_first:-<none>}"

echo
echo "--- public /metrics must be blocked at nginx ---"
curl -sS -o /dev/null -w 'api.ozzb2b.com/metrics=%{http_code}\n' https://api.ozzb2b.com/metrics

echo
echo "--- security headers on api.ozzb2b.com ---"
curl -sSI https://api.ozzb2b.com/health | grep -iE '^(strict-transport-security|x-content-type-options|x-frame-options|referrer-policy|permissions-policy|content-security-policy):'

echo
echo "--- security headers on ozzb2b.com ---"
curl -sSI https://ozzb2b.com/ | grep -iE '^(strict-transport-security|x-content-type-options|x-frame-options|referrer-policy|permissions-policy):'

echo
echo "--- auth rate limit (should go 201/409 -> 429 after 5 attempts in the same window) ---"
for i in 1 2 3 4 5 6 7; do
  body="{\"email\":\"rl-$(date +%s)-$i@example.com\",\"password\":\"ValidPassword123!\",\"display_name\":\"rl\"}"
  status=$(curl -sS -o /tmp/rl.json -w '%{http_code}' -X POST https://api.ozzb2b.com/auth/register \
    -H 'content-type: application/json' -d "$body")
  echo "register attempt #$i status=$status"
  if [ "$status" = "429" ]; then
    retry=$(curl -sSI -X POST https://api.ozzb2b.com/auth/register -H 'content-type: application/json' -d "$body" | grep -i '^retry-after' || true)
    echo "  $retry"
    break
  fi
done

echo
echo "--- cleanup: drop just-created test users ---"
docker exec ozzb2b-api python - <<'PY'
import asyncio
from sqlalchemy import delete
from ozzb2b_api.db.models import User
from ozzb2b_api.db.session import get_sessionmaker

async def main():
    sm = get_sessionmaker()
    async with sm() as s:
        await s.execute(delete(User).where(User.email.like('rl-%@example.com')))
        await s.commit()
    print('cleaned up rl-%@example.com')

asyncio.run(main())
PY
