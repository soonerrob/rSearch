#!/bin/bash

echo "Starting server cleanup..."

# Function to check if a port is in use
check_port() {
    lsof -i ":$1" >/dev/null 2>&1
    return $?
}

# Function to kill process using a specific port
free_port() {
    local port=$1
    echo "Attempting to free port $port..."
    
    # Try gentle shutdown first
    if check_port "$port"; then
        echo "Attempting gentle shutdown of port $port..."
        fuser -k -n tcp "$port" 2>/dev/null
        sleep 2
    fi
    
    # If port is still in use, force kill
    if check_port "$port"; then
        echo "Force killing processes on port $port..."
        fuser -k -n tcp -9 "$port" 2>/dev/null
        sleep 2
    fi
    
    if ! check_port "$port"; then
        echo "Successfully freed port $port"
    else
        echo "Failed to free port $port"
        return 1
    fi
}

# Clean up existing processes
cleanup_processes() {
    echo "Cleaning up uvicorn processes..."
    pkill -f "uvicorn" 2>/dev/null
    
    echo "Cleaning up next processes..."
    pkill -f "next" 2>/dev/null
    
    # Wait for processes to fully terminate
    sleep 2
}

# Start the servers
start_servers() {
    echo "Starting backend server..."
    cd backend || { echo "Failed to change to backend directory"; exit 1; }
    uvicorn app.main:app --reload --port 8001 &
    BACKEND_PID=$!
    sleep 3  # Wait for backend to initialize
    
    if ! ps -p $BACKEND_PID > /dev/null; then
        echo "Backend server failed to start"
        exit 1
    fi
    echo "Backend server started successfully (PID: $BACKEND_PID)"
    
    echo "Starting frontend server..."
    cd ../frontend || { echo "Failed to change to frontend directory"; exit 1; }
    npm run dev &
    FRONTEND_PID=$!
    sleep 3  # Wait for frontend to initialize
    
    if ! ps -p $FRONTEND_PID > /dev/null; then
        echo "Frontend server failed to start"
        exit 1
    fi
    echo "Frontend server started successfully (PID: $FRONTEND_PID)"
    
    # Return to original directory
    cd ..
    
    # Store PIDs for future reference
    echo "$BACKEND_PID" > .backend.pid
    echo "$FRONTEND_PID" > .frontend.pid
    
    echo "Both servers are now running:"
    echo "Backend: http://localhost:8001 (PID: $BACKEND_PID)"
    echo "Frontend: http://localhost:3000 (PID: $FRONTEND_PID)"
}

# Main execution
free_port 8001
free_port 3000
cleanup_processes
echo "Server cleanup completed"

echo "Starting servers..."
start_servers

echo "Server management completed. Both servers should now be running." 