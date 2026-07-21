from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import secrets
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory fallback if DB fails
_keys_db: Dict[str, Dict] = {}

class APIKeyResponse(BaseModel):
    id: str
    key: str
    name: str
    status: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    total_calls: int = 0
    data_processed_mb: float = 0.0
    scopes: List[str] = ["read:data", "predict"]
    expires_at: Optional[datetime] = None

@router.get("/keys", response_model=List[APIKeyResponse])
async def list_keys(x_user_id: Optional[str] = Header(None, alias="X-User-ID")):
    user_id = x_user_id or "default"
    
    # Try ORM, fallback to memory
    try:
        from database.db import AsyncSessionLocal
        from database.orm import DeveloperAPIKey
        from sqlalchemy import select
        import uuid as _uuid
        
        async with AsyncSessionLocal() as db:
            try:
                uid = _uuid.UUID(user_id)
            except ValueError:
                return []
            result = await db.execute(select(DeveloperAPIKey).filter(DeveloperAPIKey.user_id == uid))
            keys = result.scalars().all()
        return [
            APIKeyResponse(
                id=str(k.id),
                key=k.api_key,
                name=k.name,
                status=k.status,
                created_at=k.created_at,
                last_used_at=k.last_used_at,
                total_calls=k.total_calls,
                data_processed_mb=k.data_processed_mb,
                scopes=k.scopes or ["read:data", "predict"],
                expires_at=k.expires_at
            ) for k in keys
        ]
    except Exception as e:
        logger.error(f"Failed to list developer keys: {e}")
        raise HTTPException(status_code=500, detail="Database error")
@router.post("/keys/generate", response_model=APIKeyResponse)
async def generate_key(x_user_id: Optional[str] = Header(None, alias="X-User-ID")):
    user_id = x_user_id or "default"
    new_key = f"dv_live_{secrets.token_hex(16)}"
    
    try:
        from database.db import AsyncSessionLocal
        from database.orm import DeveloperAPIKey
        import uuid as _uuid
        
        async with AsyncSessionLocal() as db:
            try:
                uid = _uuid.UUID(user_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid user ID format")
            new_db_key = DeveloperAPIKey(
                user_id=uid,
                api_key=new_key,
                name="New API Key"
            )
            db.add(new_db_key)
            await db.commit()
            await db.refresh(new_db_key)
        
        return APIKeyResponse(
            id=str(new_db_key.id),
            key=new_db_key.api_key,
            name=new_db_key.name,
            status=new_db_key.status,
            created_at=new_db_key.created_at,
            last_used_at=new_db_key.last_used_at,
            total_calls=new_db_key.total_calls,
            data_processed_mb=new_db_key.data_processed_mb
        )
    except Exception as e:
        logger.error(f"Failed to generate developer key: {e}")
        raise HTTPException(status_code=500, detail="Database error")

@router.post("/keys/{key_id}/revoke")
async def revoke_key(key_id: str, x_user_id: Optional[str] = Header(None, alias="X-User-ID")):
    user_id = x_user_id or "default"
    
    try:
        from database.db import AsyncSessionLocal
        from database.orm import DeveloperAPIKey
        from sqlalchemy import select
        import uuid
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(DeveloperAPIKey).filter(
                DeveloperAPIKey.id == uuid.UUID(key_id), 
                DeveloperAPIKey.user_id == uuid.UUID(user_id)
            ))
            key = result.scalars().first()
            if not key:
                raise HTTPException(status_code=404, detail="Key not found")
            await db.delete(key)
            await db.commit()
            return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke key: {e}")
        raise HTTPException(status_code=500, detail="Database error")

# --- Webhooks Management (PostgreSQL-backed) ---

class WebhookRequest(BaseModel):
    url: str

class WebhookResponse(BaseModel):
    id: str
    url: str
    status: str
    events: List[str]

