import os
import sys
import time
import asyncio
# Force UTF-8 for Windows console emoji printing
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"
os.environ["TF_USE_LEGACY_KERAS"] = "1"

import uvicorn
import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv
from pathlib import Path
from starlette.middleware.sessions import SessionMiddleware

# Configure Logging
# Configure Logging
# Note: Basic logging is handled in settings.py which is imported below.
# We just ensure uvicorn loggers verify settings.
import sys
logging.getLogger("uvicorn.access").handlers = [logging.StreamHandler(sys.stdout)]
logging.getLogger("uvicorn.error").handlers = [logging.StreamHandler(sys.stdout)]
logger = logging.getLogger("main")

# Load env using the new Settings logic (it loads env automatically on import)
from config.settings import Settings

# Import Routers
from api.v1.endpoints import (
    chat, 
    files,
    analytics,
    reports,
    email_prefs,
    decisions,
    synthetic,
    anomalies,
    lineage,
    collaboration,
    simulator,
    search,
    voice,
    ws,
    live_streaming
)

# Import Autonomous Dashboard API
from api.v1.endpoints import dashboard_api

# 🧠 Import Autonomous Brain API
from api.v1.endpoints import brain
logger.info("✅ Autonomous Brain API loaded")

# Initialize App
app = FastAPI(
    title="DataVision - Autonomous AI Data Platform",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

@app.on_event("startup")
async def verify_tables():
    from database.db import engine
    from database import orm
    from database.orm import Base
    try:
        async with engine.begin() as conn:
            logger.info("📦 Verifying database tables exist (auto-healing)...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database tables verified/created successfully!")
    except Exception as e:
        logger.error(f"⚠️ Failed to auto-heal database tables: {e}")

# ============================================
# SECURITY MIDDLEWARE
# ============================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Allow embedding in HuggingFace iframe
        response.headers["X-Frame-Options"] = "ALLOWALL"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Remove server header (MutableHeaders uses del, not pop)
        if "server" in response.headers:
            del response.headers["server"]
        
        return response

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add session middleware (required for Authlib OAuth)
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("JWT_SECRET_KEY", "super-secret-session-key"))

class APICallLogMiddleware(BaseHTTPMiddleware):
    """Log all API requests to the APICallLog table"""
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time_ms = int((time.time() - start_time) * 1000)
        
        # Log all /api/ requests, ignoring /api/config and static files
        if request.url.path.startswith("/api/") and not request.url.path.startswith("/api/config"):
            asyncio.create_task(self.log_request(
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code,
                latency_ms=process_time_ms,
                user_id=request.headers.get("X-User-ID")
            ))
            
        return response

    async def log_request(self, endpoint: str, method: str, status_code: int, latency_ms: int, user_id: str):
        try:
            from database.db import AsyncSessionLocal
            from database.orm import APICallLog
            async with AsyncSessionLocal() as db:
                log = APICallLog(
                    user_id=user_id,
                    endpoint=endpoint,
                    method=method,
                    status_code=status_code,
                    latency_ms=latency_ms
                )
                db.add(log)
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to log API call: {e}")

app.add_middleware(APICallLogMiddleware)

# Rate Limit Header Middleware
from core.rate_limiter import RateLimitHeaderMiddleware, get_rate_limiter
app.add_middleware(RateLimitHeaderMiddleware)
logger.info(f"✅ Rate limiter: {type(get_rate_limiter()).__name__}")

# Trusted host middleware (prevent host header injection)
# ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
# if os.environ.get("ENVIRONMENT") == "production":
#     app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)

# CORS - Secure configuration
# Allow HuggingFace Spaces domains and local development
ALLOWED_ORIGINS = os.environ.get(
    "CORS_ORIGINS", 
    "http://localhost:5173,http://localhost:5174,http://localhost:3000,http://localhost:8000,https://huggingface.co,https://killerkumar-ai-business-analyst.hf.space,https://datavision-ai-datavision.hf.space,https://*.hf.space"
).split(",")

# For HuggingFace Spaces, we need to allow all origins for the embedded iframe
if os.path.exists("/app"):  # Running in Docker/HF
    ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],  # Allow all headers for HF compatibility
    max_age=600,
)

# Mount Static Files
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(files.router, prefix="/api/v1/files", tags=["Files"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(email_prefs.router, prefix="/api/v1/settings", tags=["Settings"])
app.include_router(decisions.router, prefix="/api/v1/decisions", tags=["Decisions"])
app.include_router(synthetic.router, prefix="/api/v1/synthetic", tags=["Synthetic Data"])

# Mount new feature APIs
app.include_router(anomalies.router, prefix="/api/v1", tags=["Anomalies"])
app.include_router(lineage.router, prefix="/api/v1/lineage", tags=["Lineage"])
app.include_router(collaboration.router, prefix="/api/v1/collaboration", tags=["Collaboration"])
app.include_router(simulator.router, prefix="/api/v1", tags=["Simulator"])
app.include_router(search.router, prefix="/api/v1", tags=["Search"])
app.include_router(voice.router, prefix="/api/v1/voice", tags=["Voice"])
app.include_router(ws.router, prefix="/api/v1/ws", tags=["WebSockets"])
app.include_router(live_streaming.router, prefix="/api/v1", tags=["Live Streaming"])

from api.v1.endpoints import auth
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])

