import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

# Database configuration
# Requires format: postgresql+asyncpg://user:password@localhost/dbname
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:Naveen%402007@127.0.0.1:5432/datavision"
)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

if "?sslmode=require" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("?sslmode=require", "?ssl=require")
elif "&sslmode=require" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("&sslmode=require", "&ssl=require")

# Async Engine
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    autocommit=False, 
    autoflush=False, 
    expire_on_commit=False,
    class_=AsyncSession
)

# Declarative Base for ORM Models
Base = declarative_base()

# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
