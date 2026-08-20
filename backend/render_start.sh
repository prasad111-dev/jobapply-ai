#!/usr/bin/env bash
set -e
cd backend
export PYTHONUNBUFFERED=1
export ENVIRONMENT=${ENVIRONMENT:-production}
exec gunicorn app.main:app \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -