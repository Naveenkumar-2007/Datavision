#!/bin/bash

# DataVision AI — Production Startup script for Hugging Face Spaces & Containers

echo "🚀 Starting DataVision AI Platform (Fresh Deployment)..."

cd /app/backend

# Initialize fresh database migrations and seed default roles/admin user if DATABASE_URL is present
if [ -n "$DATABASE_URL" ]; then
    echo "📦 [1/2] Initializing fresh database schema..."
    alembic stamp head 2>/dev/null || true
    alembic upgrade head || echo "⚠️ Migration warning: check DB logs"

    echo "🌱 [2/2] Seeding fresh system roles, permissions, and super admin user..."
    python -m app.database.seed || echo "⚠️ Seed warning: check DB logs"
else
    echo "ℹ️ DATABASE_URL not set. Running with default configuration."
fi

echo "🟢 Starting FastAPI Uvicorn server via python main.py..."
export PORT=${PORT:-7860}
exec python main.py
