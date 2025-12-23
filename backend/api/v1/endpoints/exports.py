# Exports API - Delivery Intelligence Endpoints
"""
API endpoints for generating executive-ready exports.
Supports PDF, PPTX, and Email HTML formats.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import base64

from core.export_engine import (
    ExportEngine,
    ExportContent,
    get_export_engine,
)

router = APIRouter(prefix="/exports", tags=["exports"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ExportRequest(BaseModel):
    """Request to generate an export"""
    title: str = Field(..., description="Title for the export")
    content: str = Field(..., description="Main content/answer to export")
    format: str = Field(default="pdf", description="Export format: pdf, pptx, email")
    workspace_id: Optional[str] = None
    tables: Optional[List[Dict]] = None
    charts: Optional[List[Dict]] = None


class ExportResponse(BaseModel):
    """Response with export data"""
    format: str
    filename: str
    content_base64: str  # Base64 encoded content
    content_type: str


class AvailableFormatsResponse(BaseModel):
    """Available export formats"""
    formats: List[str]


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/formats", response_model=AvailableFormatsResponse)
async def get_available_formats():
    """Get list of available export formats"""
    engine = get_export_engine()
    return AvailableFormatsResponse(formats=engine.get_available_formats())


@router.post("/generate", response_model=ExportResponse)
async def generate_export(request: ExportRequest):
    """
    Generate an export from content.
    Returns base64-encoded file content.
    """
    try:
        # Get engine with company branding
        engine = get_export_engine(request.workspace_id)
        
        # Build content
        content = ExportContent(
            title=request.title,
            answer=request.content,
            tables=request.tables or [],
            charts=request.charts or [],
        )
        
        # Generate based on format
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if request.format == "pdf":
            data = engine.export_pdf(content)
            filename = f"report_{timestamp}.pdf"
            content_type = "application/pdf"
            
        elif request.format == "pptx":
            data = engine.export_pptx(content)
            filename = f"presentation_{timestamp}.pptx"
            content_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            
        elif request.format == "email":
            data = engine.export_email(content)
            if isinstance(data, str):
                data = data.encode('utf-8')
            filename = f"email_report_{timestamp}.html"
            content_type = "text/html"
            
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format: {request.format}. Available: {engine.get_available_formats()}"
            )
        
        # Encode to base64
        content_base64 = base64.b64encode(data).decode('utf-8')
        
        return ExportResponse(
            format=request.format,
            filename=filename,
            content_base64=content_base64,
            content_type=content_type,
        )
        
    except RuntimeError as e:
        # Library not installed
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/download/{format}")
async def download_export(format: str, request: ExportRequest):
    """
    Generate and download export directly as file.
    """
    try:
        engine = get_export_engine(request.workspace_id)
        
        content = ExportContent(
            title=request.title,
            answer=request.content,
            tables=request.tables or [],
            charts=request.charts or [],
        )
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "pdf":
            data = engine.export_pdf(content)
            filename = f"report_{timestamp}.pdf"
            media_type = "application/pdf"
            
        elif format == "pptx":
            data = engine.export_pptx(content)
            filename = f"presentation_{timestamp}.pptx"
            media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            
        elif format == "email":
            html = engine.export_email(content)
            data = html.encode('utf-8')
            filename = f"email_report_{timestamp}.html"
            media_type = "text/html"
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
        
        return Response(
            content=data,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except RuntimeError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
