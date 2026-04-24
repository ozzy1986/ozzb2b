#!/usr/bin/env bash
set -euo pipefail
APP="/var/www/ozzb2b.com/app"
BACK="/root/ozzb2b-app-back-$(date +%Y%m%d-%H%M%S)"
if [ -d "$APP" ]; then
  mv "$APP" "$BACK"
fi
export GIT_SSH_COMMAND="ssh -i /root/.ssh/ozzb2b_deploy -o IdentitiesOnly=yes"
git clone "git@github.com:ozzy1986/ozzb2b.git" "$APP"
cd "$APP"
git checkout master
if [ -d "$BACK" ] && [ -f "$BACK/.env.prod" ]; then
  cp "$BACK/.env.prod" "$APP/.env.prod"
  chmod 600 "$APP/.env.prod"
  echo "restored .env.prod from $BACK"
fi
git pull --ff-only origin master
git log -1 --oneline
