"""
Autonomous Visual Intelligence API
===================================
Provides Overview and Dashboard endpoints using the Visual Intelligence Engine.
Uses user-uploaded data from storage directory.

The engine autonomously:
- Analyzes data structure and patterns
- Decides which visualizations are best
- Generates different layouts for Overview vs Dashboard
"""

from fastapi import APIRouter, HTTPException, Query, Header
from fastapi.responses import JSONResponse
from typing import Optional, Any
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path

# Import the Visual Intelligence Engine
from core.overview_engine_v2 import OverviewEngineV2
from utils.paths import get_user_paths, STORAGE_BASE

router = APIRouter()

# Initialize the engine
engine = OverviewEngineV2()


def convert_numpy_types(obj: Any) -> Any:
    """
    Recursively convert numpy types to Python native types for JSON serialization.
    """
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(v) for v in obj]
    elif isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif pd.isna(obj):
        return None
    else:
        return obj


def load_user_data(user_id: str) -> pd.DataFrame:
    """
    Load user's uploaded CSV/Excel data from storage.
    Returns combined DataFrame from all files.
    """
    paths = get_user_paths(user_id)
    files_dir = paths["files"]
    
    if not files_dir.exists():
        return pd.DataFrame()
    
    dfs = []
    for file_path in files_dir.iterdir():
        if file_path.is_file():
            try:
                if file_path.suffix.lower() == '.csv':
                    df = pd.read_csv(file_path)
                    dfs.append(df)
                    print(f"✅ Loaded CSV: {file_path.name} ({len(df)} rows)")
                elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                    df = pd.read_excel(file_path)
                    dfs.append(df)
                    print(f"✅ Loaded Excel: {file_path.name} ({len(df)} rows)")
            except Exception as e:
                print(f"⚠️ Failed to load {file_path.name}: {e}")
    
    if not dfs:
        return pd.DataFrame()
    
    # Combine all dataframes
    if len(dfs) == 1:
        return dfs[0]
    
    # Try to concatenate (same columns) or return the largest one
    try:
        combined = pd.concat(dfs, ignore_index=True)
        print(f"📊 Combined {len(dfs)} files into {len(combined)} rows")
        return combined
    except Exception:
        # Return the largest dataframe if concat fails
        largest = max(dfs, key=len)
        print(f"📊 Using largest file with {len(largest)} rows")
        return largest


