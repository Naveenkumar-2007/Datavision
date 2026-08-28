import os
import uuid
import logging
from typing import Any
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

logger = logging.getLogger(__name__)

# Database configuration
# Requires format: postgresql+asyncpg://user:password@localhost/dbname
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql+asyncpg://datavision:datavision_dev@localhost:5433/datavision"
)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

if "?sslmode=require" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("?sslmode=require", "?ssl=require")
elif "&sslmode=require" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("&sslmode=require", "&ssl=require")

# Async Engine with Enterprise High-Concurrency Connection Pooling
engine = create_async_engine(
    DATABASE_URL, 
    echo=False, 
    future=True,
    pool_size=25,
    max_overflow=35,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    autocommit=False, 
    autoflush=False, 
    expire_on_commit=False,
    class_=AsyncSession
)

from app.models.base import Base

# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            if session.is_active:
                try:
                    await session.commit()
                except Exception:
                    await session.rollback()
        except Exception:
            if session.is_active:
                await session.rollback()
            raise
        finally:
            await session.close()

async def ensure_user_exists(db: AsyncSession, user_id: Any) -> uuid.UUID:
    """Ensure a user record exists in the users table to prevent ForeignKeyViolation errors."""
    import uuid as _uuid
    import hashlib
    from sqlalchemy import text
    
    if isinstance(user_id, _uuid.UUID):
        uid = user_id
    else:
        try:
            uid = _uuid.UUID(str(user_id))
        except (ValueError, AttributeError):
            uid = _uuid.uuid5(_uuid.NAMESPACE_OID, str(user_id))
            
    email_hash = hashlib.md5(str(uid).encode()).hexdigest()[:10]
    email = f"user_{email_hash}@datavision.local"
    
    try:
        # Check if user already exists
        check_res = await db.execute(text("SELECT 1 FROM users WHERE id = :id"), {"id": str(uid)})
        if check_res.scalar():
            return uid

        # Insert inside a savepoint so failure never aborts outer transaction
        async with db.begin_nested():
            await db.execute(
                text("""
                    INSERT INTO users (id, email, full_name, is_active, created_at, updated_at)
                    VALUES (:id, :email, :full_name, true, NOW(), NOW())
                    ON CONFLICT (id) DO NOTHING
                """),
                {"id": str(uid), "email": email, "full_name": "DataVision User"}
            )
            await db.flush()
    except Exception as e:
        logger.warning(f"Could not auto-create user {uid}: {e}")
        
    return uid


