import asyncio
import asyncpg
from urllib.parse import urlparse

async def main():
    try:
        conn = await asyncpg.connect("postgresql://datavision:datavision_dev@localhost:5433/datavision")
        print("Successfully connected!")
        
        # Check if joined_at exists
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name='workspace_members' AND column_name='joined_at'
            );
        """)
        print(f"joined_at exists: {exists}")
        
        if not exists:
            print("Adding joined_at...")
            await conn.execute("ALTER TABLE workspace_members ADD COLUMN joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL;")
            print("Added successfully!")
            
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(main())
