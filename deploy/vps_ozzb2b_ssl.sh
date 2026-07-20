#!/usr/bin/env bash
# Issue Let's Encrypt certs for ozzb2b Apache vhosts (HTTP-01).
# Preconditions: DNS A records for the domains already point at this VPS.
set -euo pipefail

EMAIL="${CERTBOT_EMAIL:-ozeritski@gmail.com}"

log() { printf "[ozzb2b-ssl] %s\n" "$*"; }

need_dns() {
  local host="$1"
  local expected
  expected=$(hostname -I | awk '{print $1}')
  local actual
  actual=$(getent ahostsv4 "$host" | awk '{print $1; exit}')
  if [ "$actual" != "$expected" ]; then
    log "DNS for $host is '$actual', expected '$expected' — aborting before certbot"
    return 1
  fi
  return 0
}

need_dns ozzb2b.com
need_dns www.ozzb2b.com
need_dns api.ozzb2b.com

log "certbot apache: ozzb2b.com + www"
certbot --apache -d ozzb2b.com -d www.ozzb2b.com \
  --non-interactive --agree-tos -m "$EMAIL" --redirect

log "certbot apache: api.ozzb2b.com"
certbot --apache -d api.ozzb2b.com \
  --non-interactive --agree-tos -m "$EMAIL" --redirect

apache2ctl configtest
systemctl reload apache2
log "done"
