"""
API v1 Router
"""

from fastapi import APIRouter
from api.v1.endpoints import files, chat, analytics, reports, email_prefs, onboarding, insights, exports

router = APIRouter()

# Include all endpoint routers
router.include_router(files.router, prefix="/files", tags=["Files"])
router.include_router(chat.router, prefix="/chat", tags=["Chat"])
router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
router.include_router(reports.router, prefix="/reports", tags=["Reports"])
router.include_router(email_prefs.router, prefix="/settings", tags=["Settings"])
router.include_router(onboarding.router, tags=["Onboarding"])
router.include_router(insights.router, tags=["Insights"])
router.include_router(exports.router, tags=["Exports"])


