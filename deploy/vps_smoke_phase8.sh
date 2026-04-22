#!/usr/bin/env bash
# Phase 8 smoke test: claim-your-company flow.
#
# Verifies, against the real prod API:
# 1. Unauthenticated POST /providers/{slug}/claim is refused.
# 2. An ephemeral user can register, initiate a claim, and gets a token + meta-tag.
# 3. Verifying without publishing the tag returns 400 (meta tag missing).
# 4. The user's /me/claims lists the pending claim.
# 5. PATCH on a provider the user doesn't own is refused (403).
#
# Works without external dependencies; does NOT mutate any existing provider.

set -euo pipefail

API=${API:-https://api.ozzb2b.com}
SLUG=${SLUG:-agima}
TS=$(date -u +%s)
EMAIL="ozzb2b-smoke-${TS}@mailinator.com"
PASSWORD="test-password-${TS}"

log() { printf "[phase8_smoke] %s\n" "$*"; }
jar=$(mktemp)
trap 'rm -f "$jar"' EXIT

log "0) Provider to test against: ${SLUG}"
http_code=$(curl -sS -o /dev/null -w '%{http_code}' "${API}/providers/${SLUG}")
if [ "$http_code" != "200" ]; then
  echo "FAIL: no provider ${SLUG} (http ${http_code})"
  exit 1
fi

log "1) Unauthenticated claim is refused (expect 401)"
code=$(curl -sS -o /dev/null -w '%{http_code}' -X POST "${API}/providers/${SLUG}/claim")
if [ "$code" != "401" ]; then
  echo "FAIL: expected 401, got ${code}"
  exit 1
fi
echo "  OK: 401"

log "2) Register ephemeral user"
reg_status=$(curl -sS -c "$jar" -o /tmp/phase8_reg.json -w '%{http_code}' \
  -X POST "${API}/auth/register" \
  -H 'content-type: application/json' \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\",\"display_name\":\"phase8 smoke\"}")
if [ "$reg_status" != "201" ]; then
  echo "FAIL: register -> ${reg_status}"
  cat /tmp/phase8_reg.json
  exit 1
fi
echo "  OK: user registered, session cookie saved"

log "3) Initiate claim (expect 201 + meta-tag snippet)"
init_status=$(curl -sS -b "$jar" -c "$jar" -o /tmp/phase8_init.json -w '%{http_code}' \
  -X POST "${API}/providers/${SLUG}/claim")
if [ "$init_status" != "201" ]; then
  echo "FAIL: initiate -> ${init_status}"
  cat /tmp/phase8_init.json
  exit 1
fi
python3 -c '
import json, sys
data=json.load(open("/tmp/phase8_init.json"))
assert data["status"] == "pending", data
assert data["token"].startswith("ozzb2b-"), data
assert "<meta" in data["meta_tag"] and "ozzb2b-verify" in data["meta_tag"], data
print("  OK: token=", data["token"][:16] + "...")
'

log "4) Verify without publishing tag (expect 400/502)"
v_status=$(curl -sS -b "$jar" -c "$jar" -o /tmp/phase8_verify.json -w '%{http_code}' \
  -X POST "${API}/providers/${SLUG}/claim/verify")
case "$v_status" in
  400|502) echo "  OK: verification correctly refused (${v_status})";;
  *) echo "FAIL: unexpected verify status ${v_status}"; cat /tmp/phase8_verify.json; exit 1;;
esac

log "5) /me/claims lists the pending claim"
me_status=$(curl -sS -b "$jar" -o /tmp/phase8_me.json -w '%{http_code}' "${API}/me/claims")
if [ "$me_status" != "200" ]; then
  echo "FAIL: /me/claims -> ${me_status}"
  cat /tmp/phase8_me.json
  exit 1
fi
python3 -c '
import json
claims = json.load(open("/tmp/phase8_me.json"))
assert isinstance(claims, list) and claims, "expected non-empty list"
assert any(c["status"] == "pending" for c in claims), claims
print("  OK: pending claim visible in /me/claims")
'

log "6) PATCH on a provider the user does not own is refused (expect 403)"
patch_status=$(curl -sS -b "$jar" -o /dev/null -w '%{http_code}' \
  -X PATCH "${API}/providers/${SLUG}" \
  -H 'content-type: application/json' \
  -d '{"description":"owned by smoke"}')
if [ "$patch_status" != "403" ]; then
  echo "FAIL: expected 403, got ${patch_status}"
  exit 1
fi
echo "  OK: 403"

log "done"
