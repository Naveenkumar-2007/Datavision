"""
Email Preferences API - User email report scheduling settings
Stores and retrieves user preferences for daily/weekly email reports
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Storage directory for user preferences
PREFS_DIR = Path(__file__).parent.parent.parent / "storage" / "email_prefs"
PREFS_DIR.mkdir(parents=True, exist_ok=True)


class EmailPreferences(BaseModel):
    """User email report preferences"""
    daily_report_enabled: bool = False
    daily_report_hour: int = 8  # 8 AM default
    daily_report_minute: int = 0  # 0 minutes default
    weekly_report_enabled: bool = True
    weekly_report_day: int = 1  # Monday (0=Sun, 1=Mon, ..., 6=Sat)
    weekly_report_hour: int = 9  # 9 AM default
    weekly_report_minute: int = 0  # 0 minutes default
    email_address: Optional[str] = None  # Override Supabase email if needed


def get_prefs_path(user_id: str) -> Path:
    """Get path to user's preferences file"""
    return PREFS_DIR / f"{user_id}_email_prefs.json"


def load_user_prefs(user_id: str) -> EmailPreferences:
    """Load user preferences from file"""
    prefs_path = get_prefs_path(user_id)
    
    if prefs_path.exists():
        try:
            with open(prefs_path, 'r') as f:
                data = json.load(f)
                return EmailPreferences(**data)
        except Exception as e:
            logger.error(f"Error loading prefs for {user_id}: {e}")
    
    # Return defaults
    return EmailPreferences()


def save_user_prefs(user_id: str, prefs: EmailPreferences) -> None:
    """Save user preferences to file"""
    prefs_path = get_prefs_path(user_id)
    
    try:
        with open(prefs_path, 'w') as f:
            json.dump(prefs.dict(), f, indent=2)
        logger.info(f"Saved email prefs for user {user_id}")
    except Exception as e:
        logger.error(f"Error saving prefs for {user_id}: {e}")
        raise


@router.get("/email-prefs")
async def get_email_preferences(
    x_user_id: str = Header(None, alias="X-User-ID")
):
    """Get user's email report preferences"""
    user_id = x_user_id or "default_user"
    
    prefs = load_user_prefs(user_id)
    
    return {
        "success": True,
        "preferences": prefs.dict(),
        "day_options": [
            {"value": 0, "label": "Sunday"},
            {"value": 1, "label": "Monday"},
            {"value": 2, "label": "Tuesday"},
            {"value": 3, "label": "Wednesday"},
            {"value": 4, "label": "Thursday"},
            {"value": 5, "label": "Friday"},
            {"value": 6, "label": "Saturday"},
        ],
        "hour_options": [
            {"value": h, "label": f"{h:02d}:00"} for h in range(24)
        ]
    }


@router.put("/email-prefs")
async def update_email_preferences(
    prefs: EmailPreferences,
    x_user_id: str = Header(None, alias="X-User-ID")
):
    """Update user's email report preferences"""
    user_id = x_user_id or "default_user"
    
    # Validate hour (0-23)
    if not (0 <= prefs.daily_report_hour <= 23):
        raise HTTPException(400, "daily_report_hour must be 0-23")
    if not (0 <= prefs.weekly_report_hour <= 23):
        raise HTTPException(400, "weekly_report_hour must be 0-23")
    
    # Validate day (0-6)
    if not (0 <= prefs.weekly_report_day <= 6):
        raise HTTPException(400, "weekly_report_day must be 0-6 (Sun-Sat)")
    
    try:
        save_user_prefs(user_id, prefs)
        
        return {
            "success": True,
            "message": "Email preferences updated successfully",
            "preferences": prefs.dict()
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to save preferences: {str(e)}")


@router.post("/email-prefs/test")
async def test_email_report(
    x_user_id: str = Header(None, alias="X-User-ID")
):
    """Send a test email report to verify configuration"""
    from services.email_service import send_insight_email
    
    user_id = x_user_id or "default_user"
    prefs = load_user_prefs(user_id)
    
    if not prefs.email_address:
        raise HTTPException(400, "No email address configured. Please set your email in preferences.")
    
    try:
        await send_insight_email(
            to_email=prefs.email_address,
            title="Test Report - Your Email Configuration Works!",
            body="This is a test email to verify your AI Business Analyst email reports are configured correctly. You will receive daily and weekly reports based on your settings.",
            workspace_id=user_id
        )
        
        return {
            "success": True,
            "message": f"Test email sent to {prefs.email_address}"
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to send test email: {str(e)}")
