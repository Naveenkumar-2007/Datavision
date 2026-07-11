from fastapi import APIRouter, Depends, Query, Header
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from .anomalies import scan_real_anomalies

router = APIRouter()

class SearchResult(BaseModel):
    id: str
    title: str
    type: str  # e.g., 'anomaly', 'dataset', 'report', 'page'
    description: str
    link: str

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]

@router.get("/search", response_model=SearchResponse)
async def global_search(
    q: str = Query(..., min_length=1),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Global smart search endpoint that searches across datasets, anomalies, and reports.
    """
    query = q.lower()
    results = []
    user_id = x_user_id or "default"

    # 1. Search Anomalies
    anomalies = scan_real_anomalies(user_id)
    for anom in anomalies:
        if query in anom.metric.lower() or query in anom.description.lower() or query in anom.dataset.lower():
            results.append(SearchResult(
                id=anom.id,
                title=f"Anomaly: {anom.metric}",
                type="anomaly",
                description=anom.description,
                link="/anomalies"
            ))

    # 2. Search Datasets (Mocked for now)
    datasets = [
        {"id": "ds-1", "name": "Sales_Data_Q2.csv", "desc": "Q2 Regional sales data including revenue and units."},
        {"id": "ds-2", "name": "Logistics_2026.xlsx", "desc": "Logistics and operational costs for 2026."},
        {"id": "ds-3", "name": "User_Acquisition.csv", "desc": "Daily active users and acquisition channels."},
        {"id": "ds-4", "name": "Infra_Logs.csv", "desc": "Server performance and infrastructure logs."}
    ]
    for ds in datasets:
        if query in ds["name"].lower() or query in ds["desc"].lower():
            results.append(SearchResult(
                id=ds["id"],
                title=f"Dataset: {ds['name']}",
                type="dataset",
                description=ds["desc"],
                link="/data-hub"
            ))

    # 3. Search Reports (Mocked)
    reports = [
        {"id": "rep-1", "name": "Q1 Performance Review", "desc": "Comprehensive analysis of Q1 metrics."},
        {"id": "rep-2", "name": "Marketing ROI 2026", "desc": "Return on investment for marketing campaigns."}
    ]
    for rep in reports:
        if query in rep["name"].lower() or query in rep["desc"].lower():
            results.append(SearchResult(
                id=rep["id"],
                title=f"Report: {rep['name']}",
                type="report",
                description=rep["desc"],
                link="/reports"
            ))

    # Sort results by relevance (simple sort for now, datasets first)
    results.sort(key=lambda x: {"dataset": 0, "anomaly": 1, "report": 2}.get(x.type, 3))
    
    return SearchResponse(query=q, results=results)
