"""
Database Initialization Script — Delegates to app.database.seed
"""

import asyncio
import os
import sys

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.seed import run_seed

if __name__ == "__main__":
    print("🚀 Initializing DataVision production database...")
    asyncio.run(run_seed())
