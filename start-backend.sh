#!/bin/bash

# Exit if any command fails
set -e

# Go to backend directory
cd "$(dirname "$0")/backend"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Run FastAPI with Uvicorn
echo "🚀 Starting FastAPI backend at http://127.0.0.1:8000 ..."
uvicorn main:app --reload

# Deactivate venv after exit
deactivate
