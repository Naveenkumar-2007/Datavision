"""
Scheduled Email Reporter - Sends daily/weekly reports based on user preferences
Uses APScheduler for background job scheduling

FIXED: Proper time-window matching with last-sent tracking to ensure emails
are delivered at the scheduled time even if scheduler has minor delays.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import os
import httpx
import pandas as pd

from services.email_service import send_insight_email, RESEND_API_KEY, APP_URL
from agents.reports import generate_weekly_report, generate_monthly_report
from graph.query import revenue_dataframe, get_user_currency
from ml.automl_engine import ProductionMLEngine

logger = logging.getLogger(__name__)

# Storage directory for email preferences
PREFS_DIR = Path(__file__).parent.parent / "storage" / "email_prefs"
USERS_DIR = Path(__file__).parent.parent / "storage" / "users"
SENT_TRACKING_DIR = Path(__file__).parent.parent / "storage" / "email_sent_tracking"

# Ensure directories exist
PREFS_DIR.mkdir(parents=True, exist_ok=True)
SENT_TRACKING_DIR.mkdir(parents=True, exist_ok=True)

# Define timezone - IST (India Standard Time = UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

print(f"📁 Scheduler PREFS_DIR: {PREFS_DIR.absolute()}")
print(f"📁 PREFS_DIR exists: {PREFS_DIR.exists()}")
print(f"📁 SENT_TRACKING_DIR: {SENT_TRACKING_DIR.absolute()}")


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


def get_sent_tracking(user_id: str, report_type: str) -> dict:
    """Get the last sent tracking info for a user and report type"""
    tracking_path = SENT_TRACKING_DIR / f"{user_id}_{report_type}_tracking.json"
    
    if tracking_path.exists():
        try:
            with open(tracking_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading tracking for {user_id}/{report_type}: {e}")
    
    return {"last_sent_date": None}


def update_sent_tracking(user_id: str, report_type: str, sent_date: str):
    """Update the last sent tracking for a user and report type"""
    tracking_path = SENT_TRACKING_DIR / f"{user_id}_{report_type}_tracking.json"
    
    try:
        tracking_data = {
            "last_sent_date": sent_date,
            "last_sent_timestamp": datetime.now(IST).isoformat()
        }
        with open(tracking_path, 'w') as f:
            json.dump(tracking_data, f, indent=2)
        logger.info(f"Updated tracking for {user_id}/{report_type}: {sent_date}")
    except Exception as e:
        logger.error(f"Error updating tracking for {user_id}/{report_type}: {e}")


def get_user_timezone(prefs: dict) -> timezone:
    """Get timezone from user preferences, default to IST"""
    offset_hours = prefs.get('timezone_offset', 5.5)  # Default IST
    hours = int(offset_hours)
    minutes = int((offset_hours - hours) * 60)
    return timezone(timedelta(hours=hours, minutes=minutes))


def should_send_daily_report(user_id: str, prefs: dict, now_utc: datetime = None) -> bool:
    """
    Determine if daily report should be sent now.
    Uses a time window approach + last-sent tracking to ensure reliable delivery.
    Uses user's timezone for scheduling.
    """
    if not prefs.get('daily_report_enabled', False):
        return False
    
    # Get user's timezone
    user_tz = get_user_timezone(prefs)
    now_user = datetime.now(user_tz)
    
    pref_hour = prefs.get('daily_report_hour', 8)
    pref_minute = prefs.get('daily_report_minute', 0)
    
    current_hour = now_user.hour
    current_minute = now_user.minute
    today_date = now_user.strftime('%Y-%m-%d')
    
    # Check if already sent today
    tracking = get_sent_tracking(user_id, "daily")
    if tracking.get("last_sent_date") == today_date:
        return False  # Already sent today
    
    # TIME WINDOW APPROACH: Allow a 5-minute window after scheduled time
    # This handles cases where scheduler might be a few seconds/minutes late
    scheduled_time_today = now_user.replace(hour=pref_hour, minute=pref_minute, second=0, microsecond=0)
    window_end = scheduled_time_today + timedelta(minutes=5)
    
    # Check if we're within the sending window (scheduled time <= now <= scheduled time + 5 min)
    is_after_scheduled = now_user >= scheduled_time_today
    is_within_window = now_user <= window_end
    
    if is_after_scheduled and is_within_window:
        print(f"  ✅ MATCH! User {user_id}: scheduled={pref_hour:02d}:{pref_minute:02d}, current={current_hour:02d}:{current_minute:02d}, within window")
        return True
    
    # CATCHUP LOGIC: If we missed the window today but it's past the scheduled time
    # and we haven't sent yet today, send now (prevents missed emails)
    if is_after_scheduled and not is_within_window:
        hours_since_scheduled = (now_user - scheduled_time_today).total_seconds() / 3600
        if hours_since_scheduled < 12:  # Within 12 hours of scheduled time
            print(f"  ⚠️ CATCHUP! User {user_id}: missed window by {hours_since_scheduled:.1f}h, sending now")
            return True
    
    return False


def should_send_weekly_report(user_id: str, prefs: dict, now_utc: datetime = None) -> bool:
    """
    Determine if weekly report should be sent now.
    Uses time window + last-sent tracking for reliable delivery.
    Uses user's timezone for scheduling.
    """
    if not prefs.get('weekly_report_enabled', False):
        return False
    
    # Get user's timezone
    user_tz = get_user_timezone(prefs)
    now_user = datetime.now(user_tz)
    
    pref_day = prefs.get('weekly_report_day', 1)  # 0=Sunday, 1=Monday, etc.
    pref_hour = prefs.get('weekly_report_hour', 9)
    pref_minute = prefs.get('weekly_report_minute', 0)
    
    current_day = now_user.weekday()  # 0=Monday, 6=Sunday
    # Convert Python weekday (0=Mon) to our format (0=Sun)
    current_day_our_format = (current_day + 1) % 7
    
    if pref_day != current_day_our_format:
        return False  # Not the right day
    
    # Get week identifier (year-week number)
    year, week_num, _ = now_user.isocalendar()
    week_id = f"{year}-W{week_num:02d}"
    
    # Check if already sent this week
    tracking = get_sent_tracking(user_id, "weekly")
    if tracking.get("last_sent_date") == week_id:
        return False  # Already sent this week
    
    current_hour = now_user.hour
    current_minute = now_user.minute
    
    # Time window approach
    scheduled_time = now_user.replace(hour=pref_hour, minute=pref_minute, second=0, microsecond=0)
    window_end = scheduled_time + timedelta(minutes=5)
    
    is_after_scheduled = now_user >= scheduled_time
    is_within_window = now_user <= window_end
    
    if is_after_scheduled and is_within_window:
        return True
    
    # Catchup logic for weekly
    if is_after_scheduled:
        hours_since_scheduled = (now_user - scheduled_time).total_seconds() / 3600
        if hours_since_scheduled < 12:
            return True
    
    return False


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


async def gather_comprehensive_data_context(user_id: str) -> dict:
    """
    Gather comprehensive real user data for AI-powered email generation.
    Returns structured data including:
    - File statistics
    - Numeric column summaries
    - Category breakdowns
    - ML model details (if trained)
    - Feature importance
    - Sample predictions from ML model
    """
    context = {
        "has_data": False,
        "files": [],
        "total_rows": 0,
        "total_columns": 0,
        "numeric_stats": [],
        "category_breakdowns": [],
        "ml_model": None,
        "feature_importance": [],
        "sample_predictions": [],  # NEW: Real predictions from ML model
        "domain": "generic"
    }
    
    try:
        from utils.paths import get_user_paths
        from config.settings import Settings
        
        paths = get_user_paths(user_id)
        files_dir = paths.get('files')
        
        if not files_dir or not files_dir.exists():
            return context
        
        # Load all data files
        all_dfs = []
        for f in files_dir.iterdir():
            if f.suffix.lower() in ['.csv', '.xlsx', '.xls']:
                try:
                    if f.suffix.lower() == '.csv':
                        df = pd.read_csv(f)
                    else:
                        df = pd.read_excel(f)
                    
                    context["files"].append({
                        "name": f.name,
                        "rows": len(df),
                        "columns": len(df.columns)
                    })
                    all_dfs.append(df)
                except Exception as e:
                    logger.warning(f"Error reading {f.name}: {e}")
        
        if not all_dfs:
            return context
        
        context["has_data"] = True
        
        # Combine all dataframes
        df = pd.concat(all_dfs, ignore_index=True) if len(all_dfs) > 1 else all_dfs[0]
        df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
        
        context["total_rows"] = len(df)
        context["total_columns"] = len(df.columns)
        context["domain"] = detect_data_domain(user_id)
        
        # Numeric column statistics
        numeric_cols = df.select_dtypes(include=['int64', 'float64', 'int32', 'float32']).columns.tolist()
        for col in numeric_cols[:6]:
            context["numeric_stats"].append({
                "column": col,
                "sum": float(df[col].sum()),
                "mean": float(df[col].mean()),
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "std": float(df[col].std()) if len(df) > 1 else 0
            })
        
        # Category breakdowns
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        for col in cat_cols[:3]:
            value_counts = df[col].value_counts().head(5)
            context["category_breakdowns"].append({
                "column": col,
                "unique_count": df[col].nunique(),
                "top_values": [{"value": str(v), "count": int(c)} for v, c in value_counts.items()]
            })
        
        # Get ML model information
        try:
            engine = ProductionMLEngine()
            if engine.load(user_id):
                model_name = engine.model_name
                target = engine.target_column
                features = engine.feature_columns
                metrics = getattr(engine, 'metrics', {})
                
                # Calculate live accuracy if needed
                acc = metrics.get('accuracy', 0)
                if acc == 0 and target in df.columns:
                    try:
                        from sklearn.metrics import accuracy_score
                        import numpy as np
                        
                        eval_df = df.head(500)
                        y_true = eval_df[target]
                        
                        X_list = []
                        valid_indices = []
                        for idx, row in eval_df.iterrows():
                            try:
                                row_dict = row.to_dict()
                                X_list.append(engine._preprocess_single(row_dict))
                                valid_indices.append(idx)
                            except:
                                continue
                        
                        if X_list:
                            X_eval = np.vstack(X_list)
                            y_pred = engine.model.predict(X_eval)
                            y_true_subset = y_true.loc[valid_indices]
                            
                            if hasattr(engine, 'target_encoder') and engine.target_encoder:
                                try:
                                    y_true_enc = engine.target_encoder.transform(y_true_subset.astype(str).str.strip())
                                except:
                                    y_true_enc = pd.to_numeric(y_true_subset, errors='coerce').fillna(0)
                            else:
                                y_true_enc = pd.to_numeric(y_true_subset, errors='coerce').fillna(0)
                            
                            acc = accuracy_score(y_true_enc, y_pred)
                    except Exception as e:
                        logger.warning(f"Live eval failed: {e}")
                
                context["ml_model"] = {
                    "name": model_name,
                    "target": target,
                    "accuracy": acc * 100 if acc <= 1 else acc,
                    "feature_count": len(features),
                    "features": features[:10]  # Top 10 features
                }
                
                # Feature importance
                if hasattr(engine, 'feature_importance_') and engine.feature_importance_ is not None:
                    context["feature_importance"] = [
                        {"feature": f, "importance": float(i)} 
                        for f, i in sorted(zip(features, engine.feature_importance_), 
                                          key=lambda x: x[1], reverse=True)[:5]
                    ]
                
                # NEW: Get sample predictions from the model
                try:
                    import numpy as np
                    sample_df = df.head(5)  # Get 5 sample rows
                    predictions = []
                    for idx, row in sample_df.iterrows():
                        try:
                            row_dict = row.to_dict()
                            X_sample = engine._preprocess_single(row_dict)
                            pred = engine.model.predict([X_sample])[0]
                            
                            # Decode prediction if classifier
                            if hasattr(engine, 'target_encoder') and engine.target_encoder:
                                try:
                                    pred_label = engine.target_encoder.inverse_transform([int(pred)])[0]
                                except:
                                    pred_label = str(pred)
                            else:
                                pred_label = str(pred)
                            
                            # Get key features for this prediction
                            key_features = {}
                            for feat in features[:3]:  # Top 3 features
                                if feat in row_dict:
                                    key_features[feat] = row_dict[feat]
                            
                            predictions.append({
                                "prediction": pred_label,
                                "key_features": key_features
                            })
                        except Exception as pred_error:
                            logger.debug(f"Sample prediction failed: {pred_error}")
                            continue
                    
                    context["sample_predictions"] = predictions
                    logger.info(f"Generated {len(predictions)} sample predictions for email")
                except Exception as pred_err:
                    logger.warning(f"Could not generate sample predictions: {pred_err}")
        except Exception as e:
            logger.warning(f"Error loading ML model for {user_id}: {e}")
        
        # Check model storage for metadata (primary location)
        model_storage_dir = Settings.BASE_DIR / "storage" / "models" / user_id
        active_metadata_path = model_storage_dir / "active_metadata.json"
        
        if active_metadata_path.exists() and not context["ml_model"]:
            try:
                with open(active_metadata_path, 'r') as f:
                    model_meta = json.load(f)
                
                metrics = model_meta.get('metrics', {})
                task_type = model_meta.get('task_type', 'classification')
                
                # Get accuracy based on task type
                if task_type == 'classification':
                    acc = metrics.get('accuracy', 0)
                else:
                    acc = metrics.get('r2', metrics.get('r2_score', 0))
                
                context["ml_model"] = {
                    "name": model_meta.get('model_name', 'AutoML Model'),
                    "target": model_meta.get('target_column', 'unknown'),
                    "accuracy": acc * 100 if acc <= 1 else acc,
                    "task_type": task_type,
                    "feature_count": len(model_meta.get('feature_columns', [])),
                    "features": model_meta.get('feature_columns', [])[:10],
                    "version": model_meta.get('version', 1),
                    "training_date": model_meta.get('training_date', '')
                }
                
                if not context["feature_importance"] and model_meta.get('feature_columns'):
                    # Create basic feature list if no importance scores
                    context["feature_importance"] = [
                        {"feature": f, "importance": 0} 
                        for f in model_meta.get('feature_columns', [])[:5]
                    ]
            except Exception as e:
                logger.warning(f"Error reading model metadata for {user_id}: {e}")
        
        # Fallback: Check automl_results for more details (legacy location)
        automl_dir = Settings.BASE_DIR / "storage" / "automl_results" / user_id
        if automl_dir.exists() and not context["ml_model"]:
            result_files = sorted(automl_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
            if result_files:
                try:
                    with open(result_files[0], 'r') as f:
                        automl_data = json.load(f)
                    
                    if not context["ml_model"]:
                        best = automl_data.get('best_model', {})
                        context["ml_model"] = {
                            "name": best.get('name', 'AutoML Model'),
                            "target": automl_data.get('target_column', 'unknown'),
                            "accuracy": best.get('metrics', {}).get('accuracy', 0) * 100,
                            "task_type": automl_data.get('task_type', 'classification')
                        }
                    
                    if not context["feature_importance"]:
                        fi = automl_data.get('feature_importance', [])[:5]
                        context["feature_importance"] = fi if isinstance(fi, list) else []
                except:
                    pass
        
        return context
        
    except Exception as e:
        logger.error(f"Error gathering data context for {user_id}: {e}")
        import traceback
        traceback.print_exc()
        return context


async def generate_ai_powered_daily_report(user_id: str) -> str:
    """
    Generate an AI-powered daily report using REAL data and ML model results.
    Uses Groq API for intelligent insights generation.
    """
    try:
        # Gather comprehensive real data
        data_context = await gather_comprehensive_data_context(user_id)
        
        if not data_context["has_data"]:
            return None
        
        # Build context string for AI
        context_text = f"""
