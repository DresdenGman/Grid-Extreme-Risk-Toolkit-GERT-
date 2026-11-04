#!/bin/bash
echo ">>> Setting up GERT Environment..."

# Setup Python Virtual Environment and Install Dependencies
if [ ! -d ".venv" ]; then
    echo ">>> Creating Python virtual environment (.venv)..."
    python3 -m venv .venv
fi
source .venv/bin/activate

if [ -f "requirements.txt" ]; then
    echo ">>> Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Install Frontend Dependencies
if [ ! -d "node_modules" ]; then
    echo ">>> Installing Node modules..."
    npm install
fi

echo ">>> Starting Services..."
echo "  - Backend: http://localhost:8000"
echo "  - Frontend: http://localhost:3000"

# Run both in parallel using &
python3 main.py &
npm run dev

# Trap Ctrl+C to kill both
trap "kill 0" EXIT
