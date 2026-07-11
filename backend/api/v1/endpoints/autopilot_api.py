"""
🧠 AUTOPILOT API — Agentic Autonomous Data Science
====================================================

SSE-streaming API that runs the full autonomous pipeline.

Endpoints:
  POST /api/v1/autopilot/run      — Start autopilot (SSE stream)
  POST /api/v1/autopilot/cancel   — Cancel running session
  GET  /api/v1/autopilot/status   — Get session status
"""

import os
import json
import uuid
import logging
import pandas as pd
import asyncio
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/run")
async def run_autopilot(
    file: UploadFile = File(...),
    goal: str = Form("Perform comprehensive autonomous data analysis"),
    target_column: Optional[str] = Form(None),
    user_id: str = Form("default"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """
    🧠 Start Agentic Autopilot — streams real-time progress via SSE.
    
    Upload a CSV/Excel file and the AI autonomously:
    1. Profiles the data
    2. Cleans it
    3. Engineers features
    4. Extracts insights
    5. Generates visualizations
    6. Trains the best ML model
    7. Generates deployment code
    8. Produces a full report
    """
    from agents.autopilot import AgenticAutopilot, active_sessions
    
    # Resolve user ID
    actual_user_id = x_user_id or user_id
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        if token.startswith("dv_live_"):
            # Resolve Developer API Key
            try:
                from api.v1.endpoints.developer import _keys_db
                for k in _keys_db.values():
                    if k["key"] == token and k["status"] == "active":
                        actual_user_id = k["user_id"]
                        break
            except Exception as e:
                logger.error(f"Failed to resolve API Key: {e}")
        else:
            # Resolve JWT
            try:
                from core.auth import decode_jwt
                payload = decode_jwt(token)
                if payload and "sub" in payload:
                    actual_user_id = payload["sub"]
            except:
                pass

    # Read file
    try:
        content = await file.read()
        filename = file.filename or "data.csv"
        
        if filename.endswith('.xlsx') or filename.endswith('.xls'):
            df = pd.read_excel(io.BytesIO(content))
        else:
            # Try multiple encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(io.BytesIO(content), encoding=encoding)
                    break
                except:
                    continue
            else:
                raise ValueError("Could not read file with any encoding")
        
        if len(df) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
            
        # Limit to 50k rows for performance
        if len(df) > 50000:
            df = df.sample(n=50000, random_state=42).reset_index(drop=True)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read file: {str(e)}")

    # Create autopilot session
    session_id = str(uuid.uuid4())
    autopilot = AgenticAutopilot(
        user_id=actual_user_id,
        df=df,
        filename=filename,
        goal=goal,
        target_column=target_column if target_column and target_column.strip() else None,
        session_id=session_id
    )
    
    # Register active session
    active_sessions[session_id] = autopilot

    # SSE streaming generator
    async def event_stream():
        try:
            async for event in autopilot.run():
                # Format as SSE
                event_json = json.dumps(event, default=str)
                yield f"data: {event_json}\n\n"
                # Small delay to prevent client buffer issues
                await asyncio.sleep(0.05)
            
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Autopilot stream error: {e}")
            error_event = json.dumps({"type": "error", "data": {"error": str(e)}})
            yield f"data: {error_event}\n\n"
            yield "data: [DONE]\n\n"
        finally:
            # Clean up session
            if session_id in active_sessions:
                del active_sessions[session_id]

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


class CancelRequest(BaseModel):
    session_id: str


@router.post("/cancel")
async def cancel_autopilot(request: CancelRequest):
    """Cancel a running autopilot session."""
    from agents.autopilot import active_sessions
    
    session = active_sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.cancel()
    return {"success": True, "message": "Autopilot cancelled"}


@router.get("/status/{session_id}")
async def get_autopilot_status(session_id: str):
    """Get current status of an autopilot session."""
    from agents.autopilot import active_sessions
    
    session = active_sessions.get(session_id)
    if not session:
        return {"success": False, "detail": "Session not found or completed"}
    
    return {"success": True, "state": session.state.to_dict()}
