#!/bin/sh
set -e

export PYTHONPATH="${PYTHONPATH:-/app}"

if [ "${RUN_DB_MIGRATIONS:-1}" = "1" ]; then
  echo "Running migrations..."
  alembic upgrade head
else
  echo "Skipping migrations (RUN_DB_MIGRATIONS=${RUN_DB_MIGRATIONS})"
fi

echo "Starting application..."
exec "$@"
