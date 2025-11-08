#!/bin/bash
# S.Y.N.A.P.S.E. ENGINE Backend Startup Script

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 Starting S.Y.N.A.P.S.E. ENGINE Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
fi

# Start server
echo "✅ Starting uvicorn server on http://localhost:8000"
echo ""
echo "Available endpoints:"
echo "  - http://localhost:8000/health"
echo "  - http://localhost:8000/api/models/status"
echo "  - http://localhost:8000/api/docs (Swagger UI)"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
