#!/usr/bin/env bash
# Phase 5.5 bootstrap: prepare host dirs, inject a Grafana admin password into
# the root secrets file (if missing), rebuild and bring up the new services.

set -euo pipefail

APP=${APP:-/var/www/ozzb2b.com/app}
cd "$APP"

log() { printf "[phase5.5_bootstrap] %s\n" "$*"; }

log "create host data dirs"
install -d -m 0750 /var/www/ozzb2b.com/data/prometheus
install -d -m 0750 /var/www/ozzb2b.com/data/grafana
install -d -m 0750 /var/www/ozzb2b.com/data/loki
install -d -m 0750 /var/www/ozzb2b.com/data/promtail
# Grafana inside the image runs as uid 472.
chown -R 472:472 /var/www/ozzb2b.com/data/grafana
# Loki runs as uid 10001 since 3.x.
chown -R 10001:10001 /var/www/ozzb2b.com/data/loki
# Prometheus uses nobody (65534).
chown -R 65534:65534 /var/www/ozzb2b.com/data/prometheus

if ! grep -q '^OZZB2B_GRAFANA_ADMIN_PASSWORD=' /root/.ozzb2b_secrets; then
    pw=$(tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 24)
    printf '\nOZZB2B_GRAFANA_ADMIN_USER=admin\nOZZB2B_GRAFANA_ADMIN_PASSWORD=%s\n' "$pw" >> /root/.ozzb2b_secrets
    chmod 600 /root/.ozzb2b_secrets
    log "generated Grafana admin password:"
    log "  OZZB2B_GRAFANA_ADMIN_USER=admin"
    log "  OZZB2B_GRAFANA_ADMIN_PASSWORD=$pw"
else
    log "Grafana admin password already present in /root/.ozzb2b_secrets"
fi

log "re-applying stack (rewrites .env.prod, pulls latest images, starts new services)"
bash deploy/vps_apply_stack.sh

log "status:"
docker compose -f compose.prod.yml ps --format 'table {{.Service}}\t{{.Status}}'
