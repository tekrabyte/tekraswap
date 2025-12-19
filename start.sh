#!/bin/bash

# Start MongoDB
echo "Starting MongoDB..."
sudo systemctl start mongodb || docker start mongodb || echo "MongoDB might already be running"

# Start Backend
echo "Starting Backend API..."
cd /app/backend
uvicorn main:app --host 0.0.0.0 --port 8001 --reload &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Start Frontend
echo "Starting Frontend..."
cd /app/frontend
yarn dev --host 0.0.0.0 --port 3000 &
FRONTEND_PID=$!

echo "\n=================================="
echo "Jupiter Swap Widget is running!"
echo "=================================="
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8001"
echo "API Docs: http://localhost:8001/docs"
echo "=================================="
echo "\nPress Ctrl+C to stop all services"

# Wait for interrupt
wait
