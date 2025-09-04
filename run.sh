#!/bin/bash

# Project directory
PROJECT_DIR="/home/kida-01/Desktop/Kida-Robot"
cd "$PROJECT_DIR"

# Activate virtual environment if present
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Infinite loop to restart on crash
while true; do
    echo "Starting main.py at $(date)"
    python3 scripts/main.py
    echo "main.py crashed with exit code $? — restarting in 5 seconds..."
    sleep 5
done
