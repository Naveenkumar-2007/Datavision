import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load env
load_dotenv()

# Import Routers - CORRECTED to match actual files
from api.v1.endpoints import (
    autonomous, 
    chat, 
    files,      # Was 'upload' - file is actually named files.py
    analytics,  # Was 'data' - file is actually named analytics.py
    reports     # Added reports.py
)

# Initialize App
app = FastAPI(
    title="AI Business Analyst - Visual Intelligence Engine",
    description="Autonomous Visual Decision Intelligence System",
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

# Include Routers - CORRECTED
app.include_router(autonomous.router, prefix="/api/v1/autonomous", tags=["Autonomous Visual Engine"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(files.router, prefix="/api/v1/files", tags=["Files"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])

@app.get("/")
async def root():
    return {
        "system": "AI Business Analyst", 
        "status": "active",
        "engine": "Visual Intelligence Compiler v3 (Premium)"
    }

@app.on_event("startup")
async def startup_event():
    print("✅ Visual Intelligence Engine (v3) Starting...")
    
@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 System Shutting Down...")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