@router.get("/overview")
async def get_overview(
    user_id: Optional[str] = Query(None, description="User ID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Generate the Autonomous Overview using the Visual Intelligence Engine.
    
    Overview Mode:
    - 3-5 key visualizations
    - Executive summary focus
    - High-level insights
    """
    try:
        # Get user_id from header or query parameter
        effective_user_id = x_user_id or user_id
        
        if not effective_user_id:
            # Try to find any user with data as fallback
            if STORAGE_BASE.exists():
                for user_dir in STORAGE_BASE.iterdir():
                    if user_dir.is_dir():
                        files_dir = user_dir / "files"
                        if files_dir.exists() and list(files_dir.glob("*.csv")) + list(files_dir.glob("*.xlsx")):
                            effective_user_id = user_dir.name
                            print(f"🔍 Auto-detected user: {effective_user_id}")
                            break
        
        if not effective_user_id:
            return {
                "layout_spec": {"zones": [], "primary_focus": [], "grid_columns": 2, "aspect_ratios": []},
                "visual_primitives": [],
                "color_palette": {"primary": ["#14b8a6"], "secondary": ["#0ea5e9"], "accents": ["#f59e0b"], "text_colors": {}},
                "narrative_elements": [{"type": "text", "content": "No data found. Please upload a dataset."}],
                "data_sample": []
            }
        
        # Load user data
        df = load_user_data(effective_user_id)
        
        if df.empty:
            return {
                "layout_spec": {"zones": [], "primary_focus": [], "grid_columns": 2, "aspect_ratios": []},
                "visual_primitives": [],
                "color_palette": {"primary": ["#14b8a6"], "secondary": ["#0ea5e9"], "accents": ["#f59e0b"], "text_colors": {}},
                "narrative_elements": [{"type": "text", "content": "No data found. Please upload a dataset."}],
                "data_sample": []
            }
        
        print(f"📊 Generating OVERVIEW for user {effective_user_id} with {len(df)} rows")
        
        # Generate Visual Intelligence - OVERVIEW MODE
        result = engine.generate(df, mode='overview')
        
        # Attach data sample for frontend rendering
        data_sample = df.head(100).where(pd.notnull(df), None).to_dict(orient='records')
        result['data_sample'] = data_sample
        
        # Convert numpy types to native Python types
        result = convert_numpy_types(result)
        
        return result

    except Exception as e:
        print(f"❌ Error generating overview: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard(
    user_id: Optional[str] = Query(None, description="User ID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Generate the Autonomous Dashboard using the Visual Intelligence Engine.
    
    Dashboard Mode:
    - 6-12 diverse visualizations
    - Detailed exploration
    - Multiple KPIs and chart types
    """
    try:
        # Get user_id from header or query parameter
        effective_user_id = x_user_id or user_id
        
        if not effective_user_id:
            # Try to find any user with data as fallback
            if STORAGE_BASE.exists():
                for user_dir in STORAGE_BASE.iterdir():
                    if user_dir.is_dir():
                        files_dir = user_dir / "files"
                        if files_dir.exists() and list(files_dir.glob("*.csv")) + list(files_dir.glob("*.xlsx")):
                            effective_user_id = user_dir.name
                            print(f"🔍 Auto-detected user: {effective_user_id}")
                            break
        
        if not effective_user_id:
            return {
                "status": "error",
                "message": "No data found. Please upload a dataset first.",
                "data": None,
                "raw_data": []
            }
        
        # Load user data
        df = load_user_data(effective_user_id)
        
        if df.empty:
            return {
                "status": "error",
                "message": "No data found. Please upload a dataset first.",
                "data": None,
                "raw_data": []
            }
        
        print(f"📊 Generating DASHBOARD for user {effective_user_id} with {len(df)} rows")
        
        # Generate Visual Intelligence - DASHBOARD MODE (different from overview!)
        result = engine.generate(df, mode='dashboard')
        
        # Convert numpy types first
        result = convert_numpy_types(result)
        
        # Convert data sample to frontend format
        raw_data = df.head(100).where(pd.notnull(df), None).to_dict(orient='records')
        raw_data = convert_numpy_types(raw_data)
        
        # Build dashboard response with the autonomous engine output
        dashboard_data = {
            "layout_spec": result.get("layout_spec", {"zones": [], "primary_focus": [], "grid_columns": 2, "aspect_ratios": []}),
            "visual_primitives": result.get("visual_primitives", []),
            "color_palette": result.get("color_palette", {
                "primary": ["#14b8a6", "#0ea5e9"],
                "secondary": ["#8b5cf6", "#f59e0b"],
                "accents": ["#22c55e", "#ef4444"],
                "background_gradient": ["#0f172a", "#1e293b"]
            }),
            "interaction_config": {
                "filters": [],
                "cross_highlight": {"enabled": False}
            },
            "behavior_scores": result.get("behavior_scores", {
                "density": 0.5,
                "complexity": 0.5,
                "volatility": 0.5,
                "temporal": 0.5,
                "sparsity": 0.5
            }),
            "narrative_elements": result.get("narrative_elements", []),
            "mode": "dashboard",
            "compiler_metadata": result.get("compiler_metadata", {})
        }
        
        return {
            "status": "success",
            "message": "Dashboard generated successfully with autonomous visual intelligence",
            "data": dashboard_data,
            "raw_data": raw_data
        }

    except Exception as e:
        print(f"❌ Error generating dashboard: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e),
            "data": None,
            "raw_data": []
        }
