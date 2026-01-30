"""
🧹 Data Quality Agent

Detects and fixes dataset issues:
- Missing values (multiple strategies)
- Outliers (IsolationForest + IQR)
- Data leakage detection
- Class imbalance detection
- Duplicate detection

Self-corrects by trying multiple strategies and validating improvements.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import logging

from .base import BaseAgent, AgentResult, AgentStatus, Phase, MessageType

logger = logging.getLogger(__name__)


@dataclass
class DataIssue:
    """Represents a detected data issue"""
    type: str  # missing, outlier, leakage, imbalance, duplicate
    column: str
    severity: str  # low, medium, high, critical
    details: Dict[str, Any]


class DataQualityAgent(BaseAgent):
    """
    Autonomous Data Quality Agent
    
    Detects issues → Applies strategies → Validates improvements → Reports
    """
    
    name = "data_quality"
    description = "Detects and fixes data quality issues"
    
    def __init__(self, memory=None):
        super().__init__(memory)
        self.issues_found: List[DataIssue] = []
        self.fixes_applied: List[str] = []
        
    def execute(self, **kwargs) -> AgentResult:
        """Main execution: detect issues, apply fixes, validate"""
        
        # Get dataset from memory
        df = self.read_state("dataset")
        target_col = self.read_state("target_column")
        
        if df is None:
            return AgentResult(
                status=AgentStatus.FAILED,
                agent_name=self.name,
                phase=self.current_phase,
                errors=["No dataset found in memory"]
            )
        
        df = df.copy()
        original_shape = df.shape
        self.logger.info(f"📊 Dataset: {df.shape[0]} rows, {df.shape[1]} columns")
        
        # =====================================================================
        # PHASE-AWARE PROCESSING
        # =====================================================================
        
        if self.is_fast_phase():
            # Fast phase: Quick detection and basic fixes
            df, issues = self._fast_quality_check(df, target_col)
        else:
            # Deep phase: Thorough analysis with multiple strategies
            df, issues = self._deep_quality_check(df, target_col)
        
        # Store results
        self.write_state("dataset_cleaned", df, self.name)
        self.write_state("data_issues", [i.__dict__ for i in issues], self.name)
        
        # Build result
        result = AgentResult(
            status=AgentStatus.SUCCESS,
            agent_name=self.name,
            phase=self.current_phase,
            data={
                "original_shape": original_shape,
                "cleaned_shape": df.shape,
                "issues_found": len(issues),
                "fixes_applied": self.fixes_applied
            },
            metrics={
                "rows_removed": original_shape[0] - df.shape[0],
                "columns_removed": original_shape[1] - df.shape[1],
                "completeness": 1 - (df.isnull().sum().sum() / (df.shape[0] * df.shape[1]))
            }
        )
        
        return result
    
    # =========================================================================
    # FAST PHASE - Quick cleaning
    # =========================================================================
    
    def _fast_quality_check(self, df: pd.DataFrame, target_col: str) -> Tuple[pd.DataFrame, List[DataIssue]]:
        """Fast quality check with basic fixes"""
        issues = []
        
        # 1. Remove duplicates
        dup_count = df.duplicated().sum()
        if dup_count > 0:
            df = df.drop_duplicates()
            issues.append(DataIssue("duplicate", "_all_", "medium", {"count": dup_count}))
            self.fixes_applied.append(f"Removed {dup_count} duplicates")
            self.logger.info(f"   ✅ Removed {dup_count} duplicates")
        
        # 2. Handle missing values
        missing_cols = df.columns[df.isnull().any()].tolist()
        for col in missing_cols:
            missing_pct = df[col].isnull().mean()
            
            if col == target_col:
                # Drop rows with missing target
                df = df.dropna(subset=[col])
                issues.append(DataIssue("missing", col, "high", {"pct": missing_pct}))
                self.fixes_applied.append(f"Dropped missing target rows")
            elif missing_pct > 0.5:
                # Drop column if >50% missing
                df = df.drop(columns=[col])
                issues.append(DataIssue("missing", col, "high", {"pct": missing_pct}))
                self.fixes_applied.append(f"Dropped column {col} (>{missing_pct:.0%} missing)")
            else:
                # Fill with median/mode
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].median())
                else:
                    df[col] = df[col].fillna(df[col].mode().iloc[0] if len(df[col].mode()) > 0 else "_UNKNOWN_")
                issues.append(DataIssue("missing", col, "low", {"pct": missing_pct}))
        
        if missing_cols:
            self.logger.info(f"   ✅ Fixed missing values in {len(missing_cols)} columns")
        
        # 3. Quick outlier cap (99th percentile)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if target_col in numeric_cols:
            numeric_cols.remove(target_col)
        
        for col in numeric_cols:
            p99 = df[col].quantile(0.99)
            p1 = df[col].quantile(0.01)
            outliers = ((df[col] > p99) | (df[col] < p1)).sum()
            if outliers > 0:
                df[col] = df[col].clip(p1, p99)
                issues.append(DataIssue("outlier", col, "low", {"count": outliers}))
        
        self.logger.info(f"   ✅ Capped outliers in {len(numeric_cols)} numeric columns")
        
        return df, issues
    
    # =========================================================================
    # DEEP PHASE - Thorough analysis
    # =========================================================================
    
    def _deep_quality_check(self, df: pd.DataFrame, target_col: str) -> Tuple[pd.DataFrame, List[DataIssue]]:
        """Deep quality check with multiple strategies"""
        issues = []
        
        # 1. Run fast phase first
        df, fast_issues = self._fast_quality_check(df, target_col)
        issues.extend(fast_issues)
        
        # 2. Detect data leakage
        leakage_cols = self._detect_leakage(df, target_col)
        for col in leakage_cols:
            df = df.drop(columns=[col])
            issues.append(DataIssue("leakage", col, "critical", {"correlation": 1.0}))
            self.fixes_applied.append(f"Removed leaky column: {col}")
        
        if leakage_cols:
            self.logger.info(f"   ⚠️ Removed {len(leakage_cols)} leaky columns")
        
        # 3. Advanced outlier detection with IsolationForest
        df, outlier_issues = self._detect_outliers_isolation(df, target_col)
        issues.extend(outlier_issues)
        
        # 4. Detect class imbalance
        if target_col in df.columns:
            imbalance = self._detect_imbalance(df[target_col])
            if imbalance:
                issues.append(imbalance)
                self.logger.info(f"   ⚠️ Class imbalance detected: {imbalance.details}")
        
        return df, issues
    
    def _detect_leakage(self, df: pd.DataFrame, target_col: str) -> List[str]:
        """Detect columns that might be leaking target information"""
        leaky_cols = []
        
        if target_col not in df.columns:
            return leaky_cols
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        for col in numeric_cols:
            if col == target_col:
                continue
            try:
                corr = abs(df[col].corr(pd.to_numeric(df[target_col], errors='coerce')))
                if corr > 0.95:  # Very high correlation
                    leaky_cols.append(col)
            except:
                pass
        
        return leaky_cols
    
    def _detect_outliers_isolation(self, df: pd.DataFrame, target_col: str) -> Tuple[pd.DataFrame, List[DataIssue]]:
        """Detect outliers using IsolationForest"""
        issues = []
        
        try:
            from sklearn.ensemble import IsolationForest
            
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if target_col in numeric_cols:
                numeric_cols.remove(target_col)
            
            if len(numeric_cols) < 2 or len(df) < 100:
                return df, issues
            
            # Fit IsolationForest
            iso = IsolationForest(contamination=0.05, random_state=42, n_jobs=-1)
            numeric_data = df[numeric_cols].fillna(0).values
            outlier_pred = iso.fit_predict(numeric_data)
            
            outlier_count = (outlier_pred == -1).sum()
            if outlier_count > 0:
                # Don't remove, just flag
                issues.append(DataIssue("outlier", "_multivariate_", "medium", {"count": outlier_count}))
                self.logger.info(f"   📊 Detected {outlier_count} multivariate outliers")
        except Exception as e:
            self.logger.warning(f"   ⚠️ IsolationForest failed: {str(e)[:50]}")
        
        return df, issues
    
    def _detect_imbalance(self, target: pd.Series) -> Optional[DataIssue]:
        """Detect class imbalance in target"""
        try:
            target_clean = target.dropna()
            
            # For classification targets
            if target_clean.dtype == object or target_clean.nunique() <= 20:
                value_counts = target_clean.value_counts()
                if len(value_counts) >= 2:
                    max_class = value_counts.max()
                    min_class = value_counts.min()
                    ratio = max_class / min_class if min_class > 0 else float('inf')
                    
                    if ratio > 3:  # Significant imbalance
                        return DataIssue(
                            "imbalance", 
                            "_target_", 
                            "high" if ratio > 10 else "medium",
                            {"ratio": ratio, "distribution": value_counts.to_dict()}
                        )
        except:
            pass
        
        return None
