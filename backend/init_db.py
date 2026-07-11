import asyncio
import os
import sys

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db import engine, Base
from database.orm import UserProfile, AdminUser, Conversation, Message
from database.models import *  # Ensure all models are loaded

async def init_models():
    async with engine.begin() as conn:
        print("Creating all database tables...")
        # Note: We won't drop tables here in production, but since this is init, it's safe if empty.
        # However, to be completely safe, we'll just create_all (it won't overwrite existing)
        await conn.run_sync(Base.metadata.create_all)
        print("Successfully created all tables!")

if __name__ == "__main__":
    asyncio.run(init_models())
