#!/usr/bin/env bash
# Start the Alice FastAPI server
# Usage: bash start.sh

cd "$(dirname "$0")"

# Install dependencies if needed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo "Starting Alice server at http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
uvicorn server:app --host 127.0.0.1 --port 8000 --reload
