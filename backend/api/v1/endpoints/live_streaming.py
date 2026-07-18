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
    import uuid
    conn_id = str(uuid.uuid4())
    is_guest = str(user.id).startswith('guest_')

    if req.source_type == "api_push":
        if is_guest:
            # Embed the guest user_id into the connection_id so the push endpoint knows who it is!
            conn_id = f"{user.id}_push_{conn_id}"
        else:
            # For authenticated users, keep it as a raw UUID so it can be saved in the database
            pass

    # If guest user, bypass DB to avoid UUID errors and return mock connection for localStorage
    if is_guest:
        return {
            "connection_id": conn_id, 
            "status": "success", 
            "message": "Guest connection created.",
            "is_guest": True,
            "connection": {
                "id": conn_id,
                "source_type": req.source_type,
                "host": req.host,
                "database_name": req.database_name,
                "target_table": req.target_table,
                "created_at": datetime.utcnow().isoformat()
            }
        }
        
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
    
    return {"connection_id": conn_id, "status": "success", "is_guest": False}

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
    if str(user.id).startswith('guest_'):
        return {"status": "success"}

    from sqlalchemy import select
    from sqlalchemy.exc import DBAPIError
    
    clean_id = connection_id
    if clean_id.startswith("push_"):
        clean_id = clean_id[5:]
    elif "_push_" in clean_id:
        clean_id = clean_id.split("_push_")[1]
        
    try:
        result = await db.execute(select(DataConnection).where(DataConnection.id == clean_id, DataConnection.user_id == user.id))
        conn = result.scalar_one_or_none()
    except DBAPIError:
        # If it's completely unparseable as UUID, it doesn't exist in DB
        raise HTTPException(status_code=404, detail="Connection not found")
    
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
        # Maps connection_id to a list of active WebSockets
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, connection_id: str):
        await websocket.accept()
        if connection_id not in self.active_connections:
            self.active_connections[connection_id] = []
        self.active_connections[connection_id].append(websocket)

    def disconnect(self, websocket: WebSocket, connection_id: str):
        if connection_id in self.active_connections:
            if websocket in self.active_connections[connection_id]:
                self.active_connections[connection_id].remove(websocket)
            if not self.active_connections[connection_id]:
                del self.active_connections[connection_id]
                
    async def push_data(self, connection_id: str, data: dict):
        if connection_id in self.active_connections:
            # We must iterate over a copy in case a websocket disconnects during iteration
            for ws in list(self.active_connections[connection_id]):
                try:
                    await ws.send_text(json.dumps(data))
                except Exception as e:
                    logger.error(f"Failed to push data to websocket: {e}")
                    self.disconnect(ws, connection_id)

manager = ConnectionManager()

from database.db import AsyncSessionLocal
from sqlalchemy import select

@router.websocket("/ws/live-data/{connection_id}")
async def websocket_live_data(websocket: WebSocket, connection_id: str):
    """
    WebSocket endpoint for streaming real telemetry using actual connection classes.
    """
    await manager.connect(websocket, connection_id)
    
    # Fetch credentials
    conn_data = None
    if "_push_" in connection_id or connection_id.startswith("push_"):
        conn_data = {
            "source_type": "api_push",
            "host": "datavision",
            "database_name": "push",
            "target_table": "push",
            "credentials": "none"
        }
    else:
        # Check database. If it's a UUID, it might be an authenticated user's api_push or postgres/snowflake
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
        manager.disconnect(websocket, connection_id)
        return
    
    # Handle DataVision API Push (Passive receiver)
    if conn_data['source_type'].lower() == 'api_push':
        try:
            # Send initial confirmation
            await websocket.send_text(json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "total_rows": 0,
                "rows_per_sec": 0,
                "cpu_usage": 0.0,
                "error_rate": 0.0,
                "connector_source": "DataVision API",
                "status": "Waiting for data pushes..."
            }))
            
            # Keep connection alive indefinitely (or until client closes it)
            # The actual data will be sent via `manager.push_data` from the POST endpoint.
            while True:
                # Keep alive ping
                await asyncio.sleep(30) 
        except WebSocketDisconnect:
            manager.disconnect(websocket, connection_id)
        except Exception as e:
            print(f"WebSocket API Push Error: {e}")
            manager.disconnect(websocket, connection_id)
        return

    # Handle Active Polling Connectors
    connector = None
    if conn_data['source_type'].lower() in ('postgres', 'postgresql'):
        connector = PostgresConnector(conn_data['host'], conn_data['database_name'], conn_data['credentials'], conn_data['target_table'])
    elif conn_data['source_type'].lower() == 'snowflake':
        connector = SnowflakeConnector(conn_data['host'], conn_data['database_name'], conn_data['credentials'])
    elif conn_data['source_type'].lower() == 'kafka':
        connector = KafkaConnector(conn_data['host'], conn_data['database_name'], conn_data['credentials'])
    else:
        await websocket.send_text(json.dumps({"error": "Unsupported source type."}))
        manager.disconnect(websocket, connection_id)
        return

    try:
        # Stream metrics indefinitely
        async for metric in connector.get_metrics_stream():
            await websocket.send_text(json.dumps(metric))
    except WebSocketDisconnect:
        manager.disconnect(websocket, connection_id)
    except Exception as e:
        print(f"WebSocket Streaming Error: {e}")
        manager.disconnect(websocket, connection_id)

