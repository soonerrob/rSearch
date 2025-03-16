#!/bin/bash

echo "Stopping any existing servers..."

# Kill any processes using ports 3000 (frontend) and 8001 (backend)
echo "Killing processes on ports 3000 and 8001..."
sudo lsof -ti:3000 | xargs -r sudo kill -9
sudo lsof -ti:8001 | xargs -r sudo kill -9

# Additional process killing for thoroughness
echo "Killing any remaining Next.js or Uvicorn processes..."
pkill -f "next"
pkill -f "uvicorn"

# Wait a moment to ensure processes are fully terminated
sleep 2

# Start frontend server
echo "Starting frontend server..."
cd frontend
npm run dev &

# Wait for frontend to start
sleep 5

# Start backend server
echo "Starting backend server..."
cd ../backend
source ../venv/bin/activate
uvicorn app.main:app --reload --port 8001 --log-level debug

echo "Servers should now be running:"
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:8001"
