#!/bin/bash

# DataVision AI — Startup script for Hugging Face Spaces & Production Containers

echo "🚀 Starting DataVision AI Platform..."

cd /app/backend

# Run database migrations and seed default roles/admin user if DATABASE_URL is present
if [ -n "$DATABASE_URL" ]; then
    echo "📦 [1/2] Running database migrations..."
    alembic upgrade head || echo "⚠️ Migration warning: check DB logs"

    echo "🌱 [2/2] Seeding system roles, permissions, and admin user..."
    python -m app.database.seed || echo "⚠️ Seed warning: check DB logs"
else
    echo "ℹ️ DATABASE_URL not set. Running with default configuration."
fi

echo "🟢 Starting FastAPI Uvicorn server on port 7860..."
exec uvicorn app.main:app --host 0.0.0.0 --port 7860
