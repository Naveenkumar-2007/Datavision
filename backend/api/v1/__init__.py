"""
API v1 Router
"""

from fastapi import APIRouter
from api.v1.endpoints import files, chat, analytics, reports, email_prefs, onboarding, exports, voice, auth, admin
from api.v1.endpoints import data_health_api, explainability_api, playground_api
from api.v1.endpoints import clustering_api, async_reports, anomalies, simulator, search, ws, lineage, collaboration, deploy, monitoring, pipelines

router = APIRouter()

# Include all endpoint routers
router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(files.router, prefix="/files", tags=["Files"])
router.include_router(chat.router, prefix="/chat", tags=["Chat"])
router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
router.include_router(reports.router, prefix="/reports", tags=["Reports"])
router.include_router(email_prefs.router, prefix="/settings", tags=["Settings"])
router.include_router(onboarding.router, tags=["Onboarding"])
router.include_router(exports.router, tags=["Exports"])
router.include_router(voice.router, prefix="/voice", tags=["Voice"])
router.include_router(deploy.router, tags=["Deploy"])
router.include_router(monitoring.router, tags=["Monitoring"])
router.include_router(pipelines.router, tags=["Pipelines"])
router.include_router(async_reports.router, prefix="/async-reports", tags=["Async Tasks"])
router.include_router(anomalies.router, tags=["Anomalies"])
router.include_router(simulator.router, tags=["Simulator"])
router.include_router(search.router, tags=["Search"])
router.include_router(ws.router, prefix="/ws", tags=["WebSockets"])
router.include_router(lineage.router, prefix="/lineage", tags=["Data Lineage"])
router.include_router(collaboration.router, prefix="/collaboration", tags=["Collaboration Hub"])

# AutoML Feature APIs
router.include_router(data_health_api.router, tags=["AutoML - Data Health"])
router.include_router(explainability_api.router, tags=["AutoML - Explainability"])
router.include_router(playground_api.router, tags=["AutoML - Playground"])

# Clustering / Unsupervised Learning API
router.include_router(clustering_api.router, prefix="/ml", tags=["Clustering"])

# Admin Dashboard
router.include_router(admin.router, prefix="/admin", tags=["Admin"])
