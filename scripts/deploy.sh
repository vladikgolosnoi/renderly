#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${PROJECT_ROOT}/infra/.env.production"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Production env file not found at ${ENV_FILE}"
  exit 1
fi

echo "[deploy] pulling git"
git -C "$PROJECT_ROOT" pull --ff-only

echo "[deploy] rebuilding containers"
docker compose --env-file "$ENV_FILE" -f "${PROJECT_ROOT}/infra/docker-compose.yml" up -d --build

echo "[deploy] running migrations"
docker compose --env-file "$ENV_FILE" -f "${PROJECT_ROOT}/infra/docker-compose.yml" exec api alembic upgrade head

echo "[deploy] done"
