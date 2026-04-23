#!/usr/bin/env bash
# Store Telegram alerting creds into /root/.ozzb2b_secrets and trigger a
# full stack re-apply so Alertmanager picks them up.
#
# Usage (run on the VPS, as root):
#   OZZB2B_TELEGRAM_BOT_TOKEN=... OZZB2B_TELEGRAM_CHAT_ID=... \
#     bash /var/www/ozzb2b.com/app/deploy/vps_set_telegram.sh

set -eu

SECRETS=/root/.ozzb2b_secrets
APP=${APP:-/var/www/ozzb2b.com/app}

if [ -z "${OZZB2B_TELEGRAM_BOT_TOKEN:-}" ] || [ -z "${OZZB2B_TELEGRAM_CHAT_ID:-}" ]; then
    echo "ERROR: both OZZB2B_TELEGRAM_BOT_TOKEN and OZZB2B_TELEGRAM_CHAT_ID must be set" >&2
    exit 1
fi

# Upsert both keys in the secrets file.
upsert() {
    local key=$1 value=$2
    if grep -q "^${key}=" "$SECRETS" 2>/dev/null; then
        sed -i "s|^${key}=.*|${key}=${value}|" "$SECRETS"
    else
        printf '%s=%s\n' "$key" "$value" >> "$SECRETS"
    fi
}

touch "$SECRETS"
chmod 600 "$SECRETS"
upsert OZZB2B_TELEGRAM_BOT_TOKEN "$OZZB2B_TELEGRAM_BOT_TOKEN"
upsert OZZB2B_TELEGRAM_CHAT_ID   "$OZZB2B_TELEGRAM_CHAT_ID"

echo "[telegram] secrets stored in $SECRETS"

install -d -m 0750 /var/www/ozzb2b.com/data/alertmanager

cd "$APP"
bash deploy/vps_apply_stack.sh

echo "[telegram] stack re-applied; alertmanager should be healthy shortly"
echo "Visit http://127.0.0.1:9093 (or SSH tunnel) to inspect active alerts."