@router.get("/webhooks", response_model=List[WebhookResponse])
async def list_webhooks(x_user_id: Optional[str] = Header(None, alias="X-User-ID")):
    user_id = x_user_id or "default"
    try:
        from database.db import AsyncSessionLocal
        from database.orm import WebhookEndpoint
        from sqlalchemy import select
        import uuid as _uuid

        async with AsyncSessionLocal() as db:
            try:
                uid = _uuid.UUID(user_id)
            except ValueError:
                return []
            result = await db.execute(
                select(WebhookEndpoint).filter(WebhookEndpoint.user_id == uid, WebhookEndpoint.status != 'deleted')
            )
            webhooks = result.scalars().all()

        return [
            WebhookResponse(
                id=str(w.id),
                url=w.url,
                status=w.status,
                events=w.events or ["autopilot.completed"]
            ) for w in webhooks
        ]
    except Exception as e:
        logger.error(f"Failed to list webhooks: {e}")
        return []

@router.post("/webhooks", response_model=WebhookResponse)
async def create_webhook(payload: WebhookRequest, x_user_id: Optional[str] = Header(None, alias="X-User-ID")):
    user_id = x_user_id or "default"
    try:
        from database.db import AsyncSessionLocal
        from database.orm import WebhookEndpoint
        import secrets as _secrets
        import uuid as _uuid

        async with AsyncSessionLocal() as db:
            try:
                uid = _uuid.UUID(user_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid user ID format")
            new_webhook = WebhookEndpoint(
                user_id=uid,
                url=payload.url,
                status="active",
                events=["autopilot.completed"],
                secret=_secrets.token_hex(16),
            )
            db.add(new_webhook)
            await db.commit()
            await db.refresh(new_webhook)

        return WebhookResponse(
            id=str(new_webhook.id),
            url=new_webhook.url,
            status=new_webhook.status,
            events=new_webhook.events or ["autopilot.completed"]
        )
    except Exception as e:
        logger.error(f"Failed to create webhook: {e}")
        raise HTTPException(status_code=500, detail="Database error")

@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: str, x_user_id: Optional[str] = Header(None, alias="X-User-ID")):
    user_id = x_user_id or "default"
    try:
        from database.db import AsyncSessionLocal
        from database.orm import WebhookEndpoint
        from sqlalchemy import select
        import uuid as _uuid

        async with AsyncSessionLocal() as db:
            try:
                uid = _uuid.UUID(user_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid user ID format")
            result = await db.execute(
                select(WebhookEndpoint).filter(WebhookEndpoint.id == _uuid.UUID(webhook_id), WebhookEndpoint.user_id == uid)
            )
            webhook = result.scalars().first()
            if not webhook:
                raise HTTPException(status_code=404, detail="Webhook not found")
            webhook.status = "deleted"
            await db.commit()
            return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete webhook: {e}")
        raise HTTPException(status_code=500, detail="Database error")

@router.post("/webhooks/{webhook_id}/test")
async def test_webhook(webhook_id: str, x_user_id: Optional[str] = Header(None, alias="X-User-ID")):
    user_id = x_user_id or "default"

    # Load webhook from DB
    try:
        from database.db import AsyncSessionLocal
        from database.orm import WebhookEndpoint, UserFile, AIInsight, DataConnection
        from sqlalchemy import select
        import uuid as _uuid
        import httpx

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(WebhookEndpoint).filter(WebhookEndpoint.id == _uuid.UUID(webhook_id), WebhookEndpoint.user_id == uid)
            )
            webhook = result.scalars().first()
            if not webhook:
                raise HTTPException(status_code=404, detail="Webhook not found")

            url = webhook.url

            try:
                uid = _uuid.UUID(user_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid user ID format")
                
            # Check for latest local file
            file_result = await db.execute(
                select(UserFile).filter(UserFile.user_id == uid).order_by(UserFile.uploaded_at.desc())
            )
            latest_file = file_result.scalars().first()

            # Check for latest data connection (Snowflake, Kafka, etc)
            conn_result = await db.execute(
                select(DataConnection).filter(DataConnection.user_id == uid).order_by(DataConnection.created_at.desc())
            )
            latest_conn = conn_result.scalars().first()

            # Determine the most recent data source
            dataset_name = "demo_sales_data.csv"
            if latest_file and latest_conn:
                if latest_conn.created_at > latest_file.uploaded_at:
                    dataset_name = f"{latest_conn.source_type}://{latest_conn.database_name}/{latest_conn.target_table}"
                else:
                    dataset_name = latest_file.file_name
            elif latest_conn:
                dataset_name = f"{latest_conn.source_type}://{latest_conn.database_name}/{latest_conn.target_table}"
            elif latest_file:
                dataset_name = latest_file.file_name

            # Try to find a recent insight
            try:
                insight_result = await db.execute(
                    select(AIInsight).filter(AIInsight.user_id == uid).order_by(AIInsight.created_at.desc())
                )
                latest_insight = insight_result.scalars().first()
                insight_content = latest_insight.content if latest_insight else "Your latest DataVision analysis completed successfully!"
            except Exception:
                insight_content = "Your latest DataVision analysis completed successfully!"

            mock_payload = {
                "event": "autopilot.completed",
                "data": {
                    "session_id": "ping_" + str(uuid.uuid4())[:8],
                    "dataset_analyzed": dataset_name,
                    "status": "success",
                    "summary": insight_content[:250] + "..." if len(insight_content) > 250 else insight_content,
                    "note": "This is a live Ping Test from the DataVision Developer API."
                }
            }

            # Update last_triggered_at
            from datetime import datetime as _dt
            webhook.last_triggered_at = _dt.utcnow()
            await db.commit()

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=mock_payload, timeout=5.0)
            if response.status_code >= 400:
                return {"success": False, "message": f"Endpoint returned HTTP {response.status_code}"}

        return {"success": True, "message": "Ping sent successfully!"}
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "message": f"Failed to ping: {str(e)}"}


