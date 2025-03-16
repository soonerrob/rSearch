#!/bin/bash

# Get the absolute path to the project root directory
PROJECT_ROOT="/home/rj-linux/PycharmProjects/gummysearch"
BACKEND_DIR="$PROJECT_ROOT/backend"
PORT=8001

# Function to check if port is in use
is_port_in_use() {
    lsof -i ":$PORT" > /dev/null
    return $?
}

# Function to get PID of process using our port
get_port_pid() {
    lsof -t -i ":$PORT"
}

# Function to kill existing server
kill_server() {
    echo "Checking for processes on port $PORT..."
    
    # First try: Check if port is in use
    if is_port_in_use; then
        PID=$(get_port_pid)
        if [ ! -z "$PID" ]; then
            echo "Killing process $PID using port $PORT..."
            sudo kill -9 $PID
            sleep 2
        fi
    fi
    
    # Second try: Kill any uvicorn processes
    if pgrep -f "uvicorn app.main:app" > /dev/null; then
        echo "Killing uvicorn processes..."
        sudo pkill -9 -f "uvicorn app.main:app"
        sleep 2
    fi
    
    # Final check
    if is_port_in_use; then
        echo "ERROR: Failed to free port $PORT"
        exit 1
    fi
    
    echo "Port $PORT is now free"
}

# Function to start server
start_server() {
    if [ ! -d "$BACKEND_DIR" ]; then
        echo "ERROR: Backend directory not found: $BACKEND_DIR"
        exit 1
    fi
    
    echo "Starting server from $BACKEND_DIR"
    cd "$BACKEND_DIR" || exit 1
    uvicorn app.main:app --reload --port $PORT
}

# Main script
case "$1" in
    "start")
        kill_server
        start_server
        ;;
    "stop")
        kill_server
        ;;
    "restart")
        kill_server
        start_server
        ;;
    *)
        echo "Usage: $0 {start|stop|restart}"
        exit 1
        ;;
esac 