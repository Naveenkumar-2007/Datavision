"""
AUTONOMOUS DASHBOARD API - Power BI-Style Endpoint
====================================================

API endpoint for generating autonomous dashboards.
"""

from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from pydantic import BaseModel
import json

router = APIRouter()


class DashboardRequest(BaseModel):
    """Request model for dashboard generation"""
    user_id: Optional[str] = None
    refresh: bool = False


class DashboardResponse(BaseModel):
    """Response model for dashboard"""
    success: bool
    dashboard: Optional[dict] = None
    error: Optional[str] = None


@router.post("/generate")
async def generate_dashboard(
    request: DashboardRequest = None,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """
    Generate an autonomous dashboard from user's data.
    
    This endpoint:
    1. Loads user's uploaded data
    2. Analyzes it with AI
    3. Generates a complete dashboard
    4. Returns KPIs, charts, insights
    """
    try:
        # Get user ID
        user_id = None
        if request and request.user_id:
            user_id = request.user_id
        elif x_user_id:
            user_id = x_user_id
        elif authorization and authorization.startswith("Bearer "):
            try:
                from database.auth import decode_jwt
                token = authorization.split(" ")[1]
                payload = decode_jwt(token)
                user_id = payload.get("sub")
            except:
                pass
        
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


@router.get("/summary/{user_id}")
async def get_dashboard_summary(
    user_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Get a quick data summary for dashboard header.
    """
    try:
        from api.v1.endpoints.charts import get_user_data
        from core.autonomous_dashboard import get_dashboard_summary as get_summary
        
        df = get_user_data(user_id)
        if df is None:
            return {"error": "No data available"}
        
        return get_summary(df)
        
    except Exception as e:
        return {"error": str(e)}
