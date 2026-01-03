"""
Scheduled Email Reporter - Sends daily/weekly reports based on user preferences
Uses APScheduler for background job scheduling
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
import json

from services.email_service import send_insight_email, RESEND_API_KEY, APP_URL
from agents.reports import generate_weekly_report, generate_monthly_report
from graph.query import revenue_dataframe, get_user_currency
from ml.automl_engine import ProductionMLEngine

logger = logging.getLogger(__name__)

# Storage directory for email preferences
# scheduled_reporter.py is at: backend/scheduler/scheduled_reporter.py
# We need to get to: backend/storage/email_prefs
# So we need 2 parent levels: scheduler -> backend
import os

PREFS_DIR = Path(__file__).parent.parent / "storage" / "email_prefs"
USERS_DIR = Path(__file__).parent.parent / "storage" / "users"

# Ensure directories exist
PREFS_DIR.mkdir(parents=True, exist_ok=True)

print(f"📁 Scheduler PREFS_DIR: {PREFS_DIR.absolute()}")
print(f"📁 PREFS_DIR exists: {PREFS_DIR.exists()}")


def get_all_user_ids_with_email_prefs():
    """Get all user IDs that have email preferences configured"""
    print(f"📂 Scheduler checking PREFS_DIR: {PREFS_DIR.absolute()}")
    print(f"📂 PREFS_DIR exists: {PREFS_DIR.exists()}")
    
    if not PREFS_DIR.exists():
        print(f"⚠️ Email prefs directory does not exist: {PREFS_DIR}")
        return []
    
    # List ALL files in directory for debugging
    all_files = list(PREFS_DIR.iterdir()) if PREFS_DIR.exists() else []
    print(f"📂 All files in PREFS_DIR ({len(all_files)} total):")
    for f in all_files:
        print(f"   - {f.name}")
    
    user_ids = []
    for pref_file in PREFS_DIR.glob("*_email_prefs.json"):
        # Extract user_id from filename: {user_id}_email_prefs.json
        user_id = pref_file.stem.replace("_email_prefs", "")
        user_ids.append(user_id)
        print(f"📧 Found email prefs for user: '{user_id}'")
    
    print(f"📧 Total users with email prefs: {len(user_ids)}")
    return user_ids


def get_all_user_ids():
    """Get all user IDs that have uploaded data (legacy, kept for compatibility)"""
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


def detect_data_domain(user_id: str) -> str:
    """
    Detect the domain/type of data uploaded by the user.
    Returns: healthcare, sales, finance, hr, marketing, inventory, education, or generic
    """
    try:
        from utils.paths import get_user_paths
        import pandas as pd
        
        paths = get_user_paths(user_id)
        files_dir = paths.get("files")
        
        if not files_dir or not files_dir.exists():
            return "generic"
        
        # Collect all column names from CSV/Excel files
        all_columns = set()
        for f in files_dir.iterdir():
            if f.suffix.lower() in ['.csv', '.xlsx', '.xls']:
                try:
                    if f.suffix.lower() == '.csv':
                        df = pd.read_csv(f, nrows=1)
                    else:
                        df = pd.read_excel(f, nrows=1)
                    all_columns.update([c.lower().strip() for c in df.columns])
                except:
                    continue
        
        if not all_columns:
            return "generic"
        
        cols_str = ' '.join(all_columns)
        
        # Healthcare domain keywords
        healthcare_keywords = ['patient', 'diagnosis', 'symptom', 'disease', 'treatment', 'medicine', 
                                'prescription', 'doctor', 'hospital', 'medical', 'health', 'clinical',
                                'icd', 'medication', 'blood', 'bp', 'pulse', 'lab', 'test_result']
        if any(kw in cols_str for kw in healthcare_keywords):
            return "healthcare"
        
        # HR domain keywords
        hr_keywords = ['employee', 'salary', 'department', 'hire_date', 'termination', 'leave', 
                       'attendance', 'performance', 'bonus', 'payroll', 'position', 'designation',
                       'joining', 'resignation', 'hr', 'staff']
        if any(kw in cols_str for kw in hr_keywords):
            return "hr"
        
        # Finance domain keywords
        finance_keywords = ['account', 'debit', 'credit', 'ledger', 'balance', 'transaction',
                           'interest', 'loan', 'investment', 'profit', 'loss', 'expense',
                           'budget', 'fiscal', 'tax', 'audit']
        if any(kw in cols_str for kw in finance_keywords):
            return "finance"
        
        # Sales domain keywords
        sales_keywords = ['revenue', 'order', 'customer', 'product', 'invoice', 'sale', 'purchase',
                         'quantity', 'price', 'discount', 'amount', 'payment', 'shipping']
        if any(kw in cols_str for kw in sales_keywords):
            return "sales"
        
        # Marketing domain keywords
        marketing_keywords = ['campaign', 'click', 'impression', 'conversion', 'lead', 'engagement',
                             'reach', 'ctr', 'cpc', 'roi', 'ad', 'advertisement', 'social']
        if any(kw in cols_str for kw in marketing_keywords):
            return "marketing"
        
        # Inventory domain keywords
        inventory_keywords = ['stock', 'warehouse', 'inventory', 'sku', 'reorder', 'supplier',
                             'vendor', 'bin', 'batch', 'shelf', 'storage']
        if any(kw in cols_str for kw in inventory_keywords):
            return "inventory"
        
        # Education domain keywords
        education_keywords = ['student', 'grade', 'course', 'class', 'subject', 'teacher',
                             'enrollment', 'exam', 'score', 'gpa', 'semester', 'school']
        if any(kw in cols_str for kw in education_keywords):
            return "education"
        
        return "generic"
        
    except Exception as e:
        logger.error(f"Error detecting data domain for {user_id}: {e}")
        return "generic"


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



def _generate_model_summary_html(user_id: str, df=None) -> str:
    """Generate HTML summary for the user's active model"""
    try:
        engine = ProductionMLEngine()
        if not engine.load(user_id):
            return ""
        
        # Extract stats
        model_name = engine.model_name
        target = engine.target_column
        metrics = getattr(engine, 'metrics', {})
        acc = metrics.get('accuracy', 0) * 100
        features = engine.feature_columns
        
        # ⚡ LIVE EVALUATION FALLBACK
        # If metrics missing (old model) and we have data, calculate on-fly
        if acc == 0 and df is not None and target in df.columns:
            try:
                from sklearn.metrics import accuracy_score
                import numpy as np
                import pandas as pd
                
                # Use a sample for speed
                eval_df = df.head(500)
                y_true = eval_df[target]
                
                # Preprocess
                X_list = []
                valid_indices = []
                for idx, row in eval_df.iterrows():
                    try:
                        row_dict = row.to_dict()
                        X_list.append(engine._preprocess_single(row_dict))
                        valid_indices.append(idx)
                    except: continue
                
                if X_list:
                    X_eval = np.vstack(X_list)
                    y_pred = engine.model.predict(X_eval)
                    
                    # Align y_true
                    y_true_subset = y_true.loc[valid_indices]
                    
                    # Handle encoding
                    if hasattr(engine, 'target_encoder') and engine.target_encoder:
                        try:
                            y_true_enc = engine.target_encoder.transform(y_true_subset.astype(str).str.strip())
                        except:
                            y_true_enc = pd.to_numeric(y_true_subset, errors='coerce').fillna(0)
                    else:
                        y_true_enc = pd.to_numeric(y_true_subset, errors='coerce').fillna(0)
                        
                    acc = accuracy_score(y_true_enc, y_pred) * 100
                    
            except Exception as e:
                logger.error(f"Email report live eval failed: {e}")

        # Build HTML
        html = f"""
        <div style="background: #e0f2fe; padding: 20px; border-radius: 10px; margin: 20px 0; border: 1px solid #bae6fd;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h3 style="color: #0369a1; margin: 0; font-size: 18px;">🤖 AI Business Insight</h3>
                <span style="background: #0ea5e9; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold;">Active Model</span>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                <div style="background: white; padding: 12px; border-radius: 8px;">
                     <div style="color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Active Model</div>
                     <div style="color: #0f172a; font-weight: bold; font-size: 14px;">{model_name}</div>
                </div>
                <div style="background: white; padding: 12px; border-radius: 8px;">
                     <div style="color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Performance</div>
                     <div style="color: #22c55e; font-size: 18px; font-weight: bold;">{acc:.1f}% Accuracy</div>
                </div>
            </div>
            
            <p style="margin: 15px 0 0 0; font-size: 13px; color: #334155; line-height: 1.5;">
                🎯 Your AI is currently predicting <strong>{target}</strong> using <strong>{len(features)} key indicators</strong>.
                <a href="{APP_URL}/chat" style="color: #0284c7; text-decoration: none; font-weight: 600; margin-left: 5px;">View detailed analysis →</a>
            </p>
        </div>
        """
        return html
    except Exception as e:
        logger.error(f"Error generating model summary for {user_id}: {e}")
        return ""


