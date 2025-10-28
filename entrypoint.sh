#!/bin/sh

# Use PORT from environment or default to 8000
PORT=${PORT:-8000}

echo "Starting YouTube Social Listening API on port $PORT..."

# Start uvicorn with the PORT from environment
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --workers 1