USER DATA SUMMARY:
- Domain: {data_context['domain'].upper()}
- Total Records: {data_context['total_rows']:,}
- Total Columns: {data_context['total_columns']}
- Files: {', '.join([f['name'] for f in data_context['files']])}

NUMERIC METRICS:"""
        
        for stat in data_context["numeric_stats"]:
            col_name = stat['column'].replace('_', ' ').title()
            context_text += f"\n- {col_name}: Total={stat['sum']:,.2f}, Average={stat['mean']:,.2f}, Range=[{stat['min']:,.2f} to {stat['max']:,.2f}]"
        
        if data_context["category_breakdowns"]:
            context_text += "\n\nCATEGORY DISTRIBUTION:"
            for cat in data_context["category_breakdowns"]:
                col_name = cat['column'].replace('_', ' ').title()
                top_vals = ', '.join([f"{v['value']}: {v['count']}" for v in cat['top_values'][:3]])
                context_text += f"\n- {col_name} ({cat['unique_count']} unique): {top_vals}"
        
        if data_context["ml_model"]:
            ml = data_context["ml_model"]
            context_text += f"""

TRAINED ML MODEL:
- Model Type: {ml.get('name', 'Unknown')}
- Predicting: {ml.get('target', 'Unknown')}
- Accuracy: {ml.get('accuracy', 0):.1f}%
- Using {ml.get('feature_count', 0)} features"""
        
        if data_context["feature_importance"]:
            context_text += "\n\nTOP PREDICTIVE FEATURES:"
            for i, fi in enumerate(data_context["feature_importance"], 1):
                if isinstance(fi, dict):
                    context_text += f"\n{i}. {fi.get('feature', 'Unknown')} (importance: {fi.get('importance', 0):.3f})"
                else:
                    context_text += f"\n{i}. {fi}"
        
        # NEW: Include sample predictions in context
        if data_context.get("sample_predictions"):
            context_text += "\n\nSAMPLE PREDICTIONS FROM MODEL:"
            for i, pred in enumerate(data_context["sample_predictions"][:3], 1):
                features_str = ", ".join([f"{k}={v}" for k, v in pred.get("key_features", {}).items()])
                context_text += f"\n{i}. Prediction: {pred.get('prediction')} | Based on: {features_str}"
        
        # Use Groq API to generate intelligent report
        groq_api_key = os.environ.get("GROQ_API_KEY")
        
        if groq_api_key:
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
                                {
                                    "role": "system",
                                    "content": """You are DataVision AI, a business intelligence expert. Generate a professional, insightful daily report email.

