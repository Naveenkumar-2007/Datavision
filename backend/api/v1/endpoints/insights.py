# Insights API - Simplified Stub
"""
API endpoints for accessing proactive insights.
Simplified version - no complex dependencies.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime

router = APIRouter(prefix="/insights", tags=["insights"])


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class InsightResponse(BaseModel):
    """Single insight response"""
    id: str
    workspace_id: str
    title: str
    body: str
    category: str
    priority: int
    severity: str
    metadata: Dict[str, Any] = {}
    chart_payload: Optional[Dict] = None
    created_at: str
    seen_at: Optional[str] = None
    dismissed: bool = False


class InsightSummaryResponse(BaseModel):
    """Summary of pending insights"""
    total_unseen: int
    by_category: Dict[str, int]
    by_severity: Dict[str, int]
    high_priority_count: int
    summary_text: str


# ============================================================================
# ENDPOINTS - Simplified stubs
# ============================================================================

@router.get("/unseen/{workspace_id}", response_model=List[InsightResponse])
async def get_unseen_insights(workspace_id: str, limit: int = 5):
    """Get unseen insights for a workspace."""
    # Return empty list for now - feature to be implemented
    return []


@router.get("/summary/{workspace_id}", response_model=InsightSummaryResponse)
async def get_insights_summary(workspace_id: str):
    """Get summary of pending insights for a workspace."""
    return InsightSummaryResponse(
        total_unseen=0,
        by_category={},
        by_severity={},
        high_priority_count=0,
        summary_text="No insights available"
    )


@router.post("/seen/{insight_id}")
async def mark_insight_seen(insight_id: str):
    """Mark a single insight as seen"""
    return {"message": "Insight marked as seen", "id": insight_id}


@router.post("/dismiss/{insight_id}")
async def dismiss_insight(insight_id: str):
    """Dismiss an insight (won't show again)"""
    return {"message": "Insight dismissed", "id": insight_id}


@router.post("/generate/{workspace_id}")
async def generate_insights(workspace_id: str):
    """
    Manually trigger insight generation for a workspace.
    """
    return {
        "message": "Insight generation not yet implemented",
        "insight_ids": [],
    }
