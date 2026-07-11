from fastapi import APIRouter, Depends, Header, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import pandas as pd
import numpy as np
import os
import uuid
import datetime
from pathlib import Path

router = APIRouter()

class ColumnDef(BaseModel):
    name: str
    type: str # 'numerical', 'categorical', 'date', 'boolean'
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    categories: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    missing_pct: Optional[float] = 0.0

class SyntheticDataRequest(BaseModel):
    num_rows: int
    columns: List[ColumnDef]
    dataset_name: str

@router.post("/generate")
async def generate_synthetic_data(
    request: SyntheticDataRequest,
    x_user_id: str = Header(default="unknown")
) -> Dict[str, Any]:
    try:
        df = pd.DataFrame()
        n = request.num_rows
        
        for col in request.columns:
            if col.type == 'numerical':
                min_v = col.min_val if col.min_val is not None else 0.0
                max_v = col.max_val if col.max_val is not None else 100.0
                values = np.random.uniform(min_v, max_v, n)
            elif col.type == 'categorical':
                cats = col.categories if col.categories else ["A", "B", "C"]
                values = np.random.choice(cats, n)
            elif col.type == 'boolean':
                values = np.random.choice([True, False], n)
            elif col.type == 'date':
                start = pd.to_datetime(col.start_date if col.start_date else "2020-01-01")
                end = pd.to_datetime(col.end_date if col.end_date else "2023-12-31")
                delta = end - start
                # Generate random days to add
                random_days = np.random.randint(0, delta.days + 1, n)
                values = [start + pd.Timedelta(days=int(d)) for d in random_days]
            else:
                values = np.random.randn(n)

            # Inject missing values
            if col.missing_pct and 0 < col.missing_pct < 100:
                missing_mask = np.random.rand(n) < (col.missing_pct / 100.0)
                values = np.array(values, dtype=object)
                values[missing_mask] = np.nan

            df[col.name] = values

        # Save to user's directory
        user_dir = Path("storage") / x_user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        
        file_id = f"synth_{uuid.uuid4().hex[:8]}"
        filename = f"{request.dataset_name.strip() or 'synthetic_data'}.csv"
        # Ensure it ends with .csv
        if not filename.endswith(".csv"):
            filename += ".csv"
            
        file_path = user_dir / f"{file_id}_{filename}"
        
        df.to_csv(file_path, index=False)
        
        # Save metadata (similar to files.py logic)
        metadata = {
            "id": file_id,
            "name": filename,
            "type": "csv",
            "size": os.path.getsize(file_path),
            "uploadedAt": datetime.datetime.utcnow().isoformat(),
            "status": "completed",
            "path": str(file_path),
            "is_synthetic": True
        }
        
        # In a real system, you'd add this to a DB. 
        # Here we just return it so frontend can handle it or assume it's loaded via files.py index scan.
        return {
            "success": True,
            "message": "Synthetic data generated successfully.",
            "file": metadata,
            "preview_rows": df.head(5).to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate data: {str(e)}")