FORMAT YOUR RESPONSE AS CLEAN HTML (no markdown). Include:
1. A warm greeting
2. Key metrics with specific numbers from the data
3. If ML model exists: explain what it predicts and its accuracy in business terms
4. If feature importance exists: explain WHY these features matter for business decisions
5. 2-3 actionable recommendations based on the data
6. Encouraging closing

Use these inline styles for formatting:
- Use <strong> for emphasis
- Use color: #14b8a6 for positive metrics
- Use color: #f59e0b for warnings
- Keep it concise but insightful"""
                                },
                                {
                                    "role": "user", 
                                    "content": f"""Generate a Daily Intelligence Report for {datetime.now(IST).strftime('%B %d, %Y')}.

{context_text}

Write the email body in clean HTML. Make it professional, data-driven, and actionable."""
                                }
                            ],
                            "temperature": 0.7,
                            "max_tokens": 1500
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        ai_content = result['choices'][0]['message']['content'].strip()
                        return ai_content
            except Exception as ai_error:
                logger.warning(f"AI generation failed: {ai_error}")
        
        # Fallback: Generate structured report without AI
        return await generate_daily_report_html(user_id)
        
    except Exception as e:
        logger.error(f"Error generating AI-powered report for {user_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


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
    now_ist = datetime.now(IST)
    current_hour = now_ist.hour
    current_minute = now_ist.minute
    today_date = now_ist.strftime('%Y-%m-%d')
    print(f"📧 Checking for daily reports at {current_hour:02d}:{current_minute:02d} IST ({today_date})")
    
    if not RESEND_API_KEY:
        print("⚠️ RESEND_API_KEY not configured, skipping email send")
        return
    
    # Get ALL users who have configured email preferences
    user_ids = get_all_user_ids_with_email_prefs()
    print(f"📧 Scanning {len(user_ids)} users for daily reports")
    
    for user_id in user_ids:
        try:
            prefs = get_user_email_prefs(user_id)
            
            if not prefs:
                print(f"  ⏭️ No prefs found for {user_id}")
                continue
            
            pref_hour = prefs.get('daily_report_hour', 8)
            pref_minute = prefs.get('daily_report_minute', 0)
            daily_enabled = prefs.get('daily_report_enabled', False)
            
            print(f"  📋 User {user_id}: enabled={daily_enabled}, scheduled={pref_hour:02d}:{pref_minute:02d}")
            
            # Use the improved timing logic with catchup support
            if should_send_daily_report(user_id, prefs, now_ist):
                email = get_user_email(user_id)
                
                if not email:
                    print(f"  ⚠️ No email for user {user_id}, skipping")
                    continue
                
                print(f"  📧 Generating AI-powered report for {email}...")
                
                # Generate report with REAL ML data and AI insights
                report_html = await generate_ai_powered_daily_report(user_id)
                
                if report_html:
                    await send_insight_email(
                        to_email=email,
                        title=f"DataVision - Daily Intelligence Report | {datetime.now().strftime('%B %d, %Y')}",
                        body=report_html,
                        workspace_id=user_id
                    )
                    
                    # Mark as sent for today
                    update_sent_tracking(user_id, "daily", today_date)
                    print(f"  ✅ Sent AI-powered daily report to {email} for user {user_id}")
                else:
                    print(f"  ⚠️ No report content generated for {user_id}")
                    
        except Exception as e:
            logger.error(f"Error sending daily report to {user_id}: {e}")
            import traceback
            traceback.print_exc()


async def send_weekly_reports():
    """Send weekly reports to all users who have it enabled on the correct day/hour/minute"""
    now_ist = datetime.now(IST)
    current_day = now_ist.weekday()  # 0=Monday, 6=Sunday
    # Convert to our format (0=Sunday, 1=Monday, ..., 6=Saturday)
    current_day_our_format = (current_day + 1) % 7
    current_hour = now_ist.hour
    current_minute = now_ist.minute
    
    # Week identifier for tracking
    year, week_num, _ = now_ist.isocalendar()
    week_id = f"{year}-W{week_num:02d}"
    
    print(f"📧 Checking for weekly reports on day {current_day_our_format} at {current_hour:02d}:{current_minute:02d} IST (Week: {week_id})")
    
    if not RESEND_API_KEY:
        print("⚠️ RESEND_API_KEY not configured, skipping email send")
        return
    
    # Get all users with email preferences
    user_ids = get_all_user_ids_with_email_prefs()
    
    for user_id in user_ids:
        try:
            prefs = get_user_email_prefs(user_id)
            
            if not prefs:
                continue
            
            # Use improved timing logic with catchup support
            if should_send_weekly_report(user_id, prefs, now_ist):
                email = get_user_email(user_id)
                
                if not email:
                    logger.warning(f"No email for user {user_id}, skipping weekly report")
                    continue
                
                print(f"  📧 Generating weekly report for {email}...")
                
                # Generate AI-powered weekly report
                data_context = await gather_comprehensive_data_context(user_id)
                
                if data_context["has_data"]:
                    # Try AI-generated weekly report
                    groq_api_key = os.environ.get("GROQ_API_KEY")
                    report_html = None
                    
                    if groq_api_key:
                        try:
                            context_text = f"""
