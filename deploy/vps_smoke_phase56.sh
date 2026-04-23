#!/usr/bin/env bash
# Phase 5.6 smoke test: host/container exporters + alert rules + Alertmanager.

set -euo pipefail

APP=${APP:-/var/www/ozzb2b.com/app}
COMPOSE="docker compose -f ${APP}/compose.prod.yml"

log() { printf "[phase5.6_smoke] %s\n" "$*"; }

PROM_URL=http://127.0.0.1:9090
AM_URL=http://127.0.0.1:9093

any_up() {
    # Returns 1 if at least one active scrape target for ${1} is currently up.
    local job=$1
    curl -sSG "${PROM_URL}/api/v1/query" \
      --data-urlencode "query=sum(up{job=\"${job}\"})" \
      | python3 -c 'import json,sys; r=json.load(sys.stdin)["data"]["result"]; print(int(float(r[0]["value"][1])) if r else 0)'
}

log "1) node_exporter scraped"
n=$(any_up host)
[ "${n:-0}" -ge 1 ] && echo "  OK: up{job=host}=${n}" || { echo "FAIL: host scrape not up"; exit 1; }

log "2) cAdvisor scraped"
n=$(any_up cadvisor)
[ "${n:-0}" -ge 1 ] && echo "  OK: up{job=cadvisor}=${n}" || { echo "FAIL: cadvisor scrape not up"; exit 1; }

log "3) Host metrics present"
for metric in node_cpu_seconds_total node_memory_MemAvailable_bytes node_filesystem_avail_bytes; do
  c=$(curl -sSf --data-urlencode "query=count(${metric})" "${PROM_URL}/api/v1/query" \
    | python3 -c 'import json,sys; r=json.load(sys.stdin)["data"]["result"]; print(r[0]["value"][1] if r else 0)')
  [ "${c:-0}" != "0" ] || { echo "FAIL: missing metric ${metric}"; exit 1; }
  echo "  OK: ${metric} series=${c}"
done

log "4) Container metrics present"
c=$(curl -sSf --data-urlencode 'query=count(container_memory_working_set_bytes{name!=""})' "${PROM_URL}/api/v1/query" \
    | python3 -c 'import json,sys; r=json.load(sys.stdin)["data"]["result"]; print(r[0]["value"][1] if r else 0)')
[ "${c:-0}" != "0" ] || { echo "FAIL: no container memory samples"; exit 1; }
echo "  OK: container_memory_working_set_bytes series=${c}"

log "5) Alert rules loaded"
rules=$(curl -sSf "${PROM_URL}/api/v1/rules" \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); names={r["name"] for g in d["data"]["groups"] for r in g["rules"] if r.get("type")=="alerting"}; print("|".join(sorted(names)))')
for expected in ServiceDown APIHighErrorRate HostHighCPU HostHighMemory HostDiskSpaceLow ContainerHighMemory; do
  [[ "$rules" == *"${expected}"* ]] || { echo "FAIL: rule ${expected} missing"; exit 1; }
done
echo "  OK: all key alert rules loaded"

if $COMPOSE ps --format '{{.Service}}' | grep -q '^alertmanager$'; then
    log "6) Alertmanager reachable"
    curl -sSf "${AM_URL}/-/ready" >/dev/null && echo "  OK: Alertmanager ready"
    log "7) Prometheus is wired to Alertmanager"
    amgrs=$(curl -sSf "${PROM_URL}/api/v1/alertmanagers" \
      | python3 -c 'import json,sys; d=json.load(sys.stdin); print(len(d["data"]["activeAlertmanagers"]))')
    [ "${amgrs:-0}" -ge 1 ] && echo "  OK: active alertmanagers=${amgrs}" \
      || { echo "FAIL: no active alertmanagers"; exit 1; }
else
    log "6) Alertmanager profile not active (Telegram secrets not set yet) — skipping"
fi

log "done"
