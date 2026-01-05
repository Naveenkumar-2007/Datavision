import os
import uvicorn
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("main")

# Load env using the new Settings logic (it loads env automatically on import)
from config.settings import Settings

# Import Routers
from api.v1.endpoints import (
    chat, 
    files,
    analytics,
    reports,
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
    version="3.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    return FileResponse(os.path.join(frontend_static_dir, "logo.png"))

@app.get("/logo.jpg")
async def serve_logo_jpg():
    return FileResponse(os.path.join(frontend_static_dir, "logo.jpg"))

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
    logger.info("=" * 50)
    logger.info("📡 API v2 available at: /api/v2")
    logger.info("📚 Docs at: /docs")
    logger.info("=" * 50)
    
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 DataVision Shutting Down...")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
