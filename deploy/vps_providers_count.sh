#!/usr/bin/env bash
set -euo pipefail
sudo -u postgres psql -d ozzb2b <<'SQL'
SELECT COUNT(*) AS total FROM providers;
SELECT source, COUNT(*) AS n FROM providers GROUP BY source ORDER BY n DESC;
SELECT display_name, country_id, source FROM providers ORDER BY created_at DESC LIMIT 10;
SQL