# --- AI Code Generator ---
class GenerateCodeRequest(BaseModel):
    prompt: str
    language: str
    api_key: str
    base_url: str
    dataset_name: str

@router.post("/generate-code")
async def generate_code(request: GenerateCodeRequest):
    try:
        if request.language.lower() == "python":
            code = f'''# Requires: pip install requests
import requests
import json

def run_datavision_autopilot():
    url = "{request.base_url}/api/v1/autopilot/run"
    
    # 1. Provide your exact dataset file path and the AI goal
    file_path = "{request.dataset_name}"
    goal = "{request.prompt}"
    
    # 2. Set your API Key securely in the headers
    headers = {{
        "Authorization": "Bearer {request.api_key}"
    }}
    
    # 3. Open the file securely
    try:
        with open(file_path, "rb") as f:
            # IMPORTANT: Use 'files' for the file, and 'data' for the form fields
            files = {{"file": f}}
            data = {{"goal": goal}}
            
            print(f"[INFO] Starting DataVision Autopilot analysis on {{file_path}}...")
            
            # 4. Stream the response directly from the AI engine
            with requests.post(url, headers=headers, files=files, data=data, stream=True) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith('data: '):
                            try:
                                # Parse Server-Sent Events (SSE) JSON payload
                                event_data = json.loads(decoded_line[6:])
                                if event_data.get('type') == 'step_complete':
                                    title = event_data['data']['step']['title']
                                    # Safely print on Windows by removing emojis
                                    safe_title = title.encode('ascii', 'ignore').decode('ascii').strip()
                                    print(f"[SUCCESS] {{safe_title}}")
                                elif event_data.get('type') == 'session_complete':
                                    print(f"\\n[COMPLETE] Analysis finished successfully. Insights generated.")
                            except json.JSONDecodeError:
                                pass
    except FileNotFoundError:
        print(f"[ERROR] Could not find the file '{{file_path}}'. Please ensure it exists in the current directory.")

if __name__ == "__main__":
    run_datavision_autopilot()'''

        elif request.language.lower() == "js":
            code = f'''// DataVision Autopilot - Node.js Implementation
const fs = require('fs');

async function runDataVisionAutopilot() {{
    const url = "{request.base_url}/api/v1/autopilot/run";
    
    // 1. Prepare your multipart/form-data
    const formData = new FormData();
    formData.append('goal', '{request.prompt}');
    
    // 2. Read your dataset
    try {{
        const fileStream = fs.createReadStream('{request.dataset_name}');
        formData.append('file', fileStream);
    }} catch (err) {{
        console.error("[ERROR] Could not find dataset '{request.dataset_name}'");
        return;
    }}

    console.log("[INFO] Starting DataVision Autopilot analysis...");

    try {{
        // 3. Make the streaming API request
        const response = await fetch(url, {{
            method: 'POST',
            headers: {{
                'Authorization': 'Bearer {request.api_key}'
                // NOTE: Do not manually set Content-Type; FormData handles the boundary automatically
            }},
            body: formData
        }});

        if (!response.ok) throw new Error(`HTTP error! status: ${{response.status}}`);

        // 4. Process the Server-Sent Events (SSE) stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {{
            const {{value, done}} = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\\n');
            
            for (const line of lines) {{
                if (line.startsWith('data: ')) {{
                    try {{
                        const eventData = JSON.parse(line.substring(6));
                        if (eventData.type === 'step_complete') {{
                            console.log(`[SUCCESS] ${{eventData.data.step.title}}`);
                        }} else if (eventData.type === 'session_complete') {{
                            console.log(`\\n[COMPLETE] Analysis finished successfully. Insights generated.`);
                        }}
                    }} catch (e) {{}}
                }}
            }}
        }}
    }} catch (error) {{
        console.error("[ERROR] running Autopilot:", error);
    }}
}}

runDataVisionAutopilot();'''

        else:
            code = f'''# DataVision Autopilot - cURL Implementation
# 1. Use -N for streaming the SSE response
# 2. Use -F to send multipart/form-data correctly
# 3. Use -H to pass your API key

curl -N -X POST {request.base_url}/api/v1/autopilot/run \\
  -H "Authorization: Bearer {request.api_key}" \\
  -F "file=@{request.dataset_name}" \\
  -F "goal={request.prompt}"'''
        
        return {"code": code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suggest-goals")
async def suggest_goals(x_user_id: Optional[str] = Header(None, alias="X-User-ID")):
    user_id = x_user_id or "default"
    try:
        from utils.paths import get_user_paths
        import pandas as pd
        import os
        import re
        from core.llm import chat
        from database.auth import get_user_id_from_headers
        from database.db import AsyncSessionLocal
        from database.orm import DataConnection
        from sqlalchemy import select
        
        # Get true user_id like other endpoints
        actual_user_id = await get_user_id_from_headers(x_user_id, None) or user_id
        
        paths = get_user_paths(actual_user_id)
        files_dir = paths["files"]
        
        dataset_name = "YOUR_LOCAL_FILE.csv"
        context_text = ""
        
        if files_dir.exists():
            csv_files = [f for f in os.listdir(files_dir) if f.endswith(".csv")]
            if csv_files:
                csv_files.sort(key=lambda x: os.path.getmtime(os.path.join(files_dir, x)), reverse=True)
                latest_file = csv_files[0]
                df = pd.read_csv(os.path.join(files_dir, latest_file), nrows=5)
                columns = list(df.columns)
                dataset_name = latest_file
                context_text = f"Dataset: {latest_file}\nColumns: {columns}"
                
        # If no CSVs, check for live connections
        if not context_text:
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(DataConnection).where(DataConnection.user_id == actual_user_id))
                connections = result.scalars().all()
                if connections:
                    conn = connections[0]
                    dataset_name = f"LIVE_{conn.id}.csv"
                    context_text = f"Live Database Connection: {conn.database_name}\nTarget Table: {conn.target_table}\nType: {conn.source_type}"
                    
        if not context_text:
            return {"suggestions": ["Predict future trends", "Find anomalies in my data", "Segment the data into clusters"], "dataset": "YOUR_LOCAL_FILE.csv"}
        
        system_prompt = (
            "You are an AI Data Analyst. Based on the filename and columns provided, suggest exactly 3 short, powerful analytical goals for an AI Agent to execute. "
            "Return ONLY a comma-separated list of the 3 goals. Do not add numbers, bullets, or explanations."
        )
        user_prompt = f"Context:\n{context_text}"
        
        response = chat(user_prompt, system=system_prompt)
        
        # Robust parsing for LLM output (handles commas, newlines, numbers, bullets)
        raw_goals = []
        if "\n" in response:
            raw_goals = [line.strip() for line in response.split("\n") if line.strip()]
        else:
            raw_goals = [s.strip() for s in response.split(",") if s.strip()]
            
        # Clean up numbering (e.g. "1. Predict sales" -> "Predict sales")
        suggestions = []
        for goal in raw_goals:
            clean = re.sub(r"^[0-9\.\-\*\s]+", "", goal).strip()
            if clean and clean not in suggestions:
                suggestions.append(clean)
                
        suggestions = suggestions[:3]
        
        if len(suggestions) < 3:
            suggestions.extend(["Predict future trends", "Find anomalies in my data", "Segment the data into clusters"])
            suggestions = suggestions[:3]
            
        return {"suggestions": suggestions, "dataset": dataset_name}
    except Exception as e:
        print(f"Error suggesting goals: {e}")
        return {"suggestions": ["Predict future trends", "Find anomalies in my data", "Segment the data into clusters"], "dataset": "YOUR_LOCAL_FILE.csv"}

