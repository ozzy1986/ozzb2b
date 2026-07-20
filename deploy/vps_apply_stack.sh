#!/usr/bin/env bash
set -euo pipefail

APP="${APP:-/var/www/ozzb2b.com/app}"

log() { printf "[vps_apply_stack] %s\n" "$*"; }

cd "$APP"

export GIT_SSH_COMMAND="ssh -i /root/.ssh/ozzb2b_deploy -o IdentitiesOnly=yes"
# GitHub default branch on this repo is `master` (renamed from `main`);
# keep this in sync with `deploy/vps_bootstrap.sh` and `remote_git_clone.sh`.
DEPLOY_BRANCH="${DEPLOY_BRANCH:-master}"
log "git pull $(git rev-parse --short HEAD 2>/dev/null || echo '?') -> $DEPLOY_BRANCH ..."
git fetch origin
# Make sure HEAD is on the deploy branch. If the checkout is still on an
# older local branch (e.g. `main` from before the rename), move it across
# once and track `origin/$DEPLOY_BRANCH` from here on.
current_branch="$(git rev-parse --abbrev-ref HEAD)"
if [ "$current_branch" != "$DEPLOY_BRANCH" ]; then
    log "switching working copy from $current_branch to $DEPLOY_BRANCH"
    git checkout -B "$DEPLOY_BRANCH" "origin/$DEPLOY_BRANCH"
fi
git pull --ff-only origin "$DEPLOY_BRANCH"

log "refresh .env.prod"
set -a
source /root/.ozzb2b_secrets
set +a

cat > .env.prod <<EOF
OZZB2B_ENV=production

OZZB2B_DATABASE_URL=postgresql+asyncpg://ozzb2b:${OZZB2B_DB_PASSWORD}@host.docker.internal:5432/ozzb2b
OZZB2B_REDIS_URL=redis://:${OZZB2B_REDIS_PASSWORD}@host.docker.internal:6379/3

OZZB2B_MEILISEARCH_URL=http://meilisearch:7700
OZZB2B_MEILISEARCH_KEY=${OZZB2B_MEILISEARCH_KEY}

MEILI_MASTER_KEY=${OZZB2B_MEILISEARCH_KEY}

OZZB2B_JWT_SECRET=${OZZB2B_JWT_SECRET}
OZZB2B_JWT_ACCESS_TTL_SECONDS=900
OZZB2B_JWT_REFRESH_TTL_SECONDS=2592000
OZZB2B_AUTH_COOKIE_DOMAIN=.ozzb2b.com

OZZB2B_CORS_ORIGINS=https://ozzb2b.com,https://www.ozzb2b.com,https://api.ozzb2b.com
OZZB2B_LOG_LEVEL=INFO

# Phase 3 matcher (feature-flagged, safe to leave enabled).
OZZB2B_MATCHER_ENABLED=true
OZZB2B_MATCHER_GRPC_ADDR=matcher:9090
OZZB2B_MATCHER_TIMEOUT_MS=200

# Phase 4 analytics pipeline (Redis Streams -> ClickHouse).
OZZB2B_EVENTS_ENABLED=true
OZZB2B_EVENTS_STREAM=ozzb2b:events:v1
OZZB2B_CLICKHOUSE_URL=http://clickhouse:8123
OZZB2B_CLICKHOUSE_DATABASE=ozzb2b
OZZB2B_CLICKHOUSE_TIMEOUT_MS=2000

# Phase 5 hardening.
OZZB2B_RATE_LIMIT_ENABLED=true
OZZB2B_RATE_LIMIT_LOGIN_MAX=10
OZZB2B_RATE_LIMIT_REGISTER_MAX=5
OZZB2B_RATE_LIMIT_REFRESH_MAX=30
OZZB2B_RATE_LIMIT_WINDOW_SECONDS=300

NEXT_PUBLIC_OZZB2B_API_URL=https://api.ozzb2b.com

