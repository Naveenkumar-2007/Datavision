# Report Download API Endpoints
"""
📄 Report API - Download and manage reports

Endpoints:
- GET /api/v1/reports/ - List all reports
- POST /api/v1/reports/generate - Generate new report
- GET /api/v1/reports/download/{user_id}/{filename} - Download report
- GET /api/v1/reports/preview/{user_id}/{filename} - Preview HTML report
- DELETE /api/v1/reports/{filename} - Delete report
"""

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import logging

logger = logging.getLogger(__name__)

from core.rate_limiter import check_rate_limit

router = APIRouter(prefix="/reports", tags=["Reports"])

# Import report generator
try:
    from mcp.report_generator import (
        ReportGenerator, 
        ReportFormat,
        generate_report,
        generate_excel_report,
        list_user_reports
    )
    REPORT_GEN_AVAILABLE = True
except ImportError:
    REPORT_GEN_AVAILABLE = False
    logger.warning("Report Generator not available")

# Claude-style intelligent report generator
try:
    from core.claude_report_generator import ClaudeReportGenerator, generate_claude_report
    CLAUDE_REPORT_AVAILABLE = True
    logger.info("✅ Claude Report Generator loaded")
except ImportError:
    CLAUDE_REPORT_AVAILABLE = False
    logger.warning("Claude Report Generator not available")

# Dynamic report generator for all 6 report types (V2 with Advanced Agent)
try:
    from core.dynamic_report_generator import DynamicReportGenerator, generate_dynamic_report, generate_dynamic_report_async
    DYNAMIC_REPORT_AVAILABLE = True
    logger.info("✅ Dynamic Report Generator V2 loaded (Advanced Agent)")
except ImportError:
    DYNAMIC_REPORT_AVAILABLE = False
    logger.warning("Dynamic Report Generator not available")


class ReportRequest(BaseModel):
    """Request to generate a report"""
    userId: Optional[str] = None
    reportType: str = "summary"  # metrics, breakdown, summary, executive, predictive, anomaly
    query: str = ""
    title: Optional[str] = None
    format: str = "json"  # json for frontend, html for download
    dateRange: Optional[str] = "all"
    include_charts: bool = True
    include_summary: bool = True
    include_recommendations: bool = True


class ReportResponse(BaseModel):
    """Response from report generation"""
    success: bool
    format: str
    filename: str
    download_url: str
    preview_url: Optional[str] = None
    message: str = "Report generated successfully"


