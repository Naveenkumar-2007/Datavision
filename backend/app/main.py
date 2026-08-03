"""
DataVision — Application Factory

Creates and configures the FastAPI application.
Mounts both legacy v1 routes and new v2 routes for gradual migration.
"""

import logging
import sys
import os

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Ensure the backend directory is on the path for legacy imports
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.core.config import get_settings
from app.database.session import dispose_engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    logger.info("🚀 DataVision AI starting up...")
    yield
    logger.info("🛑 DataVision AI shutting down...")
    await dispose_engine()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="DataVision — Production-Grade AI Data Analytics Platform",
        docs_url="/api/docs" if settings.is_development else None,
        redoc_url="/api/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    # ── CORS ────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── New V2 API Routes ───────────────────────────────────────
    from app.api.v2.router import router as v2_router
    app.include_router(v2_router)

    # ── Legacy V1 API Routes ────────────────────────────────────
    # Mount the existing v1 application for backward compatibility
    try:
        from main import app as legacy_app

        # Re-mount all legacy routes under the new app
        for route in legacy_app.routes:
            if hasattr(route, 'path') and route.path.startswith('/api/v1'):
                app.routes.append(route)

        logger.info("✅ Legacy v1 routes mounted")
    except Exception as e:
        logger.warning(f"⚠️ Could not mount legacy v1 routes: {e}")
        # This is expected during initial development/testing
        # The legacy app may have import issues until fully integrated

    # ── Health Check ────────────────────────────────────────────
    @app.get("/health", tags=["System"])
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        }

    @app.get("/api/v2/health", tags=["System"])
    async def v2_health():
        return {
            "status": "healthy",
            "api_version": "v2",
            "app_version": settings.APP_VERSION,
        }

    # ── Static Files ────────────────────────────────────────────
    possible_static_dirs = [
        os.path.join(BACKEND_DIR, "static"),
        os.path.join(os.path.dirname(BACKEND_DIR), "static"),
        os.path.join(os.path.dirname(BACKEND_DIR), "frontend", "dist"),
    ]

    for static_dir in possible_static_dirs:
        if os.path.isdir(static_dir) and os.path.exists(os.path.join(static_dir, "index.html")):
            logger.info(f"✅ Serving static frontend from: {static_dir}")
            app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
            break

    return app


# Module-level app instance for uvicorn
app = create_app()
