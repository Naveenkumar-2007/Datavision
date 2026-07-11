from sqlalchemy import Column, String, Text, DateTime, JSON
from datetime import datetime
from core.database import Base

class DataConnection(Base):
    __tablename__ = "data_connections"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    source_type = Column(String, nullable=False)  # postgres, snowflake, kafka
    host = Column(String, nullable=False)
    database_name = Column(String, nullable=False)
    target_table = Column(String, nullable=False)
    credentials = Column(Text, nullable=False)  # In production, this should be encrypted
    created_at = Column(DateTime, default=datetime.utcnow)
