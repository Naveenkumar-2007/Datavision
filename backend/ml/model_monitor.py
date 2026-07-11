import os
import json
import time
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Temporary in-memory telemetry store for Phase 4 scope
# Format: { deploy_id: { "requests": [...], "latency": [...], "payloads": [...] } }
TELEMETRY_STORE: Dict[str, Dict[str, Any]] = {}

class ModelMonitor:
    """Tracks real-time telemetry and calculates data drift for deployed models."""
    
    @staticmethod
    def initialize_telemetry(deploy_id: str):
        if deploy_id not in TELEMETRY_STORE:
            TELEMETRY_STORE[deploy_id] = {
                "requests": [],  # List of timestamps
                "latency": [],   # List of (timestamp, duration_ms)
                "payloads": []   # List of (timestamp, dict)
            }
            
    @staticmethod
    def log_inference(deploy_id: str, payload: Dict[str, Any], duration_ms: float):
        ModelMonitor.initialize_telemetry(deploy_id)
        now = datetime.now().isoformat()
        
        # Keep only last 1000 items to prevent memory leaks in this temp store
        TELEMETRY_STORE[deploy_id]["requests"].append(now)
        TELEMETRY_STORE[deploy_id]["requests"] = TELEMETRY_STORE[deploy_id]["requests"][-1000:]
        
        TELEMETRY_STORE[deploy_id]["latency"].append((now, duration_ms))
        TELEMETRY_STORE[deploy_id]["latency"] = TELEMETRY_STORE[deploy_id]["latency"][-1000:]
        
        TELEMETRY_STORE[deploy_id]["payloads"].append((now, payload))
        TELEMETRY_STORE[deploy_id]["payloads"] = TELEMETRY_STORE[deploy_id]["payloads"][-1000:]

    @staticmethod
    def get_metrics(deploy_id: str) -> Dict[str, Any]:
        """Returns time-series metrics for API usage and latency."""
        ModelMonitor.initialize_telemetry(deploy_id)
        store = TELEMETRY_STORE[deploy_id]
        
        # Total requests
        total_requests = len(store["requests"])
        
        # Average Latency
        latencies = [l[1] for l in store["latency"]]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        # Time-series data (group by minute)
        # For demo purposes, we will return a simulated timeseries if empty
        if total_requests == 0:
            return {
                "total_requests": 0,
                "avg_latency_ms": 0,
                "timeseries": []
            }
            
        timeseries = []
        for r_time, lat in store["latency"]:
            timeseries.append({
                "timestamp": r_time,
                "latency_ms": lat
            })
            
        return {
            "total_requests": total_requests,
            "avg_latency_ms": round(avg_latency, 2),
            "timeseries": timeseries
        }
        
    @staticmethod
    def calculate_drift(deploy_id: str, training_df: pd.DataFrame = None) -> List[Dict[str, Any]]:
        """
        Calculates data drift between training distribution and recent inference payloads.
        Simplified statistical divergence check.
        """
        ModelMonitor.initialize_telemetry(deploy_id)
        payloads = [p[1] for p in TELEMETRY_STORE[deploy_id]["payloads"]]
        
        if not payloads or training_df is None or training_df.empty:
            return []
            
        # Convert payloads to dataframe
        inference_df = pd.DataFrame(payloads)
        
        drift_alerts = []
        
        # Check numerical columns for mean shifts
        num_cols = training_df.select_dtypes(include=[np.number]).columns
        
        for col in num_cols:
            if col in inference_df.columns:
                train_mean = training_df[col].mean()
                inf_mean = pd.to_numeric(inference_df[col], errors='coerce').mean()
                
                if pd.notna(train_mean) and pd.notna(inf_mean) and train_mean != 0:
                    shift_pct = abs((inf_mean - train_mean) / train_mean)
                    if shift_pct > 0.2:  # 20% shift threshold
                        drift_alerts.append({
                            "feature": col,
                            "training_mean": float(train_mean),
                            "inference_mean": float(inf_mean),
                            "shift_percentage": float(shift_pct * 100),
                            "severity": "high" if shift_pct > 0.5 else "medium"
                        })
                        
        return drift_alerts
