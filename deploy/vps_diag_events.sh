#!/usr/bin/env bash
# Diagnose why events are not landing in ClickHouse.
# Prints: Redis stream length, pending entries, consumer group info,
# events consumer logs tail, clickhouse row count.
set -u
set +e  # keep going through each check

ENV_FILE=/var/www/ozzb2b.com/app/.env.prod
URL=$(grep -E '^OZZB2B_REDIS_URL=' "$ENV_FILE" | sed 's/^[^=]*=//')

# URL format: redis://:PASSWORD@HOST:PORT/DB
PASSWORD=$(printf '%s' "$URL" | sed -E 's#^redis://:([^@]*)@.*$#\1#')
HOST=$(printf '%s' "$URL" | sed -E 's#^redis://:[^@]*@([^:/]+):.*#\1#')
PORT=$(printf '%s' "$URL" | sed -E 's#^redis://:[^@]*@[^:]+:([0-9]+).*#\1#')
DB=$(printf '%s' "$URL" | sed -E 's#^redis://:[^@]*@[^/]+/([0-9]+).*#\1#')

if [ "$HOST" = "host.docker.internal" ]; then
  HOST=127.0.0.1
fi

echo "redis host=$HOST port=$PORT db=$DB"

export REDISCLI_AUTH="$PASSWORD"

echo "--- XLEN ozzb2b:events:v1 ---"
redis-cli -h "$HOST" -p "$PORT" -n "$DB" XLEN ozzb2b:events:v1

echo "--- XINFO GROUPS ozzb2b:events:v1 ---"
redis-cli -h "$HOST" -p "$PORT" -n "$DB" XINFO GROUPS ozzb2b:events:v1

echo "--- last 3 entries ---"
redis-cli -h "$HOST" -p "$PORT" -n "$DB" XREVRANGE ozzb2b:events:v1 + - COUNT 3

echo "--- events logs tail ---"
docker logs --tail 20 ozzb2b-events 2>&1

echo "--- api logs tail (filter) ---"
docker logs --tail 50 ozzb2b-api 2>&1 | grep -iE 'event|search_performed|provider_view' | tail -10

echo "--- clickhouse row count ---"
curl -sS 'http://127.0.0.1:8123/?database=ozzb2b' --data-binary 'SELECT count() FROM events FORMAT TSV'
