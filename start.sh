#!/bin/bash
echo ">>> Setting up GERT Environment..."

# Install Frontend Dependencies
if [ ! -d "node_modules" ]; then
  echo ">>> Installing Node modules..."
  npm install
fi

# Check if python venv exists (optional check, assuming python environment is managed by user or system)
# echo ">>> Ensure your Python environment is active and 'uvicorn' is installed."

echo ">>> Starting Services..."
echo "    - Backend: http://localhost:8000"
echo "    - Frontend: http://localhost:3000"

# Run both in parallel using &
python3 main.py &
npm run dev

# Trap Ctrl+C to kill both
trap "kill 0" EXIT