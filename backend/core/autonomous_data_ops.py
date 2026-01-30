"""
🤖 AUTONOMOUS DATA OPERATIONS - Auto-Fix & Enhancement Engine
===============================================================

Automatically fixes and enhances data quality:
- Missing value imputation (smart strategies)
- Outlier detection and handling
- Data type corrections
- Duplicate removal
- Auto-enrichment (date features, currency, geolocation)
- Schema validation and evolution

This module runs autonomously on data upload to ensure clean, ready-to-analyze data.
"""

import pandas as pd
import numpy as np
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class DataFixResult:
    """Result from an autonomous data fix operation"""
    operation: str
    column: Optional[str]
    rows_affected: int
    description: str
    before_value: Optional[Any] = None
    after_value: Optional[Any] = None


@dataclass
class AutoFixReport:
    """Complete report of all autonomous fixes applied"""
    original_rows: int
    original_cols: int
    final_rows: int
    final_cols: int
    fixes_applied: List[DataFixResult] = field(default_factory=list)
    enrichments_added: List[str] = field(default_factory=list)
    quality_score_before: float = 0.0
    quality_score_after: float = 0.0
    processing_time_ms: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "original_shape": {"rows": self.original_rows, "cols": self.original_cols},
            "final_shape": {"rows": self.final_rows, "cols": self.final_cols},
            "fixes_applied": [
                {
                    "operation": f.operation,
                    "column": f.column,
                    "rows_affected": f.rows_affected,
                    "description": f.description
                } for f in self.fixes_applied
            ],
            "enrichments_added": self.enrichments_added,
            "quality_improvement": {
                "before": round(self.quality_score_before, 2),
                "after": round(self.quality_score_after, 2),
                "improvement": round(self.quality_score_after - self.quality_score_before, 2)
            },
            "processing_time_ms": self.processing_time_ms
        }