async def generate_daily_report_html(user_id: str) -> str:
    """Generate daily summary report HTML - works with ANY data type"""
    try:
        import pandas as pd
        from utils.paths import get_user_paths
        
        paths = get_user_paths(user_id)
        files_dir = paths.get("files")
        
        if not files_dir or not files_dir.exists():
            return None
        
        # Load all CSV/Excel files and combine
        all_data = []
        for f in files_dir.iterdir():
            if f.suffix.lower() in ['.csv', '.xlsx', '.xls']:
                try:
                    if f.suffix.lower() == '.csv':
                        df = pd.read_csv(f)
                    else:
                        df = pd.read_excel(f)
                    all_data.append(df)
                except:
                    continue
        
        if not all_data:
            return None
        
        # Combine all dataframes
        df = pd.concat(all_data, ignore_index=True) if len(all_data) > 1 else all_data[0]
        
        if df.empty:
            return None
        
        # Standardize column names
        df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
        
        # ===== DYNAMIC METRICS DETECTION =====
        total_rows = len(df)
        total_columns = len(df.columns)
        
        # Find numeric columns for statistics
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        # Find categorical columns for grouping
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Build dynamic metrics list
        metrics = []
        
        metrics.append(("📊 Total Records", f"{total_rows:,}"))
        metrics.append(("📁 Data Columns", f"{total_columns}"))
        
        # Add numeric column statistics
        for col in numeric_cols[:3]:  # Top 3 numeric columns
            col_sum = df[col].sum()
            col_avg = df[col].mean()
            col_clean = col.replace('_', ' ').title()
            if col_sum > 0:
                metrics.append((f"📈 Total {col_clean}", f"{col_sum:,.2f}"))
            if col_avg > 0:
                metrics.append((f"📉 Avg {col_clean}", f"{col_avg:,.2f}"))
        
        # Add unique counts for categorical columns
        for col in categorical_cols[:2]:  # Top 2 categorical columns
            unique_count = df[col].nunique()
            col_clean = col.replace('_', ' ').title()
            if unique_count > 0 and unique_count < len(df):  # Only if meaningful
                metrics.append((f"🏷️ Unique {col_clean}", f"{unique_count:,}"))
        
        # ===== TOP VALUES SECTION =====
        top_values_html = ""
        for col in categorical_cols[:1]:  # Top category breakdown
            if col in df.columns:
                top_items = df[col].value_counts().head(5)
                if len(top_items) > 0:
                    col_clean = col.replace('_', ' ').title()
                    top_values_html = f'''
                    <div style="background: #fef3c7; padding: 15px; border-radius: 8px; margin-top: 20px;">
                        <h4 style="color: #92400e; margin: 0 0 10px 0;">🏆 Top {col_clean}</h4>
                        <table style="width: 100%; border-collapse: collapse;">
                    '''
                    for item, count in top_items.items():
                        top_values_html += f'''
                            <tr>
                                <td style="padding: 5px 10px; border-bottom: 1px solid #fcd34d;">{str(item)[:30]}</td>
                                <td style="padding: 5px 10px; border-bottom: 1px solid #fcd34d; text-align: right; font-weight: bold;">{count:,}</td>
                            </tr>
                        '''
                    top_values_html += '</table></div>'
                    break
        
        # ===== BUILD HTML REPORT =====
        metrics_rows = ""
        for label, value in metrics[:8]:  # Limit to 8 metrics
            metrics_rows += f'''
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">
                        <strong>{label}</strong>
                    </td>
                    <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: right; font-size: 16px; color: #14b8a6;">
                        {value}
                    </td>
                </tr>
            '''
        
        # Generate Model Summary
        model_summary_html = _generate_model_summary_html(user_id, df)
        
        html = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <!-- Header with Data Vision branding -->
            <div style="background: linear-gradient(135deg, #14b8a6 0%, #0d9488 100%); padding: 25px; border-radius: 12px 12px 0 0; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">📊 Data Vision</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0; font-size: 14px;">Your Daily Data Report</p>
            </div>
            
            <!-- Main Content -->
            <div style="background: #ffffff; padding: 25px; border: 1px solid #e5e7eb; border-top: none;">
                
                {model_summary_html}
                
                <h2 style="color: #1e293b; margin-top: 0; font-size: 18px;">📈 Key Metrics Summary</h2>
                
                <div style="background: #f8fafc; padding: 20px; border-radius: 10px; margin: 15px 0;">
                    <table style="width: 100%; border-collapse: collapse;">
                        {metrics_rows}
                    </table>
                </div>
                
                {top_values_html}
                
                <!-- Data Overview -->
                <div style="background: #ecfdf5; padding: 15px; border-radius: 8px; margin-top: 20px;">
                    <h4 style="color: #065f46; margin: 0 0 10px 0;">📋 Data Overview</h4>
                    <p style="color: #047857; margin: 0; font-size: 14px;">
                        Your dataset contains <strong>{total_rows:,}</strong> records across <strong>{total_columns}</strong> columns.
                        {f"Including {len(numeric_cols)} numeric and {len(categorical_cols)} categorical fields." if numeric_cols or categorical_cols else ""}
                    </p>
                </div>
            </div>
            
            <!-- Footer -->
            <div style="background: #f1f5f9; padding: 20px; border-radius: 0 0 12px 12px; text-align: center; border: 1px solid #e5e7eb; border-top: none;">
                <p style="color: #64748b; font-size: 13px; margin: 0;">
                    This is your automated report from <strong>Data Vision</strong>.<br/>
                    <a href="{APP_URL}/analyst" style="color: #14b8a6; text-decoration: none;">💬 Ask AI for more insights →</a>
                </p>
            </div>
        </div>
        """
        
        return html
        
    except Exception as e:
        logger.error(f"Error generating daily report for {user_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


async def send_daily_reports():
    """Send daily reports to all users who have it enabled at the current time"""
    from datetime import timezone, timedelta
    
    # HF servers run on UTC, but users are typically in IST (India Standard Time = UTC+5:30)
    IST = timezone(timedelta(hours=5, minutes=30))
    now_ist = datetime.now(IST)
    current_hour = now_ist.hour
    current_minute = now_ist.minute
    print(f"📧 Checking for daily reports at {current_hour:02d}:{current_minute:02d} IST")
    
    if not RESEND_API_KEY:
        print("⚠️ RESEND_API_KEY not configured, skipping email send")
        return
    
    # Get ALL users who have configured email preferences (not just those with data)
    user_ids = get_all_user_ids_with_email_prefs()
    print(f"📧 Scanning {len(user_ids)} users for daily reports")
    
    for user_id in user_ids:
        try:
            prefs = get_user_email_prefs(user_id)
            
            if not prefs:
                print(f"  ⏭️ No prefs found for {user_id}")
                continue
            
            # Check if daily reports enabled and it's the right hour AND minute
            pref_hour = prefs.get('daily_report_hour', 8)
            pref_minute = prefs.get('daily_report_minute', 0)
            daily_enabled = prefs.get('daily_report_enabled', False)
            
            print(f"  📋 User {user_id}: enabled={daily_enabled}, scheduled={pref_hour:02d}:{pref_minute:02d}, current={current_hour:02d}:{current_minute:02d}")
            
            if (daily_enabled and 
                pref_hour == current_hour and 
                pref_minute == current_minute):
                email = get_user_email(user_id)
                
                if not email:
                    print(f"  ⚠️ No email for user {user_id}, skipping")
                    continue
                
                print(f"  📧 TIME MATCH! Generating report for {email}...")
                report_html = await generate_daily_report_html(user_id)
                
                if report_html:
                    await send_insight_email(
                        to_email=email,
                        title=f"Data Vision - Daily Report | {datetime.now().strftime('%B %d, %Y')}",
                        body=report_html,
                        workspace_id=user_id
                    )
                    print(f"  ✅ Sent Data Vision daily report to {email} for user {user_id}")
                    
        except Exception as e:
            logger.error(f"Error sending daily report to {user_id}: {e}")


async def send_weekly_reports():
    """Send weekly reports to all users who have it enabled on the correct day/hour/minute"""
    from datetime import timezone, timedelta
    
    # Use IST timezone (India Standard Time = UTC+5:30)
    IST = timezone(timedelta(hours=5, minutes=30))
    now_ist = datetime.now(IST)
    current_day = now_ist.weekday()  # 0=Monday, 6=Sunday
    # Convert to our format (0=Sunday, 1=Monday, ..., 6=Saturday)
    current_day_our_format = (current_day + 1) % 7
    current_hour = now_ist.hour
    current_minute = now_ist.minute
    
    print(f"📧 Checking for weekly reports on day {current_day_our_format} at {current_hour:02d}:{current_minute:02d} IST")
    
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
                        title=f"Data Vision - Weekly Report | Week of {datetime.now().strftime('%B %d, %Y')}",
                        body=report_html,
                        workspace_id=user_id
                    )
                    logger.info(f"Sent Data Vision weekly report to {email} for user {user_id}")
                    
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
