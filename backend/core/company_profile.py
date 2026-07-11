# Company Profile Module - PostgreSQL-backed Company Intelligence
"""
Stores and retrieves company context for ChatGPT-level business awareness.
Enables company-aware, role-aware, and context-aware responses.

Storage: Local JSON files (per-workspace)
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

import os
import logging

logger = logging.getLogger(__name__)


class Industry(Enum):
    """Supported industry types for benchmarking"""
    SAAS = "saas"
    RETAIL = "retail"
    ECOMMERCE = "ecommerce"
    MANUFACTURING = "manufacturing"
    HEALTHCARE = "healthcare"
    FINTECH = "fintech"
    CONSULTING = "consulting"
    EDUCATION = "education"
    OTHER = "other"


# Industry benchmarks for intelligent comparison
INDUSTRY_BENCHMARKS = {
    Industry.SAAS: {
        "growth_target": 0.20,  # 20% YoY growth
        "churn_target": 0.05,  # 5% annual churn
        "gross_margin": 0.75,  # 75% gross margin
        "cac_payback_months": 12,
        "ltv_cac_ratio": 3.0,
    },
    Industry.RETAIL: {
        "growth_target": 0.08,
        "churn_target": 0.15,
        "gross_margin": 0.35,
        "inventory_turnover": 8,
    },
    Industry.ECOMMERCE: {
        "growth_target": 0.15,
        "churn_target": 0.10,
        "gross_margin": 0.40,
        "cart_abandonment_rate": 0.70,
    },
    Industry.MANUFACTURING: {
        "growth_target": 0.05,
        "gross_margin": 0.25,
        "capacity_utilization": 0.80,
    },
    Industry.FINTECH: {
        "growth_target": 0.25,
        "churn_target": 0.08,
        "gross_margin": 0.65,
    },
    Industry.OTHER: {
        "growth_target": 0.10,
        "churn_target": 0.10,
        "gross_margin": 0.50,
    }
}


@dataclass
class CompanyBranding:
    """Company branding for export documents"""
    logo_base64: Optional[str] = None
    primary_color: str = "#3B82F6"
    secondary_color: str = "#1E40AF"
    font_family: str = "Inter"


@dataclass
class CompanyProfile:
    """Complete company profile for intelligent, context-aware responses"""
    
    # Core identification
    workspace_id: str
    company_name: str = "Your Company"
    
    # Industry context
    industry: str = "other"  # Maps to Industry enum
    
    # Fiscal calendar
    fiscal_year_end_month: int = 12  # 1-12 (December default)
    
    # Currency and locale
    currency: str = "USD"
    currency_symbol: str = "$"
    timezone: str = "UTC"
    
    # Custom KPI definitions
    kpi_definitions: Dict[str, str] = field(default_factory=lambda: {
        "revenue": "Total sales revenue",
        "mrr": "Monthly Recurring Revenue",
        "arr": "Annual Recurring Revenue",
        "aov": "Average Order Value",
    })
    
    # Business terminology (for language calibration)
    terminology: Dict[str, str] = field(default_factory=lambda: {
        "customer": "customer",  # Some companies use "client", "member", "subscriber"
        "revenue": "revenue",    # Some use "GMV", "sales", "bookings"
        "product": "product",    # Some use "SKU", "item", "service"
        "order": "order",        # Some use "transaction", "booking", "purchase"
    })
    
    # Custom benchmarks (override industry defaults)
    benchmarks: Dict[str, float] = field(default_factory=dict)
    
    # Branding for exports
    branding: Dict[str, str] = field(default_factory=lambda: {
        "primary_color": "#3B82F6",
        "secondary_color": "#1E40AF",
        "font_family": "Inter",
    })
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def get_fiscal_quarter(self, month: int) -> int:
        """Get fiscal quarter for a given month based on fiscal year end"""
        # Adjust month relative to fiscal year start
        fiscal_start = (self.fiscal_year_end_month % 12) + 1
        adjusted_month = (month - fiscal_start) % 12
        return (adjusted_month // 3) + 1
    
    def get_industry_benchmarks(self) -> Dict[str, float]:
        """Get benchmarks for this company's industry, with custom overrides"""
        try:
            industry_enum = Industry(self.industry.lower())
            base_benchmarks = INDUSTRY_BENCHMARKS.get(industry_enum, INDUSTRY_BENCHMARKS[Industry.OTHER])
        except ValueError:
            base_benchmarks = INDUSTRY_BENCHMARKS[Industry.OTHER]
        
        # Apply custom overrides
        merged = {**base_benchmarks}
        merged.update(self.benchmarks)
        return merged
    
    def get_term(self, key: str) -> str:
        """Get company-specific terminology"""
        return self.terminology.get(key, key)


# ============================================================================
# LOCAL FILE STORAGE (replaces Supabase)
# ============================================================================

_PROFILES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "company_profiles")

def _ensure_profiles_dir():
    """Ensure the profiles storage directory exists."""
    os.makedirs(_PROFILES_DIR, exist_ok=True)

