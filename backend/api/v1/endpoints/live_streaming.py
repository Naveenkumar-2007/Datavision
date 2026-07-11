from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, Header
from pydantic import BaseModel
import asyncio
import logging

logger = logging.getLogger(__name__)
import json
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any

from core.connectors.postgres import PostgresConnector
from core.connectors.snowflake_connector import SnowflakeConnector
from core.connectors.kafka_connector import KafkaConnector

# In-memory store for streaming sessions (will be replaced with PostgreSQL persistence)
# In prod, this interacts with public.data_connections
MOCK_DB_CONNECTIONS: Dict[str, Dict[str, Any]] = {}

router = APIRouter()

from core.auth import get_current_user, AuthenticatedUser
from database.db import get_db
from database.orm import DataConnection
from sqlalchemy.ext.asyncio import AsyncSession

class ConnectionRequest(BaseModel):
    source_type: str # 'postgres', 'snowflake', 'kafka'
    host: str
    database_name: str
    target_table: str
    credentials: str

@router.post("/connections")
async def create_connection(
    req: ConnectionRequest,
    user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Securely store user connection credentials in the native postgres DB.
    Returns a connection_id that the WebSocket can use to authenticate and stream.
    """
    # 🔍 Deduplication / Conflict Logic
    from sqlalchemy import select
    existing_result = await db.execute(select(DataConnection).where(DataConnection.user_id == user.id))
    existing_connections = existing_result.scalars().all()
    
    # 1. Check if exact same connection exists (Same Data = Don't Delete)
    for conn in existing_connections:
        if (conn.source_type == req.source_type and 
            conn.host == req.host and 
            conn.database_name == req.database_name and 
            conn.target_table == req.target_table):
            return {"connection_id": str(conn.id), "status": "success", "message": "Connection already exists. Data kept."}
            
    # 2. Check if DIFFERENT connections exist (Different Data = Tell User to Delete)
    if len(existing_connections) > 0:
        raise HTTPException(
            status_code=409, 
            detail="⚠️ Different dataset detected! Please delete your previous data connections first to avoid AI context conflicts."
        )

    conn_id = str(uuid4())
    
    # Store in the native Datavision PostgreSQL database (data_connections table)
    new_connection = DataConnection(
        id=conn_id,
        user_id=user.id,
        source_type=req.source_type,
        host=req.host,
        database_name=req.database_name,
        target_table=req.target_table,
        credentials=req.credentials
    )
    db.add(new_connection)
    await db.commit()
    
    # Clear the user's DataFrame cache so AI tools pull the new live stream
    from api.v1.endpoints.charts import clear_user_cache
    clear_user_cache(user.id)
    
    return {"connection_id": conn_id, "status": "success"}

@router.get("/connections")
async def get_connections(
    user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch all active live connections for the user."""
    from sqlalchemy import select
    result = await db.execute(select(DataConnection).where(DataConnection.user_id == user.id).order_by(DataConnection.created_at.desc()))
    connections = result.scalars().all()
    
    return {
        "connections": [
            {
                "id": str(conn.id),
                "source_type": conn.source_type,
                "host": conn.host,
                "database_name": conn.database_name,
                "target_table": conn.target_table,
                "created_at": conn.created_at.isoformat()
            }
            for conn in connections
        ]
    }

@router.delete("/connections/{connection_id}")
async def delete_connection(
    connection_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a live connection."""
    from sqlalchemy import select
    result = await db.execute(select(DataConnection).where(DataConnection.id == connection_id, DataConnection.user_id == user.id))
    conn = result.scalar_one_or_none()
    
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
        
    await db.delete(conn)
    await db.commit()
    
    # Clear the user's DataFrame cache so AI tools update immediately
    from api.v1.endpoints.charts import clear_user_cache
    clear_user_cache(user.id)
    
    return {"status": "success"}

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

manager = ConnectionManager()

from database.db import AsyncSessionLocal
from sqlalchemy import select

@router.websocket("/ws/live-data/{connection_id}")
async def websocket_live_data(websocket: WebSocket, connection_id: str):
    """
    WebSocket endpoint for streaming real telemetry using actual connection classes.
    """
    await manager.connect(websocket)
    
    # Fetch credentials from native Postgres DB without holding the session open indefinitely
    conn_data = None
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(DataConnection).where(DataConnection.id == connection_id))
        db_conn = result.scalar_one_or_none()
        if db_conn:
            conn_data = {
                "source_type": db_conn.source_type,
                "host": db_conn.host,
                "database_name": db_conn.database_name,
                "target_table": db_conn.target_table,
                "credentials": db_conn.credentials
            }
            
    if not conn_data:
        await websocket.send_text(json.dumps({"error": "Invalid connection ID or unauthorized."}))
        manager.disconnect(websocket)
        return
    
    # Instantiate the appropriate connector
    connector = None
    if conn_data['source_type'].lower() in ('postgres', 'postgresql'):
        connector = PostgresConnector(conn_data['host'], conn_data['database_name'], conn_data['credentials'], conn_data['target_table'])
    elif conn_data['source_type'].lower() == 'snowflake':
        connector = SnowflakeConnector(conn_data['host'], conn_data['database_name'], conn_data['credentials'])
    elif conn_data['source_type'].lower() == 'kafka':
        connector = KafkaConnector(conn_data['host'], conn_data['database_name'], conn_data['credentials'])
    else:
        await websocket.send_text(json.dumps({"error": "Unsupported source type."}))
        manager.disconnect(websocket)
        return

    try:
        # Stream metrics indefinitely
        async for metric in connector.get_metrics_stream():
            await websocket.send_text(json.dumps(metric))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket Streaming Error: {e}")
        manager.disconnect(websocket)

@router.get("/delta")
async def check_live_delta(user_id: str = Header(None)):
    """
    Check the total row count across all active live pipelines for auto-regeneration.
    """
    if not user_id:
        from config.settings import settings
        user_id = settings.DEFAULT_USER_ID

    try:
        total_rows = 0
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(DataConnection).where(DataConnection.user_id == user_id))
            connections = result.scalars().all()
            
            # Since live row count counting across massive tables can be slow, 
            # we do a quick count heuristic or just query it if it's indexed.
            import psycopg2
            
            for conn in connections:
                if conn.source_type.lower() in ('postgres', 'postgresql'):
                    try:
                        import urllib.parse
                        safe_creds = urllib.parse.quote_plus(conn.credentials)
                        conn_str = f"postgresql://postgres:{safe_creds}@{conn.host}/{conn.database_name}"
                        
                        with psycopg2.connect(conn_str) as pg_conn:
                            with pg_conn.cursor() as cur:
                                # Reltuples is instant (approximate, but good enough for deltas)
                                cur.execute("SELECT reltuples::bigint FROM pg_class WHERE relname = %s", (conn.target_table,))
                                row = cur.fetchone()
                                if row and row[0]:
                                    total_rows += row[0]
                                else:
                                    # Fallback to exact count if reltuples fails
                                    cur.execute(f"SELECT COUNT(*) FROM {conn.target_table}")
                                    total_rows += cur.fetchone()[0]
                    except Exception as e:
                        logger.error(f"Delta check failed for connection {conn.id}: {e}")
                        
        return {"total_rows": total_rows}
    except Exception as e:
        logger.error(f"Delta endpoint error: {e}")
        return {"error": str(e)}