class AutonomousDataOps:
    """
    🤖 Autonomous Data Operations Engine
    
    Automatically detects and fixes data quality issues:
    1. Missing Value Imputation
    2. Outlier Detection & Handling
    3. Data Type Corrections
    4. Duplicate Removal
    5. Data Enrichment
    """
    
    def __init__(self):
        self.fix_history: List[DataFixResult] = []
    
    def auto_fix(
        self,
        df: pd.DataFrame,
        fix_missing: bool = True,
        fix_outliers: bool = True,
        fix_duplicates: bool = True,
        fix_types: bool = True,
        enrich_dates: bool = True,
        aggressive: bool = False
    ) -> Tuple[pd.DataFrame, AutoFixReport]:
        """
        🚀 Main entry point - Automatically fix all data issues.
        
        Args:
            df: Input DataFrame
            fix_missing: Impute missing values
            fix_outliers: Cap/handle outliers
            fix_duplicates: Remove duplicate rows
            fix_types: Correct data types
            enrich_dates: Add date-based features
            aggressive: Apply more aggressive fixes
        
        Returns:
            Tuple of (fixed DataFrame, AutoFixReport)
        """
        start_time = datetime.now()
        
        # Initialize report
        report = AutoFixReport(
            original_rows=len(df),
            original_cols=len(df.columns),
            quality_score_before=self._calculate_quality_score(df)
        )
        
        # Make a copy to avoid modifying original
        df_fixed = df.copy()
        
        logger.info(f"🤖 Starting Autonomous Data Fix ({len(df)} rows, {len(df.columns)} cols)")
        
        # Step 1: Remove duplicates
        if fix_duplicates:
            df_fixed, dup_fixes = self._fix_duplicates(df_fixed)
            report.fixes_applied.extend(dup_fixes)
        
        # Step 2: Fix data types
        if fix_types:
            df_fixed, type_fixes = self._fix_data_types(df_fixed)
            report.fixes_applied.extend(type_fixes)
        
        # Step 3: Handle missing values
        if fix_missing:
            df_fixed, missing_fixes = self._fix_missing_values(df_fixed, aggressive)
            report.fixes_applied.extend(missing_fixes)
        
        # Step 4: Handle outliers
        if fix_outliers:
            df_fixed, outlier_fixes = self._fix_outliers(df_fixed, aggressive)
            report.fixes_applied.extend(outlier_fixes)
        
        # Step 5: Enrich data (add derived features)
        if enrich_dates:
            df_fixed, enrichments = self._enrich_data(df_fixed)
            report.enrichments_added.extend(enrichments)
        
        # Calculate final metrics
        report.final_rows = len(df_fixed)
        report.final_cols = len(df_fixed.columns)
        report.quality_score_after = self._calculate_quality_score(df_fixed)
        report.processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        logger.info(f"✅ Auto-fix complete: {len(report.fixes_applied)} fixes, "
                   f"quality {report.quality_score_before:.0%} → {report.quality_score_after:.0%}")
        
        return df_fixed, report
    
    # =========================================================================
    # DUPLICATE HANDLING
    # =========================================================================
    
    def _fix_duplicates(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[DataFixResult]]:
        """Remove duplicate rows"""
        fixes = []
        
        n_duplicates = df.duplicated().sum()
        if n_duplicates > 0:
            df = df.drop_duplicates().reset_index(drop=True)
            fixes.append(DataFixResult(
                operation="remove_duplicates",
                column=None,
                rows_affected=n_duplicates,
                description=f"Removed {n_duplicates} duplicate rows"
            ))
            logger.info(f"   🗑️ Removed {n_duplicates} duplicate rows")
        
        return df, fixes
    
    # =========================================================================
    # DATA TYPE CORRECTIONS
    # =========================================================================
    
    def _fix_data_types(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[DataFixResult]]:
        """Automatically correct data types"""
        fixes = []
        
        for col in df.columns:
            original_dtype = str(df[col].dtype)
            
            # Try to detect and convert types
            if df[col].dtype == 'object':
                # Try numeric conversion
                numeric_converted = self._try_convert_numeric(df[col])
                if numeric_converted is not None:
                    df[col] = numeric_converted
                    fixes.append(DataFixResult(
                        operation="convert_to_numeric",
                        column=col,
                        rows_affected=len(df),
                        description=f"Converted '{col}' from {original_dtype} to numeric"
                    ))
                    continue
                
                # Try datetime conversion
                date_converted = self._try_convert_datetime(df[col])
                if date_converted is not None:
                    df[col] = date_converted
                    fixes.append(DataFixResult(
                        operation="convert_to_datetime",
                        column=col,
                        rows_affected=len(df),
                        description=f"Converted '{col}' from {original_dtype} to datetime"
                    ))
                    continue
                
                # Try boolean conversion
                bool_converted = self._try_convert_boolean(df[col])
                if bool_converted is not None:
                    df[col] = bool_converted
                    fixes.append(DataFixResult(
                        operation="convert_to_boolean",
                        column=col,
                        rows_affected=len(df),
                        description=f"Converted '{col}' from {original_dtype} to boolean"
                    ))
        
        return df, fixes
    
    def _try_convert_numeric(self, series: pd.Series) -> Optional[pd.Series]:
        """Try to convert a series to numeric"""
        try:
            # Remove common formatting (currency, commas)
            cleaned = series.astype(str).str.replace(r'[$,€£¥₹%]', '', regex=True)
            cleaned = cleaned.str.strip()
            
            # Convert to numeric
            numeric = pd.to_numeric(cleaned, errors='coerce')
            
            # Only convert if >80% are valid numbers
            valid_ratio = numeric.notna().sum() / len(series)
            if valid_ratio > 0.8 and series.notna().sum() > 0:
                return numeric
        except:
            pass
        return None
    
    def _try_convert_datetime(self, series: pd.Series) -> Optional[pd.Series]:
        """Try to convert a series to datetime"""
        try:
            # Check if column name suggests date
            col_name = series.name.lower() if series.name else ""
            date_keywords = ['date', 'time', 'created', 'updated', 'timestamp', 'dt']
            
            if not any(kw in col_name for kw in date_keywords):
                return None
            
            # Try conversion
            dates = pd.to_datetime(series, errors='coerce', infer_datetime_format=True)
            
            # Only convert if >70% are valid dates
            valid_ratio = dates.notna().sum() / len(series)
            if valid_ratio > 0.7:
                return dates
        except:
            pass
        return None
    
    def _try_convert_boolean(self, series: pd.Series) -> Optional[pd.Series]:
        """Try to convert a series to boolean"""
        try:
            unique_vals = set(series.dropna().astype(str).str.lower().str.strip())
            
            true_vals = {'true', 'yes', 'y', '1', 'on', 'active'}
            false_vals = {'false', 'no', 'n', '0', 'off', 'inactive'}
            
            if unique_vals.issubset(true_vals | false_vals) and len(unique_vals) <= 2:
                return series.astype(str).str.lower().str.strip().isin(true_vals)
        except:
            pass
        return None
    
    # =========================================================================
    # MISSING VALUE HANDLING
    # =========================================================================
    
    def _fix_missing_values(
        self, 
        df: pd.DataFrame, 
        aggressive: bool = False
    ) -> Tuple[pd.DataFrame, List[DataFixResult]]:
        """Smart imputation of missing values"""
        fixes = []
        
        for col in df.columns:
            n_missing = df[col].isna().sum()
            if n_missing == 0:
                continue
            
            missing_pct = n_missing / len(df)
            
            # Skip if too many missing (>50% for non-aggressive, >80% for aggressive)
            threshold = 0.8 if aggressive else 0.5
            if missing_pct > threshold:
                if aggressive:
                    # Drop column entirely
                    df = df.drop(columns=[col])
                    fixes.append(DataFixResult(
                        operation="drop_column",
                        column=col,
                        rows_affected=len(df),
                        description=f"Dropped column '{col}' ({missing_pct:.0%} missing)"
                    ))
                continue
            
            # Choose imputation strategy based on data type
            if pd.api.types.is_numeric_dtype(df[col]):
                # Numeric: use median (robust to outliers)
                fill_value = df[col].median()
                df[col] = df[col].fillna(fill_value)
                strategy = "median"
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                # Datetime: forward fill or use mode
                df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
                strategy = "forward/backward fill"
            else:
                # Categorical/text: use mode (most frequent)
                mode_val = df[col].mode()
                fill_value = mode_val.iloc[0] if len(mode_val) > 0 else "Unknown"
                df[col] = df[col].fillna(fill_value)
                strategy = "mode"
            
            fixes.append(DataFixResult(
                operation="impute_missing",
                column=col,
                rows_affected=n_missing,
                description=f"Imputed {n_missing} missing values in '{col}' using {strategy}"
            ))
            logger.info(f"   🔧 Imputed {n_missing} missing in '{col}' ({strategy})")
        
        return df, fixes
    
    # =========================================================================
    # OUTLIER HANDLING
    # =========================================================================
    
    def _fix_outliers(
        self, 
        df: pd.DataFrame, 
        aggressive: bool = False
    ) -> Tuple[pd.DataFrame, List[DataFixResult]]:
        """Detect and handle outliers in numeric columns"""
        fixes = []
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            # Skip columns with too few unique values (likely categorical encoded as numeric)
            if df[col].nunique() < 10:
                continue
            
            # Calculate IQR bounds
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            
            if iqr == 0:
                continue
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            # Find outliers
            outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
            n_outliers = outliers.sum()
            
            if n_outliers > 0 and n_outliers < len(df) * 0.1:  # Cap if <10% are outliers
                # Winsorize (cap at percentiles)
                if aggressive:
                    # Remove outlier rows
                    df = df[~outliers]
                    fixes.append(DataFixResult(
                        operation="remove_outliers",
                        column=col,
                        rows_affected=n_outliers,
                        description=f"Removed {n_outliers} outlier rows from '{col}'"
                    ))
                else:
                    # Cap outliers at bounds (winsorizing)
                    p1, p99 = df[col].quantile([0.01, 0.99])
                    df[col] = df[col].clip(lower=p1, upper=p99)
                    fixes.append(DataFixResult(
                        operation="cap_outliers",
                        column=col,
                        rows_affected=n_outliers,
                        description=f"Capped {n_outliers} outliers in '{col}' to [1st, 99th] percentile"
                    ))
                    logger.info(f"   📊 Capped {n_outliers} outliers in '{col}'")
        
        return df, fixes
    
    # =========================================================================
    # DATA ENRICHMENT
    # =========================================================================
    
    def _enrich_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Add derived features to enrich the data"""
        enrichments = []
        
        # Enrich datetime columns
        datetime_cols = df.select_dtypes(include=['datetime64']).columns
        
        for col in datetime_cols:
            base_name = col.replace('_date', '').replace('date_', '').replace('Date', '')
            
            # Extract year, month, day, weekday
            if f"{base_name}_year" not in df.columns:
                df[f"{base_name}_year"] = df[col].dt.year
                enrichments.append(f"{base_name}_year")
            
            if f"{base_name}_month" not in df.columns:
                df[f"{base_name}_month"] = df[col].dt.month
                enrichments.append(f"{base_name}_month")
            
            if f"{base_name}_day_of_week" not in df.columns:
                df[f"{base_name}_day_of_week"] = df[col].dt.dayofweek
                enrichments.append(f"{base_name}_day_of_week")
            
            if f"{base_name}_is_weekend" not in df.columns:
                df[f"{base_name}_is_weekend"] = df[col].dt.dayofweek >= 5
                enrichments.append(f"{base_name}_is_weekend")
            
            logger.info(f"   ✨ Enriched datetime column '{col}' with {len(enrichments)} features")
        
        # Detect and create interaction features for important columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Create ratios for common patterns
        if 'price' in [c.lower() for c in numeric_cols] and 'quantity' in [c.lower() for c in numeric_cols]:
            price_col = [c for c in numeric_cols if 'price' in c.lower()][0]
            qty_col = [c for c in numeric_cols if 'quantity' in c.lower()][0]
            if 'total_value' not in df.columns:
                df['total_value'] = df[price_col] * df[qty_col]
                enrichments.append('total_value')
        
        return df, enrichments
    
    # =========================================================================
    # QUALITY SCORING
    # =========================================================================
    
    def _calculate_quality_score(self, df: pd.DataFrame) -> float:
        """Calculate data quality score (0-1)"""
        if len(df) == 0 or len(df.columns) == 0:
            return 0.0
        
        scores = []
        
        # Completeness: % non-missing
        total_cells = len(df) * len(df.columns)
        missing_cells = df.isna().sum().sum()
        completeness = 1 - (missing_cells / total_cells)
        scores.append(completeness)
        
        # Uniqueness: % non-duplicate rows
        n_duplicates = df.duplicated().sum()
        uniqueness = 1 - (n_duplicates / len(df))
        scores.append(uniqueness)
        
        # Consistency: % of columns with consistent types
        type_consistent = sum(1 for col in df.columns 
                             if df[col].apply(type).nunique() <= 2)
        consistency = type_consistent / len(df.columns)
        scores.append(consistency)
        
        # Weighted average
        return np.average(scores, weights=[0.4, 0.3, 0.3])
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def detect_issues(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """Detect data quality issues without fixing them"""
        issues = {
            "missing_values": [],
            "duplicates": [],
            "outliers": [],
            "type_issues": []
        }
        
        # Check missing values
        for col in df.columns:
            missing_pct = df[col].isna().mean()
            if missing_pct > 0.05:
                issues["missing_values"].append(f"{col}: {missing_pct:.1%} missing")
        
        # Check duplicates
        n_dups = df.duplicated().sum()
        if n_dups > 0:
            issues["duplicates"].append(f"{n_dups} duplicate rows ({n_dups/len(df):.1%})")
        
        # Check outliers in numeric columns
        for col in df.select_dtypes(include=[np.number]).columns:
            if df[col].nunique() > 10:
                q1, q3 = df[col].quantile([0.25, 0.75])
                iqr = q3 - q1
                if iqr > 0:
                    outliers = ((df[col] < q1 - 1.5*iqr) | (df[col] > q3 + 1.5*iqr)).sum()
                    if outliers > len(df) * 0.01:
                        issues["outliers"].append(f"{col}: {outliers} outliers ({outliers/len(df):.1%})")
        
        return issues
    
    def get_fix_recommendation(self, df: pd.DataFrame) -> str:
        """Get human-readable fix recommendations"""
        issues = self.detect_issues(df)
        
        recommendations = []
        
        if issues["duplicates"]:
            recommendations.append(f"🗑️ Remove {issues['duplicates'][0]}")
        
        if issues["missing_values"]:
            recommendations.append(f"🔧 Fill missing values in {len(issues['missing_values'])} columns")
        
        if issues["outliers"]:
            recommendations.append(f"📊 Handle outliers in {len(issues['outliers'])} columns")
        
        if not recommendations:
            return "✅ Data looks clean! No major issues detected."
        
        return "\n".join(recommendations)


# Global instance
autonomous_data_ops = AutonomousDataOps()
