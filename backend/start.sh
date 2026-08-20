#!/bin/bash
echo "Starting JobApply AI Backend..."
echo "Running migrations..."
alembic upgrade head
echo "Seeding database..."
python -m app.core.seed
echo "Starting server..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
