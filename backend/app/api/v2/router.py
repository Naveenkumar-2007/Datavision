"""V2 API Router — aggregates all v2 endpoint routers."""

from fastapi import APIRouter

from app.api.v2.endpoints.auth import router as auth_router
from app.api.v2.endpoints.admin import router as admin_router

router = APIRouter(prefix="/api/v2")
router.include_router(auth_router)
router.include_router(admin_router)
