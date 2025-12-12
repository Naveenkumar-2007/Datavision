"""
Complete working backend with proper multi-tenant RAG system
Real data processing, no fake data
Enterprise-grade error handling
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import sys
import traceback
import io
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding for emoji characters
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root AND backend to Python path for proper imports
project_root = Path(__file__).parent.parent
backend_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_root))

# Import routers
from api.v1.endpoints import files, chat, analytics, reports, graph, auth, admin, notifications

app = FastAPI(
    title="AI Business Analyst API - Enterprise Edition",
    description="Multi-tenant AI-powered business intelligence with real RAG",
    version="2.0.0"
)


# Global Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured response"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "HTTPException"
            },
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": {
                "code": 400,
                "message": str(exc),
                "type": "ValidationError"
            },
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    # Log the full error
    error_id = datetime.now().strftime("%Y%m%d%H%M%S")
    print(f"❌ Error ID: {error_id}")
    print(f"❌ Path: {request.url.path}")
    print(f"❌ Error: {type(exc).__name__}: {exc}")
    traceback.print_exc()
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": 500,
                "message": "An internal error occurred. Please try again.",
                "type": type(exc).__name__,
                "error_id": error_id
            },
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url.path)
        }
    )


# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "*"  # For development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(files.router, prefix="/api/v1/files", tags=["Files"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(graph.router, prefix="/api/v1/graph", tags=["Graph"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])

# Serve frontend static files in production
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

static_dir = Path("/app/static")
if static_dir.exists():
    # Mount static files
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")
    
    # Serve index.html for all other routes (SPA routing)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the SPA for all non-API routes"""
        # Don't intercept API routes
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi"):
            raise HTTPException(status_code=404, detail="Not found")
        
        # Serve index.html for all other routes
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Frontend not found")

@app.get("/")
async def root():
    return {
        "message": "AI Business Analyst API - Enterprise Edition",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Multi-tenant RAG",
            "Real data processing",
            "FAISS vector search",
            "Knowledge graph",
            "Chat history per user",
            "Real analytics from uploaded data"
        ],
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "database": "file-based",
        "vector_store": "FAISS",
        "graph": "NetworkX"
    }

# ===== TEST ENDPOINTS FOR NOTIFICATION SYSTEM =====
@app.post("/test-email")
async def test_email_notification():
    """Send a test email notification"""
    from services.email_service import send_insight_email
    
    try:
        await send_insight_email(
            to_email="naveenkumarchapala123@gmail.com",
            title="🎉 Test AI Insight - Revenue Alert",
            body="This is a test notification from your AI Business Analyst. Your revenue increased by 25% this week! Great work!",
            chart_payload=None,
            workspace_id="test-workspace"
        )
        return {
            "success": True,
            "message": "Test email sent to naveenkumarchapala123@gmail.com! Check your inbox.",
            "email": "naveenkumarchapala123@gmail.com"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to send email. Check your Resend API key and console logs."
        }

@app.post("/test-agent")
async def test_monitoring_agent():
    """Run the MonitoringAgent to create insights"""
    from agents.monitoring_agent import MonitoringAgent
    
    # Use a test workspace ID - replace with real ID if you have one
    workspace_id = "00000000-0000-0000-0000-000000000000"
    
    try:
        agent = MonitoringAgent()
        await agent.run(workspace_id)
        
        return {
            "success": True,
            "message": "MonitoringAgent completed! Check Supabase ai_insights table.",
            "workspace_id": workspace_id
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Agent failed. Check console logs for details."
        }


# ===== STATIC FILE SERVING FOR PRODUCTION =====
# Serve React frontend build in production (Hugging Face Spaces)
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="static")
    
    # Serve index.html for all other routes (SPA routing)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve React SPA - all routes go to index.html"""
        # If it's an API route, skip
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi"):
            raise HTTPException(status_code=404, detail="Not found")
        
        # Serve index.html
        index_file = frontend_dist / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        raise HTTPException(status_code=404, detail="Frontend not built")

if __name__ == "__main__":
    # Use PORT environment variable for Hugging Face (7860) or default to 8000
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True if port == 8000 else False,
        log_level="info"
    )
