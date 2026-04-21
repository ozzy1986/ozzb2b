#!/usr/bin/env bash
# Phase 0 VPS setup: db, redis namespace, secrets, nginx vhosts, compose up.
set -euo pipefail

APP_DIR="/var/www/ozzb2b.com/app"
SITE_DIR="/var/www/ozzb2b.com"
SECRETS_FILE="/root/.ozzb2b_secrets"

log() { printf "[phase0] %s\n" "$*"; }

log "postgres role/db"
if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='ozzb2b'" | grep -q 1; then
    log "role ozzb2b already exists"
    if [ ! -f "$SECRETS_FILE" ] || ! grep -q '^OZZB2B_DB_PASSWORD=' "$SECRETS_FILE"; then
        NEW_PW=$(openssl rand -hex 24)
        sudo -u postgres psql -c "ALTER ROLE ozzb2b WITH PASSWORD '$NEW_PW';"
        touch "$SECRETS_FILE"; chmod 600 "$SECRETS_FILE"
        grep -v '^OZZB2B_DB_PASSWORD=' "$SECRETS_FILE" > "${SECRETS_FILE}.new" || true
        mv "${SECRETS_FILE}.new" "$SECRETS_FILE"
        echo "OZZB2B_DB_PASSWORD=$NEW_PW" >> "$SECRETS_FILE"
        log "rotated ozzb2b password"
    fi
else
    NEW_PW=$(openssl rand -hex 24)
    sudo -u postgres psql -c "CREATE ROLE ozzb2b WITH LOGIN PASSWORD '$NEW_PW';"
    touch "$SECRETS_FILE"; chmod 600 "$SECRETS_FILE"
    echo "OZZB2B_DB_PASSWORD=$NEW_PW" >> "$SECRETS_FILE"
    log "created role ozzb2b"
fi

if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='ozzb2b'" | grep -q 1; then
    sudo -u postgres psql -c "CREATE DATABASE ozzb2b OWNER ozzb2b;"
    log "created database ozzb2b"
fi

log "generating meili/jwt secrets if missing"
touch "$SECRETS_FILE"; chmod 600 "$SECRETS_FILE"
grep -q '^OZZB2B_MEILISEARCH_KEY=' "$SECRETS_FILE" || echo "OZZB2B_MEILISEARCH_KEY=$(openssl rand -hex 32)" >> "$SECRETS_FILE"
grep -q '^OZZB2B_JWT_SECRET=' "$SECRETS_FILE"        || echo "OZZB2B_JWT_SECRET=$(openssl rand -hex 48)" >> "$SECRETS_FILE"

set -a; . "$SECRETS_FILE"; set +a

log "writing .env.prod"
cat > "$APP_DIR/.env.prod" <<EOF
OZZB2B_ENV=production

OZZB2B_DATABASE_URL=postgresql+asyncpg://ozzb2b:${OZZB2B_DB_PASSWORD}@host.docker.internal:5432/ozzb2b
OZZB2B_REDIS_URL=redis://host.docker.internal:6379/3

OZZB2B_MEILISEARCH_URL=http://meilisearch:7700
OZZB2B_MEILISEARCH_KEY=${OZZB2B_MEILISEARCH_KEY}

OZZB2B_JWT_SECRET=${OZZB2B_JWT_SECRET}
OZZB2B_JWT_ACCESS_TTL_SECONDS=900
OZZB2B_JWT_REFRESH_TTL_SECONDS=2592000

OZZB2B_CORS_ORIGINS=https://ozzb2b.com,https://www.ozzb2b.com
OZZB2B_LOG_LEVEL=INFO

NEXT_PUBLIC_OZZB2B_API_URL=https://api.ozzb2b.com
EOF
chmod 600 "$APP_DIR/.env.prod"

log "ensuring data dirs"
mkdir -p "$SITE_DIR/data/meilisearch"

log "nginx vhosts"
install -m 0644 "$APP_DIR/infra/nginx/ozzb2b.com.conf"     /etc/nginx/sites-available/ozzb2b.com.new
install -m 0644 "$APP_DIR/infra/nginx/api.ozzb2b.com.conf" /etc/nginx/sites-available/api.ozzb2b.com.new

log "building images"
cd "$APP_DIR"
docker compose -f compose.prod.yml build api web

log "bringing up meilisearch + api + web"
docker compose -f compose.prod.yml up -d --build

log "waiting for api health"
for i in $(seq 1 30); do
    if curl -sfo /dev/null http://127.0.0.1:8001/health; then
        log "api is healthy"
        break
    fi
    sleep 2
done

log "waiting for web health"
for i in $(seq 1 30); do
    if curl -sfo /dev/null http://127.0.0.1:3101/api/health; then
        log "web is healthy"
        break
    fi
    sleep 2
done

log "switching nginx ozzb2b.com to new backend"
# Replace the static placeholder vhost with the proxy-to-Next.js one.
# Preserve whatever certbot already installed for SSL if present.
mv /etc/nginx/sites-available/ozzb2b.com.new     /etc/nginx/sites-available/ozzb2b.com
mv /etc/nginx/sites-available/api.ozzb2b.com.new /etc/nginx/sites-available/api.ozzb2b.com
ln -sfn /etc/nginx/sites-available/ozzb2b.com     /etc/nginx/sites-enabled/ozzb2b.com
ln -sfn /etc/nginx/sites-available/api.ozzb2b.com /etc/nginx/sites-enabled/api.ozzb2b.com

log "nginx -t"
nginx -t
systemctl reload nginx

log "letsencrypt for api.ozzb2b.com (idempotent; will no-op until DNS points to this host)"
certbot --nginx -d api.ozzb2b.com --non-interactive --agree-tos -m ozeritski@gmail.com --redirect || log "certbot for api.ozzb2b.com skipped (DNS?)"

log "compose status"
docker compose -f compose.prod.yml ps
log "done"
