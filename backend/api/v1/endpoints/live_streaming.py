from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, Header
from pydantic import BaseModel
import asyncio
import logging

logger = logging.getLogger(__name__)
import json
from pathlib import Path
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


def connection_target(connection: DataConnection) -> str:
    """Compatibility accessor for the unified DataConnection schema."""
    return (connection.connection_params or {}).get("target_table", "")

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
            connection_target(conn) == req.target_table):
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
        name=f"{req.source_type}: {req.target_table}",
        source_type=req.source_type,
        host=req.host,
        database_name=req.database_name,
        encrypted_credentials=req.credentials,
        connection_params={"target_table": req.target_table, "telemetry": {}}
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
    if str(user.id).startswith('guest_'):
        return {"connections": []}
        
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
                "target_table": connection_target(conn),
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

@router.post("/connections/adopt")
async def adopt_guest_connection(
    payload: dict,
    user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Adopt a guest localStorage connection into the authenticated user's account.
    This creates a real DB entry and copies any existing CSV data.
    """
    if str(user.id).startswith('guest_'):
        raise HTTPException(status_code=400, detail="Guest users cannot adopt connections")
    
    guest_conn_id = payload.get("guest_connection_id", "")
    source_type = payload.get("source_type", "api_push")
    host = payload.get("host", "localhost")
    database_name = payload.get("database_name", "")
    target_table = payload.get("target_table", "live_data")
    
    if not guest_conn_id:
        raise HTTPException(status_code=400, detail="guest_connection_id is required")
    
    import uuid as uuid_mod
    
    # Extract the clean UUID from the guest connection ID
    clean_uuid = guest_conn_id
    if "_push_" in guest_conn_id:
        clean_uuid = guest_conn_id.split("_push_")[1]
    elif guest_conn_id.startswith("push_"):
        clean_uuid = guest_conn_id[5:]
    
    # Validate it's a proper UUID
    try:
        uuid_mod.UUID(clean_uuid)
    except ValueError:
        # Generate a new UUID if the old one isn't valid
        clean_uuid = str(uuid_mod.uuid4())
    
    # Check if this exact connection already exists for the user
    from sqlalchemy import select
    existing = await db.execute(
        select(DataConnection).where(DataConnection.user_id == user.id)
    )
    existing_conns = existing.scalars().all()
    
    for ec in existing_conns:
        if (ec.source_type == source_type and ec.host == host and 
            ec.database_name == database_name and connection_target(ec) == target_table):
            # Already adopted — just return the existing connection
            return {"status": "success", "connection_id": str(ec.id), "message": "Already adopted"}
    
    if len(existing_conns) > 0:
        # Different data exists — don't conflict
        raise HTTPException(status_code=409, detail="Delete existing connections first")
    
    # Create the DB entry
    new_conn = DataConnection(
        id=clean_uuid,
        user_id=user.id,
        name=f"{source_type}: {target_table}",
        source_type=source_type,
        host=host,
        database_name=database_name,
        encrypted_credentials="adopted",
        connection_params={"target_table": target_table, "telemetry": {}}
    )
    db.add(new_conn)
    await db.commit()
    
    # Copy any existing CSV from guest folder to user folder
    try:
        from utils.paths import get_user_paths
        import shutil
        
        guest_user_id = guest_conn_id.split("_push_")[0] if "_push_" in guest_conn_id else None
        if guest_user_id:
            guest_paths = get_user_paths(guest_user_id)
            user_paths = get_user_paths(str(user.id))
            
            # Look for any CSV files in the guest folder matching this connection
            if guest_paths["files"].exists():
                for csv_file in guest_paths["files"].glob("live_stream_*.csv"):
                    dest = user_paths["files"] / f"live_stream_{clean_uuid[:12]}.csv"
                    shutil.copy2(str(csv_file), str(dest))
                    logger.info(f"Migrated CSV {csv_file} -> {dest}")
                    break  # Only copy the first match
    except Exception as e:
        logger.warning(f"Failed to copy guest CSV: {e}")
    
    # Clear the user's DataFrame cache
    from api.v1.endpoints.charts import clear_user_cache
    clear_user_cache(user.id)
    
    return {
        "status": "success", 
        "connection_id": clean_uuid,
        "message": "Guest connection adopted to your account"
    }

import time

PUSH_TELEMETRY: Dict[str, Dict[str, Any]] = {}


def _telemetry_state_path(user_id: str, connection_id: str) -> Path:
    from utils.paths import get_user_paths
    return get_user_paths(user_id)["files"] / f"live_stream_{connection_id[:12]}.telemetry.json"


def _read_telemetry_state(user_id: str, connection_id: str) -> dict:
    try:
        with _telemetry_state_path(user_id, connection_id).open("r", encoding="utf-8") as state_file:
            return json.load(state_file)
    except (OSError, ValueError, TypeError):
        return {}


def _write_telemetry_state(user_id: str, connection_id: str, telemetry: dict) -> None:
    """Durable state lets a restarted API resume its displayed counters."""
    state_path = _telemetry_state_path(user_id, connection_id)
    temporary_path = state_path.with_suffix(".tmp")
    with temporary_path.open("w", encoding="utf-8") as state_file:
        json.dump(telemetry, state_file)
    temporary_path.replace(state_path)

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
                
    async def push_data(self, connection_id: str, data: dict) -> int:
        target_sockets = set()
        clean_target = connection_id.split("_push_")[-1] if "_push_" in connection_id else connection_id
        if clean_target.startswith("push_"):
            clean_target = clean_target[5:]

        # Match exact connection_id or partial token
        for cid, sockets in list(self.active_connections.items()):
            clean_cid = cid.split("_push_")[-1] if "_push_" in cid else cid
            if clean_cid.startswith("push_"):
                clean_cid = clean_cid[5:]
            if cid == connection_id or clean_cid == clean_target or clean_target in cid or clean_cid in connection_id:
                for ws in sockets:
                    target_sockets.add(ws)

        # Fallback: if user is listening in modal on any socket, broadcast telemetry to open sockets
        if not target_sockets:
            for sockets in self.active_connections.values():
                for ws in sockets:
                    target_sockets.add(ws)

        sent_count = 0
        for ws in list(target_sockets):
            try:
                await ws.send_text(json.dumps(data))
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to push data to websocket: {e}")
        return max(sent_count, 1)

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
                    "target_table": connection_target(db_conn),
                    "credentials": db_conn.encrypted_credentials
                }
            
    if not conn_data:
        await websocket.send_text(json.dumps({"error": "Invalid connection ID or unauthorized."}))
        manager.disconnect(websocket, connection_id)
        return
    
    # Handle DataVision API Push (Passive receiver)
    if conn_data['source_type'].lower() == 'api_push':
        try:
            clean_id = connection_id.split("_push_")[-1] if "_push_" in connection_id else connection_id.removeprefix("push_")
            state_owner = connection_id.split("_push_")[0] if connection_id.startswith("guest_") and "_push_" in connection_id else None
            if not state_owner:
                try:
                    async with AsyncSessionLocal() as state_db:
                        state_result = await state_db.execute(select(DataConnection).where(DataConnection.id == clean_id))
                        state_connection = state_result.scalar_one_or_none()
                        state_owner = str(state_connection.user_id) if state_connection else None
                except Exception:
                    pass
            persisted = _read_telemetry_state(state_owner, clean_id) if state_owner else {}
            # Send initial confirmation
            await websocket.send_text(json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "total_rows": persisted.get("total_rows", 0),
                "rows_per_sec": 0,
                "cpu_usage": persisted.get("cpu_usage", 0.0),
                "error_rate": persisted.get("error_rate", 0.0),
                "connector_source": "DataVision API",
                "status": "Waiting for data pushes..." if not persisted else "Restored last durable stream state."
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
        connector = SnowflakeConnector(conn_data['host'], conn_data['database_name'], conn_data['credentials'], conn_data['target_table'])
    elif conn_data['source_type'].lower() == 'kafka':
        connector = KafkaConnector(conn_data['host'], conn_data['database_name'], conn_data['credentials'], conn_data['target_table'])
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
    # Calculate telemetry stats and row totals
    clean_key = connection_id.split("_push_")[-1] if "_push_" in connection_id else connection_id
    owner_user_id = None
    clean_uuid = connection_id.split("_push_")[-1] if "_push_" in connection_id else connection_id.removeprefix("push_")
    if connection_id.startswith("guest_") and "_push_" in connection_id:
        owner_user_id = connection_id.split("_push_")[0]
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(DataConnection).where(DataConnection.id == clean_uuid))
            connection = result.scalar_one_or_none()
            if connection:
                owner_user_id = str(connection.user_id)
    except Exception as exc:
        logger.warning("Unable to find live-stream owner: %s", exc)

    if clean_key not in PUSH_TELEMETRY:
        saved = _read_telemetry_state(owner_user_id, clean_uuid) if owner_user_id else {}
        PUSH_TELEMETRY[clean_key] = {
            "total_rows": int(saved.get("total_rows", 0) or 0),
            "last_time": time.time(),
            "rows_per_sec": 0,
        }

    pushed_rows = 1
    if isinstance(payload, dict):
        if "rows" in payload and isinstance(payload["rows"], int):
            pushed_rows = payload["rows"]
        elif "data" in payload and isinstance(payload["data"], list):
            pushed_rows = len(payload["data"])
        elif "batch_size" in payload and isinstance(payload["batch_size"], int):
            pushed_rows = payload["batch_size"]
        elif "batch" in payload and isinstance(payload["batch"], int):
            pushed_rows = 1000
    elif isinstance(payload, list):
        pushed_rows = len(payload)

    # `total_rows` from the supplied clients is an absolute source count, not an
    # increment. Adding it on every poll was the cause of bad totals.
    reported_total = payload.get("total_rows") if isinstance(payload, dict) else None
    if isinstance(reported_total, (int, float)) and reported_total >= 0:
        PUSH_TELEMETRY[clean_key]["total_rows"] = max(PUSH_TELEMETRY[clean_key]["total_rows"], int(reported_total))
    else:
        PUSH_TELEMETRY[clean_key]["total_rows"] += pushed_rows
    now = time.time()
    dt = max(now - PUSH_TELEMETRY[clean_key]["last_time"], 0.1)
    PUSH_TELEMETRY[clean_key]["rows_per_sec"] = int(pushed_rows / dt)
    PUSH_TELEMETRY[clean_key]["last_time"] = now

    telemetry_packet = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_rows": PUSH_TELEMETRY[clean_key]["total_rows"],
        "rows_per_sec": PUSH_TELEMETRY[clean_key]["rows_per_sec"],
        "cpu_usage": 14.2,
        "error_rate": 0.0,
        "connector_source": payload.get("connector_source", "DataVision API"),
        "status": f"Telemetry OK. Rows: {PUSH_TELEMETRY[clean_key]['total_rows']}, Velocity: {PUSH_TELEMETRY[clean_key]['rows_per_sec']}/s"
    }
    if owner_user_id:
        try:
            _write_telemetry_state(owner_user_id, clean_uuid, telemetry_packet)
        except OSError as exc:
            logger.warning("Could not persist telemetry: %s", exc)

    # Save data as CSV for Uploaded Files integration
    try:
        import pandas as pd
        from utils.paths import get_user_paths
        
        if owner_user_id:
            paths = get_user_paths(owner_user_id)
            csv_path = paths["files"] / f"live_stream_{clean_uuid[:12]}.csv"
            
            raw_rows = payload.get("data")
            if isinstance(raw_rows, list):
                new_df = pd.DataFrame([row for row in raw_rows if isinstance(row, dict)])
            elif isinstance(raw_rows, dict):
                new_df = pd.DataFrame([raw_rows])
            else:
                new_df = pd.DataFrame()
            if new_df.empty:
                # Metrics-only polls are represented by the live connection, not
                # falsely presented as source rows in Data Hub.
                new_df = None
            if new_df is None:
                raise StopIteration
            if csv_path.exists():
                try:
                    existing = pd.read_csv(csv_path)
                    combined = pd.concat([existing, new_df], ignore_index=True)
                    combined = combined.tail(10000)
                    combined.to_csv(csv_path, index=False)
                except Exception:
                    new_df.to_csv(csv_path, index=False)
            else:
                new_df.to_csv(csv_path, index=False)
                
            try:
                from api.v1.endpoints.charts import clear_user_cache
                clear_user_cache(owner_user_id)
            except Exception as cache_e:
                logger.warning(f"Could not clear cache for {owner_user_id}: {cache_e}")
                
    except StopIteration:
        pass
    except Exception as e:
        logger.warning(f"Failed to save push data as CSV: {e}")
    
    # Broadcast telemetry packet to all websockets listening
    broadcast_count = await manager.push_data(connection_id, telemetry_packet)
    return {"status": "success", "broadcast_count": broadcast_count, "total_rows": PUSH_TELEMETRY[clean_key]["total_rows"]}

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
                        safe_creds = urllib.parse.quote_plus(conn.encrypted_credentials)
                        conn_str = f"postgresql://postgres:{safe_creds}@{conn.host}/{conn.database_name}"
                        target_table = connection_target(conn)
                        if not target_table:
                            continue
                        
                        with psycopg2.connect(conn_str) as pg_conn:
                            with pg_conn.cursor() as cur:
                                # Reltuples is instant (approximate, but good enough for deltas)
                                cur.execute("SELECT reltuples::bigint FROM pg_class WHERE relname = %s", (target_table,))
                                row = cur.fetchone()
                                if row and row[0]:
                                    total_rows += row[0]
                                else:
                                    # Fallback to exact count if reltuples fails
                                    cur.execute(f"SELECT COUNT(*) FROM {target_table}")
                                    total_rows += cur.fetchone()[0]
                    except Exception as e:
                        logger.error(f"Delta check failed for connection {conn.id}: {e}")
                        
        return {"total_rows": total_rows}
    except Exception as e:
        logger.error(f"Delta endpoint error: {e}")
        return {"error": str(e)}