WEEKLY REPORT DATA:
- Domain: {data_context['domain'].upper()}
- Total Records: {data_context['total_rows']:,}
- Files: {', '.join([f['name'] for f in data_context['files']])}
"""
                            for stat in data_context["numeric_stats"]:
                                col_name = stat['column'].replace('_', ' ').title()
                                context_text += f"\n- {col_name}: Total={stat['sum']:,.2f}, Avg={stat['mean']:,.2f}"
                            
                            if data_context["ml_model"]:
                                ml = data_context["ml_model"]
                                context_text += f"\n\nML Model: {ml.get('name')} predicting {ml.get('target')} with {ml.get('accuracy', 0):.1f}% accuracy"
                            
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
                                            {
                                                "role": "system",
                                                "content": "You are DataVision AI. Generate a professional weekly summary report in clean HTML with key insights, trends, and recommendations."
                                            },
                                            {
                                                "role": "user",
                                                "content": f"Generate a Weekly Summary Report for week of {now_ist.strftime('%B %d, %Y')}.\n\n{context_text}"
                                            }
                                        ],
                                        "temperature": 0.7,
                                        "max_tokens": 1500
                                    }
                                )
                                
                                if response.status_code == 200:
                                    result = response.json()
                                    report_html = result['choices'][0]['message']['content'].strip()
                        except Exception as e:
                            logger.warning(f"AI weekly report generation failed: {e}")
                    
                    # Fallback to basic report
                    if not report_html:
                        report_html = generate_weekly_report(user_id)
                    
                    if report_html:
                        await send_insight_email(
                            to_email=email,
                            title=f"DataVision - Weekly Intelligence Report | Week of {now_ist.strftime('%B %d, %Y')}",
                            body=report_html,
                            workspace_id=user_id
                        )
                        
                        # Mark as sent for this week
                        update_sent_tracking(user_id, "weekly", week_id)
                        print(f"  ✅ Sent weekly report to {email} for user {user_id}")
                    
        except Exception as e:
            logger.error(f"Error sending weekly report to {user_id}: {e}")
            import traceback
            traceback.print_exc()
                    
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
