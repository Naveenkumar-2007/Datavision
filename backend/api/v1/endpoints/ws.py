from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import asyncio
import random
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total clients: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message to ws: {e}")

    async def broadcast(self, message: str):
        for connection in self.active_connections[:]:
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(connection)
            
    async def broadcast_json(self, data: dict):
        for connection in self.active_connections[:]:
            try:
                await connection.send_json(data)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

@router.websocket("")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for ping/pong or process command
            await manager.send_personal_message(f'{{"type": "ACK", "message": "Received"}}', websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

async def push_realtime_updates():
    """Background task to push live updates to all connected WS clients"""
    while True:
        try:
            await asyncio.sleep(5)  # Update interval
            if len(manager.active_connections) > 0:
                # Simulated live dashboard metrics (in a real app, this would query a DB/Redis)
                live_data = {
                    "type": "REALTIME_METRICS",
                    "payload": {
                        "active_users": random.randint(120, 150),
                        "cpu_load": round(random.uniform(25.0, 65.0), 1),
                        "memory_usage": round(random.uniform(40.0, 80.0), 1),
                        "queries_per_sec": random.randint(10, 50),
                        "anomaly_score": round(random.uniform(0.01, 0.05), 3)
                    }
                }
                await manager.broadcast_json(live_data)
        except Exception as e:
            logger.error(f"Error in push_realtime_updates: {e}")
            await asyncio.sleep(5)
