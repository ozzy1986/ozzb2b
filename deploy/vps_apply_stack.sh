#!/usr/bin/env bash
set -euo pipefail

APP="${APP:-/var/www/ozzb2b.com/app}"

log() { printf "[vps_apply_stack] %s\n" "$*"; }

cd "$APP"

export GIT_SSH_COMMAND="ssh -i /root/.ssh/ozzb2b_deploy -o IdentitiesOnly=yes"
log "git pull $(git rev-parse --short HEAD 2>/dev/null || echo '?') ..."
git fetch origin
git pull --ff-only origin main

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

OZZB2B_CORS_ORIGINS=https://ozzb2b.com,https://www.ozzb2b.com,https://api.ozzb2b.com
OZZB2B_LOG_LEVEL=INFO

NEXT_PUBLIC_OZZB2B_API_URL=https://api.ozzb2b.com
EOF
chmod 600 .env.prod

log "docker compose up --build"
docker compose -f compose.prod.yml up -d --build

docker compose -f compose.prod.yml ps
