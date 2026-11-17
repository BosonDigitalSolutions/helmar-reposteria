#!/bin/sh
set -eu
cd "$(dirname "$0")/.."

if [ ! -d .git ]; then
  echo "Esta carpeta no es un clon del repositorio." >&2
  exit 1
fi

if [ ! -f .env ]; then
  echo "Falta .env. No se despliega para no crear una base vacía." >&2
  exit 1
fi

git pull --ff-only
docker compose up -d --build