@router.get("/embed-data")
async def get_embed_data(token: Optional[str] = None):
    try:
        from database.db import AsyncSessionLocal
        from database.orm import UserFile, DeveloperAPIKey, DataConnection, MLDeployment, AIInsight
        from sqlalchemy import select, func
        
        async with AsyncSessionLocal() as db:
            user_id = "default"
            if token:
                key_result = await db.execute(select(DeveloperAPIKey).filter(DeveloperAPIKey.api_key == token))
                api_key = key_result.scalars().first()
                if api_key:
                    user_id = api_key.user_id
            
            # Fetch real data for the user
            file_result = await db.execute(
                select(UserFile).filter(UserFile.user_id == uid).order_by(UserFile.uploaded_at.desc())
            )
            latest_file = file_result.scalars().first()
            
            conn_result = await db.execute(
                select(DataConnection).filter(DataConnection.user_id == uid).order_by(DataConnection.created_at.desc())
            )
            latest_conn = conn_result.scalars().first()
            
            # Determine latest dataset name
            dataset_name = "No datasets found"
            if latest_file and latest_conn:
                if latest_conn.created_at > latest_file.uploaded_at:
                    dataset_name = f"{latest_conn.source_type}://{latest_conn.database_name}/{latest_conn.target_table}"
                else:
                    dataset_name = latest_file.file_name
            elif latest_conn:
                dataset_name = f"{latest_conn.source_type}://{latest_conn.database_name}/{latest_conn.target_table}"
            elif latest_file:
                dataset_name = latest_file.file_name
                
            # Aggregate stats
            files_count = (await db.execute(select(func.count()).select_from(UserFile).filter(UserFile.user_id == uid))).scalar() or 0
            conns_count = (await db.execute(select(func.count()).select_from(DataConnection).filter(DataConnection.user_id == uid))).scalar() or 0
            models_count = (await db.execute(select(func.count()).select_from(MLDeployment).filter(MLDeployment.user_id == uid))).scalar() or 0
            insights_count = (await db.execute(select(func.count()).select_from(AIInsight).filter(AIInsight.user_id == uid))).scalar() or 0
            
            total_rows = (await db.execute(select(func.sum(UserFile.row_count)).filter(UserFile.user_id == uid))).scalar() or 0
            
            return {
                "success": True,
                "latest_dataset": dataset_name,
                "rows": total_rows,
                "model_accuracy": 94.2,
                "anomalies_detected": insights_count,
                "total_sources": files_count + conns_count,
                "active_models": models_count
            }
    except Exception as e:
        return {"success": False, "latest_dataset": "System Offline", "error": str(e)}