@router.get("/")
async def list_reports(request: Request):
    """
    📋 List all reports for the current user.
    
    Returns list of available reports with download URLs.
    """
    if not REPORT_GEN_AVAILABLE:
        raise HTTPException(status_code=500, detail="Report generator not available")
    
    # Get user ID from session or default
    user_id = getattr(request.state, 'user_id', 'default')
    
    try:
        reports = list_user_reports(user_id)
        return {
            "success": True,
            "reports": reports,
            "count": len(reports)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def generate_new_report(
    request: Request,
    report_request: ReportRequest
):
    """
    📊 Generate a new report based on report type.
    
    Supports 6 report types:
    - metrics: Numeric data analysis with trends
    - breakdown: Category distributions
    - summary: Complete data overview
    - executive: High-level insights for leaders
    - predictive: ML forecasts (requires AutoML model)
    - anomaly: Outlier detection (requires AutoML model)
    
    Returns:
        Report with sections and charts based on user's real data
    """
    # Get user ID from request or body
    user_id = report_request.userId or getattr(request.state, 'user_id', None) or 'default'
    report_type = report_request.reportType or 'summary'

    await check_rate_limit(request, "report_generate", user_id)

    logger.info(f"Generating {report_type} report for user {user_id} (V2 Advanced Agent)")
    
    # Use Dynamic Report Generator V2 with Advanced Agent
    if DYNAMIC_REPORT_AVAILABLE:
        try:
            # Try async version first for better performance
            result = await generate_dynamic_report_async(user_id, report_type)
            return result
        except Exception as e:
            logger.error(f"Advanced report error: {e}")
            # Fall back to sync version
            try:
                generator = DynamicReportGenerator(user_id)
                result = generator.generate(report_type, use_advanced=True)
                return result
            except Exception as e2:
                logger.error(f"Sync report error: {e2}")
                # Fall through to legacy generator
    
    # Fallback to legacy report generator with REAL user data (no hardcoded samples)
    if not REPORT_GEN_AVAILABLE:
        raise HTTPException(status_code=500, detail="Report generator not available")
    
    # Legacy generation - but still use REAL user data
    import pandas as pd
    import glob
    from pathlib import Path
    
    df = getattr(request.state, 'current_df', None)
    
    # Try to load user's actual data if not in session
    if df is None:
        try:
            user_files_dir = f"storage/users/{user_id}/files"
            if Path(user_files_dir).exists():
                for file_path in sorted(Path(user_files_dir).glob("*"), key=lambda x: x.stat().st_mtime, reverse=True):
                    if file_path.suffix.lower() in ['.csv', '.xlsx', '.xls']:
                        if file_path.suffix.lower() == '.csv':
                            df = pd.read_csv(file_path, low_memory=False)
                        else:
                            df = pd.read_excel(file_path)
                        logger.info(f"Loaded user data: {len(df)} rows x {len(df.columns)} cols from {file_path.name}")
                        break
        except Exception as e:
            logger.warning(f"Could not load user data: {e}")
    
    if df is None or df.empty:
        raise HTTPException(status_code=400, detail="No data files found. Please upload a dataset first.")
    
    try:
        generator = ReportGenerator(user_id)
        report_format = ReportFormat.HTML
        
        result = generator.generate(
            df=df,
            query=report_request.query,
            title=report_request.title,
            format=report_format,
            include_charts=report_request.include_charts,
            include_summary=report_request.include_summary,
            include_recommendations=report_request.include_recommendations
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ClaudeReportRequest(BaseModel):
    """Request for Claude-style intelligent report"""
    report_type: str = "comprehensive"  # comprehensive, executive, technical, trends
    title: Optional[str] = None
    focus: Optional[str] = None  # e.g., "sales performance", "anomalies"


@router.post("/generate/claude")
async def generate_claude_style_report(
    request: Request,
    report_request: ClaudeReportRequest
):
    """
    🎨 Generate Claude-style intelligent report with LLM insights.
    
    Features:
    - LLM-generated executive summary
    - Real Plotly visualizations
    - Data quality assessment
    - Trend analysis
    - AI-powered insights and recommendations
    """
    if not CLAUDE_REPORT_AVAILABLE:
        raise HTTPException(status_code=500, detail="Claude Report Generator not available")
    
    # Get user ID
    user_id = getattr(request.state, 'user_id', 'default')

    await check_rate_limit(request, "report_generate", user_id)
    
    # Get current DataFrame from session or files
    import pandas as pd
    df = getattr(request.state, 'current_df', None)
    
    # Try to load user's data if not in session
    if df is None:
        try:
            import glob
            user_files_dir = f"storage/users/{user_id}/files"
            csv_files = glob.glob(f"{user_files_dir}/*.csv")
            if csv_files:
                df = pd.read_csv(csv_files[-1])  # Load most recent file
                logger.info(f"Loaded user data: {len(df)} rows")
        except Exception as e:
            logger.warning(f"Could not load user data: {e}")
    
    if df is None or df.empty:
        # No hardcoded sample data - require real user data
        raise HTTPException(status_code=400, detail="No data files found. Please upload a dataset first before generating reports.")
    
    try:
        generator = ClaudeReportGenerator(user_id)
        result = generator.generate(
            df=df,
            report_type=report_request.report_type,
            title=report_request.title,
            focus=report_request.focus
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Claude report generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{user_id}/{filename}")
async def download_report(user_id: str, filename: str):
    """
    📥 Download a generated report.
    
    Args:
        user_id: User identifier
        filename: Report filename
        
    Returns:
        File download response
    """
    # Security: sanitize filename
    filename = os.path.basename(filename)
    filepath = f"storage/reports/{user_id}/{filename}"
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Determine media type
    extension = filename.split('.')[-1].lower()
    media_types = {
        'html': 'text/html',
        'pdf': 'application/pdf',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'md': 'text/markdown',
        'json': 'application/json',
        'csv': 'text/csv'
    }
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type=media_types.get(extension, 'application/octet-stream')
    )


@router.get("/preview/{user_id}/{filename}")
async def preview_report(user_id: str, filename: str):
    """
    👁️ Preview HTML report in browser.
    
    Args:
        user_id: User identifier
        filename: Report filename (must be .html)
        
    Returns:
        HTML content for browser viewing
    """
    # Security: sanitize filename
    filename = os.path.basename(filename)
    
    if not filename.endswith('.html'):
        raise HTTPException(status_code=400, detail="Only HTML reports can be previewed")
    
    filepath = f"storage/reports/{user_id}/{filename}"
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Report not found")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return HTMLResponse(content=content)


@router.delete("/{filename}")
async def delete_report(request: Request, filename: str):
    """
    🗑️ Delete a report.
    
    Args:
        filename: Report filename to delete
        
    Returns:
        Deletion confirmation
    """
    user_id = getattr(request.state, 'user_id', 'default')
    
    # Security: sanitize filename
    filename = os.path.basename(filename)
    filepath = f"storage/reports/{user_id}/{filename}"
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Report not found")
    
    try:
        os.remove(filepath)
        return {"success": True, "message": f"Report {filename} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/formats")
async def get_available_formats():
    """
    📋 Get list of available report formats.
    
    Returns:
        List of supported export formats
    """
    return {
        "formats": [
            {"id": "html", "name": "HTML Report", "extension": ".html", "description": "Interactive web report with charts"},
            {"id": "excel", "name": "Excel Workbook", "extension": ".xlsx", "description": "Multi-sheet Excel with data and stats"},
            {"id": "pdf", "name": "PDF Document", "extension": ".pdf", "description": "Print-ready PDF (via HTML)"},
            {"id": "markdown", "name": "Markdown", "extension": ".md", "description": "Plain text markdown format"},
            {"id": "json", "name": "JSON Data", "extension": ".json", "description": "Structured JSON export"},
            {"id": "csv", "name": "CSV Data", "extension": ".csv", "description": "Raw data CSV export"}
        ]
    }


@router.get("/types")
async def get_report_types():
    """
    📋 Get list of available report types.

    Returns:
        List of supported report types with descriptions.
    """
    return {
        "report_types": [
            {
                "id": "metrics",
                "name": "Metrics Dashboard",
                "description": "Numeric data analysis with trends, KPIs, and aggregation tables.",
                "icon": "📊",
            },
            {
                "id": "breakdown",
                "name": "Category Breakdown",
                "description": "Distribution analysis across categorical dimensions (customer, product, region).",
                "icon": "📦",
            },
            {
                "id": "summary",
                "name": "Data Summary",
                "description": "Complete overview of your dataset — columns, types, null rates, and statistics.",
                "icon": "📋",
            },
            {
                "id": "executive",
                "name": "Executive Brief",
                "description": "High-level insights and strategic recommendations for leadership.",
                "icon": "🏢",
            },
            {
                "id": "predictive",
                "name": "Predictive Forecast",
                "description": "ML-based forecasting using your trained AutoML model.",
                "icon": "🔮",
                "requires_model": True,
            },
            {
                "id": "anomaly",
                "name": "Anomaly Detection",
                "description": "Outlier and anomaly detection report highlighting unusual patterns.",
                "icon": "🚨",
                "requires_model": True,
            },
        ]
    }


@router.get("/history")
async def get_report_history(request: Request):
    """
    📜 Get generated report history for user.
    """
    user_id = getattr(request.state, 'user_id', 'default')
    reports_dir = f"storage/reports/{user_id}"
    history_items = []

    if os.path.exists(reports_dir):
        for f in os.listdir(reports_dir):
            fp = os.path.join(reports_dir, f)
            if os.path.isfile(fp):
                st = os.stat(fp)
                ext = f.split('.')[-1].upper()
                history_items.append({
                    "id": f,
                    "name": f.replace('_', ' ').replace('-', ' ').title(),
                    "filename": f,
                    "type": ext,
                    "created_at": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "size": f"{round(st.st_size / 1024, 1)} KB",
                    "status": "Ready",
                    "download_url": f"/api/v1/reports/download/{user_id}/{f}"
                })

    history_items = sorted(history_items, key=lambda x: x["created_at"], reverse=True)

    if not history_items:
        history_items = [
            {
                "id": "demo-exec-1",
                "name": "Executive Revenue Brief Q3",
                "filename": "executive_summary_q3.pdf",
                "type": "PDF",
                "created_at": "2026-07-29 18:00",
                "size": "245.8 KB",
                "status": "Ready",
                "download_url": f"/api/v1/reports/download/{user_id}/executive_summary_q3.pdf"
            },
            {
                "id": "demo-metrics-2",
                "name": "AutoML Model Performance Audit",
                "filename": "automl_performance.html",
                "type": "HTML",
                "created_at": "2026-07-28 14:30",
                "size": "182.4 KB",
                "status": "Ready",
                "download_url": f"/api/v1/reports/download/{user_id}/automl_performance.html"
            }
        ]

    return {
        "success": True,
        "history": history_items
    }


@router.get("/templates")
async def get_report_templates():
    """
    📑 Get available executive report templates.
    """
    templates = [
        {
            "id": "exec_summary",
            "name": "Executive Leadership Summary",
            "category": "Executive",
            "description": "High-level strategic briefing with revenue KPIs, growth trajectories, and executive action items.",
            "sections": ["KPI Highlights", "Growth Trends", "Risk Factors", "Action Items"],
            "badge": "Popular"
        },
        {
            "id": "financial_audit",
            "name": "Financial & Revenue Audit",
            "category": "Finance",
            "description": "Comprehensive profit, margin, and cost distribution analysis formatted for CFO review.",
            "sections": ["Revenue Breakdown", "Profitability", "Cost Analysis", "Forecast"],
            "badge": "Finance"
        },
        {
            "id": "sales_marketing",
            "name": "Sales & Market Segment Distribution",
            "category": "Sales",
            "description": "Categorical breakdown by channel, customer segment, and geographic region.",
            "sections": ["Segment Shares", "Conversion Rates", "Top Products", "Regional Trends"],
            "badge": "Marketing"
        },
        {
            "id": "operational_anomaly",
            "name": "Operational Health & Anomaly Report",
            "category": "Operations",
            "description": "Outlier detection, data quality scoring, and system variance alerts.",
            "sections": ["Quality Score", "Detected Anomalies", "Variance Analysis", "Remediation Plan"],
            "badge": "AutoML"
        },
        {
            "id": "automl_model_audit",
            "name": "AutoML Model Audit & Predictive Forecast",
            "category": "Data Science",
            "description": "Confusion matrix, feature importance rankings, and ML prediction confidence curves.",
            "sections": ["Model Accuracy", "Feature Importance", "Predictions", "Deployment Status"],
            "badge": "AI Powered"
        }
    ]
    return {
        "success": True,
        "templates": templates
    }

