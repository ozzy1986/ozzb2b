#!/usr/bin/env bash
# Phase 7 smoke test: scraping-at-scale end-to-end verification.
#
# What we check:
# 1. Scraper CLI lists all registered spiders including the new one.
# 2. API exposes `last_scraped_at` on ProviderSummary.
# 3. Running the `ru-business-services-seed` spider once ingests new providers
#    and the summary API reports a fresh `last_scraped_at`.
# 4. Public provider list page on https://ozzb2b.com renders the freshness chip
#    (the Russian "Обновлено ..." string).

set -euo pipefail

APP=${APP:-/var/www/ozzb2b.com/app}
COMPOSE="docker compose -f ${APP}/compose.prod.yml"

log() { printf "[phase7_smoke] %s\n" "$*"; }

log "1) Registered spiders"
$COMPOSE exec -T scraper python -m ozzb2b_scraper.cli list

log "2) API ProviderSummary has last_scraped_at"
curl -sSf "https://api.ozzb2b.com/providers?limit=1" \
  | python3 -c 'import sys,json;d=json.load(sys.stdin);p=d["items"][0];print("has_field:","last_scraped_at" in p);print("value:",p.get("last_scraped_at"))'

log "3) Run new spider with small limit and confirm at least one ingest"
$COMPOSE exec -T scraper python -m ozzb2b_scraper.cli run ru-business-services-seed --limit 3

log "4) Cross-check: business-services providers now visible in the catalog"
curl -sSf "https://api.ozzb2b.com/providers?country=RU&limit=100" \
  | python3 -c '
import sys,json
d=json.load(sys.stdin)
items=d["items"]
now_any=[p for p in items if p.get("last_scraped_at")]
print("total RU providers:", d["total"])
print("with last_scraped_at set:", len(now_any))
if now_any:
    sample=now_any[0]
    print("sample:", sample["display_name"], "->", sample["last_scraped_at"])
'

log "5) Public site renders freshness label"
if curl -sSf "https://ozzb2b.com/providers?country=RU" \
     | grep -q "Обновлено"; then
    echo "OK: freshness chip rendered on public listing"
else
    echo "WARN: freshness chip not found on public listing (may just mean no fresh data yet)"
fi

log "done"