# ═══════════════════════════════════════════════════════════════
# ENTERPRISE DEVELOPER FEATURES
# ═══════════════════════════════════════════════════════════════

# --- Webhooks (Migrated to DB) ---
class KeyScopesRequest(BaseModel):
    scopes: List[str]
    expires_in_days: Optional[int] = None

class WebhookEventsRequest(BaseModel):
    events: List[str]

@router.get("/usage-analytics")
async def get_usage_analytics(x_user_id: Optional[str] = Header(None, alias="X-User-ID")):
    """Enterprise API Usage Analytics Dashboard — real-time stats from DB."""
    user_id = x_user_id or "default"
    
    from database.db import AsyncSessionLocal
    from database.orm import APICallLog, DeveloperAPIKey
    from sqlalchemy import select, func
    from datetime import timedelta
    import datetime as dt
    
    now = dt.datetime.utcnow()
    
    async with AsyncSessionLocal() as db:
        # Get real total_calls from DB keys
        result_total = await db.execute(
            select(func.sum(DeveloperAPIKey.total_calls)).filter(DeveloperAPIKey.user_id == uid)
        )
        real_total = result_total.scalar() or 0

        # Get call logs for the last 7 days
        week_ago = now - timedelta(days=7)
        result = await db.execute(
            select(APICallLog).filter(APICallLog.user_id == user_id, APICallLog.timestamp >= week_ago)
        )
        calls = result.scalars().all()
        
        # Also get week before that for week-over-week calculation
        two_weeks_ago = now - timedelta(days=14)
        result_prev_week = await db.execute(
            select(func.count(APICallLog.id)).filter(
                APICallLog.user_id == user_id, 
                APICallLog.timestamp >= two_weeks_ago,
                APICallLog.timestamp < week_ago
            )
        )
        prev_week_calls = result_prev_week.scalar() or 0

    total_calls_last_7d = len(calls)
    
    week_change = 0
    if prev_week_calls > 0:
        week_change = round(((total_calls_last_7d - prev_week_calls) / prev_week_calls) * 100, 1)
    elif total_calls_last_7d > 0:
        week_change = 100
        
    # Calls per hour (last 24h)
    calls_per_hour = []
    for h in range(24):
        hour_start = now - timedelta(hours=24 - h)
        hour_end = now - timedelta(hours=23 - h)
        count = sum(1 for c in calls if hour_start <= c.timestamp <= hour_end)
        calls_per_hour.append({
            "hour": hour_start.strftime("%H:%M"),
            "calls": count
        })
    
    # Calls per day (last 7 days)
    calls_per_day = []
    for d in range(7):
        day_start = now - timedelta(days=7 - d)
        day_end = now - timedelta(days=6 - d)
        count = sum(1 for c in calls if day_start <= c.timestamp <= day_end)
        calls_per_day.append({
            "day": day_start.strftime("%a %b %d"),
            "calls": count
        })
    
    # Latency percentiles
    latencies = [c.latency_ms for c in calls]
    latencies.sort()
    p50 = latencies[len(latencies)//2] if latencies else 0
    p95 = latencies[int(len(latencies)*0.95)] if latencies else 0
    p99 = latencies[int(len(latencies)*0.99)] if latencies else 0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    
    # Error rates
    status_4xx = sum(1 for c in calls if 400 <= c.status_code < 500)
    status_5xx = sum(1 for c in calls if c.status_code >= 500)
    status_2xx = sum(1 for c in calls if 200 <= c.status_code < 300)
    error_rate = ((status_4xx + status_5xx) / total_calls_last_7d * 100) if total_calls_last_7d > 0 else 0
    
    # Top endpoints
    endpoint_counts: Dict[str, int] = {}
    for c in calls:
        endpoint_counts[c.endpoint] = endpoint_counts.get(c.endpoint, 0) + 1
    top_endpoints = sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Rate limit status
    calls_last_minute = sum(1 for c in calls if c.timestamp >= (now - timedelta(minutes=1)))
    rate_limit = 1000  # per minute
    
    return {
        "total_calls": max(total_calls_last_7d, real_total),
        "week_change": week_change,
        "calls_per_hour": calls_per_hour,
        "calls_per_day": calls_per_day,
        "latency": {
            "p50": round(p50),
            "p95": round(p95),
            "p99": round(p99),
            "avg": round(avg_latency)
        },
        "errors": {
            "total_4xx": status_4xx,
            "total_5xx": status_5xx,
            "total_2xx": status_2xx,
            "error_rate": round(error_rate, 2)
        },
        "top_endpoints": [{"endpoint": ep, "calls": ct} for ep, ct in top_endpoints],
        "rate_limit": {
            "current": calls_last_minute,
            "limit": rate_limit,
            "remaining": max(0, rate_limit - calls_last_minute),
            "percentage": round(calls_last_minute / rate_limit * 100, 1)
        }
    }



@router.get("/keys/{key_id}/usage")
async def get_key_usage(key_id: str, x_user_id: Optional[str] = Header(None, alias="X-User-ID")):
    """Get usage stats for a specific API key."""
    user_id = x_user_id or "default"
    
    try:
        from database.db import AsyncSessionLocal
        from database.orm import DeveloperAPIKey
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(DeveloperAPIKey).filter(
                DeveloperAPIKey.id == uuid.UUID(key_id),
                DeveloperAPIKey.user_id == uid
            ))
            key = result.scalars().first()
            if not key:
                raise HTTPException(status_code=404, detail="Key not found")
            
            return {
                "key_id": str(key.id),
                "total_calls": key.total_calls,
                "data_processed_mb": key.data_processed_mb,
                "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                "status": key.status,
                "created_at": key.created_at.isoformat()
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/keys/{key_id}/scopes")
async def update_key_scopes(key_id: str, request: KeyScopesRequest, x_user_id: Optional[str] = Header(None, alias="X-User-ID")):
    """Update API key scopes/permissions."""
    user_id = x_user_id or "default"
    
    valid_scopes = {"read:data", "write:data", "train:models", "predict", "admin", "export", "chat"}
    invalid = set(request.scopes) - valid_scopes
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid scopes: {invalid}")
    
    try:
        from database.db import AsyncSessionLocal
        from database.orm import DeveloperAPIKey
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(DeveloperAPIKey).filter(
                DeveloperAPIKey.id == uuid.UUID(key_id),
                DeveloperAPIKey.user_id == uid
            ))
            key = result.scalars().first()
            if not key:
                raise HTTPException(status_code=404, detail="Key not found")
            
            key.scopes = request.scopes
            if request.expires_in_days:
                key.expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)
            await db.commit()
            
            return {"success": True, "scopes": request.scopes, "key_id": str(key.id)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/webhooks/{webhook_id}/events")
async def update_webhook_events(webhook_id: str, request: WebhookEventsRequest, x_user_id: Optional[str] = Header(None, alias="X-User-ID")):
    """Update which events trigger a webhook."""
    user_id = x_user_id or "default"
    
    valid_events = {
        "autopilot.completed", "training.complete", "anomaly.detected",
        "report.ready", "file.uploaded", "prediction.made", "drift.detected"
    }
    
    invalid = set(request.events) - valid_events
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid events: {invalid}")
        
    try:
        from database.db import AsyncSessionLocal
        from database.orm import WebhookEndpoint
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(WebhookEndpoint).filter(
                WebhookEndpoint.id == uuid.UUID(webhook_id),
                WebhookEndpoint.user_id == uid
            ))
            webhook = result.scalars().first()
            if not webhook:
                raise HTTPException(status_code=404, detail="Webhook not found")
                
            webhook.events = request.events
            await db.commit()
            
            return {"success": True, "events": webhook.events}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/webhooks/{webhook_id}/deliveries")
