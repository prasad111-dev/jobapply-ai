#!/usr/bin/env bash
set -e
cd backend
export PYTHONUNBUFFERED=1
export ENVIRONMENT=${ENVIRONMENT:-production}
export PLAYWRIGHT_BROWSERS_PATH=${PLAYWRIGHT_BROWSERS_PATH:-/data/playwright}
export RESUME_STORAGE_PATH=${RESUME_STORAGE_PATH:-/data/uploads/resumes}
mkdir -p "$RESUME_STORAGE_PATH" 2>/dev/null || true

exec gunicorn app.main:app \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -