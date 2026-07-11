import asyncio
import asyncpg

async def create_db():
    try:
        # Connect to the default 'postgres' database to create the new one
        conn = await asyncpg.connect(user='postgres', password='Naveen@2007', host='127.0.0.1', port=5432, database='postgres')
        
        # Check if database exists
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = 'datavision'")
        if not exists:
            # Create database cannot be run inside a transaction block
            await conn.execute('CREATE DATABASE datavision')
            print("Database 'datavision' created successfully!")
        else:
            print("Database 'datavision' already exists.")
            
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(create_db())
