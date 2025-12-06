"""
API v1 Router
"""

from fastapi import APIRouter
from api.v1.endpoints import files, chat, analytics, reports

router = APIRouter()

# Include all endpoint routers
router.include_router(files.router, prefix="/files", tags=["Files"])
router.include_router(chat.router, prefix="/chat", tags=["Chat"])
router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
router.include_router(reports.router, prefix="/reports", tags=["Reports"])
