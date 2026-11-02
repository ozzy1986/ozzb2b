#!/usr/bin/env bash
# Allow the ozzb2b Docker containers to reach the host Redis.
# Containers reach the host via `host.docker.internal` (host-gateway =
# docker0, 172.17.0.1), so Redis binds only to localhost + that address,
# never the public IP. protected-mode + requirepass + UFW (Docker bridge
# interfaces only) are kept as extra layers.
set -euo pipefail

REDIS_CONF="/etc/redis/redis.conf"
SECRETS_FILE="/root/.ozzb2b_secrets"

log() { printf "[redis-allow-docker] %s\n" "$*"; }

[ -f "$REDIS_CONF" ] || { log "redis.conf not found"; exit 1; }

# Generate a password and persist in secrets file if missing.
touch "$SECRETS_FILE"; chmod 600 "$SECRETS_FILE"
if ! grep -q '^OZZB2B_REDIS_PASSWORD=' "$SECRETS_FILE"; then
    echo "OZZB2B_REDIS_PASSWORD=$(openssl rand -hex 32)" >> "$SECRETS_FILE"
fi
# shellcheck disable=SC1090
set -a; . "$SECRETS_FILE"; set +a

# docker0 may not exist yet when Redis starts at boot; allow binding to it anyway.
echo "net.ipv4.ip_nonlocal_bind = 1" > /etc/sysctl.d/60-db-bind-docker0.conf
sysctl -q -p /etc/sysctl.d/60-db-bind-docker0.conf

log "binding redis on localhost + docker0"
if grep -qE '^[^#]*bind ' "$REDIS_CONF"; then
    sed -i -E 's|^[[:space:]]*bind .*|bind 127.0.0.1 -::1 172.17.0.1|' "$REDIS_CONF"
else
    echo "bind 127.0.0.1 -::1 172.17.0.1" >> "$REDIS_CONF"
fi

if grep -qE '^[^#]*protected-mode ' "$REDIS_CONF"; then
    sed -i -E 's|^[[:space:]]*protected-mode .*|protected-mode yes|' "$REDIS_CONF"
else
    echo "protected-mode yes" >> "$REDIS_CONF"
fi

if grep -qE '^[^#]*requirepass ' "$REDIS_CONF"; then
    sed -i -E "s|^[[:space:]]*requirepass .*|requirepass ${OZZB2B_REDIS_PASSWORD}|" "$REDIS_CONF"
else
    echo "requirepass ${OZZB2B_REDIS_PASSWORD}" >> "$REDIS_CONF"
fi

systemctl restart redis-server
log "redis restarted"

ufw allow in on docker0 to any port 6379 proto tcp || true
for iface in $(ip -4 -br addr | awk '/^br-/{print $1}'); do
    ufw allow in on "$iface" to any port 6379 proto tcp || true
done
ufw reload

ss -ltnp | awk '/:6379 /{print}'
log "done"
