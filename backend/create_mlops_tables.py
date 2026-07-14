import asyncio
from database.db import engine, Base
from database.orm import *

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("MLOps tables created successfully!")

if __name__ == "__main__":
    asyncio.run(main())