# Phase 5.5 observability (Grafana admin login)
OZZB2B_GRAFANA_ADMIN_USER=${OZZB2B_GRAFANA_ADMIN_USER:-admin}
OZZB2B_GRAFANA_ADMIN_PASSWORD=${OZZB2B_GRAFANA_ADMIN_PASSWORD:?missing Grafana admin password}
EOF
chmod 600 .env.prod

log "render alertmanager.yml"
if [ -n "${OZZB2B_TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${OZZB2B_TELEGRAM_CHAT_ID:-}" ]; then
    # Use envsubst-free sed to avoid extra deps; tokens / chat id never go through
    # the shell's history (both live in /root/.ozzb2b_secrets, root-owned 600).
    sed \
        -e "s|__TELEGRAM_BOT_TOKEN__|${OZZB2B_TELEGRAM_BOT_TOKEN}|g" \
        -e "s|__TELEGRAM_CHAT_ID__|${OZZB2B_TELEGRAM_CHAT_ID}|g" \
        infra/alertmanager/alertmanager.yml.tmpl \
        > infra/alertmanager/alertmanager.yml
    log "alertmanager.yml rendered with Telegram receiver"
else
    cp infra/alertmanager/alertmanager.noop.yml infra/alertmanager/alertmanager.yml
    log "Telegram creds absent — using secret-free no-op receiver"
fi
chown root:65534 infra/alertmanager/alertmanager.yml
chmod 640 infra/alertmanager/alertmanager.yml

# Front proxy: this VPS also hosts unrelated sites on Apache. Prefer Apache
# reverse-proxy vhosts when Apache owns :80/:443; fall back to nginx only when
# nginx is the active public edge (legacy single-stack layout).
if systemctl is-active --quiet apache2 2>/dev/null && ! systemctl is-active --quiet nginx 2>/dev/null; then
    log "sync apache vhosts (Apache is public edge)"
    install -m 0644 infra/apache/api.ozzb2b.com.conf /etc/apache2/sites-available/api.ozzb2b.com.conf
    install -m 0644 infra/apache/ozzb2b.com.conf     /etc/apache2/sites-available/ozzb2b.com.conf
    install -m 0644 infra/apache/grafana.ozzb2b.com.conf /etc/apache2/sites-available/grafana.ozzb2b.com.conf
    a2ensite ozzb2b.com.conf api.ozzb2b.com.conf grafana.ozzb2b.com.conf >/dev/null
    apache2ctl configtest
    systemctl reload apache2
else
    log "sync nginx vhosts"
    # Existing vhost file on the VPS is /etc/nginx/sites-{available,enabled}/<host>
    # (no .conf suffix). Write to that exact path to avoid ending up with two vhosts.
    install -m 0644 infra/nginx/api.ozzb2b.com.conf /etc/nginx/sites-available/api.ozzb2b.com
    install -m 0644 infra/nginx/ozzb2b.com.conf     /etc/nginx/sites-available/ozzb2b.com
    ln -sf /etc/nginx/sites-available/api.ozzb2b.com /etc/nginx/sites-enabled/api.ozzb2b.com
    ln -sf /etc/nginx/sites-available/ozzb2b.com     /etc/nginx/sites-enabled/ozzb2b.com
    # Grafana vhost only enabled when its Let's Encrypt cert already exists;
    # certbot must be run manually the first time (deploy/vps_grafana_ssl.sh).
    if [ -f /etc/letsencrypt/live/grafana.ozzb2b.com/fullchain.pem ]; then
        install -m 0644 infra/nginx/grafana.ozzb2b.com.conf /etc/nginx/sites-available/grafana.ozzb2b.com
        ln -sf /etc/nginx/sites-available/grafana.ozzb2b.com /etc/nginx/sites-enabled/grafana.ozzb2b.com
        log "grafana vhost enabled"
    else
        log "grafana vhost skipped (no SSL cert yet; run deploy/vps_grafana_ssl.sh)"
    fi
    # Clean up any stray .conf variant we might have created on earlier attempts.
    rm -f /etc/nginx/sites-available/api.ozzb2b.com.conf /etc/nginx/sites-enabled/api.ozzb2b.com.conf
    rm -f /etc/nginx/sites-available/ozzb2b.com.conf     /etc/nginx/sites-enabled/ozzb2b.com.conf
    nginx -t && systemctl reload nginx
