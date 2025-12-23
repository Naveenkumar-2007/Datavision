# Onboarding API - Company Profile Setup
"""
API endpoints for company profile onboarding.
Enables users to configure their company context for intelligent responses.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime

from core.company_profile import (
    CompanyProfile,
    get_company_profile,
    save_company_profile,
    delete_company_profile,
    get_company_benchmarks,
    INDUSTRY_BENCHMARKS,
    Industry,
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CompanyProfileRequest(BaseModel):
    """Request model for creating/updating company profile"""
    company_name: str = Field(..., min_length=1, max_length=200)
    industry: str = Field(default="other", description="Industry type for benchmarking")
    fiscal_year_end_month: int = Field(default=12, ge=1, le=12)
    currency: str = Field(default="USD", max_length=3)
    currency_symbol: str = Field(default="$", max_length=5)
    timezone: str = Field(default="UTC")
    
    # Optional customizations
    kpi_definitions: Optional[Dict[str, str]] = None
    terminology: Optional[Dict[str, str]] = None
    benchmarks: Optional[Dict[str, float]] = None
    branding: Optional[Dict[str, str]] = None


class CompanyProfileResponse(BaseModel):
    """Response model for company profile"""
    workspace_id: str
    company_name: str
    industry: str
    fiscal_year_end_month: int
    currency: str
    currency_symbol: str
    timezone: str
    kpi_definitions: Dict[str, str]
    terminology: Dict[str, str]
    benchmarks: Dict[str, float]
    branding: Dict[str, str]
    created_at: str
    updated_at: str
    
    # Computed fields
    industry_benchmarks: Dict[str, float]


class IndustryOption(BaseModel):
    """Industry option for dropdown"""
    value: str
    label: str
    benchmarks: Dict[str, float]


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/industries", response_model=List[IndustryOption])
async def get_industries():
    """Get list of available industries with their benchmarks"""
    industries = []
    for industry in Industry:
        benchmarks = INDUSTRY_BENCHMARKS.get(industry, {})
        industries.append(IndustryOption(
            value=industry.value,
            label=industry.value.replace("_", " ").title(),
            benchmarks={k: float(v) for k, v in benchmarks.items()}
        ))
    return industries


@router.get("/company-profile/{workspace_id}", response_model=CompanyProfileResponse)
async def get_profile(workspace_id: str):
    """Get company profile for a workspace"""
    profile = get_company_profile(workspace_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Company profile not found")
    
    return CompanyProfileResponse(
        workspace_id=profile.workspace_id,
        company_name=profile.company_name,
        industry=profile.industry,
        fiscal_year_end_month=profile.fiscal_year_end_month,
        currency=profile.currency,
        currency_symbol=profile.currency_symbol,
        timezone=profile.timezone,
        kpi_definitions=profile.kpi_definitions,
        terminology=profile.terminology,
        benchmarks=profile.benchmarks,
        branding=profile.branding,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        industry_benchmarks=profile.get_industry_benchmarks(),
    )


@router.post("/company-profile/{workspace_id}", response_model=CompanyProfileResponse)
async def create_profile(workspace_id: str, request: CompanyProfileRequest):
    """Create or update company profile for a workspace"""
    
    # Build profile from request
    profile = CompanyProfile(
        workspace_id=workspace_id,
        company_name=request.company_name,
        industry=request.industry.lower(),
        fiscal_year_end_month=request.fiscal_year_end_month,
        currency=request.currency.upper(),
        currency_symbol=request.currency_symbol,
        timezone=request.timezone,
    )
    
    # Apply optional customizations
    if request.kpi_definitions:
        profile.kpi_definitions.update(request.kpi_definitions)
    if request.terminology:
        profile.terminology.update(request.terminology)
    if request.benchmarks:
        profile.benchmarks.update(request.benchmarks)
    if request.branding:
        profile.branding.update(request.branding)
    
    # Save to Supabase
    success = save_company_profile(profile)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save company profile")
    
    # Return the saved profile
    return CompanyProfileResponse(
        workspace_id=profile.workspace_id,
        company_name=profile.company_name,
        industry=profile.industry,
        fiscal_year_end_month=profile.fiscal_year_end_month,
        currency=profile.currency,
        currency_symbol=profile.currency_symbol,
        timezone=profile.timezone,
        kpi_definitions=profile.kpi_definitions,
        terminology=profile.terminology,
        benchmarks=profile.benchmarks,
        branding=profile.branding,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        industry_benchmarks=profile.get_industry_benchmarks(),
    )


@router.put("/company-profile/{workspace_id}", response_model=CompanyProfileResponse)
async def update_profile(workspace_id: str, request: CompanyProfileRequest):
    """Update existing company profile"""
    # Same as create - upsert behavior
    return await create_profile(workspace_id, request)


@router.delete("/company-profile/{workspace_id}")
async def remove_profile(workspace_id: str):
    """Delete company profile"""
    success = delete_company_profile(workspace_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete company profile")
    
    return {"message": "Company profile deleted successfully"}


@router.get("/company-profile/{workspace_id}/benchmarks")
async def get_workspace_benchmarks(workspace_id: str):
    """Get benchmarks for a workspace (industry defaults + custom overrides)"""
    benchmarks = get_company_benchmarks(workspace_id)
    return {
        "workspace_id": workspace_id,
        "benchmarks": benchmarks,
    }
