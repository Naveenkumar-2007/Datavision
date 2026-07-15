import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator
import logging

logger = logging.getLogger(__name__)

# Fallback to local SQLite if Postgres URL is not provided
# In production, set DATABASE_URL="postgresql://user:password@localhost/datavision"
default_db_path = "/data/datavision.db" if os.path.exists("/data") else "./datavision.db"
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{default_db_path}")

try:
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
        )
    else:
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    SessionLocal = None
    Base = None

def get_db() -> Generator:
    """FastAPI Dependency for database sessions."""
    if not SessionLocal:
        yield None
        return
        
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
