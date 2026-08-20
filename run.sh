#!/bin/bash
# Kill any existing instances
kill $(lsof -ti:8000) 2>/dev/null
kill $(lsof -ti:3000) 2>/dev/null
sleep 1

echo "========================================="
echo "   JobApply AI - Starting Everything"
echo "========================================="

# Start Backend
echo ""
echo "[1/2] Starting Backend on port 8000..."
cd /home/prasad_0727/Documents/Job_apply_platfroms/backend
setsid python3.11 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log > /tmp/jobapply_backend.log 2>&1 &
echo "   Backend PID: $!"
sleep 3

# Start Frontend
echo "[2/2] Starting Frontend on port 3000..."
cd /home/prasad_0727/Documents/Job_apply_platfroms/frontend
setsid npm run dev > /tmp/jobapply_frontend.log 2>&1 &
echo "   Frontend PID: $!"
sleep 5

echo ""
echo "========================================="
echo "   JobApply AI is Running!"
echo "========================================="
echo ""
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "   Logs:"
echo "     Backend:  tail -f /tmp/jobapply_backend.log"
echo "     Frontend: tail -f /tmp/jobapply_frontend.log"
echo ""
echo "   Stop: kill \$(lsof -ti:8000) \$(lsof -ti:3000)"
echo "========================================="
