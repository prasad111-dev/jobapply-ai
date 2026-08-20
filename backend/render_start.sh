#!/usr/bin/env bash
set -e
cd backend
export PYTHONUNBUFFERED=1
export ENVIRONMENT=${ENVIRONMENT:-production}
# Free tier: no persistent disk, so default to a writable folder on the container
# (ephemeral - wiped on redeploy - but keeps resume uploads working between requests)
BACKEND_ROOT="$(pwd)"
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$BACKEND_ROOT/../playwright_cache}"
export RESUME_STORAGE_PATH="${RESUME_STORAGE_PATH:-$BACKEND_ROOT/uploads}"
mkdir -p "$RESUME_STORAGE_PATH"

exec gunicorn app.main:app \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -