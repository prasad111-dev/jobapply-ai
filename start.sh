#!/bin/bash
echo "========================================="
echo "   JobApply AI - Production Start"
echo "========================================="

echo ""
echo "[1/5] Starting PostgreSQL & Redis..."
docker-compose up -d db redis
sleep 3

echo ""
echo "[2/5] Installing Python dependencies..."
cd backend
pip install -r requirements.txt -q 2>/dev/null
playwright install chromium 2>/dev/null

echo ""
echo "[3/5] Running database migrations..."
alembic upgrade head 2>/dev/null || echo "Migrations skipped (no alembic configured)"

echo ""
echo "[4/5] Seeding database..."
python -m app.core.seed 2>/dev/null || echo "Seeding skipped"

echo ""
echo "[5/5] Starting Backend + Celery Worker..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
celery -A app.workers.celery_app worker --loglevel=info --concurrency=2 &
CELERY_PID=$!
cd ..

echo ""
echo "Starting Frontend..."
cd frontend
npm install --silent 2>/dev/null
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "========================================="
echo "   All Services Running!"
echo "========================================="
echo ""
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   Celery:    Worker running"
echo ""
echo "   Press Ctrl+C to stop all services"
echo "========================================="

trap "kill $BACKEND_PID $CELERY_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
