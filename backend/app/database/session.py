"""
Database Session Module — Async engine and session factory.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import get_settings


def _create_engine():
    """Create the async SQLAlchemy engine from settings."""
    settings = get_settings()
    url = settings.DATABASE_URL
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    return create_async_engine(
        url,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=settings.DB_POOL_PRE_PING,
        pool_recycle=settings.DB_POOL_RECYCLE,
        echo=settings.DB_ECHO,
    )


_engine = None
_session_factory = None


def get_engine():
    """Get or create the global engine singleton."""
    global _engine
    if _engine is None:
        _engine = _create_engine()
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the global session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_db() -> AsyncSession:
    """
    FastAPI dependency — yields an async database session.

    Usage:
        @router.get("/users")
        async def list_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def dispose_engine():
    """Dispose the engine on shutdown."""
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None
