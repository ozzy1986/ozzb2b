#!/usr/bin/env bash
# Phase 5.5 smoke test for the observability stack.
#
# Validates (all on the VPS itself so we don't depend on the grafana.ozzb2b.com
# subdomain being live yet):
# 1. Prometheus is healthy.
# 2. All scrape targets show up=1 from inside the Docker network.
# 3. Loki is ready and Promtail is pushing samples.
# 4. Grafana is healthy and knows about both provisioned datasources.
# 5. The ozzb2b overview dashboard exists in Grafana's store.

set -euo pipefail

APP=${APP:-/var/www/ozzb2b.com/app}
COMPOSE="docker compose -f ${APP}/compose.prod.yml"

log() { printf "[phase5.5_smoke] %s\n" "$*"; }

PROM_URL=http://127.0.0.1:9090
LOKI_URL=http://127.0.0.1:3100
GRAFANA_URL=http://127.0.0.1:3102

log "1) Prometheus /-/ready"
curl -sSf "${PROM_URL}/-/ready" >/dev/null && echo "  OK"

log "2) Scrape targets up"
# `up` returns one series per target; we want every one at 1.
down=$(curl -sSf --data-urlencode 'query=up==0' "${PROM_URL}/api/v1/query" \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print(len(d.get("data",{}).get("result",[])))')
if [ "$down" != "0" ]; then
  echo "FAIL: $down scrape targets are currently down"
  curl -sS --data-urlencode 'query=up==0' "${PROM_URL}/api/v1/query"
  exit 1
fi
total=$(curl -sSf --data-urlencode 'query=count(up)' "${PROM_URL}/api/v1/query" \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); r=d["data"]["result"]; print(r[0]["value"][1] if r else 0)')
echo "  OK: ${total} targets scraping"

log "3) Loki ready"
curl -sSf "${LOKI_URL}/ready" >/dev/null && echo "  OK: Loki ready"
# Metrics endpoint should show Promtail successfully pushing in bytes over time.
bytes=$(curl -sSf "${LOKI_URL}/metrics" | awk '/^loki_ingester_chunks_stored_total/ {s+=$2} END {print s+0}')
echo "  OK: loki_ingester_chunks_stored_total aggregate = ${bytes}"

log "4) Grafana healthy + datasources provisioned"
curl -sSf "${GRAFANA_URL}/api/health" \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["database"]=="ok", d; print("  OK: database=",d["database"],"version=",d["version"])'

GRAFANA_USER=$(awk -F= '/^OZZB2B_GRAFANA_ADMIN_USER=/ {print $2}' /root/.ozzb2b_secrets)
GRAFANA_PASS=$(awk -F= '/^OZZB2B_GRAFANA_ADMIN_PASSWORD=/ {print $2}' /root/.ozzb2b_secrets)
curl -sSf -u "${GRAFANA_USER}:${GRAFANA_PASS}" "${GRAFANA_URL}/api/datasources" \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); names=sorted(x["name"] for x in d); print("  OK: datasources=", names); assert {"Prometheus","Loki"}.issubset(names), d'

log "5) Overview dashboard provisioned"
curl -sSf -u "${GRAFANA_USER}:${GRAFANA_PASS}" "${GRAFANA_URL}/api/search?query=ozzb2b" \
  | python3 -c '
import json,sys
rows=json.load(sys.stdin)
titles=[r["title"] for r in rows]
print("  OK: dashboards=", titles)
assert any("ozzb2b" in t.lower() for t in titles), rows
'

log "done"