# 📤 Exports API (PDF, PPTX, Email)
from api.v1.endpoints import exports
app.include_router(exports.router, prefix="/api/v1", tags=["Exports"])
logger.info("✅ Exports API loaded (PDF, PPTX, Email)")


# 🏆 Autonomous Dashboard API
app.include_router(dashboard_api.router, prefix="/api/v1/dashboard", tags=["Dashboard"])

# 🧠 Autonomous Brain API
app.include_router(brain.router, prefix="/api/v1/brain", tags=["Brain"])

# 🚀 DataVision API v2 (All Features)
from api.v1.endpoints import datavision_api
app.include_router(datavision_api.router, prefix="/api/v2", tags=["DataVision v2"])
logger.info("✅ DataVision API v2 loaded")

# 🤖 AutoML API (Production ML)
from api.v1.endpoints import automl_api
app.include_router(automl_api.router, prefix="/api/v2/automl", tags=["AutoML"])
app.include_router(automl_api.router, prefix="/api/v1/automl", tags=["AutoML v1"])  # Also register at v1 for compatibility
logger.info("✅ AutoML API loaded")

# 🤖 Autonomous API (Model Management + Auto-Fix)
from api.v1.endpoints import autonomous_api
app.include_router(autonomous_api.router, prefix="/api/v2/autonomous", tags=["Autonomous"])
logger.info("✅ Autonomous API loaded (Model Management + Auto-Fix)")

# 🤖 Agentic AutoML (Multi-Agent ML Pipeline)
from api.v1.endpoints import agentic_automl_api
app.include_router(agentic_automl_api.router, prefix="/api/v2", tags=["Agentic AutoML"])
logger.info("✅ Agentic AutoML API loaded (9 Specialized Agents)")

# 🏥 Data Health API
from api.v1.endpoints import data_health_api
app.include_router(data_health_api.router, prefix="/api/v1", tags=["Data Health"])
logger.info("✅ Data Health API loaded")

# 🎮 Playground API
from api.v1.endpoints import playground_api
app.include_router(playground_api.router, prefix="/api/v1", tags=["Playground"])
logger.info("✅ Playground API loaded")

# 🔍 Explainability API
from api.v1.endpoints import explainability_api
app.include_router(explainability_api.router, prefix="/api/v1", tags=["Explainability"])
logger.info("✅ Explainability API loaded")

# 🚢 Enterprise MLOps Deployment API
from api.v1.endpoints import mlops
app.include_router(mlops.router, prefix="/api/v1", tags=["MLOps"])
logger.info("✅ MLOps API loaded")

# 🎯 Clustering API (Unsupervised Learning)
from api.v1.endpoints import clustering_api
app.include_router(clustering_api.router, prefix="/api/v1/ml", tags=["Clustering"])
logger.info("✅ Clustering API loaded (K-Means, DBSCAN, GMM, Spectral)")

# 💻 Web IDE API (Execution & Chat)
from api.v1.endpoints import ide_api
app.include_router(ide_api.router, prefix="/api/v1/ide", tags=["Web IDE"])
logger.info("✅ Web IDE API loaded (Code Execution)")

# 🧠 Agentic Autopilot API (V5 — Autonomous Data Science)
# ⚙️ Autopilot & Agents
from api.v1.endpoints import autopilot_api
app.include_router(autopilot_api.router, prefix="/api/v1/autopilot", tags=["Autopilot"])

# 🛠 Developer & API Center
from api.v1.endpoints import developer
app.include_router(developer.router, prefix="/api/v1/developer", tags=["Developer"])

# 🚀 Model Deploy API
from api.v1.endpoints import deploy
app.include_router(deploy.router, prefix="/api/v1", tags=["Deploy"])

# 🚨 Anomaly Detection
from api.v1.endpoints import anomalies
app.include_router(anomalies.router, prefix="/api/v1/anomalies", tags=["Anomalies"])

# ==========================================
# 🚀 V2 APIs (Agentic + RAG)
# ==========================================

from fastapi.responses import FileResponse

# Frontend static directory (pre-built React app)
frontend_static_dir = "/app/static"

@app.get("/api/config")
async def get_frontend_config():
    """
    Secure config endpoint for frontend.
    Returns only PUBLIC configuration needed for client-side operations.
    """
    return {
        "VITE_API_URL": os.environ.get("VITE_API_URL", ""),
        "auth_mode": "jwt"
    }

@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "platform": "DataVision - Universal AI Data Platform", 
        "version": "2.0.0",
        "status": "active",
        "apis": {
            "v1": "/api/v1/* (legacy endpoints)",
            "v2": "/api/v2/* (all features)"
        },
        "capabilities": [
            "autonomous_brain",
            "universal_agent",
            "chain_of_thought_reasoning",
            "react_framework",
            "knowledge_graphs",
            "predictive_intelligence",
            "root_cause_analysis",
            "ai_segmentation",
            "trend_detection",
            "cohort_analysis",
            "automl",
            "what_if_simulation",
            "enterprise_exports"
        ]
    }

