"""
AUTONOMOUS DASHBOARD API - Power BI-Style Endpoint
====================================================

API endpoint for generating autonomous dashboards.
SECURED: Uses JWT authentication for proper user isolation.
"""

from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional
from pydantic import BaseModel
import json

from api.deps import get_current_user_id

router = APIRouter()


class DashboardRequest(BaseModel):
    """Request model for dashboard generation"""
    user_id: Optional[str] = None  # Legacy - ignored, use JWT instead
    refresh: bool = False


class DashboardResponse(BaseModel):
    """Response model for dashboard"""
    success: bool
    dashboard: Optional[dict] = None
    error: Optional[str] = None


@router.post("/generate")
async def generate_dashboard(
    request: DashboardRequest = None,
    user_id: str = Depends(get_current_user_id)
):
    """
    Generate an autonomous dashboard from user's data.
    SECURED: user_id extracted from JWT token, NOT from request body.
    
    This endpoint:
    1. Loads user's uploaded data (user-isolated)
    2. Analyzes it with AI
    3. Generates a complete dashboard
    4. Returns KPIs, charts, insights
    """
    try:
        # user_id is now securely obtained from JWT via get_current_user_id
        if not user_id:
            return DashboardResponse(
                success=False,
                error="User ID required. Please log in."
            )
        
        # Load user's data
        from api.v1.endpoints.charts import get_user_data
        df = get_user_data(user_id)
        
        if df is None or df.empty:
            return DashboardResponse(
                success=False,
                error="No data available. Please upload files first in DataHub."
            )
        
        # Generate REAL dashboard with pandas calculations - NOT LLM math!
        from core.real_dashboard import generate_real_dashboard
        dashboard = generate_real_dashboard(df, user_id)
        
        if "error" in dashboard:
            return DashboardResponse(
                success=False,
                error=dashboard["error"]
            )
        
        return DashboardResponse(
            success=True,
            dashboard=dashboard
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return DashboardResponse(
            success=False,
            error=str(e)
        )


@router.get("/summary/{path_user_id}")
async def get_dashboard_summary(
    path_user_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get a quick data summary for dashboard header.
    SECURED: Validates that path user_id matches authenticated user.
    """
    try:
        # Use authenticated user_id, not path parameter (for security)
        user_id = current_user_id
        
        # Optionally verify path matches authenticated user (prevent URL manipulation)
        if path_user_id != current_user_id and not current_user_id.startswith("guest_"):
            return {"error": "Unauthorized access to another user's data"}
        
        from api.v1.endpoints.charts import get_user_data
        from core.autonomous_dashboard import get_dashboard_summary as get_summary
        
        df = get_user_data(user_id)
        if df is None:
            return {"error": "No data available"}
        
        return get_summary(df)
        
    except Exception as e:
        return {"error": str(e)}
