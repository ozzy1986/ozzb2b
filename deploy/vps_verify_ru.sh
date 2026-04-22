#!/usr/bin/env bash
# Verify the RU outsourcing ingest: print totals, by-country breakdown and
# a sample of RU rows with their resolved city / legal_form / contacts.
set -euo pipefail

SECRETS=/root/.ozzb2b_secrets
# shellcheck disable=SC1090
set -a
source "$SECRETS"
set +a

PG="psql -h 127.0.0.1 -U ozzb2b -d ozzb2b -tAc"
export PGPASSWORD="$OZZB2B_DB_PASSWORD"

echo "== providers_total =="
$PG "SELECT COUNT(*) FROM providers;"

echo "== by_source =="
$PG "SELECT source, COUNT(*) FROM providers GROUP BY source ORDER BY 2 DESC;"

echo "== by_country =="
$PG "SELECT c.code, COUNT(*) FROM providers p LEFT JOIN countries c ON c.id=p.country_id GROUP BY c.code ORDER BY 2 DESC;"

echo "== ru_rows =="
$PG "SELECT p.display_name || ' | ' || COALESCE(ci.name,'-') || ' | ' || COALESCE(lf.code,'-') || ' | ' || COALESCE(p.email,'-') || ' | ' || COALESCE(p.phone,'-')
       FROM providers p
       LEFT JOIN cities ci ON ci.id=p.city_id
       LEFT JOIN legal_forms lf ON lf.id=p.legal_form_id
       LEFT JOIN countries c ON c.id=p.country_id
       WHERE c.code='RU'
       ORDER BY p.display_name;"

echo "== api_smoke =="
curl -s 'http://127.0.0.1:8001/catalog/providers?country=RU&per_page=5' | head -c 800 | sed 's/,/,\n/g' | head -n 20
