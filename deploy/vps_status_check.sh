#!/usr/bin/env bash
set -euo pipefail
sudo -u postgres psql -d ozzb2b <<'SQL'
SELECT status, COUNT(*) FROM providers GROUP BY status;
SQL
