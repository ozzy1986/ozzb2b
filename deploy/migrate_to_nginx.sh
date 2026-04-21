#!/usr/bin/env bash
# Global switch: Apache (public) -> nginx(public) + Apache(backend 127.0.0.1:8081)
set -euo pipefail

TS=$(date +%Y%m%d-%H%M%S)
BACKUP="/root/backups/migration-$TS"
BACKEND_PORT=8081
DRYRUN="${DRYRUN:-0}"

DOMAINS_APACHE_BACKEND=(
  "encarparse.ozzy1986.com"
  "laravel.ozzy1986.com"
  "mvp-python-react.ozzy1986.com"
  "round.ozzy1986.com"
  "site-generator.ozzy1986.com"
  "wordpress.ozzy1986.com"
  "xsiblings.com"
)

echo "[1/7] Backing up configs to $BACKUP"
mkdir -p "$BACKUP"
cp -a /etc/apache2 "$BACKUP/apache2"
cp -a /etc/nginx  "$BACKUP/nginx"

echo "[2/7] Rewriting Apache ports & vhosts to backend 127.0.0.1:$BACKEND_PORT"
cat > /etc/apache2/ports.conf <<EOF
# Managed: Apache is a backend behind nginx. TLS terminates at nginx.
Listen 127.0.0.1:$BACKEND_PORT
EOF

shopt -s nullglob
for f in /etc/apache2/sites-available/*.conf; do
  sed -i -E "s|<VirtualHost \*:80>|<VirtualHost 127.0.0.1:$BACKEND_PORT>|g; s|<VirtualHost \*:443>|<VirtualHost 127.0.0.1:$BACKEND_PORT>|g" "$f"
done

# Disable SSL vhosts; nginx terminates TLS now
a2dissite 'default-ssl' >/dev/null 2>&1 || true
for d in "${DOMAINS_APACHE_BACKEND[@]}"; do
  a2dissite "${d}-le-ssl.conf" >/dev/null 2>&1 || true
done

# Disable old Apache vhost for ozzb2b.com (becomes native nginx)
a2dissite 'ozzb2b.com.conf' >/dev/null 2>&1 || true

# Strip HTTPS-redirect RewriteRules from remaining :8081 vhosts (nginx handles redirect)
python3 - <<'PY'
import re, glob
paths = glob.glob('/etc/apache2/sites-available/*.conf')
patterns = [
    r"\nRewriteEngine on\nRewriteCond %\{SERVER_NAME\} =[^\n]+\nRewriteRule \^ https://%\{SERVER_NAME\}%\{REQUEST_URI\} \[END,NE,R=permanent\]\n",
    r"\nRewriteEngine on\nRewriteCond %\{SERVER_NAME\} =[^\n]+ \[OR\]\nRewriteCond %\{SERVER_NAME\} =[^\n]+\nRewriteRule \^ https://%\{SERVER_NAME\}%\{REQUEST_URI\} \[END,NE,R=permanent\]\n",
    r"    RewriteEngine On\n    RewriteCond %\{HTTPS\} off\n    RewriteRule \^\(\.\*\)\$ https://%\{HTTP_HOST\}\$1 \[R=301,L\]\n",
    r"    RewriteEngine on\n    RewriteCond %\{SERVER_NAME\} =[^\n]+\n    RewriteRule \^ https://%\{SERVER_NAME\}%\{REQUEST_URI\} \[END,NE,R=permanent\]\n",
]
for p in paths:
    s = open(p).read()
    orig = s
    for pat in patterns:
        s = re.sub(pat, "\n", s)
    if s != orig:
        open(p, 'w').write(s)
        print("cleaned:", p)
PY

echo "[3/7] apache2ctl configtest"
apache2ctl configtest

echo "[4/7] Writing nginx vhosts"
rm -f /etc/nginx/sites-enabled/mvp-python-react.ozzy1986.com \
      /etc/nginx/sites-enabled/round.ozzy1986.com \
      /etc/nginx/sites-enabled/round \
      /etc/nginx/sites-enabled/default 2>/dev/null || true

mkdir -p /etc/nginx/snippets
cat > /etc/nginx/snippets/ssl-modern.conf <<'EOF'
ssl_session_timeout 1d;
ssl_session_cache shared:MozSSL:10m;
ssl_session_tickets off;
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
add_header Strict-Transport-Security "max-age=63072000" always;
EOF

cat > /etc/nginx/snippets/proxy-to-apache.conf <<'EOF'
proxy_http_version 1.1;
proxy_set_header Host              $host;
proxy_set_header X-Real-IP         $remote_addr;
proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Forwarded-Host  $host;
proxy_read_timeout 300s;
proxy_send_timeout 300s;
client_max_body_size 64m;
EOF

gen_domain_conf() {
  local primary="$1"; shift
  local aliases="$*"
  local file="/etc/nginx/sites-available/${primary}"
  local cert="/etc/letsencrypt/live/${primary}/fullchain.pem"
  local key="/etc/letsencrypt/live/${primary}/privkey.pem"
  local all_names="$primary $aliases"
  cat > "$file" <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name $all_names;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $all_names;

    ssl_certificate     $cert;
    ssl_certificate_key $key;
    include snippets/ssl-modern.conf;

    access_log /var/log/nginx/${primary}_access.log;
    error_log  /var/log/nginx/${primary}_error.log;

    location / {
        include snippets/proxy-to-apache.conf;
        proxy_pass http://127.0.0.1:$BACKEND_PORT;
    }
}
EOF
  ln -sf "$file" "/etc/nginx/sites-enabled/${primary}"
}

gen_domain_conf "encarparse.ozzy1986.com"
gen_domain_conf "laravel.ozzy1986.com"
gen_domain_conf "mvp-python-react.ozzy1986.com"
gen_domain_conf "round.ozzy1986.com"
gen_domain_conf "site-generator.ozzy1986.com"
gen_domain_conf "wordpress.ozzy1986.com"
gen_domain_conf "xsiblings.com" "www.xsiblings.com"

cat > /etc/nginx/sites-available/ozzb2b.com <<'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name ozzb2b.com www.ozzb2b.com;
    root /var/www/ozzb2b.com;
    index index.html;
    access_log /var/log/nginx/ozzb2b.com_access.log;
    error_log  /var/log/nginx/ozzb2b.com_error.log;
    location /.well-known/acme-challenge/ {
        root /var/www/ozzb2b.com;
    }
    location / {
        try_files $uri $uri/ =404;
    }
}
EOF
ln -sf /etc/nginx/sites-available/ozzb2b.com /etc/nginx/sites-enabled/ozzb2b.com

echo "[5/7] nginx -t"
nginx -t

if [ "$DRYRUN" = "1" ]; then
  echo "DRYRUN=1 -> stopping before reload"
  exit 0
fi

echo "[6/7] Reloading Apache (switches to 127.0.0.1:$BACKEND_PORT)"
systemctl reload apache2 || systemctl restart apache2

echo "[6b/7] Starting/reloading nginx (binds :80/:443)"
systemctl reload nginx 2>/dev/null || systemctl restart nginx

sleep 1
echo "[7/7] Listener status"
ss -ltnp | awk '/:80 |:443 |:8081 /{print}'
