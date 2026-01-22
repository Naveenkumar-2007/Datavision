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
import os
import httpx
from datetime import datetime
from services.email_service import send_insight_email

logger = logging.getLogger(__name__)

router = APIRouter()

# Storage directory for user preferences
# email_prefs.py is at: backend/api/v1/endpoints/email_prefs.py
# We need to get to: backend/storage/email_prefs
# So we need 4 parent levels: endpoints -> v1 -> api -> backend
import os

# Use absolute path that matches scheduler
PREFS_DIR = Path(__file__).parent.parent.parent.parent / "storage" / "email_prefs"

PREFS_DIR.mkdir(parents=True, exist_ok=True)
print(f"📁 Email Prefs PREFS_DIR: {PREFS_DIR.absolute()}")


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
        print(f"💾 SAVING email prefs for user '{user_id}' to: {prefs_path.absolute()}")
        with open(prefs_path, 'w') as f:
            json.dump(prefs.dict(), f, indent=2)
        print(f"✅ SAVED successfully! File exists: {prefs_path.exists()}")
        logger.info(f"Saved email prefs for user {user_id}")
    except Exception as e:
        print(f"❌ FAILED to save: {e}")
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


class TestEmailRequest(BaseModel):
    """Request body for test email"""
    email_address: str


@router.post("/email-prefs/test")
async def test_email_report(
    request: TestEmailRequest = None,
    x_user_id: str = Header(None, alias="X-User-ID")
):
    """Send a test email report to verify configuration"""
    from services.email_service import send_insight_email
    
    user_id = x_user_id or "default_user"
    
    # Get email from request body OR from saved preferences
    email_to_use = None
    if request and request.email_address:
        email_to_use = request.email_address
    else:
        prefs = load_user_prefs(user_id)
        email_to_use = prefs.email_address
    
    if not email_to_use:
        raise HTTPException(400, "No email address provided. Please enter your email address.")
    
    try:
        print(f"📧 Sending test email to: {email_to_use}")
        await send_insight_email(
            to_email=email_to_use,
            title="DataVision - Test Email | Configuration Verified",
            body="This is a test email from DataVision. Your email configuration is working correctly. You will receive automated data insights based on your preferences.",
            workspace_id=user_id
        )
        
        return {
            "success": True,
            "message": f"Test email sent to {email_to_use}"
        }
    except Exception as e:
        print(f"❌ Email send failed: {e}")
        raise HTTPException(500, f"Failed to send test email: {str(e)}")


def generate_fallback_email_body(data_context: str) -> str:
    """Generate a nicely formatted email body when AI is unavailable"""
    from datetime import datetime
    return f"""Hi there! 👋

Here's your DataVision Daily Report for {datetime.now().strftime('%B %d, %Y')}.

📊 YOUR DATA SUMMARY
{data_context}

💡 WHAT THIS MEANS
Your data has been processed and is ready for analysis. Visit your DataVision dashboard to explore interactive charts, run predictions, and gain deeper insights.

🚀 NEXT STEPS
• Check your ML Predictions page to make new predictions
• Explore the Dashboard for visual insights
• Use the AI Chat to ask questions about your data

Best regards,
DataVision AI Analytics

---
This report was automatically generated by DataVision.
"""


