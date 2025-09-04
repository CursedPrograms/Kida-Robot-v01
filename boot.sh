#!/bin/bash

# Go to project directory
cd /home/kida-01/Desktop/Kida-Robot

# Activate virtual environment (ignore errors if not found)
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the Python script
python3 run.py
