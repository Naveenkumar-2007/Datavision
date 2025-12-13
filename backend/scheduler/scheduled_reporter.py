"""
Scheduled Email Reporter - Sends daily/weekly reports based on user preferences
Uses APScheduler for background job scheduling
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
import json

from services.email_service import send_insight_email, RESEND_API_KEY
from agents.reports import generate_weekly_report, generate_monthly_report
from graph.query import revenue_dataframe, get_user_currency

logger = logging.getLogger(__name__)

# Storage directory for email preferences  
PREFS_DIR = Path(__file__).parent.parent / "storage" / "email_prefs"
USERS_DIR = Path(__file__).parent.parent / "storage" / "users"


def get_all_user_ids():
    """Get all user IDs that have uploaded data"""
    if not USERS_DIR.exists():
        return []
    
    user_ids = []
    for user_dir in USERS_DIR.iterdir():
        if user_dir.is_dir():
            user_ids.append(user_dir.name)
    
    return user_ids


def get_user_email_prefs(user_id: str):
    """Load user email preferences"""
    prefs_path = PREFS_DIR / f"{user_id}_email_prefs.json"
    
    if prefs_path.exists():
        try:
            with open(prefs_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading prefs for {user_id}: {e}")
    
    return None


def get_user_email(user_id: str):
    """Get user's email address from preferences or Supabase"""
    prefs = get_user_email_prefs(user_id)
    
    if prefs and prefs.get('email_address'):
        return prefs['email_address']
    
    # Try to get from user profile
    profile_path = USERS_DIR / user_id / "profile.json"
    if profile_path.exists():
        try:
            with open(profile_path, 'r') as f:
                profile = json.load(f)
                return profile.get('email')
        except:
            pass
    
    return None


async def generate_daily_report_html(user_id: str) -> str:
    """Generate daily summary report HTML"""
    try:
        df = revenue_dataframe(user_id)
        
        if df.empty:
            return None
        
        currency_symbol, currency_code = get_user_currency(user_id)
        
        # Calculate daily metrics
        total_revenue = df['amount'].sum()
        total_orders = len(df)
        unique_customers = df['customer'].nunique() if 'customer' in df.columns else 0
        top_product = df.groupby('product')['amount'].sum().idxmax() if 'product' in df.columns else "N/A"
        avg_order = total_revenue / total_orders if total_orders > 0 else 0
        
        html = f"""
        <h2>📊 Your Daily Business Summary</h2>
        
        <div style="background: #f8fafc; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <h3 style="color: #1e293b; margin-top: 0;">Key Metrics</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">
                        <strong>💰 Total Revenue</strong>
                    </td>
                    <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: right; font-size: 18px; color: #22c55e;">
                        {currency_symbol}{total_revenue:,.2f}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">
                        <strong>📦 Total Orders</strong>
                    </td>
                    <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: right;">
                        {total_orders}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">
                        <strong>👥 Active Customers</strong>
                    </td>
                    <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: right;">
                        {unique_customers}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">
                        <strong>📈 Avg Order Value</strong>
                    </td>
                    <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: right;">
                        {currency_symbol}{avg_order:,.2f}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px;">
                        <strong>⭐ Top Product</strong>
                    </td>
                    <td style="padding: 10px; text-align: right;">
                        {top_product}
                    </td>
                </tr>
            </table>
        </div>
        
        <p style="color: #64748b; font-size: 14px;">
            This is your automated daily summary from AI Business Analyst.
            <a href="https://naveen-2007-ai-business-analyst.hf.space/chat" style="color: #f97316;">Ask AI for more insights →</a>
        </p>
        """
        
        return html
        
    except Exception as e:
        logger.error(f"Error generating daily report for {user_id}: {e}")
        return None


async def send_daily_reports():
    """Send daily reports to all users who have it enabled at the current time"""
    current_hour = datetime.now().hour
    current_minute = datetime.now().minute
    print(f"📧 Checking for daily reports at {current_hour:02d}:{current_minute:02d}")
    
    if not RESEND_API_KEY:
        print("⚠️ RESEND_API_KEY not configured, skipping email send")
        return
    
    user_ids = get_all_user_ids()
    
    for user_id in user_ids:
        try:
            prefs = get_user_email_prefs(user_id)
            
            if not prefs:
                continue
            
            # Check if daily reports enabled and it's the right hour AND minute
            pref_hour = prefs.get('daily_report_hour', 8)
            pref_minute = prefs.get('daily_report_minute', 0)
            
            if (prefs.get('daily_report_enabled') and 
                pref_hour == current_hour and 
                pref_minute == current_minute):
                email = get_user_email(user_id)
                
                if not email:
                    logger.warning(f"No email for user {user_id}, skipping daily report")
                    continue
                
                report_html = await generate_daily_report_html(user_id)
                
                if report_html:
                    await send_insight_email(
                        to_email=email,
                        title=f"Daily Business Summary - {datetime.now().strftime('%B %d, %Y')}",
                        body=report_html,
                        workspace_id=user_id
                    )
                    print(f"✅ Sent daily report to {email} for user {user_id}")
                    
        except Exception as e:
            logger.error(f"Error sending daily report to {user_id}: {e}")


async def send_weekly_reports():
    """Send weekly reports to all users who have it enabled on the correct day/hour/minute"""
    current_day = datetime.now().weekday()  # 0=Monday, 6=Sunday
    # Convert to our format (0=Sunday, 1=Monday, ..., 6=Saturday)
    current_day_our_format = (current_day + 1) % 7
    current_hour = datetime.now().hour
    current_minute = datetime.now().minute
    
    print(f"📧 Checking for weekly reports on day {current_day_our_format} at {current_hour:02d}:{current_minute:02d}")
    
    if not RESEND_API_KEY:
        print("⚠️ RESEND_API_KEY not configured, skipping email send")
        return
    
    user_ids = get_all_user_ids()
    
    for user_id in user_ids:
        try:
            prefs = get_user_email_prefs(user_id)
            
            if not prefs:
                continue
            
            # Check if weekly reports enabled and it's the right day/hour/minute
            pref_day = prefs.get('weekly_report_day', 1)
            pref_hour = prefs.get('weekly_report_hour', 9)
            pref_minute = prefs.get('weekly_report_minute', 0)
            
            if (prefs.get('weekly_report_enabled') and 
                pref_day == current_day_our_format and
                pref_hour == current_hour and
                pref_minute == current_minute):
                
                email = get_user_email(user_id)
                
                if not email:
                    logger.warning(f"No email for user {user_id}, skipping weekly report")
                    continue
                
                # Generate weekly report
                report_html = generate_weekly_report(user_id)
                
                if report_html:
                    await send_insight_email(
                        to_email=email,
                        title=f"Weekly Business Report - Week of {datetime.now().strftime('%B %d, %Y')}",
                        body=report_html,
                        workspace_id=user_id
                    )
                    logger.info(f"Sent weekly report to {email} for user {user_id}")
                    
        except Exception as e:
            logger.error(f"Error sending weekly report to {user_id}: {e}")


# Entry point for scheduler
async def check_and_send_reports():
    """Check and send both daily and weekly reports (called hourly)"""
    logger.info(f"Running scheduled report check at {datetime.now()}")
    
    await send_daily_reports()
    await send_weekly_reports()
    
    logger.info("Completed scheduled report check")


# For testing
if __name__ == "__main__":
    asyncio.run(check_and_send_reports())