@router.post("/email-prefs/send-daily-report")
async def send_daily_report_now(
    request: TestEmailRequest = None,
    x_user_id: str = Header(None, alias="X-User-ID")
):
    """
    🤖 AI-POWERED DAILY REPORT
    Automatically generates personalized email content using:
    - Real uploaded data insights
    - ML training results (if available)
    - Dashboard analytics
    """
    import os
    import httpx
    from services.email_service import send_insight_email
    from datetime import datetime
    
    user_id = x_user_id or "default_user"
    
    # Get email from request body OR from saved preferences
    email_to_use = None
    if request and request.email_address:
        email_to_use = request.email_address
    else:
        prefs = load_user_prefs(user_id)
        email_to_use = prefs.email_address
    
    if not email_to_use:
        raise HTTPException(400, "No email address provided. Please enter your email address.")
    
    try:
        # 1. Gather REAL user data context
        print(f"🔍 Gathering real data context for user: {user_id}")
        data_context = await gather_user_data_context(user_id)
        print(f"📊 Data context:\n{data_context}")
        
        if data_context == "No data uploaded yet.":
            raise HTTPException(400, "No data available. Please upload some data first to generate a report.")
        
        # 2. Use AI to generate personalized email content WITH explanations
        groq_api_key = os.getenv("GROQ_API_KEY")
        
        if groq_api_key:
            print(f"🤖 Using AI to generate personalized report with ML explanations...")
            
            system_prompt = """You are DataVision AI, a business intelligence expert. Generate a professional, insightful email report.

Your email should:
1. Have a clear, engaging SUBJECT LINE (start with "Subject: ")
2. Include a warm greeting
3. Provide DATA HIGHLIGHTS with specific numbers
4. Explain ML MODEL INSIGHTS in simple business terms:
   - What the model predicts
   - How accurate it is (explain what the accuracy means)
   - Which features matter most and WHY they matter for business
5. Include ACTIONABLE RECOMMENDATIONS based on the data
6. End with an encouraging sign-off

FORMAT: Write in clean, readable paragraphs with emoji for visual appeal.
DO NOT return JSON. Write the email directly.

Example format:
Subject: 📊 Your Data Intelligence Report - Key Insights Revealed

Hi there! 👋

Here's your personalized data intelligence report...

📈 DATA HIGHLIGHTS
...

🤖 ML MODEL INSIGHTS  
...

💡 RECOMMENDATIONS
...

Best regards,
DataVision AI Analytics"""

            user_prompt = f"""Generate a comprehensive Daily Intelligence Report email for today ({datetime.now().strftime('%B %d, %Y')}).

USER'S REAL DATA:
{data_context}

Create an insightful, business-friendly email that:
1. Explains what the ML model does in simple terms
2. Interprets the accuracy score for business users
3. Explains WHY the top features are important
4. Gives 2-3 actionable recommendations

Write the complete email directly (not JSON). Start with "Subject: " on the first line."""

            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {groq_api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "llama-3.3-70b-versatile",
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            "temperature": 0.7,
                            "max_tokens": 1500
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        content = result['choices'][0]['message']['content'].strip()
                        
                        # Extract subject line if present
                        if content.lower().startswith("subject:"):
                            lines = content.split("\n", 1)
                            subject = lines[0].replace("Subject:", "").replace("subject:", "").strip()
                            body = lines[1].strip() if len(lines) > 1 else content
                        else:
                            subject = f"📊 DataVision Daily Report - {datetime.now().strftime('%B %d, %Y')}"
                            body = content
                    else:
                        # Fallback to formatted report
                        subject = f"📊 DataVision Daily Report - {datetime.now().strftime('%B %d, %Y')}"
                        body = generate_fallback_email_body(data_context)
            except Exception as ai_error:
                logger.warning(f"AI generation failed, using fallback: {ai_error}")
                subject = f"📊 DataVision Daily Report - {datetime.now().strftime('%B %d, %Y')}"
                body = generate_fallback_email_body(data_context)
        else:
            # No API key - use formatted fallback
            subject = f"📊 DataVision Daily Report - {datetime.now().strftime('%B %d, %Y')}"
            body = generate_fallback_email_body(data_context)
        
        # 3. Send the AI-generated email
        print(f"📧 Sending AI-generated report to: {email_to_use}")
        await send_insight_email(
            to_email=email_to_use,
            title=subject,
            body=body,
            workspace_id=user_id
        )
        
        return {
            "success": True,
            "message": f"🤖 AI-generated Daily Report sent to {email_to_use}",
            "data_context": data_context
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send daily report: {e}")
        raise HTTPException(500, f"Failed to send daily report: {str(e)}")


@router.post("/email-prefs/send-weekly-report")
async def send_weekly_report_now(
    request: TestEmailRequest = None,
    x_user_id: str = Header(None, alias="X-User-ID")
):
    """Send a weekly summary report with AI-generated insights immediately"""
    from datetime import datetime  # Import here to ensure availability
    
    user_id = x_user_id or "default"
    
    # Get email address
    email_to_use = None
    if request and request.email_address:
        email_to_use = request.email_address
    else:
        prefs = load_user_prefs(user_id)
        email_to_use = prefs.email_address
    
    if not email_to_use:
        raise HTTPException(400, "No email address provided.")
    
    try:
        # Gather data context
        data_context = await gather_user_data_context(user_id)
        
        if data_context == "No data uploaded yet.":
            raise HTTPException(400, "No data available. Please upload some data first.")
        
        # Use AI for weekly insights
        groq_api_key = os.getenv("GROQ_API_KEY")
        
        if groq_api_key:
            system_prompt = """You are DataVision AI, a business intelligence expert. Generate a WEEKLY summary report.

Your email should include:
1. SUBJECT LINE starting with "Subject: 📈 Weekly"
2. Week-over-week analysis and trends
3. Key achievements and metrics
4. ML model performance summary  
5. Strategic recommendations for the coming week
6. Areas requiring attention

Write in professional, actionable paragraphs with emoji."""

            user_prompt = f"""Generate a Weekly Intelligence Report for the week ending {datetime.now().strftime('%B %d, %Y')}.

USER'S DATA SUMMARY:
{data_context}

Create an executive-level weekly summary with trends, insights, and recommendations."""

            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {groq_api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "llama-3.3-70b-versatile",
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            "temperature": 0.7,
                            "max_tokens": 2000
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        content = result['choices'][0]['message']['content'].strip()
                        
                        if content.lower().startswith("subject:"):
                            lines = content.split("\n", 1)
                            subject = lines[0].replace("Subject:", "").replace("subject:", "").strip()
                            body = lines[1].strip() if len(lines) > 1 else content
                        else:
                            subject = f"📈 DataVision Weekly Report - Week of {datetime.now().strftime('%B %d, %Y')}"
                            body = content
                    else:
                        subject = f"📈 DataVision Weekly Report - {datetime.now().strftime('%B %d, %Y')}"
                        body = generate_weekly_fallback(data_context)
            except Exception as e:
                logger.warning(f"AI weekly generation failed: {e}")
                subject = f"📈 DataVision Weekly Report - {datetime.now().strftime('%B %d, %Y')}"
                body = generate_weekly_fallback(data_context)
        else:
            subject = f"📈 DataVision Weekly Report - {datetime.now().strftime('%B %d, %Y')}"
            body = generate_weekly_fallback(data_context)
        
        # Send the email
        await send_insight_email(
            to_email=email_to_use,
            title=subject,
            body=body,
            workspace_id=user_id
        )
        
        return {
            "success": True,
            "message": f"🤖 AI-generated Weekly Report sent to {email_to_use}",
            "data_context": data_context
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send weekly report: {e}")
        raise HTTPException(500, f"Failed to send weekly report: {str(e)}")


def generate_weekly_fallback(data_context: str) -> str:
    """Fallback weekly email body"""
    from datetime import datetime
    return f"""Hi there! 👋

Here's your DataVision Weekly Summary for the week ending {datetime.now().strftime('%B %d, %Y')}.

📊 THIS WEEK'S DATA OVERVIEW
{data_context}

📈 WEEKLY HIGHLIGHTS
Your data has been continuously monitored throughout the week. All systems are running smoothly.

💡 RECOMMENDATIONS FOR NEXT WEEK
• Review your ML model predictions for any emerging patterns
• Check the Dashboard for updated visualizations
• Use the AI Chat to dive deeper into specific metrics

🎯 COMING UP
Continue monitoring your key metrics and consider setting up custom alerts for important thresholds.

Best regards,
DataVision AI Analytics

---
This weekly report was automatically generated by DataVision.
"""


# ============================================================================
# AI EMAIL WRITING AGENT - Generates personalized emails with real data
# ============================================================================

class GenerateEmailRequest(BaseModel):
    """Request body for AI email generation"""
    prompt: str  # What the email should be about
    email_address: str  # Where to send
    send_immediately: bool = False  # If true, send after generation


class GeneratedEmail(BaseModel):
    """Generated email response"""
    subject: str
    body: str
    data_summary: Optional[str] = None


async def gather_user_data_context(user_id: str) -> str:
    """
    Gather REAL user data for context in email generation.
    Reads actual uploaded CSV files, calculates real statistics,
    and fetches ML training results.
    """
    context_parts = []
    
    try:
        # Use the correct get_user_paths utility (same as rest of app)
        from utils.paths import get_user_paths
        import pandas as pd
        paths = get_user_paths(user_id)
        
        # 1. Get uploaded files and read REAL data
        files_dir = paths.get('files')
        if files_dir and files_dir.exists():
            files = [f for f in files_dir.glob("*") if f.is_file()]
            if files:
                file_names = [f.name for f in files[:5]]
                context_parts.append(f"📁 UPLOADED FILES ({len(files)} total): {', '.join(file_names)}")
                
                # Read CSV/Excel files for real data summary
                data_files = [f for f in files if f.suffix.lower() in ['.csv', '.xlsx', '.xls']]
                
                total_rows = 0
                total_columns = 0
                all_column_stats = []
                
                for data_file in data_files[:3]:  # Process up to 3 files
                    try:
                        if data_file.suffix.lower() == '.csv':
                            df = pd.read_csv(data_file)
                        else:
                            df = pd.read_excel(data_file)
                        
                        total_rows += len(df)
                        total_columns = max(total_columns, len(df.columns))
                        
                        context_parts.append(f"\n📊 FILE: {data_file.name}")
                        context_parts.append(f"   • Rows: {len(df):,} | Columns: {len(df.columns)}")
                        context_parts.append(f"   • Columns: {', '.join(df.columns.tolist()[:8])}{'...' if len(df.columns) > 8 else ''}")
                        
                        # Numeric column statistics
                        numeric_cols = df.select_dtypes(include=['int64', 'float64', 'int32', 'float32']).columns.tolist()
                        if numeric_cols:
                            context_parts.append(f"   📈 NUMERIC SUMMARY:")
                            for col in numeric_cols[:5]:  # Top 5 numeric columns
                                col_mean = df[col].mean()
                                col_sum = df[col].sum()
                                col_min = df[col].min()
                                col_max = df[col].max()
                                context_parts.append(f"      • {col}: Sum={col_sum:,.2f}, Mean={col_mean:,.2f}, Range=[{col_min:,.2f} to {col_max:,.2f}]")
                                all_column_stats.append({
                                    'column': col,
                                    'sum': col_sum,
                                    'mean': col_mean,
                                    'min': col_min,
                                    'max': col_max
                                })
                        
                        # Categorical column breakdown
                        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
                        if cat_cols:
                            context_parts.append(f"   📋 CATEGORY BREAKDOWN:")
                            for col in cat_cols[:3]:  # Top 3 categories
                                value_counts = df[col].value_counts().head(5)
                                top_values = ', '.join([f"{v}: {c}" for v, c in value_counts.items()])
                                context_parts.append(f"      • {col}: {top_values}")
                    
                    except Exception as e:
                        logger.warning(f"Error reading {data_file.name}: {e}")
                
                if total_rows > 0:
                    context_parts.insert(1, f"📈 TOTAL DATA: {total_rows:,} rows across {len(data_files)} file(s)")
        
        # 2. Get ML training results from automl storage
        from config.settings import Settings
        automl_results_dir = Settings.BASE_DIR / "storage" / "automl_results" / user_id
        
        ml_found = False
        if automl_results_dir.exists():
            result_files = list(automl_results_dir.glob("*.json"))
            if result_files:
                # Sort by modification time to get latest
                result_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                try:
                    with open(result_files[0], 'r') as f:
                        ml_data = json.load(f)
                        
                    if ml_data:
                        ml_found = True
                        best_model = ml_data.get('best_model', {})
                        task_type = ml_data.get('task_type', 'classification')
                        target = ml_data.get('target_column', 'unknown')
                        metrics = best_model.get('metrics', {})
                        
                        context_parts.append(f"\n🤖 ML MODEL TRAINED:")
                        context_parts.append(f"   • Model: {best_model.get('name', 'AutoML Model')}")
                        context_parts.append(f"   • Task Type: {task_type.upper()}")
                        context_parts.append(f"   • Target Column: {target}")
                        
                        # Report metrics based on task type
                        if task_type == 'classification':
                            acc = metrics.get('accuracy', 0)
                            f1 = metrics.get('f1_score', metrics.get('f1', 0))
                            precision = metrics.get('precision', 0)
                            recall = metrics.get('recall', 0)
                            context_parts.append(f"   📊 PERFORMANCE METRICS:")
                            context_parts.append(f"      • Accuracy: {acc:.1%}")
                            if f1: context_parts.append(f"      • F1 Score: {f1:.1%}")
                            if precision: context_parts.append(f"      • Precision: {precision:.1%}")
                            if recall: context_parts.append(f"      • Recall: {recall:.1%}")
                        else:  # regression
                            r2 = metrics.get('r2', metrics.get('r2_score', 0))
                            rmse = metrics.get('rmse', 0)
                            mae = metrics.get('mae', 0)
                            context_parts.append(f"   📊 PERFORMANCE METRICS:")
                            context_parts.append(f"      • R² Score: {r2:.3f}")
                            if rmse: context_parts.append(f"      • RMSE: {rmse:,.2f}")
                            if mae: context_parts.append(f"      • MAE: {mae:,.2f}")
                        
                        # Feature importance
                        features = ml_data.get('feature_importance', [])[:5]
                        if features:
                            context_parts.append(f"   🔑 TOP FEATURES (most predictive):")
                            for idx, feat in enumerate(features, 1):
                                if isinstance(feat, dict):
                                    fname = feat.get('feature', feat.get('name', str(feat)))
                                    importance = feat.get('importance', 0)
                                    context_parts.append(f"      {idx}. {fname} (importance: {importance:.3f})")
                                else:
                                    context_parts.append(f"      {idx}. {feat}")
                except Exception as e:
                    logger.warning(f"Error reading ML results: {e}")
        
        # 3. Check for unified analytics cache
        analytics_cache_dir = Settings.BASE_DIR / "storage" / "analytics_cache"
        if analytics_cache_dir.exists():
            cache_files = list(analytics_cache_dir.glob(f"{user_id}*.json"))
            if cache_files:
                try:
                    with open(cache_files[-1], 'r') as f:
                        analytics = json.load(f)
                    
                    kpis = analytics.get('overviewLayout', {}).get('kpis', [])
                    if kpis:
                        context_parts.append(f"\n📈 KEY PERFORMANCE INDICATORS:")
                        for kpi in kpis[:4]:
                            title = kpi.get('title', 'Metric')
                            value = kpi.get('value', 0)
                            delta = kpi.get('delta')
                            delta_str = f" ({'+' if delta > 0 else ''}{delta:.1f}%)" if delta else ""
                            context_parts.append(f"   • {title}: {value:,}{delta_str}")
                except Exception as e:
                    logger.warning(f"Error reading analytics cache: {e}")
        
        if not ml_found:
            context_parts.append(f"\n💡 TIP: No ML model trained yet. Consider training a model for predictions!")
        
    except Exception as e:
        logger.error(f"Error gathering user data context: {e}")
        import traceback
        traceback.print_exc()
        context_parts.append("(Limited data available due to error)")
    
    return "\n".join(context_parts) if context_parts else "No data uploaded yet."


@router.post("/email-prefs/generate-email")
async def generate_ai_email(
    request: GenerateEmailRequest,
    x_user_id: str = Header(None, alias="X-User-ID")
):
    """
    🤖 AI EMAIL WRITING AGENT
    
    Generates personalized emails using LLM based on:
    - User's uploaded data
    - ML training results
    - Dashboard insights
    - Custom prompt
    """
    import os
    import httpx
    from services.email_service import send_insight_email
    
    user_id = x_user_id or "default_user"
    
    if not request.email_address:
        raise HTTPException(400, "Email address is required")
    
    if not request.prompt or len(request.prompt.strip()) < 5:
        raise HTTPException(400, "Please provide a description of what the email should contain")
    
    try:
        # 1. Gather real user data context
        print(f"🔍 Gathering data context for user: {user_id}")
        data_context = await gather_user_data_context(user_id)
        print(f"📊 Data context:\n{data_context}")
        
        # 2. Build LLM prompt
        system_prompt = """You are DataVision AI, a professional business email writer. 
Generate professional, data-driven emails based on user data and requirements.
Your emails should:
- Be clear, concise, and professional
- Include specific data insights when available
- Use a friendly but business-appropriate tone
- Format with proper paragraphs and bullet points where appropriate
- Always sign off as "DataVision AI Analytics"

Output format: Return ONLY valid JSON with exactly these fields:
{"subject": "Email subject line", "body": "Full email body text"}"""

        user_prompt = f"""Generate a professional email based on this request:

USER REQUEST: {request.prompt}

AVAILABLE DATA CONTEXT:
{data_context}

Generate a personalized email that incorporates the available data insights.
If specific data is mentioned in the context, reference it naturally in the email.
Remember to return ONLY valid JSON with "subject" and "body" fields."""

        # 3. Call Groq LLM
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise HTTPException(500, "LLM service not configured. Add GROQ_API_KEY to enable AI email generation.")
        
        print(f"🤖 Calling Groq LLM for email generation...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {groq_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1024
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Groq API error: {response.text}")
                raise HTTPException(500, f"LLM service error: {response.status_code}")
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Parse the JSON response
            try:
                # Clean up the response (remove markdown code blocks if present)
                content = content.strip()
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                content = content.strip()
                
                email_data = json.loads(content)
                subject = email_data.get('subject', 'DataVision Insights')
                body = email_data.get('body', content)
            except json.JSONDecodeError:
                # Fallback: use raw content
                subject = f"DataVision: {request.prompt[:50]}..."
                body = content
        
        print(f"✅ Email generated successfully!")
        
        # 4. Send immediately if requested
        if request.send_immediately:
            print(f"📧 Sending email to: {request.email_address}")
            await send_insight_email(
                to_email=request.email_address,
                title=subject,
                body=body,
                workspace_id=user_id
            )
            
            return {
                "success": True,
                "sent": True,
                "message": f"AI-generated email sent to {request.email_address}",
                "email": {
                    "subject": subject,
                    "body": body
                },
                "data_context_used": data_context
            }
        
        # Return generated email without sending
        return {
            "success": True,
            "sent": False,
            "message": "Email generated successfully. Review and click send when ready.",
            "email": {
                "subject": subject,
                "body": body
            },
            "data_context_used": data_context
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI email generation failed: {e}")
        raise HTTPException(500, f"Failed to generate email: {str(e)}")


@router.post("/email-prefs/send-custom-email")
async def send_custom_email(
    request: dict,
    x_user_id: str = Header(None, alias="X-User-ID")
):
    """Send a custom email (after user reviews AI-generated content)"""
    from services.email_service import send_insight_email
    
    user_id = x_user_id or "default_user"
    
    email_address = request.get('email_address')
    subject = request.get('subject')
    body = request.get('body')
    
    if not email_address or not subject or not body:
        raise HTTPException(400, "Missing email_address, subject, or body")
    
    try:
        await send_insight_email(
            to_email=email_address,
            title=subject,
            body=body,
            workspace_id=user_id
        )
        
        return {
            "success": True,
            "message": f"Email sent successfully to {email_address}"
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to send email: {str(e)}")