# Serve React frontend - must be after all API routes
@app.get("/")
async def serve_frontend():
    """Serve React frontend"""
    index_path = os.path.join(frontend_static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "Frontend not found", "path": index_path}

# Serve logo files
@app.get("/logo.svg")
async def serve_logo_svg():
    logo_path = os.path.join(frontend_static_dir, "logo.svg")
    if os.path.exists(logo_path):
        return FileResponse(logo_path, media_type="image/svg+xml")
    return {"error": "logo.svg not found"}

@app.get("/logo.png")
async def serve_logo_png():
    logo_path = os.path.join(frontend_static_dir, "logo.png")
    if os.path.exists(logo_path):
        return FileResponse(logo_path)
    return {"error": "logo.png not found"}

@app.get("/logo.jpg")
async def serve_logo_jpg():
    logo_path = os.path.join(frontend_static_dir, "logo.jpg")
    if os.path.exists(logo_path):
        return FileResponse(logo_path)
    return {"error": "logo.jpg not found"}

@app.get("/datavision-logo.jpg")
async def serve_datavision_logo():
    logo_path = os.path.join(frontend_static_dir, "datavision-logo.jpg")
    if os.path.exists(logo_path):
        return FileResponse(logo_path, media_type="image/jpeg")
    return {"error": "datavision-logo.jpg not found"}

@app.get("/datavision-logo-dark.jpg")
async def serve_datavision_logo_dark():
    logo_path = os.path.join(frontend_static_dir, "datavision-logo-dark.jpg")
    if os.path.exists(logo_path):
        return FileResponse(logo_path, media_type="image/jpeg")
    return {"error": "datavision-logo-dark.jpg not found"}

@app.get("/datavision-logo-light.jpg")
async def serve_datavision_logo_light():
    logo_path = os.path.join(frontend_static_dir, "datavision-logo-light.jpg")
    if os.path.exists(logo_path):
        return FileResponse(logo_path, media_type="image/jpeg")
    return {"error": "datavision-logo-light.jpg not found"}

@app.get("/logo_transparent.png")
async def serve_logo_transparent():
    logo_path = os.path.join(frontend_static_dir, "logo_transparent.png")
    if os.path.exists(logo_path):
        return FileResponse(logo_path)
    return {"error": "logo_transparent.png not found"}

@app.get("/datavision_icon_v3.png")
async def serve_datavision_icon():
    icon_path = os.path.join(frontend_static_dir, "datavision_icon_v3.png")
    if os.path.exists(icon_path):
        return FileResponse(icon_path)
    return {"error": "datavision_icon_v3.png not found"}

# Serve service worker
@app.get("/sw.js")
async def serve_sw():
    return FileResponse(os.path.join(frontend_static_dir, "sw.js"))

# Mount static assets (JS, CSS, images)
if os.path.exists(frontend_static_dir):
    assets_dir = os.path.join(frontend_static_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

# Catch-all route for SPA (React Router) - must be LAST
@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    """Fallback for client-side routing"""
    # Don't catch API routes or FastAPI built-in docs
    if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path.startswith("openapi.json"):
        return {"error": "Not found"}
    index_path = os.path.join(frontend_static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "Frontend not found"}

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 50)
    logger.info("🚀 DATAVISION 2.0 - Universal AI Data Platform")
    logger.info("=" * 50)
    logger.info("🧠 Autonomous Brain: ACTIVE")
    logger.info("🤖 Universal Agent: ACTIVE")
    logger.info("🔗 Knowledge Graphs: ACTIVE")
    logger.info("🔮 Predictive Intelligence: ACTIVE")
    logger.info("⚡ Advanced MCPs: LOADED")
    logger.info("🏢 Enterprise Features: ENABLED")
    
    # 📧 Start Email Scheduler for Daily/Weekly Reports
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger
        from scheduler.scheduled_reporter import check_and_send_reports
        
        scheduler = AsyncIOScheduler()
        
        # Run every minute to check for scheduled email times
        scheduler.add_job(
            check_and_send_reports,
            CronTrigger(minute="*"),  # Every minute
            id="email_report_checker",
            name="Check and send scheduled email reports",
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("📧 Email Scheduler: ACTIVE (checking every minute)")
        
    except Exception as e:
        logger.warning(f"⚠️ Email scheduler not started: {e}")
        
    # 🔌 Start WebSocket real-time updates task
    try:
        from api.v1.endpoints.ws import push_realtime_updates
        import asyncio
        asyncio.create_task(push_realtime_updates())
        logger.info("🔌 WebSocket real-time updates: ACTIVE")
    except Exception as e:
        logger.warning(f"⚠️ WebSocket task not started: {e}")
    
    logger.info("=" * 50)
    logger.info("📡 API v2 available at: /api/v2")
    logger.info("📚 Docs at: /docs")
    logger.info("=" * 50)
    
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 DataVision Shutting Down...")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
