#!/bin/bash

# DataVision AI — Production Startup script for Hugging Face Spaces & Containers

echo "🚀 Starting DataVision AI Platform (Fresh Deployment)..."

cd /app/backend

# Initialize fresh database migrations and seed default roles/admin user if DATABASE_URL is present
if [ -n "$DATABASE_URL" ]; then
    echo "📦 [1/2] Initializing fresh database schema..."
    
    # Auto-healing check for legacy v1 schema or orphan tables
    python -c "
import asyncio
from sqlalchemy import text
from database.db import engine

async def auto_clean_legacy_schema():
    try:
        async with engine.begin() as conn:
            # Check if old v1 'profiles' table exists
            res = await conn.execute(text(\"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'profiles')\"))
            has_profiles = res.scalar()
            if has_profiles:
                print('⚠️ Legacy v1 database schema detected. Performing automated fresh schema reset...')
                await conn.execute(text('DROP SCHEMA public CASCADE'))
                await conn.execute(text('CREATE SCHEMA public'))
                await conn.execute(text('GRANT ALL ON SCHEMA public TO public'))
    except Exception as e:
        print(f'DB verification notice: {e}')

asyncio.run(auto_clean_legacy_schema())
" 2>/dev/null || true

    # Clean stale alembic version from legacy migrations
    python -c "
import asyncio
from sqlalchemy import text
from database.db import engine

async def fix_alembic():
    try:
        async with engine.begin() as conn:
            await conn.execute(text('DROP TABLE IF EXISTS alembic_version'))
    except:
        pass

asyncio.run(fix_alembic())
" 2>/dev/null || true

    # Run migrations to create any missing tables
    alembic upgrade head || echo "⚠️ Migration warning: check DB logs"

    echo "🌱 [2/2] Seeding fresh system roles, permissions, and super admin user..."
    python -m app.database.seed || echo "⚠️ Seed warning: check DB logs"
else
    echo "ℹ️ DATABASE_URL not set. Running with default configuration."
fi

echo "🟢 Starting FastAPI Uvicorn server via python main.py..."
export PORT=${PORT:-7860}
exec python main.py
