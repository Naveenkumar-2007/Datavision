# Insights API - Proactive Intelligence Endpoints
"""
API endpoints for accessing proactive insights.
Surfaces anomalies and insights on dashboard login.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.insight_queue import (
    InsightQueue,
    QueuedInsight,
    get_insight_queue,
    InsightPriority,
    InsightCategory,
)

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


class MarkSeenRequest(BaseModel):
    """Request to mark insight as seen"""
    insight_ids: List[str]


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/unseen/{workspace_id}", response_model=List[InsightResponse])
async def get_unseen_insights(workspace_id: str, limit: int = 5):
    """
    Get unseen insights for a workspace.
    Ordered by priority (highest first).
    """
    queue = get_insight_queue()
    insights = queue.get_unseen(workspace_id, limit=limit)
    
    return [
        InsightResponse(
            id=i.id,
            workspace_id=i.workspace_id,
            title=i.title,
            body=i.body,
            category=i.category,
            priority=i.priority,
            severity=i.severity,
            metadata=i.metadata,
            chart_payload=i.chart_payload,
            created_at=i.created_at,
            seen_at=i.seen_at,
            dismissed=i.dismissed,
        )
        for i in insights
    ]


@router.get("/summary/{workspace_id}", response_model=InsightSummaryResponse)
async def get_insights_summary(workspace_id: str):
    """
    Get summary of pending insights for a workspace.
    Used for dashboard notification badges.
    """
    queue = get_insight_queue()
    summary = queue.get_summary(workspace_id)
    
    return InsightSummaryResponse(**summary)


@router.post("/seen/{insight_id}")
async def mark_insight_seen(insight_id: str):
    """Mark a single insight as seen"""
    queue = get_insight_queue()
    success = queue.mark_seen(insight_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Insight not found")
    
    return {"message": "Insight marked as seen", "id": insight_id}


@router.post("/seen")
async def mark_multiple_seen(request: MarkSeenRequest):
    """Mark multiple insights as seen"""
    queue = get_insight_queue()
    results = []
    
    for insight_id in request.insight_ids:
        success = queue.mark_seen(insight_id)
        results.append({"id": insight_id, "success": success})
    
    return {"results": results}


@router.post("/dismiss/{insight_id}")
async def dismiss_insight(insight_id: str):
    """Dismiss an insight (won't show again)"""
    queue = get_insight_queue()
    success = queue.dismiss(insight_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Insight not found")
    
    return {"message": "Insight dismissed", "id": insight_id}


@router.post("/generate/{workspace_id}")
async def generate_insights(workspace_id: str):
    """
    Manually trigger insight generation for a workspace.
    Normally this runs automatically via scheduler.
    """
    try:
        from agents.monitoring_agent import MonitoringAgent
        
        agent = MonitoringAgent()
        insights = await agent.detect_insights(workspace_id)
        
        # Add to queue
        queue = get_insight_queue()
        queued = []
        
        for insight in insights:
            queued_insight = queue.add(
                workspace_id=workspace_id,
                title=insight.title,
                body=insight.body,
                category="anomaly",
                priority=8 if insight.severity == "high" else 5,
                severity=insight.severity,
                metadata=insight.metadata,
                chart_payload=insight.chart_payload,
            )
            queued.append(queued_insight.id)
        
        return {
            "message": f"Generated {len(queued)} insights",
            "insight_ids": queued,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