fi

log "ensure observability data dir ownership"
ensure_data_dir() {
    local path="$1"
    local owner="$2"
    local group="$3"
    install -d -m 0750 "$path"
    chown "$owner:$group" "$path"
}
ensure_data_dir /var/www/ozzb2b.com/data/prometheus 65534 65534
ensure_data_dir /var/www/ozzb2b.com/data/alertmanager 65534 65534
ensure_data_dir /var/www/ozzb2b.com/data/loki 10001 10001
ensure_data_dir /var/www/ozzb2b.com/data/grafana 472 0
install -d -m 0750 \
    /var/www/ozzb2b.com/data/promtail \
    /var/www/ozzb2b.com/data/meilisearch \
    /var/www/ozzb2b.com/data/clickhouse

log "docker compose up --build"
compose_args=(-f compose.prod.yml --profile alerts)
docker compose "${compose_args[@]}" up -d --build

log "synchronize Grafana admin password"
grafana_password_synced=0
for _ in $(seq 1 15); do
    if docker compose -f compose.prod.yml exec -T grafana \
        grafana cli admin reset-admin-password "$OZZB2B_GRAFANA_ADMIN_PASSWORD" \
        >/dev/null 2>&1; then
        grafana_password_synced=1
        break
    fi
    sleep 2
done
if [ "$grafana_password_synced" -ne 1 ]; then
    log "failed to synchronize Grafana admin password"
    exit 1
fi

# Compose may create a new br-* after first up. Keep UFW open for Docker
# subnets without restarting Postgres/Redis on every deploy.
for iface in $(ip -4 -br addr | awk '/^br-/{print $1}'); do
    ufw allow in on "$iface" to any port 5432 proto tcp >/dev/null 2>&1 || true
    ufw allow in on "$iface" to any port 6379 proto tcp >/dev/null 2>&1 || true
done

# Wait for the API container to become healthy before running migrations
# against it. The compose healthcheck targets /health which doesn't touch
# the DB, so we additionally probe /ready (which does) before applying
# migrations to fail fast if the container can't reach Postgres at all.
log "wait for api /ready"
ready=0
for _ in $(seq 1 30); do
    if docker compose -f compose.prod.yml exec -T api \
        python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/ready',timeout=2).getcode()==200 else 1)" \
        >/dev/null 2>&1; then
        ready=1
        break
    fi
    sleep 2
done
if [ "$ready" -ne 1 ]; then
    log "api /ready never returned 200; aborting before migrations"
    docker compose -f compose.prod.yml ps
    exit 1
fi

# Always run migrations after the new image is up. Alembic upgrades are
# additive in this codebase (expand-then-contract pattern), so re-running an
# already-applied migration is a no-op. Doing this in the deploy script
# means a fresh release never serves traffic against an out-of-date schema.
log "run alembic migrations"
bash deploy/vps_migrate.sh

# Run the latest smoke suite so a regression in container start-up,
# nginx routing or core flow trips the deploy here instead of being
# noticed by users. Fall through if no phase smoke script exists yet.
latest_smoke=$(ls deploy/vps_smoke_phase*.sh 2>/dev/null | sort -V | tail -n1 || true)
if [ -n "${latest_smoke:-}" ] && [ -f "$latest_smoke" ]; then
    log "post-deploy smoke: $latest_smoke"
    if ! bash "$latest_smoke"; then
        log "smoke failed; rolling back to previous git ref"
        git reset --hard HEAD@{1} || true
        docker compose "${compose_args[@]}" up -d --build
        exit 1
    fi
fi

docker compose -f compose.prod.yml ps
