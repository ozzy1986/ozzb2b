#!/usr/bin/env bash
# Run Alembic migrations and seed reference data inside the running API container.
set -euo pipefail

APP_DIR="/var/www/ozzb2b.com/app"
cd "$APP_DIR"

echo "[migrate] upgrade"
docker compose -f compose.prod.yml exec -T api python -m ozzb2b_api.db.cli migrate

echo "[migrate] seed"
docker compose -f compose.prod.yml exec -T api python -m ozzb2b_api.db.cli seed
