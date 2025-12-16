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
from api.v1.endpoints import files, chat, analytics, reports, graph, auth, admin, notifications, email_prefs, charts

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
            }
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
                "type": "ValueError"
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    # Print stack trace for debugging
    traceback.print_exc()
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": 500,
                "message": str(exc),
                "type": type(exc).__name__,
                "timestamp": datetime.now().isoformat(),
                "path": str(request.url.path)
            }
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
app.include_router(email_prefs.router, prefix="/api/v1/settings", tags=["Settings"])
app.include_router(charts.router, prefix="/api/v1/charts", tags=["Charts"])

# ===== AUTOMATIC EMAIL SCHEDULER =====
import asyncio
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Global scheduler instance
email_scheduler = None

def run_email_check():
    """Background task to check and send scheduled emails"""
    import traceback
    from datetime import timezone, timedelta
    
    # Get IST time for logging
    IST = timezone(timedelta(hours=5, minutes=30))
    now_ist = datetime.now(IST)
    
    print(f"\n{'='*50}")
    print(f"🕐 SCHEDULER CHECK at {now_ist.strftime('%H:%M:%S')} IST")
    print(f"{'='*50}")
    
    try:
        from scheduler.scheduled_reporter import check_and_send_reports
        # Run the async function in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(check_and_send_reports())
        loop.close()
        print(f"✅ Scheduler check COMPLETED at {now_ist.strftime('%H:%M:%S')} IST")
        print(f"{'='*50}\n")
    except Exception as e:
        print(f"❌ SCHEDULER ERROR: {e}")
        traceback.print_exc()
        print(f"{'='*50}\n")

@app.on_event("startup")
async def start_email_scheduler():
    """Start the background email scheduler on app startup"""
    global email_scheduler
    try:
        email_scheduler = BackgroundScheduler()
        # Run every minute to check for scheduled reports
        email_scheduler.add_job(
            run_email_check,
            CronTrigger(minute='*'),  # Every minute
            id='email_report_checker',
            name='Check and send scheduled email reports',
            replace_existing=True
        )
        email_scheduler.start()
        print("📧 Email scheduler started - checking every minute for scheduled reports")
    except Exception as e:
        print(f"❌ Failed to start email scheduler: {e}")

@app.on_event("shutdown")
async def stop_email_scheduler():
    """Stop the background email scheduler on app shutdown"""
    global email_scheduler
    if email_scheduler:
        email_scheduler.shutdown()
        print("📧 Email scheduler stopped")


# Serve frontend static files in production
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

static_dir = Path("/app/static")
# Search for possible static locations
possible_static_dirs = [
    Path("static"),
    Path("../frontend/dist"),
    Path("frontend/dist"),
]

for d in possible_static_dirs:
    if d.exists() and d.is_dir():
        static_dir = d
        break

print(f"📁 Static directory exists: {static_dir.exists()}")

if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")

    def get_index_with_env():
        """Inject environment variables into index.html"""
        index_path = static_dir / "index.html"
        if not index_path.exists():
            return "index.html not found"
        
        content = index_path.read_text(encoding="utf-8")
        
        # Get Supabase env vars (check multiple possible names)
        supabase_url = os.getenv('VITE_SUPABASE_URL') or os.getenv('SUPABASE_URL', '')
        supabase_anon_key = os.getenv('VITE_SUPABASE_ANON_KEY') or os.getenv('SUPABASE_ANON_KEY', '')
        
        # Inject detailed environment config - use window._env_ to match frontend
        env_config = f"""
        <script>
            window._env_ = {{
                API_URL: "/api/v1",
                VITE_API_URL: "/api/v1",
                VITE_SUPABASE_URL: "{supabase_url}",
                VITE_SUPABASE_ANON_KEY: "{supabase_anon_key}",
                MODE: "production"
            }};
            // Also set window.ENV for backwards compatibility
            window.ENV = window._env_;
            console.log("🚀 Environment injected:", window._env_);
        </script>
        """
        return content.replace("</head>", f"{env_config}</head>")

    # Serve index.html for root
    @app.get("/")
    async def serve_root():
        return HTMLResponse(content=get_index_with_env())
    
    # Serve index.html for all SPA routes
    # API routes are handled by the routers mounted before this catch-all
    # FastAPI processes routes in order, so API routes will be matched first
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Check if file exists in static (e.g. icons, images)
        file_path = static_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        
        # For all other paths (SPA routes), return index.html
        return HTMLResponse(content=get_index_with_env())
else:
    # No static dir - just serve API info
    @app.get("/")
    async def root():
        return {
            "message": "AI Business Analyst API - Enterprise Edition",
            "version": "2.0.0",
            "status": "online",
            "docs": "/docs"
        }

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/scheduler-status")
async def scheduler_status():
    """Check scheduler status and list pending jobs"""
    from datetime import timezone, timedelta
    IST = timezone(timedelta(hours=5, minutes=30))
    now_ist = datetime.now(IST)
    
    global email_scheduler
    if email_scheduler:
        jobs = []
        for job in email_scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else "None"
            })
        return {
            "scheduler_running": email_scheduler.running,
            "current_time_ist": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
            "jobs": jobs
        }
    return {"scheduler_running": False, "error": "Scheduler not initialized"}

@app.post("/api/trigger-scheduler")
async def trigger_scheduler():
    """Manually trigger the scheduler check"""
    from datetime import timezone, timedelta
    IST = timezone(timedelta(hours=5, minutes=30))
    now_ist = datetime.now(IST)
    
    try:
        run_email_check()
        return {
            "success": True,
            "message": f"Scheduler check triggered at {now_ist.strftime('%H:%M:%S')} IST"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ===== TEST ENDPOINTS FOR NOTIFICATION SYSTEM =====

@app.get("/test-email")
async def test_email_notification():
    """Send a test email notification"""
    try:
        from services.email_service import send_email
        
        success = await send_email(
            to_email="test@example.com", 
            subject="Test Notification",
            body="<h1>It Works!</h1><p>This is a test email from the AI Business Analyst.</p>"
        )
        
        return {"success": success, "message": "Email sent" if success else "Failed to send email"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/test-agent")
async def test_monitoring_agent():
    """Run the MonitoringAgent to create insights"""
    try:
        from agents.monitoring import MonitoringAgent
        
        # Run agent for a default user
        agent = MonitoringAgent()
        insights = await agent.run("default_user")
        
        return {
            "success": True, 
            "insights_generated": len(insights),
            "insights": insights
        }
    except Exception as e:
        traceback.print_exc()
        return {"success": False, "error": str(e)}



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
