#!/bin/bash
set -e

# Use PORT from environment or default to 8000
export PORT="${PORT:-8000}"

echo "============================================"
echo "Starting YouTube Social Listening API"
echo "Port: $PORT"
echo "Environment: ${RAILWAY_ENVIRONMENT:-local}"
echo "============================================"

# Start uvicorn with the PORT from environment
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1

