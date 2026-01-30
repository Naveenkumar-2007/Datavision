"""
🏥 DATA HEALTH API
==================

Provides data quality analysis endpoints:
- POST /api/v1/automl/health - Analyze data health
- GET /api/v1/automl/health/quick - Quick health check
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import pandas as pd
import logging

from utils.paths import get_user_paths
from ml.data_quality import DataQualityAnalyzer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/automl", tags=["AutoML - Data Health"])


class HealthRequest(BaseModel):
    file_name: str
    target_column: Optional[str] = None
    user_id: str = "default"


class HealthIssue(BaseModel):
    severity: str
    category: str
    column: Optional[str] = None
    description: str
    recommendation: str


class HealthResponse(BaseModel):
    success: bool
    overall_score: float
    grade: str
    issues: List[HealthIssue]
    recommendations: List[str]
    metrics: Dict[str, Any]
    column_scores: Dict[str, float]


@router.post("/health", response_model=HealthResponse)
async def analyze_data_health(request: HealthRequest):
    """🏥 Analyze data health and return quality score with recommendations."""
    try:
        user_paths = get_user_paths(request.user_id)
        file_path = user_paths['files'] / request.file_name
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {request.file_name}")
        
        if request.file_name.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif request.file_name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        logger.info(f"🏥 Analyzing data health for {request.file_name} ({len(df)} rows)")
        
        analyzer = DataQualityAnalyzer()
        report = analyzer.analyze(df, request.target_column)
        
        issues = [
            HealthIssue(
                severity=issue.severity,
                category=issue.category,
                column=issue.column,
                description=issue.description,
                recommendation=issue.recommendation
            )
            for issue in report.issues
        ]
        
        return HealthResponse(
            success=True,
            overall_score=report.overall_score,
            grade=report.grade,
            issues=issues,
            recommendations=report.recommendations,
            metrics=report.metrics,
            column_scores=report.column_scores
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Data health error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/quick")
async def quick_health_check(
    file_name: str = Query(...),
    user_id: str = Query(default="default")
):
    """⚡ Quick health check - returns just the score and grade."""
    try:
        user_paths = get_user_paths(user_id)
        file_path = user_paths['files'] / file_name
        
        if not file_path.exists():
            return {"score": None, "grade": "?", "error": "File not found"}
        
        if file_name.endswith('.csv'):
            df = pd.read_csv(file_path, nrows=1000)
        elif file_name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path, nrows=1000)
        else:
            return {"score": None, "grade": "?", "error": "Unsupported format"}
        
        analyzer = DataQualityAnalyzer()
        report = analyzer.analyze(df)
        
        return {
            "score": round(report.overall_score, 1),
            "grade": report.grade,
            "issue_count": len(report.issues),
            "critical_issues": len([i for i in report.issues if i.severity == 'critical'])
        }
        
    except Exception as e:
        logger.error(f"Quick health check error: {e}")
        return {"score": None, "grade": "?", "error": str(e)[:50]}
