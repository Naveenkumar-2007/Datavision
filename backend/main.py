import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path

# Load env from multiple possible locations
# Try: backend/.env, project_root/.env
env_paths = [
    Path(__file__).parent / ".env",  # backend/.env
    Path(__file__).parent.parent / ".env",  # project_root/.env
]

for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment from: {env_path}")
        break
else:
    load_dotenv()  # Try default location
    print("⚠️ Using default .env location")

# Import Routers
from api.v1.endpoints import (
    chat, 
    files,
    analytics,
    reports,
    email_prefs
)

# Import Autonomous Dashboard API
try:
    from api.v1.endpoints import dashboard_api
    DASHBOARD_API_AVAILABLE = True
except ImportError:
    DASHBOARD_API_AVAILABLE = False
    print("⚠️ Dashboard API not available")

# 🧠 Import Autonomous Brain API
try:
    from api.v1.endpoints import brain
    BRAIN_API_AVAILABLE = True
    print("✅ Autonomous Brain API loaded")
except ImportError as e:
    BRAIN_API_AVAILABLE = False
    print(f"⚠️ Brain API not available: {e}")

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
if DASHBOARD_API_AVAILABLE:
    app.include_router(dashboard_api.router, prefix="/api/v1/dashboard", tags=["Dashboard"])

# 🧠 Autonomous Brain API
if BRAIN_API_AVAILABLE:
    app.include_router(brain.router, prefix="/api/v1/brain", tags=["Brain"])

# 🚀 DataVision API v2 (All Features)
try:
    from api.v1.endpoints import datavision_api
    app.include_router(datavision_api.router, prefix="/api/v2", tags=["DataVision v2"])
    print("✅ DataVision API v2 loaded")
except ImportError as e:
    print(f"⚠️ DataVision API v2 not available: {e}")

# 🤖 AutoML API (Production ML)
try:
    from api.v1.endpoints import automl_api
    app.include_router(automl_api.router, prefix="/api/v2/automl", tags=["AutoML"])
    print("✅ AutoML API loaded")
except ImportError as e:
    print(f"⚠️ AutoML API not available: {e}")

@app.get("/")
async def root():
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

@app.on_event("startup")
async def startup_event():
    print("=" * 50)
    print("🚀 DATAVISION 2.0 - Universal AI Data Platform")
    print("=" * 50)
    print("🧠 Autonomous Brain: ACTIVE")
    print("🤖 Universal Agent: ACTIVE")
    print("🔗 Knowledge Graphs: ACTIVE")
    print("🔮 Predictive Intelligence: ACTIVE")
    print("⚡ Advanced MCPs: LOADED")
    print("🏢 Enterprise Features: ENABLED")
    print("=" * 50)
    print("📡 API v2 available at: http://localhost:8000/api/v2")
    print("📚 Docs at: http://localhost:8000/docs")
    print("=" * 50)
    
@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 DataVision Shutting Down...")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
