#!/usr/bin/env bash
# One-off bootstrap for grafana.ozzb2b.com: obtain a Let's Encrypt cert and
# install the vhost for whichever public edge is active. Safe to re-run.
#
# Prereqs on DNS: an A record for grafana.ozzb2b.com pointing to this VPS.

set -euo pipefail

APP=${APP:-/var/www/ozzb2b.com/app}
cd "$APP"

log() { printf "[vps_grafana_ssl] %s\n" "$*"; }

if systemctl is-active --quiet apache2 2>/dev/null && ! systemctl is-active --quiet nginx 2>/dev/null; then
    log "installing Apache HTTP vhost"
    install -m 0644 infra/apache/grafana.ozzb2b.com.conf \
        /etc/apache2/sites-available/grafana.ozzb2b.com.conf
    a2enmod proxy proxy_http proxy_wstunnel headers rewrite ssl >/dev/null
    a2ensite grafana.ozzb2b.com.conf >/dev/null
    apache2ctl configtest
    systemctl reload apache2

    log "running certbot for Apache"
    certbot --apache -d grafana.ozzb2b.com \
        --non-interactive --agree-tos -m hello@ozzb2b.com --redirect
    apache2ctl configtest
    systemctl reload apache2
else
    log "installing nginx HTTP vhost"
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
    ln -sf /etc/nginx/sites-available/grafana.ozzb2b.com \
        /etc/nginx/sites-enabled/grafana.ozzb2b.com
    nginx -t
    systemctl reload nginx

    log "running certbot for nginx"
    certbot --nginx -d grafana.ozzb2b.com \
        --non-interactive --agree-tos -m hello@ozzb2b.com --redirect

    log "installing full nginx vhost"
    install -m 0644 infra/nginx/grafana.ozzb2b.com.conf \
        /etc/nginx/sites-available/grafana.ozzb2b.com
    nginx -t
    systemctl reload nginx
fi

log "done. Grafana will be reachable at https://grafana.ozzb2b.com"
