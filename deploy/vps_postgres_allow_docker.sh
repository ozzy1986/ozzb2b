#!/usr/bin/env bash
# Allow the ozzb2b Docker containers to reach the host Postgres.
# We bind Postgres on all interfaces and restrict access at the firewall +
# pg_hba.conf level to the Docker bridge subnets. External access to 5432
# is still blocked by UFW default policy (DROP on INPUT).
set -euo pipefail

PG_CONF=$(ls /etc/postgresql/*/main/postgresql.conf | head -n 1)
PG_HBA=$(ls /etc/postgresql/*/main/pg_hba.conf    | head -n 1)

log() { printf "[pg-allow-docker] %s\n" "$*"; }

log "conf=$PG_CONF"
log "hba =$PG_HBA"

# Force listen_addresses to all interfaces (firewall and pg_hba constrain who gets in).
if grep -qE "^[^#]*listen_addresses" "$PG_CONF"; then
    sed -i -E "s|^([[:space:]]*)listen_addresses[[:space:]]*=.*|listen_addresses = '*'|" "$PG_CONF"
else
    echo "listen_addresses = '*'" >> "$PG_CONF"
fi
log "listen_addresses = '*'"

# Remove any previous ozzb2b entries we added (matching 172.17.0.0/16 or anything marked with this comment).
sed -i -E "/^# ozzb2b: allow the ozzb2b role from Docker bridge networks$/,+2d" "$PG_HBA" || true
sed -i -E "/^host[[:space:]]+ozzb2b[[:space:]]+ozzb2b[[:space:]]+172\.17\.0\.0\/16/d" "$PG_HBA" || true

# Add a single block allowing Docker subnets (17.x default + 19.x compose + 18.x spare).
cat >> "$PG_HBA" <<'EOF'
# ozzb2b: allow the ozzb2b role from Docker bridge networks
host    ozzb2b          ozzb2b          172.17.0.0/16           scram-sha-256
host    ozzb2b          ozzb2b          172.18.0.0/16           scram-sha-256
host    ozzb2b          ozzb2b          172.19.0.0/16           scram-sha-256
host    ozzb2b          ozzb2b          172.20.0.0/16           scram-sha-256
host    ozzb2b          ozzb2b          172.21.0.0/16           scram-sha-256
EOF
log "pg_hba: docker subnets granted"

systemctl restart postgresql
log "postgresql restarted"

# Firewall: allow the docker bridges to reach 5432; external still blocked by default DROP.
ufw allow in on docker0 to any port 5432 proto tcp || true
for iface in $(ip -4 -br addr | awk '/^br-/{print $1}'); do
    ufw allow in on "$iface" to any port 5432 proto tcp || true
done
ufw reload

ss -ltnp | awk '/:5432 /{print}'
