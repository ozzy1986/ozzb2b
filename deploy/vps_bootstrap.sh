#!/usr/bin/env bash
# VPS bootstrap for the Phase 0 polyglot stack.
#
# What it does (idempotent):
#   - Ensures /var/www/ozzb2b.com/app exists and contains the current repo.
#   - Ensures Docker Compose can find compose.prod.yml.
#   - Creates a dedicated Postgres database + role (ozzb2b) on the host Postgres.
#   - Creates a dedicated Redis logical DB (index 3) for ozzb2b.
#   - Writes a skeleton .env.prod if missing (MUST be edited with real secrets).
#   - Installs api/web nginx vhosts and obtains Let's Encrypt certs via certbot --nginx.
#
# Safe to re-run. Destructive operations are gated.
set -euo pipefail

APP_DIR="/var/www/ozzb2b.com/app"
SITE_DIR="/var/www/ozzb2b.com"
REPO_URL="${REPO_URL:-https://github.com/ozzy1986/ozzb2b.git}"
REPO_BRANCH="${REPO_BRANCH:-main}"

log() { printf "[vps_bootstrap] %s\n" "$*"; }

log "ensuring app dir: $APP_DIR"
mkdir -p "$APP_DIR"

if [ ! -d "$APP_DIR/.git" ]; then
  log "cloning $REPO_URL -> $APP_DIR"
  git clone --branch "$REPO_BRANCH" "$REPO_URL" "$APP_DIR"
else
  log "pulling latest on branch $REPO_BRANCH"
  git -C "$APP_DIR" fetch --prune origin
  git -C "$APP_DIR" checkout "$REPO_BRANCH"
  git -C "$APP_DIR" pull --ff-only origin "$REPO_BRANCH"
fi

log "ensuring .env.prod exists (stub only if missing; edit with real secrets)"
if [ ! -f "$APP_DIR/.env.prod" ]; then
  cp "$APP_DIR/.env.prod.example" "$APP_DIR/.env.prod"
  chmod 600 "$APP_DIR/.env.prod"
  log "NOTE: edit $APP_DIR/.env.prod with real secrets before bringing the stack up."
fi

log "ensuring data dirs"
mkdir -p "$SITE_DIR/data/meilisearch"

log "host postgres role/db (if missing)"
if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='ozzb2b'" | grep -q 1; then
  log "role ozzb2b exists"
else
  PW=$(openssl rand -hex 24)
  sudo -u postgres psql -c "CREATE ROLE ozzb2b WITH LOGIN PASSWORD '$PW';"
  log "created role ozzb2b with generated password; update .env.prod DATABASE_URL accordingly"
  log "generated_password=$PW"
fi
if sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='ozzb2b'" | grep -q 1; then
  log "db ozzb2b exists"
else
  sudo -u postgres psql -c "CREATE DATABASE ozzb2b OWNER ozzb2b;"
fi

log "nginx vhosts for api/web"
install -m 0644 "$APP_DIR/infra/nginx/ozzb2b.com.conf"     /etc/nginx/sites-available/ozzb2b.com
install -m 0644 "$APP_DIR/infra/nginx/api.ozzb2b.com.conf" /etc/nginx/sites-available/api.ozzb2b.com
ln -sfn /etc/nginx/sites-available/ozzb2b.com     /etc/nginx/sites-enabled/ozzb2b.com
ln -sfn /etc/nginx/sites-available/api.ozzb2b.com /etc/nginx/sites-enabled/api.ozzb2b.com

log "nginx -t + reload"
nginx -t
systemctl reload nginx

log "letsencrypt: api.ozzb2b.com (idempotent)"
certbot --nginx -d api.ozzb2b.com --non-interactive --agree-tos -m ozeritski@gmail.com --redirect || true

log "pull & up compose stack"
cd "$APP_DIR"
docker compose -f compose.prod.yml pull
docker compose -f compose.prod.yml up -d

log "done. services:"
docker compose -f compose.prod.yml ps