def _profile_path(workspace_id: str) -> str:
    """Get the file path for a workspace's company profile."""
    return os.path.join(_PROFILES_DIR, f"{workspace_id}.json")


def save_company_profile(profile: CompanyProfile) -> bool:
    """
    Save company profile to local JSON file.
    Creates or updates the profile for the workspace.
    """
    _ensure_profiles_dir()
    
    try:
        profile.updated_at = datetime.now().isoformat()
        profile_data = asdict(profile)
        
        path = _profile_path(profile.workspace_id)
        with open(path, 'w') as f:
            json.dump(profile_data, f, indent=2, default=str)
        
        logger.info(f"Saved company profile for {profile.company_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving company profile: {e}")
        return False


def get_company_profile(workspace_id: str) -> Optional[CompanyProfile]:
    """
    Retrieve company profile from local storage.
    Returns default profile if not found.
    """
    _ensure_profiles_dir()
    
    try:
        path = _profile_path(workspace_id)
        if not os.path.exists(path):
            return CompanyProfile(workspace_id=workspace_id)
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        return CompanyProfile(
            workspace_id=data.get("workspace_id", workspace_id),
            company_name=data.get("company_name", "Your Company"),
            industry=data.get("industry", "other"),
            fiscal_year_end_month=data.get("fiscal_year_end_month", 12),
            currency=data.get("currency", "USD"),
            currency_symbol=data.get("currency_symbol", "$"),
            timezone=data.get("timezone", "UTC"),
            kpi_definitions=data.get("kpi_definitions", {}),
            terminology=data.get("terminology", {}),
            benchmarks=data.get("benchmarks", {}),
            branding=data.get("branding", {}),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
        )
        
    except Exception as e:
        logger.warning(f"Error loading company profile: {e}")
        return CompanyProfile(workspace_id=workspace_id)


def delete_company_profile(workspace_id: str) -> bool:
    """Delete company profile from local storage."""
    try:
        path = _profile_path(workspace_id)
        if os.path.exists(path):
            os.remove(path)
        return True
    except Exception as e:
        logger.error(f"Error deleting company profile: {e}")
        return False


# ============================================================================
# CONTEXT BUILDING FOR LLM INJECTION
# ============================================================================

def build_company_context(workspace_id: str) -> str:
    """
    Build formatted company context string for LLM prompt injection.
    This is the core function that makes answers feel company-aware.
    """
    profile = get_company_profile(workspace_id)
    
    if not profile:
        return ""
    
    # Get benchmarks
    benchmarks = profile.get_industry_benchmarks()
    
    # Build fiscal calendar context
    fiscal_start_month = (profile.fiscal_year_end_month % 12) + 1
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    fiscal_q1_start = month_names[fiscal_start_month - 1]
    
    context = f"""
═══════════════════════════════════════════════════════════════
                    COMPANY CONTEXT
═══════════════════════════════════════════════════════════════
COMPANY: {profile.company_name}
INDUSTRY: {profile.industry.upper()}
CURRENCY: {profile.currency_symbol} ({profile.currency})
TIMEZONE: {profile.timezone}

FISCAL CALENDAR:
- Fiscal Year ends: {month_names[profile.fiscal_year_end_month - 1]}
- Q1 starts: {fiscal_q1_start}
- When user asks about "Q1", count from {fiscal_q1_start}

TERMINOLOGY (use these terms):
- Use "{profile.get_term('customer')}" instead of "customer"
- Use "{profile.get_term('revenue')}" instead of "revenue"
- Use "{profile.get_term('product')}" instead of "product"
- Use "{profile.get_term('order')}" instead of "order"

INDUSTRY BENCHMARKS (for comparison):
- Target Growth: {benchmarks.get('growth_target', 0.1)*100:.0f}% YoY
- Target Churn: {benchmarks.get('churn_target', 0.1)*100:.0f}% annual
- Expected Margin: {benchmarks.get('gross_margin', 0.5)*100:.0f}%

When analyzing performance, compare against these benchmarks.
Say "above industry average" or "below target" when relevant.
═══════════════════════════════════════════════════════════════
"""
    
    return context


def get_company_terminology(workspace_id: str) -> Dict[str, str]:
    """Get terminology mapping for a workspace."""
    profile = get_company_profile(workspace_id)
    if profile:
        return profile.terminology
    return {}


def get_company_benchmarks(workspace_id: str) -> Dict[str, float]:
    """Get benchmarks for a workspace."""
    profile = get_company_profile(workspace_id)
    if profile:
        return profile.get_industry_benchmarks()
    return INDUSTRY_BENCHMARKS[Industry.OTHER]


def get_company_branding(workspace_id: str) -> CompanyBranding:
    """Get branding settings for exports."""
    profile = get_company_profile(workspace_id)
    if profile and profile.branding:
        return CompanyBranding(
            primary_color=profile.branding.get("primary_color", "#3B82F6"),
            secondary_color=profile.branding.get("secondary_color", "#1E40AF"),
            font_family=profile.branding.get("font_family", "Inter"),
            logo_base64=profile.branding.get("logo_base64"),
        )
    return CompanyBranding()
