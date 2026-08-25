"""
AUTONOMOUS DASHBOARD API - Power BI-Style Endpoint
====================================================

API endpoint for generating autonomous dashboards.
SECURED: Uses JWT authentication for proper user isolation.
"""

from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional, Dict, List, Any
from pydantic import BaseModel
import json

from api.deps import get_current_user_id
from database.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class DashboardRequest(BaseModel):
    """Request model for dashboard generation"""
    user_id: Optional[str] = None  # Legacy - ignored, use JWT instead
    refresh: bool = False
    # Slicers are applied server-side before every KPI/chart is calculated.
    active_filters: Dict[str, List[str]] = {}


class ChartExplainRequest(BaseModel):
    chart_title: str
    chart_type: str = "chart"
    chart_data: Any = None


class DashboardResponse(BaseModel):
    """Response model for dashboard"""
    success: bool
    dashboard: Optional[dict] = None
    error: Optional[str] = None


@router.post("/generate")
async def generate_dashboard(
    request: DashboardRequest = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
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
        
        # Apply the selected slicers before generating every dashboard artifact.
        # Ignore stale/unknown columns and empty selections so a saved dashboard
        # still opens after a data-source schema change.
        selected_filters = request.active_filters if request else {}
        for column, values in selected_filters.items():
            if column in df.columns and values:
                normalized = {str(value) for value in values}
                df = df[df[column].astype(str).isin(normalized)]

        if df.empty:
            return DashboardResponse(
                success=False,
                error="The selected slicers do not match any rows. Clear one or more filters and try again."
            )

        # Generate REAL dashboard with pandas calculations - NOT LLM math!
        from core.real_dashboard import generate_real_dashboard
        is_refresh = request.refresh if request else False
        dashboard = generate_real_dashboard(df, user_id, refresh=is_refresh)
        
        if "error" in dashboard:
            return DashboardResponse(
                success=False,
                error=dashboard["error"]
            )
            
        # SAVE TO DB for Admin visibility
        try:
            import uuid as _uuid
            from database.orm import Dashboard, Chart
            
            try:
                uid = _uuid.UUID(user_id)
            except ValueError:
                uid = _uuid.uuid5(_uuid.NAMESPACE_OID, str(user_id))
                
            title = dashboard.get('title', 'Autonomous Dashboard')
            new_dashboard = Dashboard(user_id=uid, title=title, layout=dashboard.get('layout', []))
            db.add(new_dashboard)
            await db.flush()

            for chart in dashboard.get('charts', []):
                new_chart = Chart(
                    dashboard_id=new_dashboard.id,
                    title=chart.get('title', 'Untitled Chart'),
                    chart_type=chart.get('type', 'bar'),
                    data=chart.get('data', []),
                    config=chart.get('config', {})
                )
                db.add(new_chart)
                
            await db.commit()
            print("✅ Dashboard saved to database for admin visibility.")
        except Exception as db_e:
            print(f"⚠️ Could not save dashboard to DB: {db_e}")
            await db.rollback()
        
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


@router.post("/explain-chart")
async def explain_chart(request: ChartExplainRequest):
    """Provide a data-grounded explanation for a chart without inventing facts."""
    try:
        traces = request.chart_data or []
        if isinstance(traces, dict):
            traces = [traces]
        if not isinstance(traces, list):
            traces = []

        points: List[tuple[str, float]] = []
        for trace in traces:
            if not isinstance(trace, dict):
                continue
            labels = trace.get("x") or trace.get("labels") or []
            values = trace.get("y") or trace.get("values") or []
            if not isinstance(labels, list): labels = [labels]
            if not isinstance(values, list): values = [values]
            for label, value in zip(labels, values):
                try:
                    points.append((str(label), float(value)))
                except (TypeError, ValueError):
                    continue

        if not points:
            explanation = (
                f"**{request.chart_title}** is a {request.chart_type} visualization. "
                "There are no numeric points available in this chart payload yet, so no trend or ranking is inferred."
            )
        else:
            values = [value for _, value in points]
            total = sum(values)
            top_label, top_value = max(points, key=lambda item: item[1])
            bottom_label, bottom_value = min(points, key=lambda item: item[1])
            share = (top_value / total * 100) if total else 0
            trend = ""
            if len(values) >= 2:
                change = values[-1] - values[0]
                direction = "increased" if change > 0 else "decreased" if change < 0 else "was unchanged"
                trend = f" Across the displayed order, the value {direction} from {values[0]:,.2f} to {values[-1]:,.2f}."
            explanation = (
                f"**{request.chart_title}** contains {len(points)} plotted values. "
                f"The highest value is **{top_label}** at **{top_value:,.2f}**"
                f" ({share:,.1f}% of the displayed total); the lowest is **{bottom_label}** at **{bottom_value:,.2f}**."
                f" The displayed total is **{total:,.2f}**.{trend}"
            )
        return {"success": True, "explanation": explanation}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unable to explain chart data: {exc}")


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

from database.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.orm import Dashboard, Chart

@router.post('/save')
async def save_dashboard(
    dashboard_data: dict,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    try:
        title = dashboard_data.get('title', 'Saved Dashboard')
        new_dashboard = Dashboard(user_id=user_id, title=title, layout=dashboard_data.get('layout', []))
        db.add(new_dashboard)
        await db.flush()

        for chart in dashboard_data.get('charts', []):
            new_chart = Chart(
                dashboard_id=new_dashboard.id,
                title=chart.get('title', 'Untitled Chart'),
                chart_type=chart.get('type', 'bar'),
                data=chart.get('data', []),
                config=chart.get('config', {})
            )
            db.add(new_chart)
            
        await db.commit()
        return {'success': True, 'message': 'Dashboard saved successfully', 'dashboard_id': str(new_dashboard.id)}
    except Exception as e:
        await db.rollback()
        return {'success': False, 'error': str(e)}

@router.get('/saved')
async def get_saved_dashboards(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    try:
        stmt = select(Dashboard).where(Dashboard.user_id == user_id)
        result = await db.execute(stmt)
        dashboards = result.scalars().all()
        
        return {
            'success': True, 
            'dashboards': [{'id': str(d.id), 'title': d.title, 'created_at': d.created_at.isoformat()} for d in dashboards]
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}
