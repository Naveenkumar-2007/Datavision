#!/bin/bash

# Start script for Hugging Face Spaces
# Serves both the FastAPI backend and React frontend

echo "🚀 Starting DataVision AI..."

cd /app/backend

# Run database migrations if DATABASE_URL is set
if [ -n "$DATABASE_URL" ]; then
    echo "📦 Running database migrations..."
    # We must use the synchronous connection string for alembic if it uses asyncpg
    # But usually Alembic handles async pg if configured correctly in env.py
    alembic upgrade head
else
    echo "⚠️ DATABASE_URL not set! Skipping database migrations."
fi

echo "🟢 Starting Uvicorn server..."
# Use uvicorn to serve the application
exec uvicorn main:app --host 0.0.0.0 --port 7860
