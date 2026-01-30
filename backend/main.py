import os
import uvicorn
import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv
from pathlib import Path

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
    email_prefs
)

# Import Autonomous Dashboard API
from api.v1.endpoints import dashboard_api

# 🧠 Import Autonomous Brain API
from api.v1.endpoints import brain
logger.info("✅ Autonomous Brain API loaded")

# Initialize App
app = FastAPI(
    title="DataVision - Autonomous AI Data Platform",
    description="$50B Silicon Valley AI Data Analysis System",
    version="3.0.0",
    # Security: Hide docs in production
    docs_url="/docs" if os.environ.get("ENVIRONMENT", "development") != "production" else None,
    redoc_url="/redoc" if os.environ.get("ENVIRONMENT", "development") != "production" else None,
)

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

# Trusted host middleware (prevent host header injection)
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
if os.environ.get("ENVIRONMENT") == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)

# CORS - Secure configuration
# Allow HuggingFace Spaces domains and local development
ALLOWED_ORIGINS = os.environ.get(
    "CORS_ORIGINS", 
    "http://localhost:5173,http://localhost:3000,http://localhost:8000,https://huggingface.co,https://killerkumar-ai-business-analyst.hf.space,https://*.hf.space"
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

from fastapi.responses import FileResponse

# Frontend static directory (pre-built React app)
frontend_static_dir = "/app/static"

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
    # Don't catch API routes
    if full_path.startswith("api/"):
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
    
    logger.info("=" * 50)
    logger.info("📡 API v2 available at: /api/v2")
    logger.info("📚 Docs at: /docs")
    logger.info("=" * 50)
    
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 DataVision Shutting Down...")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