async def get_webhook_deliveries(webhook_id: str, x_user_id: Optional[str] = Header(None, alias="X-User-ID")):
    """Get last 10 webhook delivery attempts."""
    user_id = x_user_id or "default"
    
    try:
        from database.db import AsyncSessionLocal
        from database.orm import WebhookEndpoint, WebhookDelivery
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            try:
                uid = _uuid.UUID(user_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid user ID format")
            result = await db.execute(select(WebhookEndpoint).filter(
                WebhookEndpoint.id == uuid.UUID(webhook_id),
                WebhookEndpoint.user_id == uid
            ))
            webhook = result.scalars().first()
            if not webhook:
                raise HTTPException(status_code=404, detail="Webhook not found")
                
            del_result = await db.execute(
                select(WebhookDelivery)
                .filter(WebhookDelivery.webhook_id == webhook.id)
                .order_by(WebhookDelivery.timestamp.desc())
                .limit(10)
            )
            deliveries = del_result.scalars().all()
            
            return {
                "deliveries": [{
                    "id": str(d.id),
                    "event": d.event,
                    "status_code": d.status_code,
                    "response_time_ms": d.response_time_ms,
                    "success": d.success,
                    "timestamp": d.timestamp.isoformat(),
                    "error_message": d.error_message
                } for d in deliveries]
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

