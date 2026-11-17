#!/bin/sh
set -eu
cd /home/ubuntu/helmar-reposteria

if [ ! -f .env ]; then
  python3 - << 'PY'
import secrets
from pathlib import Path
password = secrets.token_hex(24)
secret = secrets.token_urlsafe(48)
Path(".env").write_text(
    "\n".join([
        "DEBUG=False",
        f"SECRET_KEY={secret}",
        "ALLOWED_HOSTS=helymar.com,www.helymar.com",
        "CSRF_TRUSTED_ORIGINS=https://helymar.com,https://www.helymar.com",
        "POSTGRES_DB=helymar",
        "POSTGRES_USER=helymar",
        f"POSTGRES_PASSWORD={password}",
        "HELYMAR_WHATSAPP_NUMBER=",
        "",
    ]),
    encoding="utf-8",
)
Path(".env").chmod(0o600)
PY
fi

docker compose up -d --build

ready=0
i=0
while [ "$i" -lt 60 ]; do
  if curl -fsS --max-time 3 -H "Host: helymar.com" http://127.0.0.1:8001/ >/dev/null 2>&1; then
    ready=1
    break
  fi
  i=$((i + 1))
  sleep 5
done
if [ "$ready" -ne 1 ]; then
  docker compose logs --tail 80 web
  echo "La aplicación no respondió a tiempo." >&2
  exit 1
fi

admin_password="$(python3 -c 'import secrets; print(secrets.token_urlsafe(18))')"
docker compose exec -T -e ADMIN_PASSWORD="$admin_password" web python - << 'PY'
import os
import django
django.setup()
from apps.accounts.models import User
username = "admin"
if User.objects.filter(username=username).exists():
    print("ADMIN_STATUS=exists")
else:
    User.objects.create_superuser(
        username=username,
        email="admin@helymar.com",
        password=os.environ["ADMIN_PASSWORD"],
        role="administrador",
    )
    print("ADMIN_STATUS=created")
    print("ADMIN_USERNAME=admin")
    print("ADMIN_PASSWORD=" + os.environ["ADMIN_PASSWORD"])
PY

sudo cp deploy/apache/helymar.conf /etc/apache2/sites-available/helymar.conf
sudo a2ensite helymar.conf
sudo apache2ctl configtest
sudo systemctl reload apache2

if [ ! -f /etc/letsencrypt/live/helymar.com/fullchain.pem ]; then
  sudo certbot certonly --webroot -w /var/www/html -d helymar.com -d www.helymar.com --non-interactive --agree-tos --register-unsafely-without-email --keep-until-expiring
fi

sudo cp deploy/apache/helymar-le-ssl.conf /etc/apache2/sites-available/helymar-le-ssl.conf
sudo a2ensite helymar-le-ssl.conf
sudo apache2ctl configtest
sudo systemctl reload apache2