@router.post("/push/{connection_id}")
async def push_live_data(connection_id: str, payload: dict):
    """
    Endpoint for users to push data directly into DataVision.
    This bypasses the need for tunnels or local databases.
    Also saves data as CSV so it appears in Uploaded Files and feeds AI/ML/Dashboard.
    """
    # Add timestamp and source if not provided
    if "timestamp" not in payload:
        payload["timestamp"] = datetime.utcnow().isoformat()
    if "connector_source" not in payload:
        payload["connector_source"] = "DataVision API"
    if "status" not in payload:
        payload["status"] = "Receiving Data"
    
    # Save data as CSV for Uploaded Files integration
    try:
        import pandas as pd
        from utils.paths import get_user_paths
        
        # Determine the user who owns this connection
        owner_user_id = None
        if "_push_" in connection_id and connection_id.startswith("guest_"):
            owner_user_id = connection_id.split("_push_")[0]
        else:
            # Clean up old connection IDs that might still have "push_" prefix (backwards compatibility)
            clean_id = connection_id
            if clean_id.startswith("push_"):
                clean_id = clean_id[5:]
            elif "_push_" in clean_id:
                clean_id = clean_id.split("_push_")[1]
                
            from sqlalchemy.exc import DBAPIError
            try:
                # Always check the DB to find the owner, even for push connections
                async with AsyncSessionLocal() as db:
                    result = await db.execute(select(DataConnection).where(DataConnection.id == clean_id))
                    conn = result.scalar_one_or_none()
                    if conn:
                        owner_user_id = str(conn.user_id)
            except DBAPIError:
                # If clean_id is totally invalid UUID, ignore it
                owner_user_id = None
        
        if owner_user_id:
            paths = get_user_paths(owner_user_id)
            csv_path = paths["files"] / f"live_stream_{connection_id[:12]}.csv"
            
            # Build a row from the payload (exclude internal fields)
            row_data = {k: v for k, v in payload.items() if k not in ('connector_source', 'status')}
            
            # Append to existing CSV or create new one
            new_df = pd.DataFrame([row_data])
            if csv_path.exists():
                try:
                    existing = pd.read_csv(csv_path)
                    combined = pd.concat([existing, new_df], ignore_index=True)
                    # Keep last 10000 rows to prevent unbounded growth
                    combined = combined.tail(10000)
                    combined.to_csv(csv_path, index=False)
                except Exception:
                    new_df.to_csv(csv_path, index=False)
            else:
                new_df.to_csv(csv_path, index=False)
    except Exception as e:
        logger.warning(f"Failed to save push data as CSV: {e}")
    
    # Broadcast to all websockets listening to this connection_id
    if connection_id in manager.active_connections:
        await manager.push_data(connection_id, payload)
        return {"status": "success", "broadcast_count": len(manager.active_connections[connection_id])}
    
    return {"status": "ignored", "message": "No active dashboard listening to this connection."}

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
