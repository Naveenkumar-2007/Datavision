"""
Complete working backend with proper multi-tenant RAG system
Real data processing, no fake data
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
from pathlib import Path

# Add project root AND backend to Python path for proper imports
project_root = Path(__file__).parent.parent
backend_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_root))

# Import routers
from api.v1.endpoints import files, chat, analytics, reports, graph

app = FastAPI(
    title="AI Business Analyst API - Enterprise Edition",
    description="Multi-tenant AI-powered business intelligence with real RAG",
    version="2.0.0"
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

# Include REAL routers (no fake data)
app.include_router(files.router, prefix="/api/v1/files", tags=["Files"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(graph.router, prefix="/api/v1", tags=["Graph Visualization"])

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

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
