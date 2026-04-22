#!/usr/bin/env bash
# One-off bootstrap for grafana.ozzb2b.com: obtain Let's Encrypt cert and
# install the nginx vhost. Safe to re-run; certbot --nginx is idempotent.
#
# Prereqs on DNS: an A record for grafana.ozzb2b.com pointing to this VPS.

set -euo pipefail

APP=${APP:-/var/www/ozzb2b.com/app}
cd "$APP"

log() { printf "[vps_grafana_ssl] %s\n" "$*"; }

# Install an HTTP-only vhost first so certbot can do the http-01 challenge.
cat > /etc/nginx/sites-available/grafana.ozzb2b.com <<'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name grafana.ozzb2b.com;

    location /.well-known/acme-challenge/ {
        root /var/www/ozzb2b.com;
    }

    location / {
        return 503 "Grafana SSL setup in progress. Come back in a minute.";
    }
}
EOF
ln -sf /etc/nginx/sites-available/grafana.ozzb2b.com /etc/nginx/sites-enabled/grafana.ozzb2b.com
nginx -t && systemctl reload nginx

log "running certbot"
certbot --nginx -d grafana.ozzb2b.com --non-interactive --agree-tos -m hello@ozzb2b.com

log "installing full vhost"
install -m 0644 infra/nginx/grafana.ozzb2b.com.conf /etc/nginx/sites-available/grafana.ozzb2b.com
nginx -t && systemctl reload nginx

log "done. Grafana will be reachable at https://grafana.ozzb2b.com"
