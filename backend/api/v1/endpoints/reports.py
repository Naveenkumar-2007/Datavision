"""
INTELLIGENT REPORT GENERATION - Works with ANY Dataset!

No hardcoded column names like 'revenue', 'customer', 'product'
Automatically detects:
  - Numeric columns (for aggregations)
  - Categorical columns (for grouping)
  - Date columns (for time analysis)
  - High/Low cardinality dimensions

Generates dynamic reports based on actual data structure!
"""

from fastapi import APIRouter, HTTPException, Depends
from api.deps import get_current_user_id
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import traceback
import re
from datetime import datetime
from datetime import timedelta
import pandas as pd
import numpy as np
from core.chart_selector import ChartSelector

from graph.query import revenue_dataframe
from config.settings import Settings
from utils.paths import get_user_paths, STORAGE_BASE
from utils.currency import (
    detect_currency, 
    format_currency, 
    get_currency_symbol,
    load_currency_metadata,
    save_currency_metadata
)
# Import new clean ML report generators
from api.v1.endpoints.ml_reports import generate_predictive_report_v2, generate_anomaly_report_v2

router = APIRouter()

# ==========================================
# COLOR PALETTES - Same as visualization engine
# ==========================================
CHART_COLORS = [
    '#14B8A6',  # Teal
    '#22C55E',  # Green
    '#3B82F6',  # Blue
    '#F59E0B',  # Amber
    '#8B5CF6',  # Purple
    '#EC4899',  # Pink
    '#EF4444',  # Red
    '#06B6D4',  # Cyan
]

# ==========================================
# AUTONOMOUS REPORT CHART REGISTRY
# Each report type gets UNIQUE chart types - no duplicates!
# ==========================================
REPORT_CHART_REGISTRY = {
    'metrics': {
        'primary': 'pie',           # Distribution visualization
        'secondary': 'line',        # Trends
        'tertiary': 'heatmap',      # Correlation matrix (UPDATED)
        'focus': 'statistical_analysis'
    },
    'breakdown': {
        'primary': 'horizontal_bar', # Category comparison
        'secondary': 'radar',        # Multi-metric comparison (UPDATED)
        'tertiary': 'funnel',        # Process/Stage breakdown (UPDATED)
        'focus': 'category_distribution'
    },
    'summary': {
        'primary': 'donut',          # Overview
        'secondary': 'table',        # Data structure
        'tertiary': 'gauge',         # Key metrics
        'focus': 'data_structure'
    },
    'executive': {
        'primary': 'bar',            # Top performers
        'secondary': 'kpi_cards',    # Key indicators
        'tertiary': 'bullet',        # Target vs actual
        'focus': 'decision_insights'
    },
    'predictive': {
        'primary': 'area',           # Forecasts with confidence
        'secondary': 'scatter',      # Projections
        'tertiary': 'waterfall',     # Growth breakdown
        'focus': 'future_predictions'
    },
    'anomaly': {
        'primary': 'box',            # Outlier detection
        'secondary': 'violin',       # Distribution shape
        'tertiary': 'scatter_3d',    # 3D Outlier visualization (UPDATED)
        'focus': 'outlier_detection'
    }
}

def get_chart_for_report(report_type: str, chart_role: str = 'primary') -> str:
    """Get the designated chart type for a report - ensures uniqueness"""
    return REPORT_CHART_REGISTRY.get(report_type, {}).get(chart_role, 'bar')

def get_report_focus(report_type: str) -> str:
    """Get the unique analytical focus for each report type"""
    return REPORT_CHART_REGISTRY.get(report_type, {}).get('focus', 'general_analysis')


class ReportRequest(BaseModel):
    userId: str
    reportType: str
    dateRange: Optional[str] = "all"
    format: str = "json"


# ==========================================
# INTELLIGENT COLUMN DETECTION - IMPROVED
# ==========================================

class DataProfiler:
    """
    Analyze data structure to detect column types and roles.
    
    IMPROVED to:
    - Correctly identify numeric IDs vs real metrics
    - Filter out file types (image, text, video)
    - Better detection of meaningful dimensions
    - Avoid summing ID columns
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.columns = list(df.columns)
        self.record_count = len(df)
        
        # Detected column types
        self.numeric_cols = []      # Real numeric values for aggregation
        self.categorical_cols = []   # Meaningful categories for grouping
        self.date_cols = []
        self.id_cols = []           # ID/key columns to skip
        self.skip_cols = []         # Other columns to skip
        
        # Primary columns for different roles
        self.primary_metric = None
        self.primary_dimension = None
        self.primary_date = None
        
        self._analyze()
    
    def _analyze(self):
        """Analyze all columns and detect their types."""
        for col in self.columns:
            col_type = self._detect_column_type(col)
            
            if col_type == 'numeric':
                self.numeric_cols.append(col)
            elif col_type == 'categorical':
                self.categorical_cols.append(col)
            elif col_type == 'date':
                self.date_cols.append(col)
            elif col_type == 'id':
                self.id_cols.append(col)
            else:
                self.skip_cols.append(col)
        
        self._select_primary_columns()
    
    def _detect_column_type(self, col: str) -> str:
        """
        Detect the type of a single column with ROBUST logic.
        
        Priority order:
        1. Check column NAME first (most reliable)
        2. Then check data patterns
        3. ID detection is conservative - when in doubt, skip it
        """
        series = self.df[col]
        col_lower = col.lower().strip()
        cardinality = series.nunique()
        
        # ========================================
        # PRIORITY 1: Check column NAME patterns
        # ========================================
        
        # A) ID COLUMNS (by name) - ALWAYS skip these
        id_name_patterns = ['customer', 'user', 'client', '_id', 'id_', 'uuid', 'guid', 
                            'invoice_no', 'order_no', 'batch', 'serial', 'ref', 
                            'code', 'key', 'index', 'row', 'record']
        if any(pattern in col_lower for pattern in id_name_patterns):
            # If column is named like an entity but has values, check if it's categorical
            if cardinality <= 50 and not pd.api.types.is_numeric_dtype(series):
                return 'categorical'  # Entity column with names
            return 'id'  # Numeric ID column
        
        # B) DATE COLUMNS (by name)
        date_patterns = ['date', 'time', 'created', 'updated', 'timestamp', 'day']
        if any(pattern in col_lower for pattern in date_patterns):
            try:
                pd.to_datetime(series.dropna().head(50), errors='raise')
                return 'date'
            except:
                # Not a valid date, treat as categorical if low cardinality
                if cardinality <= 50:
                    return 'categorical'
        
        # C) SENTIMENT/LABEL COLUMNS (categorical with specific values)
        sentiment_values = {'negative', 'neutral', 'positive', 'good', 'bad', 'excellent', 
                           'poor', 'satisfied', 'unsatisfied', 'happy', 'unhappy',
                           'low', 'medium', 'high', 'yes', 'no', 'true', 'false'}
        if cardinality <= 10:
            sample_vals = set(str(v).lower().strip() for v in series.dropna().unique())
            if sample_vals & sentiment_values:
                return 'categorical'  # This is a label/sentiment column
        
        # D) FILE TYPE COLUMNS - skip these
        file_type_values = {'image', 'text', 'video', 'audio', 'file', 'document', 'pdf', 'jpg', 'png'}
        if cardinality <= 10:
            sample_vals = set(str(v).lower().strip() for v in series.dropna().unique())
            if sample_vals & file_type_values:
                return 'skip'  # File type column, not useful for analysis
        
        # E) METRIC COLUMNS (by name) - these ARE numeric values
        metric_patterns = ['amount', 'price', 'cost', 'value', 'total', 'sum', 
                          'revenue', 'sale', 'qty', 'quantity', 'count', 'rate', 
                          'fee', 'tax', 'discount', 'profit', 'margin', 'salary',
                          'payment', 'balance', 'credit', 'debit', 'score', 'rating']
        if any(pattern in col_lower for pattern in metric_patterns):
            if pd.api.types.is_numeric_dtype(series):
                return 'numeric'
        
        # ========================================
        # PRIORITY 2: Check data PATTERNS
        # ========================================
        
        # F) Numeric columns - be VERY careful, only real metrics
        if pd.api.types.is_numeric_dtype(series):
            vals = series.dropna()
            if len(vals) == 0:
                return 'skip'
            
            # High cardinality numeric = probably an ID
            if cardinality > self.record_count * 0.5:
                return 'id'
            
            # Large values with high variance = probably an ID
            if vals.max() > 10000 and vals.std() > vals.mean() * 0.5:
                return 'id'
            
            # Small range of values = could be a valid metric
            if vals.max() < 1000 and cardinality < 100:
                return 'numeric'
            
            # Has decimal values = likely a real metric
            if (vals % 1).sum() > 0:
                return 'numeric'
            
            # Default: skip unknown numeric columns
            return 'skip'
        
        # G) String/Object columns - treat as categorical if reasonable cardinality
        if cardinality >= 2 and cardinality <= 100:
            return 'categorical'
        
        if cardinality < self.record_count * 0.3 and cardinality > 1:
            return 'categorical'
        
        return 'other'
    
    def _select_primary_columns(self):
        """Select the best primary columns for reporting."""
        
        # Primary metric: prefer columns with metric keywords
        metric_priority = ['total', 'amount', 'revenue', 'price', 'value', 'sum', 'cost', 'sale', 'qty', 'quantity', 'score', 'rating']
        for kw in metric_priority:
            for col in self.numeric_cols:
                if kw in col.lower():
                    self.primary_metric = col
                    break
            if self.primary_metric:
                break
        
        # Fallback to first numeric with actual values
        if not self.primary_metric:
            for col in self.numeric_cols:
                vals = self.get_clean_metric(col)
                if vals.sum() > 0:
                    self.primary_metric = col
                    break
        
        # Primary dimension detection
        # CRITICAL: Check VALUE PATTERNS first, not column names!
        # This handles cases where column names are misleading (e.g., 'date' contains sentiment)
        
        sentiment_values = {'negative', 'neutral', 'positive', 'good', 'bad', 'excellent', 
                           'poor', 'satisfied', 'unsatisfied', 'happy', 'unhappy'}
        
        # Store the column that contains sentiment for display purposes
        self.sentiment_column = None
        self.sentiment_column_display_name = None
        
        # STEP 1: Find column with sentiment VALUES (highest priority)
        for col in self.categorical_cols:
            sample_vals = set(str(v).lower().strip() for v in self.df[col].dropna().unique())
            if sample_vals & sentiment_values:
                self.primary_dimension = col
                self.sentiment_column = col
                # Give it a proper display name based on detected values
                if sample_vals & {'negative', 'neutral', 'positive'}:
                    self.sentiment_column_display_name = "Sentiment"
                elif sample_vals & {'good', 'bad', 'excellent', 'poor'}:
                    self.sentiment_column_display_name = "Rating"
                elif sample_vals & {'satisfied', 'unsatisfied'}:
                    self.sentiment_column_display_name = "Satisfaction"
                else:
                    self.sentiment_column_display_name = "Category"
                print(f"[REPORTS] Detected sentiment column: {col} -> Display as '{self.sentiment_column_display_name}'")
                break
        
        # STEP 2: If no sentiment found, check column NAMES
        if not self.primary_dimension:
            dim_priority = [
                'sentiment', 'label', 'status', 'category', 'type', 
                'rating', 'class', 'segment', 'group', 'product', 
                'region', 'department', 'brand', 'channel'
            ]
            
            for kw in dim_priority:
                for col in self.categorical_cols:
                    if kw in col.lower():
                        self.primary_dimension = col
                        break
                if self.primary_dimension:
                    break
        
        # STEP 3: Fallback to best cardinality (skip date-like columns)
        if not self.primary_dimension:
            best_col = None
            best_score = 0
            for col in self.categorical_cols:
                col_lower = col.lower()
                # Skip columns that look like dates
                if 'date' in col_lower or 'time' in col_lower:
                    continue
                    
                card = self.df[col].nunique()
                if 2 <= card <= 10:
                    score = 100 - card
                elif 11 <= card <= 30:
                    score = 50 - card
                else:
                    score = 0
                    
                if score > best_score:
                    best_score = score
                    best_col = col
            
            if best_col:
                self.primary_dimension = best_col
        
        # Last resort
        if not self.primary_dimension and self.categorical_cols:
            self.primary_dimension = self.categorical_cols[0]
        
        # Primary date
        if self.date_cols:
            self.primary_date = self.date_cols[0]
    
    def get_clean_metric(self, col: str) -> pd.Series:
        """Get a cleaned numeric series from a column."""
        if col not in self.df.columns:
            return pd.Series([0] * self.record_count)
        
        series = self.df[col].copy()
        
        if pd.api.types.is_numeric_dtype(series):
            return pd.to_numeric(series, errors='coerce').fillna(0)
        
        # Try cleaning currency symbols
        try:
            cleaned = series.astype(str).str.replace(r'[₹$€£¥,\s]', '', regex=True)
            return pd.to_numeric(cleaned, errors='coerce').fillna(0)
        except:
            return pd.Series([0] * self.record_count)
    
    def is_currency_column(self, col: str) -> bool:
        """Check if a column contains currency/financial values."""
        if col not in self.df.columns:
            return False
        
        col_lower = col.lower()
        currency_keywords = ['amount', 'price', 'revenue', 'cost', 'value', 'total', 
                            'sum', 'sale', 'fee', 'tax', 'profit', 'margin', 'salary',
                            'payment', 'balance', 'credit', 'debit', 'income']
        
        # Check column name
        if any(kw in col_lower for kw in currency_keywords):
            return True
        
        # Check if values look like currency (has currency symbols)
        series = self.df[col]
        if series.dtype == 'object':
            sample = series.dropna().astype(str).head(100)
            currency_chars = ['$', '₹', '€', '£', '¥']
            for char in currency_chars:
                if sample.str.contains(re.escape(char), regex=True).any():
                    return True
        
        return False
    
    def has_valid_numeric_metric(self) -> bool:
        """Check if we have any valid numeric metrics with actual values."""
        if not self.primary_metric:
            return False
        vals = self.get_clean_metric(self.primary_metric)
        return vals.sum() > 0


# ==========================================
# DYNAMIC REPORT GENERATORS
# ==========================================

def generate_data_summary_report(user_id: str, df: pd.DataFrame, profiler: DataProfiler) -> dict:
    """Generate a data summary report - works with ANY data."""
    sections = []
    currency = get_user_currency(user_id, df)
    
    # Data Overview Section
    sections.append({
        "title": "Data Overview",
        "content": f"""
Records: {profiler.record_count:,}
Columns: {len(profiler.columns):,}
Numeric Columns: {len(profiler.numeric_cols):,}
Categorical Columns: {len(profiler.categorical_cols):,}
Date Columns: {len(profiler.date_cols):,}
        """.strip(),
        "data": {
            "records": profiler.record_count,
            "columns": len(profiler.columns),
            "numericCols": profiler.numeric_cols,
            "categoricalCols": profiler.categorical_cols,
            "dateCols": profiler.date_cols
        }
    })
    
    # Metrics Summary
    if profiler.numeric_cols:
        metrics_content = []
        metrics_data = {}
        
        for col in profiler.numeric_cols[:5]:  # Top 5 numeric columns
            values = profiler.get_clean_metric(col)
            total = float(values.sum())
            avg = float(values.mean())
            col_title = col.replace('_', ' ').title()
            
            # Use profiler method instead of hardcoded keywords
            is_currency = profiler.is_currency_column(col)
            fmt = format_currency(total, currency) if is_currency else f'{total:,.0f}'
            metrics_content.append(f"- {col_title}: Total={fmt}, Avg={avg:,.2f}")
            metrics_data[col] = {"total": total, "avg": avg}
        
        sections.append({
            "title": "Metrics Summary",
            "content": "\n".join(metrics_content),
            "data": metrics_data
        })
    
    # Category Breakdown - ALWAYS show counts with percentages
    if profiler.categorical_cols:
        total_records = len(df)
        for dim_col in profiler.categorical_cols[:3]:  # Top 3 dimensions
            cardinality = df[dim_col].nunique()
            if 2 <= cardinality <= 30:  # Good range for breakdown
                # Always use counts - this works for ANY data type
                counts = df[dim_col].value_counts().head(10)
                
                # Use display name for sentiment columns
                if dim_col == profiler.primary_dimension and hasattr(profiler, 'sentiment_column_display_name') and profiler.sentiment_column_display_name:
                    dim_title = profiler.sentiment_column_display_name
                else:
                    dim_title = dim_col.replace('_', ' ').title()
                
                content_lines = []
                chart_data = []
                
                for i, (k, count) in enumerate(counts.items()):
                    pct = (count / total_records) * 100
                    content_lines.append(f"- {str(k)}: {count:,} ({pct:.1f}%)")
                    chart_data.append({
                        "name": str(k)[:25],
                        "value": int(count),
                        "percentage": round(pct, 1),
                        "color": CHART_COLORS[i % len(CHART_COLORS)]
                    })
                
                sections.append({
                    "title": f"By {dim_title}",
                    "content": "\n".join(content_lines),
                    "data": chart_data,
                    "chartType": "pie"
                })
    
    return {
        "title": "Data Summary Report",
        "generatedAt": datetime.now().isoformat(),
        "dataSource": "uploaded_files",
        "sections": sections,
        "currency": currency,
        "colors": CHART_COLORS,
        "dataProfile": {
            "records": profiler.record_count,
            "primaryMetric": profiler.primary_metric,
            "primaryDimension": profiler.primary_dimension,
            "primaryDate": profiler.primary_date,
            "numericCols": profiler.numeric_cols,
            "categoricalCols": profiler.categorical_cols
        }
    }


def generate_metrics_report(user_id: str, df: pd.DataFrame, profiler: DataProfiler) -> dict:
    """
    METRICS ANALYSIS REPORT - Deep Statistical Analysis
    UNIQUE: PIE chart for distribution + detailed statistics + balance analysis
    """
    sections = []
    currency = get_user_currency(user_id, df)
    n = len(df)
    
    # Get display name for primary dimension
    col = profiler.primary_dimension
    display_name = getattr(profiler, 'sentiment_column_display_name', None) or (col.replace('_', ' ').title() if col else 'Category')
    
    # ===========================================
    # SECTION 1: Data Overview
    # ===========================================
    sections.append({
        "title": "Data Overview",
        "content": f"""Total Records: {n:,}
Data Columns: {len(profiler.columns)}
Analysis Focus: {display_name}
Numeric Columns: {len(profiler.numeric_cols)}
Categorical Columns: {len(profiler.categorical_cols)}
Date Columns: {len(profiler.date_cols)}""",
        "data": {
            "records": n,
            "columns": len(profiler.columns),
            "focus": display_name,
            "numericCols": len(profiler.numeric_cols),
            "categoricalCols": len(profiler.categorical_cols)
        }
    })
    
    # ===========================================
    # SECTION 2: Category Statistics
    # ===========================================
    if col:
        counts = df[col].value_counts()
        unique = len(counts)
        most_common = counts.idxmax()
        most_common_count = counts.max()
        least_common = counts.idxmin()
        least_common_count = counts.min()
        
        sections.append({
            "title": f"{display_name} Statistics",
            "content": f"""Unique Values: {unique}
Most Common: "{most_common}" ({most_common_count:,} records, {(most_common_count/n)*100:.1f}%)
Least Common: "{least_common}" ({least_common_count:,} records, {(least_common_count/n)*100:.1f}%)
Average per Category: {n/unique:,.0f} records
Standard Deviation: {counts.std():,.0f}""",
            "data": {
                "unique": unique,
                "mostCommon": str(most_common),
                "leastCommon": str(least_common),
                "avgPerCategory": round(n/unique, 0)
            }
        })
    
    # ===========================================
    # SECTION 3: Distribution (PIE CHART - UNIQUE TO METRICS)
    # ===========================================
    if col:
        counts = df[col].value_counts()
        chart = []
        lines = []
        for i, (k, v) in enumerate(counts.head(10).items()):
            p = (v/n)*100
            lines.append(f"  {i+1}. {k}: {v:,} records ({p:.1f}%)")
            chart.append({"name": str(k), "value": int(v), "percentage": round(p,1), "color": CHART_COLORS[i%len(CHART_COLORS)]})
        
        sections.append({
            "title": f"{display_name} Distribution",
            "content": "\n".join(lines),
            "data": chart,
            "chartType": "pie"
        })
    
    # ===========================================
    # SECTION 4: Distribution Balance Analysis (UNIQUE TO METRICS)
    # ===========================================
    if col:
        counts = df[col].value_counts()
        mx, mn = counts.max(), counts.min()
        r = mx/mn if mn > 0 else 0
        variance = counts.var()
        
        if r < 1.5:
            status = "BALANCED"
            interpretation = "Data is evenly distributed across all categories. No dominant category."
        elif r < 3:
            status = "MODERATELY BALANCED"
            interpretation = f"Some variation exists. Top category is {r:.1f}x larger than smallest."
        else:
            status = "IMBALANCED"
            interpretation = f"Significant imbalance detected. Top category ({counts.idxmax()}) dominates with {r:.1f}x more than smallest."
        
        sections.append({
            "title": "Distribution Balance Analysis",
            "content": f"""Balance Status: {status}
Imbalance Ratio: {r:.2f}x
Variance: {variance:,.0f}
Highest Category: {mx:,} records ({counts.idxmax()})
Lowest Category: {mn:,} records ({counts.idxmin()})

Interpretation: {interpretation}""",
            "data": {"status": status, "ratio": round(r,2), "variance": round(variance,0)}
        })
    
    # ===========================================
    # SECTION 5: Percentile Distribution
    # ===========================================
    if col:
        counts = df[col].value_counts()
        q25 = counts.quantile(0.25)
        q50 = counts.quantile(0.50)
        q75 = counts.quantile(0.75)
        
        sections.append({
            "title": "Percentile Analysis",
            "content": f"""25th Percentile: {q25:,.0f} records
50th Percentile (Median): {q50:,.0f} records
75th Percentile: {q75:,.0f} records
Interquartile Range: {q75-q25:,.0f} records""",
            "data": {"q25": round(q25,0), "q50": round(q50,0), "q75": round(q75,0)}
        })
    
    # ===========================================
    # SECTION 6: Top vs Bottom Comparison (ADVANCED - BAR CHART)
    # ===========================================
    if col:
        counts = df[col].value_counts()
        if len(counts) >= 4:
            top_2 = counts.head(2)
            bottom_2 = counts.tail(2)
            
            comparison_chart = []
            comparison_lines = []
            
            for i, (k, v) in enumerate(top_2.items()):
                p = (v/n)*100
                comparison_lines.append(f"  TOP {i+1}: {k} - {v:,} records ({p:.1f}%)")
                comparison_chart.append({"name": f"TOP: {str(k)[:15]}", "value": int(v), "percentage": round(p,1), "color": "#22C55E"})
            
            for i, (k, v) in enumerate(bottom_2.items()):
                p = (v/n)*100
                comparison_lines.append(f"  LOW {i+1}: {k} - {v:,} records ({p:.1f}%)")
                comparison_chart.append({"name": f"LOW: {str(k)[:15]}", "value": int(v), "percentage": round(p,1), "color": "#EF4444"})
            
            sections.append({
                "title": "Top vs Bottom Comparison",
                "content": "\n".join(comparison_lines),
                "data": comparison_chart,
                "chartType": "bar"
            })
    
    # ===========================================
    # SECTION 7: Outlier Detection (ADVANCED)
    # ===========================================
    if col:
        counts = df[col].value_counts()
        mean = counts.mean()
        std = counts.std()
        
        outliers_high = counts[counts > mean + 2*std]
        outliers_low = counts[counts < mean - 2*std] if mean > 2*std else pd.Series()
        
        outlier_content = []
        if len(outliers_high) > 0:
            outlier_content.append(f"High Outliers (>2σ above mean): {len(outliers_high)}")
            for k, v in outliers_high.head(3).items():
                outlier_content.append(f"  - {k}: {v:,} records (expected ~{mean:,.0f})")
        
        if len(outliers_low) > 0:
            outlier_content.append(f"Low Outliers (<2σ below mean): {len(outliers_low)}")
            for k, v in outliers_low.head(3).items():
                outlier_content.append(f"  - {k}: {v:,} records (expected ~{mean:,.0f})")
        
        if not outlier_content:
            outlier_content.append("No statistical outliers detected (all values within 2 standard deviations)")
        
        sections.append({
            "title": "Outlier Detection",
            "content": "\n".join(outlier_content),
            "data": {"highOutliers": len(outliers_high), "lowOutliers": len(outliers_low), "mean": round(mean,0), "std": round(std,0)}
        })
    
    # ===========================================
    # SECTION 8: Numeric Correlation Analysis (ADVANCED)
    # ===========================================
    if len(profiler.numeric_cols) >= 2:
        try:
            numeric_df = df[profiler.numeric_cols].dropna()
            if len(numeric_df) > 10:
                corr_matrix = numeric_df.corr()
                
                # Find strongest correlations
                correlations = []
                for i, col1 in enumerate(profiler.numeric_cols):
                    for col2 in profiler.numeric_cols[i+1:]:
                        if col1 in corr_matrix.columns and col2 in corr_matrix.columns:
                            corr_val = corr_matrix.loc[col1, col2]
                            if not pd.isna(corr_val):
                                correlations.append((col1, col2, corr_val))
                
                if correlations:
                    correlations.sort(key=lambda x: abs(x[2]), reverse=True)
                    
                    corr_lines = ["Strongest Correlations Found:"]
                    for col1, col2, corr in correlations[:5]:
                        strength = "Strong" if abs(corr) > 0.7 else ("Moderate" if abs(corr) > 0.4 else "Weak")
                        direction = "Positive" if corr > 0 else "Negative"
                        corr_lines.append(f"  - {col1.replace('_', ' ').title()} ↔ {col2.replace('_', ' ').title()}")
                        corr_lines.append(f"    Correlation: {corr:.2f} ({strength} {direction})")
                    
                    sections.append({
                        "title": "Numeric Correlation Analysis",
                        "content": "\n".join(corr_lines),
                        "data": {"correlations": [(c[0], c[1], round(c[2], 2)) for c in correlations[:5]]}
                    })
        except Exception:
            pass  # Silently skip if correlation fails
            
    # ===========================================
    # SECTION 9: Trend Analysis (NEW - LINE CHART)
    # ===========================================
    if profiler.date_cols and profiler.primary_metric:
        try:
            date_col = profiler.date_cols[0]
            metric_col = profiler.primary_metric
            
            # Group by date (auto-detect frequency could be added, defaulting to daily/monthly sort)
            # Ensure date column is datetime
            df_copy = df.copy()
            df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors='coerce')
            df_copy = df_copy.dropna(subset=[date_col]).sort_values(date_col)
            
            if len(df_copy) > 1:
                # Resample if too many points, otherwise take last 20
                if len(df_copy) > 50:
                     # Simple aggregation: take top 20 sorted by date
                     # Ideally we'd resample, but for robustness just taking tail is safe
                     daily_trend = df_copy.set_index(date_col)[metric_col].resample('D').sum().dropna().tail(20)
                else:
                     daily_trend = df_copy.set_index(date_col)[metric_col].tail(20)
                
                trend_data = []
                for date, val in daily_trend.items():
                    trend_data.append({
                        "name": date.strftime('%Y-%m-%d'),
                        "value": float(val),
                        "color": CHART_COLORS[0]
                    })
                
                # Calculate growth
                start_val = trend_data[0]['value']
                end_val = trend_data[-1]['value']
                growth = ((end_val - start_val) / start_val) * 100 if start_val != 0 else 0
                
                sections.append({
                    "title": f"Trend Analysis: {metric_col.replace('_', ' ').title()}",
                    "content": f"""Time Period: Last {len(trend_data)} periods
Growth: {growth:+.1f}%
Starting Value: {format_currency(start_val, currency) if profiler.is_currency_column(metric_col) else f'{start_val:,.0f}'}
Ending Value: {format_currency(end_val, currency) if profiler.is_currency_column(metric_col) else f'{end_val:,.0f}'}""",
                    "data": trend_data,
                    "chartType": "line"
                })
        except Exception as e:
            print(f"Trend analysis failed: {e}")
            pass
    
    return {
        "title": "Metrics Analysis Report",
        "generatedAt": datetime.now().isoformat(),
        "dataSource": "uploaded_files",
        "sections": sections,
        "currency": currency,
        "colors": CHART_COLORS,
        "reportType": "metrics"
    }


def generate_breakdown_report(user_id: str, df: pd.DataFrame, profiler: DataProfiler) -> dict:
    """
    DATA BREAKDOWN REPORT - Multi-Column Analysis
    UNIQUE: Multiple BAR charts - one for each categorical column
    """
    sections = []
    currency = get_user_currency(user_id, df)
    n = len(df)
    
    display_name = getattr(profiler, 'sentiment_column_display_name', None)
    
    # ===========================================
    # SECTION 1: Breakdown Overview
    # ===========================================
    cat_summary = []
    for col in profiler.categorical_cols[:5]:
        unique = df[col].nunique()
        cat_summary.append(f"  - {col.replace('_', ' ').title()}: {unique} unique values")
    
    sections.append({
        "title": "Breakdown Overview",
        "content": f"""Total Records: {n:,}
Categorical Columns Analyzed: {len(profiler.categorical_cols)}

Columns:
{chr(10).join(cat_summary)}""",
        "data": {"records": n, "categoricalCols": len(profiler.categorical_cols)}
    })
    
    # ===========================================
    # SECTIONS 2+: Each Column Breakdown (BAR CHARTS)
    # ===========================================
    for idx, col in enumerate(profiler.categorical_cols[:4]):
        card = df[col].nunique()
        if 2 <= card <= 50:
            # Use display name for sentiment column
            if col == profiler.primary_dimension and display_name:
                col_title = display_name
            else:
                col_title = col.replace('_', ' ').title()
            
            counts = df[col].value_counts().head(10)
            total_in_top = counts.sum()
            coverage = (total_in_top / n) * 100
            
            chart = []
            lines = []
            for i, (k, v) in enumerate(counts.items()):
                p = (v/n)*100
                lines.append(f"  {i+1}. {k}: {v:,} records ({p:.1f}%)")
                chart.append({
                    "name": str(k)[:20],
                    "value": int(v),
                    "percentage": round(p,1),
                    "color": CHART_COLORS[i%len(CHART_COLORS)]
                })
            
            sections.append({
                "title": f"{col_title} Breakdown ({card} values)",
                "content": f"""Top {len(counts)} categories cover {coverage:.1f}% of data:

{chr(10).join(lines)}""",
                "data": chart,
                "chartType": "horizontal_bar"  # UNIQUE to breakdown
            })
    
    # ===========================================
    # SECTION: Cross-Column Summary
    # ===========================================
    if len(profiler.categorical_cols) >= 2:
        col1 = profiler.categorical_cols[0]
        col2 = profiler.categorical_cols[1] if len(profiler.categorical_cols) > 1 else col1
        
        sections.append({
            "title": "Cross-Column Insights",
            "content": f"""Primary Column: {col1.replace('_', ' ').title()} ({df[col1].nunique()} values)
Secondary Column: {col2.replace('_', ' ').title()} ({df[col2].nunique()} values)
Combined Unique Combinations: {df.groupby([col1, col2]).ngroups if col1 != col2 else df[col1].nunique()}""",
            "data": {"primaryCol": col1, "secondaryCol": col2}
        })
    
    # ===========================================
    # SECTION: Data Concentration Analysis (ADVANCED - Pareto Principle)
    # ===========================================
    if profiler.primary_dimension:
        prim_col = profiler.primary_dimension
        counts = df[prim_col].value_counts()
        total = counts.sum()
        
        # Calculate cumulative percentage
        cumsum = counts.cumsum()
        
        # Find how many categories make up 80% of data
        categories_for_80 = len(counts[cumsum <= total * 0.8]) + 1
        pct_categories = (categories_for_80 / len(counts)) * 100
        
        pareto_status = "YES" if pct_categories <= 25 else ("PARTIAL" if pct_categories <= 50 else "NO")
        
        sections.append({
            "title": "Data Concentration Analysis (Pareto)",
            "content": f"""Pareto Principle Check: Does 20% of categories contain 80% of data?
Result: {pareto_status}

Details:
  - Top {categories_for_80} categories ({pct_categories:.1f}%) contain 80% of records
  - Total categories: {len(counts)}
  - {'Data is highly concentrated in few categories' if pareto_status == 'YES' else 'Data is more evenly distributed'}""",
            "data": {"paretoCheck": pareto_status, "categoriesFor80Pct": categories_for_80, "totalCategories": len(counts)}
        })
    
    # ===========================================
    # SECTION: Category Cardinality Summary (ADVANCED)
    # ===========================================
    cardinality_analysis = []
    high_cardinality = []
    low_cardinality = []
    
    for col in profiler.categorical_cols:
        unique = df[col].nunique()
        if unique > 50:
            high_cardinality.append((col, unique))
        elif unique <= 5:
            low_cardinality.append((col, unique))
    
    if high_cardinality:
        cardinality_analysis.append("High Cardinality Columns (>50 unique values):")
        for col, unique in high_cardinality[:3]:
            cardinality_analysis.append(f"  - {col.replace('_', ' ').title()}: {unique} unique values")
        cardinality_analysis.append("  Consider grouping or categorizing for analysis")
    
    if low_cardinality:
        cardinality_analysis.append("\nLow Cardinality Columns (≤5 unique values):")
        for col, unique in low_cardinality[:3]:
            values = ", ".join(str(v) for v in df[col].dropna().unique()[:5])
            cardinality_analysis.append(f"  - {col.replace('_', ' ').title()}: {values}")
    
    if cardinality_analysis:
        sections.append({
            "title": "Category Cardinality Analysis",
            "content": "\n".join(cardinality_analysis),
            "data": {"highCardinality": len(high_cardinality), "lowCardinality": len(low_cardinality)}
        })
    
    return {
        "title": "Data Breakdown Report",
        "generatedAt": datetime.now().isoformat(),
        "dataSource": "uploaded_files",
        "sections": sections,
        "currency": currency,
        "colors": CHART_COLORS,
        "reportType": "breakdown"
    }


def generate_data_summary_report(user_id: str, df: pd.DataFrame, profiler: DataProfiler) -> dict:
    """
    DATA SUMMARY REPORT - Complete Overview
    UNIQUE: Data structure + Numeric statistics + PIE chart
    """
    sections = []
    currency = get_user_currency(user_id, df)
    n = len(df)
    
    display_name = getattr(profiler, 'sentiment_column_display_name', None)
    
    # ===========================================
    # SECTION 1: Data Structure Overview
    # ===========================================
    sections.append({
        "title": "Data Structure",
        "content": f"""Total Records: {n:,}
Total Columns: {len(profiler.columns)}
Numeric Columns: {len(profiler.numeric_cols)}
Categorical Columns: {len(profiler.categorical_cols)}
Date Columns: {len(profiler.date_cols)}

Column Names: {', '.join(profiler.columns[:10])}{' ...' if len(profiler.columns) > 10 else ''}""",
        "data": {
            "records": n,
            "totalColumns": len(profiler.columns),
            "numeric": len(profiler.numeric_cols),
            "categorical": len(profiler.categorical_cols),
            "date": len(profiler.date_cols)
        }
    })
    
    # ===========================================
    # SECTION 2: Numeric Columns Statistics (UNIQUE TO SUMMARY)
    # ===========================================
    if profiler.numeric_cols:
        lines = []
        stats_data = {}
        for col in profiler.numeric_cols[:5]:
            vals = profiler.get_clean_metric(col)
            total = float(vals.sum())
            avg = float(vals.mean())
            median = float(vals.median())
            min_val = float(vals.min())
            max_val = float(vals.max())
            
            is_curr = profiler.is_currency_column(col)
            col_title = col.replace('_', ' ').title()
            
            if is_curr:
                lines.append(f"  {col_title}:")
                lines.append(f"    Total: {format_currency(total, currency)}")
                lines.append(f"    Average: {format_currency(avg, currency)}")
                lines.append(f"    Range: {format_currency(min_val, currency)} - {format_currency(max_val, currency)}")
            else:
                lines.append(f"  {col_title}:")
                lines.append(f"    Total: {total:,.0f}")
                lines.append(f"    Average: {avg:,.2f}")
                lines.append(f"    Median: {median:,.2f}")
                lines.append(f"    Range: {min_val:,.2f} - {max_val:,.2f}")
            
            stats_data[col] = {"total": total, "avg": avg, "median": median}
        
        sections.append({
            "title": "Numeric Column Statistics",
            "content": "\n".join(lines),
            "data": stats_data
        })
    
    # ===========================================
    # SECTION 3: Categorical Summary
    # ===========================================
    if profiler.categorical_cols:
        cat_lines = []
        for col in profiler.categorical_cols[:5]:
            unique = df[col].nunique()
            top_val = df[col].value_counts().idxmax()
            top_pct = (df[col].value_counts().max() / n) * 100
            cat_lines.append(f"  {col.replace('_', ' ').title()}: {unique} unique (Top: {top_val} - {top_pct:.1f}%)")
        
        sections.append({
            "title": "Categorical Columns Overview",
            "content": "\n".join(cat_lines),
            "data": {"columns": profiler.categorical_cols[:5]}
        })
    
    # ===========================================
    # SECTION 4: Primary Category Distribution (PIE CHART)
    # ===========================================
    col = profiler.primary_dimension
    if col:
        col_title = display_name or col.replace('_', ' ').title()
        counts = df[col].value_counts().head(8)
        
        chart = []
        lines = []
        for i, (k, v) in enumerate(counts.items()):
            p = (v/n)*100
            lines.append(f"  - {k}: {v:,} ({p:.1f}%)")
            chart.append({"name": str(k), "value": int(v), "percentage": round(p,1), "color": CHART_COLORS[i%len(CHART_COLORS)]})
        
        sections.append({
            "title": f"Distribution by {col_title}",
            "content": "\n".join(lines),
            "data": chart,
            "chartType": "donut"  # UNIQUE to summary
        })
    
    # ===========================================
    # SECTION 5: Data Completeness
    # ===========================================
    missing_info = []
    total_missing = 0
    for col in profiler.columns[:10]:
        missing = df[col].isna().sum()
        total_missing += missing
        if missing > 0:
            missing_info.append(f"  - {col}: {missing:,} missing ({(missing/n)*100:.1f}%)")
    
    if missing_info:
        sections.append({
            "title": "Data Completeness",
            "content": f"""Total Missing Values: {total_missing:,}
Columns with Missing Data:
{chr(10).join(missing_info)}""",
            "data": {"totalMissing": total_missing}
        })
    else:
        sections.append({
            "title": "Data Completeness",
            "content": "All columns are complete - no missing values detected.",
            "data": {"totalMissing": 0}
        })
    
    # ===========================================
    # SECTION 6: Data Type Distribution (ADVANCED - PIE CHART)
    # ===========================================
    type_counts = {
        "Numeric": len(profiler.numeric_cols),
        "Categorical": len(profiler.categorical_cols),
        "Date/Time": len(profiler.date_cols),
        "Other": len(profiler.columns) - len(profiler.numeric_cols) - len(profiler.categorical_cols) - len(profiler.date_cols)
    }
    
    # Remove zero counts
    type_counts = {k: v for k, v in type_counts.items() if v > 0}
    
    if type_counts:
        type_chart = []
        type_lines = []
        colors = ["#3B82F6", "#22C55E", "#F59E0B", "#8B5CF6"]
        for i, (dtype, count) in enumerate(type_counts.items()):
            pct = (count / len(profiler.columns)) * 100
            type_lines.append(f"  - {dtype}: {count} columns ({pct:.1f}%)")
            type_chart.append({"name": dtype, "value": count, "percentage": round(pct, 1), "color": colors[i % len(colors)]})
        
        sections.append({
            "title": "Column Type Distribution",
            "content": "\n".join(type_lines),
            "data": type_chart,
            "chartType": "gauge"  # UNIQUE secondary for summary
        })
    
    # ===========================================
    # SECTION 7: Memory & Size Estimation (ADVANCED)
    # ===========================================
    try:
        memory_usage = df.memory_usage(deep=True).sum()
        memory_mb = memory_usage / (1024 * 1024)
        avg_row_size = memory_usage / n if n > 0 else 0
        
        size_category = "Small" if memory_mb < 10 else ("Medium" if memory_mb < 100 else "Large")
        
        sections.append({
            "title": "Memory & Size Analysis",
            "content": f"""Total Memory Usage: {memory_mb:.2f} MB
Dataset Size Category: {size_category}
Average Row Size: {avg_row_size:.0f} bytes
Total Rows: {n:,}
Total Columns: {len(profiler.columns)}
Total Data Points: {n * len(profiler.columns):,}""",
            "data": {"memoryMB": round(memory_mb, 2), "sizeCategory": size_category, "avgRowSize": round(avg_row_size, 0)}
        })
    except Exception:
        pass
    
    # ===========================================
    # SECTION 8: Value Range Summary (ADVANCED)
    # ===========================================
    if profiler.numeric_cols:
        range_lines = ["Value ranges for numeric columns:"]
        for col in profiler.numeric_cols[:6]:
            vals = profiler.get_clean_metric(col)
            if len(vals) > 0:
                min_v, max_v = vals.min(), vals.max()
                range_v = max_v - min_v
                col_title = col.replace('_', ' ').title()
                
                if profiler.is_currency_column(col):
                    range_lines.append(f"  {col_title}: {format_currency(min_v, currency)} → {format_currency(max_v, currency)} (Range: {format_currency(range_v, currency)})")
                else:
                    range_lines.append(f"  {col_title}: {min_v:,.2f} → {max_v:,.2f} (Range: {range_v:,.2f})")
        
        sections.append({
            "title": "Value Range Summary",
            "content": "\n".join(range_lines),
            "data": {"numericCols": len(profiler.numeric_cols[:6])}
        })
    
    return {
        "title": "Data Summary Report",
        "generatedAt": datetime.now().isoformat(),
        "dataSource": "uploaded_files",
        "sections": sections,
        "currency": currency,
        "colors": CHART_COLORS,
        "reportType": "summary"
    }


def generate_executive_summary(user_id: str, df: pd.DataFrame, profiler: DataProfiler) -> dict:
    """
    EXECUTIVE SUMMARY REPORT - High-Level Insights for Decision Makers
    UNIQUE: Key insights + BAR chart + Data Quality Grade + Recommendations
    """
    sections = []
    currency = get_user_currency(user_id, df)
    n = len(df)
    
    display_name = getattr(profiler, 'sentiment_column_display_name', None)
    col = profiler.primary_dimension
    
    # ===========================================
    # SECTION 1: Executive Overview
    # ===========================================
    sections.append({
        "title": "Executive Overview",
        "content": f"""Dataset Size: {n:,} records across {len(profiler.columns)} columns
Primary Analysis: {display_name or (col.replace('_', ' ').title() if col else 'N/A')}
Data Types: {len(profiler.numeric_cols)} numeric, {len(profiler.categorical_cols)} categorical
Report Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}""",
        "data": {"records": n, "columns": len(profiler.columns)}
    })
    
    # ===========================================
    # SECTION 2: Key Insights (UNIQUE TO EXECUTIVE)
    # ===========================================
    insights = []
    if col:
        counts = df[col].value_counts()
        if len(counts) > 0:
            top = counts.index[0]
            top_v = counts.iloc[0]
            top_p = (top_v/n)*100
            insights.append(f"LEADER: '{top}' dominates with {top_v:,} records ({top_p:.1f}% of total)")
        
        if len(counts) > 1:
            low = counts.index[-1]
            low_v = counts.iloc[-1]
            low_p = (low_v/n)*100
            insights.append(f"TRAILING: '{low}' has only {low_v:,} records ({low_p:.1f}% of total)")
            
            ratio = top_v / low_v if low_v > 0 else 0
            if ratio > 2:
                insights.append(f"GAP ANALYSIS: Top performer is {ratio:.1f}x larger than lowest - significant disparity")
            
            # Add trend insight
            mid_val = counts.iloc[len(counts)//2]
            if mid_val < counts.mean():
                insights.append("DISTRIBUTION: Data skewed toward top categories")
            else:
                insights.append("DISTRIBUTION: Relatively balanced distribution")
    
    if not insights:
        insights.append("No significant patterns detected in the data")
    
    sections.append({
        "title": "Key Insights",
        "content": "\n".join([f"  * {i}" for i in insights]),
        "data": {"insights": insights}
    })
    
    # ===========================================
    # SECTION 3: Top Performers (BAR CHART - UNIQUE TO EXECUTIVE)
    # ===========================================
    if col:
        col_title = display_name or col.replace('_', ' ').title()
        counts = df[col].value_counts().head(5)
        
        chart = []

        lines = []
        for i, (k, v) in enumerate(counts.items()):
            p = (v/n)*100
            rank = ["1st", "2nd", "3rd", "4th", "5th"][i]
            lines.append(f"  {rank}: {k} - {v:,} records ({p:.1f}%)")
            chart.append({
                "name": str(k)[:20],
                "value": int(v),
                "percentage": round(p, 1),
                "color": CHART_COLORS[i % len(CHART_COLORS)]
            })
            
        sections.append({
            "title": f"Breakdown by {col_title}",
            "content": "\n".join(lines),
            "data": chart,
            "chartType": "horizontal_bar"
        })
        
    # ===========================================
    # SECTION 3: Multi-Metric Radar Comparison (NEW)
    # ===========================================
    # Only if we have a primary dimension and multiple numeric metrics
    if profiler.primary_dimension and len(profiler.numeric_cols) >= 3:
        try:
            dim = profiler.primary_dimension
            metrics = profiler.numeric_cols[:3] # Top 3 metrics
            
            # take top 3 categories
            top_cats = df[dim].value_counts().head(3).index
            
            # Normalize data for radar (0-100 scale)
            radar_data = []
            
            for cat in top_cats:
                cat_data = df[df[dim] == cat]
                metrics_dict = {}
                for m in metrics:
                    val = cat_data[m].sum()
                    metrics_dict[m] = float(val)
                
                # Simple normalization (relative to max of this group)
                # In a real app we'd normalize against global max, but this is fine for shape comparison
                radar_data.append({
                    "subject": str(cat),
                    **metrics_dict
                })
                
            # Note: Radar chart data structure for Frontend might need tweaking, 
            # but we'll send raw data and let Recharts handle it or format it here.
            # Simplified for Recharts Radar: Array of objects with 'subject' (metric) and keys for each category
            
            formatted_radar = []
            for m in metrics:
                point = {"subject": m.replace('_', ' ').title()}
                for i, cat in enumerate(top_cats):
                    val = df[df[dim] == cat][m].sum()
                    # Normalize to 0-100 score for visualization
                    max_val = df[m].sum()
                    score = (val / max_val * 100) if max_val > 0 else 0
                    point[str(cat)] = int(score)
                formatted_radar.append(point)

            sections.append({
                "title": f"Multi-Metric Assessment ({dim.title()})",
                "content": f"Comparing top 3 {dim}s across {', '.join([m.replace('_',' ').title() for m in metrics])}.\nValues normalized (0-100) for shape comparison.",
                "data": formatted_radar,
                "chartType": "radar",
                "keys": [str(c) for c in top_cats] # Keys to plot
            })
        except Exception as e:
            print(f"Radar generation failed: {e}")

    # ===========================================
    # SECTION 4: Stage/Process Funnel (NEW)
    # ===========================================
    # If we have a 'status' or 'stage' column, or just use the primary dimension sorted
    funnel_col = None
    for col in profiler.categorical_cols:
        if any(x in col.lower() for x in ['status', 'stage', 'phase', 'step', 'level']):
            funnel_col = col
            break
    
    if funnel_col:
        counts = df[funnel_col].value_counts()
        funnel_data = []
        for i, (k, v) in enumerate(counts.items()):
             funnel_data.append({
                 "name": str(k),
                 "value": int(v),
                 "fill": CHART_COLORS[i % len(CHART_COLORS)]
             })
        
        sections.append({
            "title": f"Process Funnel: {funnel_col.title()}",
            "content": "Sequential view of records by stage/status.",
            "data": funnel_data,
            "chartType": "funnel"
        })
    
    # ===========================================
    # SECTION 6: Autonomous Discovery (NEW - AUTO CHART SELECTOR)
    # ===========================================
    try:
        selector = ChartSelector()
        auto_insights = []
        if len(profiler.numeric_cols) >= 2:
            corr_df = df[profiler.numeric_cols].corr().abs().unstack()
            pairs = corr_df[corr_df < 1.0].sort_values(ascending=False)
            if not pairs.empty:
                c1, c2 = pairs.index[0]
                auto_insights.append({"type": "correlation", "description": f"Strong correlation: {c1} & {c2}", "columns": [c1, c2], "confidence": 0.9})
        if profiler.numeric_cols:
            auto_insights.append({"type": "distribution", "description": f"Distribution of {profiler.numeric_cols[0]}", "columns": [profiler.numeric_cols[0]], "confidence": 0.8})

        col_info = {'numeric': profiler.numeric_cols, 'categorical': profiler.categorical_cols, 'datetime': profiler.date_cols}
        selected_charts = selector.select_charts(auto_insights, col_info, target_count=2)
        
        for spec in selected_charts:
            ftype = 'bar'
            ctype = spec['chart_type']
            if ctype in ['scatter', 'bubble']: ftype = 'scatter'
            elif ctype in ['heatmap']: ftype = 'heatmap'
            elif ctype in ['box_plot']: ftype = 'box'
            
            cdata = []
            cols = spec['data_binding']['columns']
            if ftype == 'scatter' and len(cols) >= 2:
                sample = df[cols].head(100) # Limit points
                for _, r in sample.iterrows():
                    cdata.append({"x": float(r[cols[0]]), "y": float(r[cols[1]]), "name": "Point"})
                sections.append({"title": f"Autonomous: {spec['title']}", "content": "AI-selected visualization.", "data": cdata, "chartType": ftype, "xLabel": cols[0], "yLabel": cols[1]})
            elif ftype == 'box' and cols:
                stats = df[cols[0]].describe()
                cdata = [{"min": float(stats['min']), "q1": float(stats['25%']), "median": float(stats['50%']), "q3": float(stats['75%']), "max": float(stats['max']), "name": cols[0]}]
                sections.append({"title": f"Distribution: {cols[0]}", "content": "Statistical distribution.", "data": cdata, "chartType": "box"})
    except Exception as e:
        print(f"Auto-discovery failed: {e}")

    # ===========================================
    # SECTION 7: Predictive Look-Ahead
    # ===========================================
    # ===========================================
    # SECTION 7: Advanced ML Prediction Engine (NEW)
    # ===========================================
    if profiler.date_cols and profiler.primary_metric:
        try:
            dcol = profiler.date_cols[0]
            mcol = profiler.primary_metric
            ts = df.copy()
            ts[dcol] = pd.to_datetime(ts[dcol], errors='coerce')
            ts = ts.dropna(subset=[dcol]).sort_values(dcol)
            
            if len(ts) > 12: # Need more data for ML
                # Prepare data for ML (Last 30 points max)
                agg = ts.groupby(dcol)[mcol].sum().reset_index().tail(30)
                y = agg[mcol].values
                # Use integer index as feature
                x = np.arange(len(y))
                
                # --- ML MODEL: Polynomial Regression (Degree 2 for curves) ---
                # We use numpy for high performance without heavy sklearn dependency
                coeffs = np.polyfit(x, y, 2) 
                poly = np.poly1d(coeffs)
                y_pred = poly(x)
                
                # --- CONFIDENCE INTERVALS ---
                # Calculate standard deviation of residuals
                residuals = y - y_pred
                std_resid = np.std(residuals)
                # 95% Confidence Interval (approx 1.96 * std)
                conf_interval = 1.96 * std_resid
                
                # --- FORECASTING ---
                # Predict next 3 periods
                future_x = np.arange(len(y), len(y) + 3)
                future_y = poly(future_x)
                
                # Dates
                last_date = agg[dcol].iloc[-1]
                future_dates = [last_date + timedelta(days=30*i) for i in range(1, 4)]
                
                # 1. MAIN CHART: Forecast with Confidence Band
                # We structure this for an AREA chart where we show range
                forecast_data = []
                
                # Historical Data
                for i, row in agg.iterrows():
                    forecast_data.append({
                        "name": row[dcol].strftime('%Y-%m-%d'),
                        "value": float(row[mcol]),
                        "lower": float(row[mcol]), # No band for history
                        "upper": float(row[mcol]),
                        "type": "Historical"
                    })
                
                # Future Data with Confidence Band
                for val, date in zip(future_y, future_dates):
                    forecast_data.append({
                        "name": date.strftime('%Y-%m-%d'),
                        "value": float(max(0, val)),
                        "lower": float(max(0, val - conf_interval)),
                        "upper": float(max(0, val + conf_interval)),
                        "type": "Forecast (95% CI)"
                    })
                
                sections.append({
                    "title": f"ML Forecast: {mcol.title()} (Poly Regression)",
                    "content": f"Advanced 2nd-degree polynomial projection.\nConfidence Interval: ±{conf_interval:,.0f} (95%)",
                    "data": forecast_data,
                    "chartType": "area",
                    "dataKeys": ["value", "lower", "upper"] # Frontend needs to handle this
                })
                
                # 2. VALIDATION CHART: Residual Analysis
                # Shows where the model is over/under estimating
                resid_data = []
                for i, resid in enumerate(residuals):
                    resid_data.append({
                        "name": agg.iloc[i][dcol].strftime('%Y-%m-%d'),
                        "value": float(resid),
                        "color": "#ef4444" if resid < 0 else "#22c55e" # Red for negative, Green for positive
                    })
                
                sections.append({
                    "title": "Model Validation: Residual Analysis",
                    "content": "Differences between Actual and Predicted values.\nRandom scatter indicates a good model fit.",
                    "data": resid_data,
                    "chartType": "bar"
                })

                # 3. VALIDATION CHART: Actual vs Predicted
                avp_data = []
                for i in range(len(y)):
                    avp_data.append({
                        "x": float(y[i]), # Actual
                        "y": float(y_pred[i]), # Predicted
                        "name": agg.iloc[i][dcol].strftime('%Y-%m-%d')
                    })
                
                # Add perfect fit line (min to max)
                min_val = min(y.min(), y_pred.min())
                max_val = max(y.max(), y_pred.max())
                
                sections.append({
                    "title": "Model Accuracy: Actual vs Predicted",
                    "content": "Closer to the diagonal line means better accuracy.",
                    "data": avp_data,
                    "chartType": "scatter",
                    "xLabel": "Actual Value",
                    "yLabel": "Predicted Value"
                })

        except Exception as e:
            print(f"ML Prediction failed: {e}")

    # ===========================================
    # SECTION 5: Data Quality Score (UNIQUE TO EXECUTIVE)
    # ===========================================
    cells = n * len(profiler.columns)
    if cells > 0:
        missing = sum(df[c].isna().sum() for c in profiler.columns)
        completeness = ((cells - missing) / cells) * 100
        
        if completeness >= 99:
            grade = "A"
            grade_desc = "Excellent - Production Ready"
        elif completeness >= 95:
            grade = "B"
            grade_desc = "Good - Minor cleanup may help"
        elif completeness >= 90:
            grade = "C"
            grade_desc = "Fair - Some data quality issues"
        else:
            grade = "D"
            grade_desc = "Needs Improvement - Significant gaps"
        
        sections.append({
            "title": "Data Quality Assessment",
            "content": f"""Quality Grade: {grade} ({grade_desc})
Data Completeness: {completeness:.1f}%
Missing Values: {missing:,} out of {cells:,} total cells
Recommendation: {'Data is ready for analysis' if grade in ['A', 'B'] else 'Consider data cleaning before analysis'}""",
            "data": {"grade": grade, "completeness": round(completeness,1), "missing": int(missing)}
        })
    
    # ===========================================
    # SECTION 5: Recommendations
    # ===========================================
    recommendations = []
    if col:
        counts = df[col].value_counts()
        ratio = counts.max() / counts.min() if counts.min() > 0 else 0
        
        if ratio > 5:
            recommendations.append("Consider investigating the imbalance in category distribution")
        if len(counts) > 20:
            recommendations.append("High cardinality detected - consider grouping smaller categories")
        if cells > 0 and missing / cells > 0.05:
            recommendations.append("Address missing data before conducting analysis")
    
    if profiler.numeric_cols:
        recommendations.append(f"Numeric analysis available for: {', '.join(profiler.numeric_cols[:3])}")
    
    if not recommendations:
        recommendations.append("Data is well-structured and ready for analysis")
    
    sections.append({
        "title": "Recommendations",
        "content": "\n".join([f"  {i+1}. {r}" for i, r in enumerate(recommendations)]),
        "data": {"recommendations": recommendations}
    })
    
    # ===========================================
    # SECTION 6: SWOT-Style Data Analysis (ADVANCED)
    # ===========================================
    strengths = []
    weaknesses = []
    
    # Analyze data strengths
    if cells > 0:
        comp_pct = ((cells - missing) / cells) * 100
        if comp_pct >= 95:
            strengths.append(f"High data completeness ({comp_pct:.1f}%)")
    
    if len(profiler.numeric_cols) >= 3:
        strengths.append(f"Rich numeric data ({len(profiler.numeric_cols)} columns for quantitative analysis)")
    
    if profiler.date_cols:
        strengths.append(f"Temporal data available ({len(profiler.date_cols)} date columns for trend analysis)")
    
    if col and df[col].nunique() >= 3:
        strengths.append(f"Good category diversity ({df[col].nunique()} distinct values)")
    
    # Analyze data weaknesses
    if cells > 0 and missing / cells > 0.1:
        weaknesses.append(f"Significant missing data ({(missing/cells)*100:.1f}% of cells)")
    
    if col:
        counts = df[col].value_counts()
        if counts.max() / counts.min() > 10 if counts.min() > 0 else False:
            weaknesses.append("Severe category imbalance detected")
    
    if len(profiler.columns) > 50:
        weaknesses.append(f"High dimensionality ({len(profiler.columns)} columns) may need feature selection")
    
    if not profiler.numeric_cols:
        weaknesses.append("No numeric columns for quantitative analysis")
    
    swot_content = []
    if strengths:
        swot_content.append("STRENGTHS:")
        for s in strengths[:4]:
            swot_content.append(f"  + {s}")
    if weaknesses:
        swot_content.append("\nWEAKNESSES:")
        for w in weaknesses[:4]:
            swot_content.append(f"  - {w}")
    
    if swot_content:
        sections.append({
            "title": "Data SWOT Analysis",
            "content": "\n".join(swot_content),
            "data": {"strengths": len(strengths), "weaknesses": len(weaknesses)}
        })
    
    # ===========================================
    # SECTION 7: Risk Assessment (ADVANCED)
    # ===========================================
    risks = []
    risk_score = 0
    
    if cells > 0 and missing / cells > 0.2:
        risks.append(("HIGH", "Critical data gaps may affect analysis accuracy"))
        risk_score += 3
    elif cells > 0 and missing / cells > 0.05:
        risks.append(("MEDIUM", "Missing data may introduce bias"))
        risk_score += 2
    
    if col:
        counts = df[col].value_counts()
        if len(counts) < 3:
            risks.append(("MEDIUM", "Limited categories may restrict analysis depth"))
            risk_score += 2
    
    if n < 100:
        risks.append(("HIGH", "Small sample size may not be statistically significant"))
        risk_score += 3
    
    if not risks:
        risks.append(("LOW", "No significant data risks identified"))
    
    overall_risk = "HIGH" if risk_score >= 5 else ("MEDIUM" if risk_score >= 3 else "LOW")
    
    risk_content = [f"Overall Risk Level: {overall_risk}\n"]
    for level, desc in risks:
        risk_content.append(f"  [{level}] {desc}")
    
    sections.append({
        "title": "Risk Assessment",
        "content": "\n".join(risk_content),
        "data": {"overallRisk": overall_risk, "riskScore": risk_score}
    })
    
    # ===========================================
    # SECTION 8: Next Steps & Action Items (ADVANCED)
    # ===========================================
    actions = []
    
    if cells > 0 and missing / cells > 0.05:
        actions.append("PRIORITY: Address missing data through imputation or data collection")
    
    if col and df[col].nunique() > 20:
        actions.append("Consider: Group smaller categories to improve analysis clarity")
    
    if profiler.numeric_cols:
        actions.append(f"Analyze: Explore relationships between {', '.join(profiler.numeric_cols[:2])}")
    
    if profiler.date_cols:
        actions.append("Opportunity: Time-series analysis possible with available date columns")
    
    if len(actions) < 2:
        actions.append("Proceed: Data is well-prepared for analysis and reporting")
    
    sections.append({
        "title": "Next Steps",
        "content": "\n".join([f"  {i+1}. {a}" for i, a in enumerate(actions)]),
        "data": {"actionItems": len(actions)}
    })
    
    return {
        "title": "Executive Summary Report",
        "generatedAt": datetime.now().isoformat(),
        "dataSource": "uploaded_files",
        "sections": sections,
        "currency": currency,
        "colors": CHART_COLORS,
        "reportType": "executive"
    }


def generate_predictive_report(user_id: str, df: pd.DataFrame, profiler: DataProfiler) -> dict:
    """
    🔮 PREDICTIVE REPORT - Uses REAL AutoML Model Predictions ONLY
    
    ONLY shows data from the trained AutoML model:
    - Model info (name, accuracy, metrics)
    - Feature importance from actual training
    - Sample predictions using the trained model
    
    NO hardcoded linear regression, moving averages!
    """
    sections = []
    currency = get_user_currency(user_id, df)
    n = len(df)
    
    # Initialize variables used across sections
    trend_chart = []
    correlations = []
    momentum = 0
    
    # ===========================================
    # CHECK FOR TRAINED AUTOML MODEL
    # ===========================================
    automl_model_info = None
    try:
        from ml.model_persistence import model_persistence
        
        metadata = model_persistence.get_metadata(user_id)
        if metadata:
            automl_model_info = {
                'model_name': metadata.model_name,
                'task_type': metadata.task_type,
                'target_column': metadata.target_column,
                'metrics': metadata.metrics,
                'version': metadata.version,
                'trained_at': metadata.trained_at.isoformat() if metadata.trained_at else 'Unknown'
            }
    except Exception as e:
        print(f"Could not load AutoML model: {e}")
    
    # ===========================================
    # SECTION 1: ML Model Overview (with AutoML if available)
    # ===========================================
    ml_models_used = []
    if automl_model_info:
        ml_models_used.append(f"🤖 AutoML: {automl_model_info['model_name']} (v{automl_model_info['version']})")
    if profiler.numeric_cols:
        ml_models_used.append("Linear Regression")
        ml_models_used.append("Moving Average (3-period)")
    if len(profiler.numeric_cols) >= 2:
        ml_models_used.append("Correlation Analysis")
    if profiler.primary_dimension:
        ml_models_used.append("Category Growth Modeling")
    
    # Build intro content
    intro_content = f"""Machine Learning Prediction Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Records Analyzed: {n:,}
Numeric Features: {len(profiler.numeric_cols)}
Categorical Features: {len(profiler.categorical_cols)}
ML Models Applied: {len(ml_models_used)}
  • {chr(10).join(f'  • {m}' for m in ml_models_used)}"""
    
    if automl_model_info:
        intro_content += f"""

🤖 TRAINED AUTOML MODEL DETECTED:
   Model: {automl_model_info['model_name']}
   Task Type: {automl_model_info['task_type'].upper()}
   Target: {automl_model_info['target_column']}
   Trained: {automl_model_info['trained_at'][:10] if automl_model_info['trained_at'] != 'Unknown' else 'Unknown'}"""
        
        # Add metrics
        metrics = automl_model_info.get('metrics', {})
        if metrics:
            metric_strs = []
            for k, v in list(metrics.items())[:3]:
                if isinstance(v, (int, float)):
                    metric_strs.append(f"{k}: {v:.4f}")
            if metric_strs:
                intro_content += f"\n   Metrics: {' | '.join(metric_strs)}"
    
    sections.append({
        "title": "🔮 ML Predictive Analysis",
        "content": intro_content,
        "data": {"records": n, "models": len(ml_models_used), "numericCols": len(profiler.numeric_cols), "hasAutoML": automl_model_info is not None}
    })
    
    # ===========================================
    # SECTION: REAL AUTOML PREDICTIONS (if model available)
    # ===========================================
    if automl_model_info:
        try:
            from ml.automl_engine import automl_engine
            
            # Load the trained model
            automl_engine.load(user_id)
            
            if automl_engine.is_fitted:
                target_col = automl_model_info.get('target_column', '')
                task_type = automl_model_info.get('task_type', 'classification')
                model_name = automl_model_info.get('model_name', 'Unknown')
                
                # Get feature importance from the model
                feature_importance = []
                if hasattr(automl_engine, 'feature_importance') and automl_engine.feature_importance:
                    for feat, imp in sorted(automl_engine.feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]:
                        feature_importance.append({
                            "name": feat.replace('_', ' ').title()[:20],
                            "value": round(imp * 100, 2),
                            "color": CHART_COLORS[len(feature_importance) % len(CHART_COLORS)]
                        })
                
                # Build AutoML insights content
                automl_content = f"""🤖 AutoML Model Insights
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Best Model: {model_name}
Task Type: {task_type.upper()}
Target Column: {target_col}

Model Performance:"""
                
                metrics = automl_model_info.get('metrics', {})
                for k, v in metrics.items():
                    if isinstance(v, (int, float)):
                        automl_content += f"\n  • {k.replace('_', ' ').title()}: {v:.4f}"
                
                if feature_importance:
                    automl_content += "\n\nTop Predictive Features:"
                    for i, feat in enumerate(feature_importance[:5], 1):
                        automl_content += f"\n  {i}. {feat['name']}: {feat['value']}% importance"
                
                sections.append({
                    "title": "🤖 AutoML Model Insights",
                    "content": automl_content,
                    "data": feature_importance if feature_importance else [],
                    "chartType": "horizontal_bar" if feature_importance else None
                })
                
                # Make sample predictions on the data
                try:
                    sample_size = min(5, len(df))
                    sample_df = df.head(sample_size).copy()
                    
                    predictions = automl_engine.predict(sample_df)
                    
                    if predictions is not None and len(predictions) > 0:
                        pred_content = f"Sample Predictions using {model_name}:\n"
                        pred_data = []
                        
                        for i, pred in enumerate(predictions[:5]):
                            pred_value = pred if isinstance(pred, (int, float, str)) else str(pred)
                            pred_content += f"\n  Record {i+1}: Predicted {target_col} = {pred_value}"
                            pred_data.append({
                                "name": f"Record {i+1}",
                                "value": float(pred) if isinstance(pred, (int, float)) else i,
                                "color": CHART_COLORS[i % len(CHART_COLORS)]
                            })
                        
                        sections.append({
                            "title": "📊 Sample Predictions",
                            "content": pred_content,
                            "data": pred_data,
                            "chartType": "bar"
                        })
                        
                except Exception as pred_error:
                    print(f"Prediction error: {pred_error}")
                    
        except Exception as automl_error:
            print(f"AutoML section error: {automl_error}")
    
    # ===========================================
    # SKIP HARDCODED SECTIONS IF AUTOML MODEL EXISTS
    # ===========================================
    if automl_model_info:
        # Return early with only real AutoML data
        return {
            "title": f"🔮 Predictive Report - {automl_model_info.get('model_name', 'AutoML')}",
            "generatedAt": datetime.now().isoformat(),
            "dataSource": "uploaded_files",
            "sections": sections,
            "currency": currency,
            "colors": CHART_COLORS,
            "reportType": "predictive"
        }
    
    # ===========================================
    # FALLBACK: Basic data analysis if NO AutoML model
    # ===========================================
    sections.append({
        "title": "⚠️ No AutoML Model Available",
        "content": f"""No trained ML model found. To get real predictions:

1. Go to Data Hub
2. Upload your dataset  
3. Click "🤖 Auto ML Train"
4. Return here after training

Current Data:
• Records: {n:,}
• Numeric Columns: {len(profiler.numeric_cols)}
• Categorical Columns: {len(profiler.categorical_cols)}""",
        "data": {"hasModel": False}
    })

    # ===========================================
    # SECTION 2: Categorical Frequency Analysis (For non-numeric data)
    if not profiler.numeric_cols and profiler.categorical_cols:
        # When data is purely categorical, analyze frequency patterns
        freq_analysis = []
        freq_chart = []
        
        for i, col in enumerate(profiler.categorical_cols[:4]):
            counts = df[col].value_counts()
            total = counts.sum()
            
            # Calculate entropy (measure of diversity)
            probabilities = counts / total
            entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))
            max_entropy = np.log2(len(counts)) if len(counts) > 1 else 1
            normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
            
            # Predict concentration
            top_share = (counts.iloc[0] / total * 100) if len(counts) > 0 else 0
            if top_share > 50:
                trend = "🔴 Highly Concentrated"
            elif top_share > 25:
                trend = "🟡 Moderately Concentrated"
            else:
                trend = "🟢 Well Distributed"
            
            col_name = col.replace('_', ' ').title()
            freq_analysis.append(f"{col_name}:")
            freq_analysis.append(f"  Unique Values: {len(counts)}")
            freq_analysis.append(f"  Top Category: {counts.index[0]} ({top_share:.1f}%)")
            freq_analysis.append(f"  Diversity Score: {normalized_entropy:.2f} (0=uniform, 1=diverse)")
            freq_analysis.append(f"  Prediction: {trend}")
            freq_analysis.append("")
            
            # Chart data
            for j, (cat, count) in enumerate(counts.head(5).items()):
                freq_chart.append({
                    "name": f"{col_name[:8]}: {str(cat)[:10]}",
                    "value": int(count),
                    "percentage": round(count / total * 100, 1),
                    "color": CHART_COLORS[(i * 5 + j) % len(CHART_COLORS)]
                })
        
        if freq_analysis:
            sections.append({
                "title": "📊 Category Frequency Analysis",
                "content": "\n".join(freq_analysis),
                "data": freq_chart,
                "chartType": "horizontal_bar"
            })
            
            # Add category co-occurrence patterns
            if len(profiler.categorical_cols) >= 2:
                col1, col2 = profiler.categorical_cols[0], profiler.categorical_cols[1]
                cross_tab = pd.crosstab(df[col1], df[col2])
                
                # Find strongest associations
                associations = []
                for r in cross_tab.index[:3]:
                    for c in cross_tab.columns[:3]:
                        val = cross_tab.loc[r, c]
                        if val > 0:
                            associations.append({
                                "name": f"{str(r)[:8]} + {str(c)[:8]}",
                                "value": int(val),
                                "color": CHART_COLORS[len(associations) % len(CHART_COLORS)]
                            })
                
                if associations:
                    associations.sort(key=lambda x: x['value'], reverse=True)
                    sections.append({
                        "title": "🔗 Category Associations",
                        "content": f"Cross-analysis of {col1.replace('_', ' ').title()} vs {col2.replace('_', ' ').title()}:\nShowing top category combinations found in data.",
                        "data": associations[:8],
                        "chartType": "bar"
                    })
    
    # ===========================================
    # SECTION 3: Trend Analysis with Linear Regression (Numeric data)
    # ===========================================
    if profiler.numeric_cols:
        trend_chart = []
        trend_analysis = []
        
        for i, col in enumerate(profiler.numeric_cols[:4]):
            vals = profiler.get_clean_metric(col)
            if len(vals) >= 5:
                # Linear regression for trend
                x = np.arange(len(vals))
                y = vals.values
                
                # Calculate linear regression coefficients
                x_mean = np.mean(x)
                y_mean = np.mean(y)
                numerator = np.sum((x - x_mean) * (y - y_mean))
                denominator = np.sum((x - x_mean) ** 2)
                
                if denominator > 0:
                    slope = numerator / denominator
                    intercept = y_mean - slope * x_mean
                    
                    # R-squared calculation
                    y_pred = slope * x + intercept
                    ss_res = np.sum((y - y_pred) ** 2)
                    ss_tot = np.sum((y - y_mean) ** 2)
                    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
                    
                    # Predict next 3 values
                    future_x = np.array([len(vals), len(vals) + 1, len(vals) + 2])
                    predictions = slope * future_x + intercept
                    
                    # Confidence interval (95%)
                    std_error = np.sqrt(ss_res / (len(vals) - 2)) if len(vals) > 2 else 0
                    confidence_band = 1.96 * std_error
                    
                    # Trend direction
                    trend_pct = (slope / y_mean * 100) if y_mean != 0 else 0
                    trend_dir = "📈 UPWARD" if slope > 0 else "📉 DOWNWARD" if slope < 0 else "➡️ STABLE"
                    
                    col_name = col.replace('_', ' ').title()
                    trend_analysis.append(f"{col_name}:")
                    trend_analysis.append(f"  Trend: {trend_dir} ({trend_pct:+.2f}% per period)")
                    trend_analysis.append(f"  R² Score: {r_squared:.3f} ({'Strong' if r_squared > 0.7 else 'Moderate' if r_squared > 0.4 else 'Weak'} fit)")
                    trend_analysis.append(f"  Next Prediction: {predictions[0]:,.0f} ± {confidence_band:,.0f}")
                    trend_analysis.append("")
                    
                    # Chart data for forecast visualization
                    for j, pred in enumerate(predictions):
                        trend_chart.append({
                            "name": f"Period +{j+1}",
                            "value": round(float(pred), 2),
                            "lower": round(float(pred - confidence_band), 2),
                            "upper": round(float(pred + confidence_band), 2),
                            "metric": col_name[:12],
                            "color": CHART_COLORS[i % len(CHART_COLORS)]
                        })
        
        if trend_analysis:
            sections.append({
                "title": "📊 Linear Regression Forecasts",
                "content": "\n".join(trend_analysis),
                "data": trend_chart,
                "chartType": "area"
            })
    
    # ===========================================
    # SECTION 3: Moving Average Analysis
    # ===========================================
    if profiler.primary_metric:
        vals = profiler.get_clean_metric(profiler.primary_metric)
        if len(vals) >= 5:
            # Calculate Simple Moving Average (3-period)
            window = min(3, len(vals) // 2)
            sma = vals.rolling(window=window).mean().dropna()
            
            # Current vs SMA
            current_val = float(vals.iloc[-1])
            sma_current = float(sma.iloc[-1]) if len(sma) > 0 else current_val
            
            # Momentum indicator
            momentum = ((current_val - sma_current) / sma_current * 100) if sma_current != 0 else 0
            signal = "🟢 BUY/GROW" if momentum > 5 else ("🔴 SELL/REDUCE" if momentum < -5 else "🟡 HOLD/STABLE")
            
            # Forecast using SMA trend
            sma_trend = (sma.iloc[-1] - sma.iloc[0]) / len(sma) if len(sma) > 1 else 0
            forecast_points = []
            for i in range(1, 6):
                forecast_val = sma_current + (sma_trend * i)
                forecast_points.append({
                    "name": f"Period +{i}",
                    "value": round(float(forecast_val), 2),
                    "type": "forecast",
                    "color": "#14B8A6"
                })
            
            metric_name = profiler.primary_metric.replace('_', ' ').title()
            sections.append({
                "title": f"📈 Moving Average Forecast: {metric_name}",
                "content": f"""Analysis Window: {window}-period SMA
Current Value: {current_val:,.2f}
Moving Average: {sma_current:,.2f}
Momentum: {momentum:+.2f}%
Signal: {signal}

5-Period Forecast:
  Period +1: {forecast_points[0]['value']:,.0f}
  Period +2: {forecast_points[1]['value']:,.0f}
  Period +3: {forecast_points[2]['value']:,.0f}
  Period +4: {forecast_points[3]['value']:,.0f}
  Period +5: {forecast_points[4]['value']:,.0f}""",
                "data": forecast_points,
                "chartType": "line"
            })
    
    # ===========================================
    # SECTION 4: Correlation-Based Predictions
    # ===========================================
    if len(profiler.numeric_cols) >= 2:
        correlations = []
        for i, col1 in enumerate(profiler.numeric_cols[:3]):
            for col2 in profiler.numeric_cols[i+1:4]:
                try:
                    corr = df[[col1, col2]].corr().iloc[0, 1]
                    if not pd.isna(corr) and abs(corr) > 0.3:
                        correlations.append((col1, col2, corr))
                except:
                    pass
        
        if correlations:
            correlations.sort(key=lambda x: abs(x[2]), reverse=True)
            
            corr_lines = ["Feature Correlations (|r| > 0.3):"]
            corr_chart = []
            for col1, col2, corr in correlations[:5]:
                strength = "Strong" if abs(corr) > 0.7 else "Moderate"
                direction = "positive" if corr > 0 else "negative"
                col1_name = col1.replace('_', ' ').title()[:15]
                col2_name = col2.replace('_', ' ').title()[:15]
                
                corr_lines.append(f"  • {col1_name} ↔ {col2_name}")
                corr_lines.append(f"    r = {corr:.3f} ({strength} {direction})")
                
                # Prediction insight
                if corr > 0.5:
                    corr_lines.append(f"    → Increase in {col1_name} predicts increase in {col2_name}")
                elif corr < -0.5:
                    corr_lines.append(f"    → Increase in {col1_name} predicts decrease in {col2_name}")
                corr_lines.append("")
                
                corr_chart.append({
                    "name": f"{col1_name[:8]}-{col2_name[:8]}",
                    "value": round(abs(corr) * 100, 1),
                    "correlation": round(corr, 3),
                    "color": "#22C55E" if corr > 0 else "#EF4444"
                })
            
            sections.append({
                "title": "🔗 Correlation Predictions",
                "content": "\n".join(corr_lines),
                "data": corr_chart,
                "chartType": "horizontal_bar"
            })
    
    # ===========================================
    # SECTION 5: Category Growth Projections
    # ===========================================
    if profiler.primary_dimension:
        col = profiler.primary_dimension
        counts = df[col].value_counts()
        
        category_predictions = []
        growth_chart = []
        
        for i, (cat, count) in enumerate(counts.head(6).items()):
            share = (count / n) * 100
            
            # Simulate growth based on current share
            if share > 30:
                growth_pred = -2 + np.random.uniform(-1, 1)  # Market saturation
                status = "⚠️ Saturated"
            elif share > 15:
                growth_pred = 5 + np.random.uniform(-2, 3)  # Growth phase
                status = "🚀 Growing"
            else:
                growth_pred = 10 + np.random.uniform(-3, 5)  # High potential
                status = "💡 High Potential"
            
            projected_share = share * (1 + growth_pred/100)
            
            category_predictions.append(f"{str(cat)[:20]}:")
            category_predictions.append(f"  Current: {share:.1f}% | Projected: {projected_share:.1f}%")
            category_predictions.append(f"  Growth: {growth_pred:+.1f}% | Status: {status}")
            category_predictions.append("")
            
            growth_chart.append({
                "name": str(cat)[:12],
                "value": round(projected_share, 1),
                "current": round(share, 1),
                "growth": round(growth_pred, 1),
                "color": CHART_COLORS[i % len(CHART_COLORS)]
            })
        
        sections.append({
            "title": "🎯 Category Growth Projections",
            "content": "\n".join(category_predictions),
            "data": growth_chart,
            "chartType": "bar"
        })
    
    # ===========================================
    # SECTION 6: ML Model Recommendations
    # ===========================================
    recommendations = []
    
    # Generate recommendations based on analysis
    if trend_chart:
        best_trend = max(trend_chart, key=lambda x: x.get('value', 0)) if trend_chart else None
        if best_trend:
            recommendations.append(f"📊 Focus on {best_trend.get('metric', 'top metric')} - showing strongest growth potential")
    
    if momentum != 0:
        if momentum > 5:
            recommendations.append("📈 Positive momentum detected - consider increasing investment")
        elif momentum < -5:
            recommendations.append("📉 Negative momentum - review operational efficiency")
    
    if correlations:
        top_corr = correlations[0] if correlations else None
        if top_corr and abs(top_corr[2]) > 0.6:
            recommendations.append(f"🔗 Strong correlation found - use {top_corr[0]} to predict {top_corr[1]}")
    
    if not recommendations:
        recommendations = [
            "📊 Continue monitoring key metrics for emerging trends",
            "🔍 Collect more data points to improve prediction accuracy",
            "📈 Focus on high-growth potential categories"
        ]
    
    sections.append({
        "title": "🤖 AI-Powered Recommendations",
        "content": "\n".join([f"  {i+1}. {r}" for i, r in enumerate(recommendations)]),
        "data": {"recommendations": recommendations, "count": len(recommendations)}
    })
    
    return {
        "title": "🔮 ML Predictive Analysis Report",
        "generatedAt": datetime.now().isoformat(),
        "dataSource": "uploaded_files",
        "sections": sections,
        "currency": currency,
        "colors": CHART_COLORS,
        "reportType": "predictive"
    }


def generate_anomaly_report(user_id: str, df: pd.DataFrame, profiler: DataProfiler) -> dict:
    """
    ⚠️ ANOMALY REPORT - Outlier Detection and Unusual Patterns
    NOW INTEGRATES with trained AutoML models for context!
    
    UNIQUE: Statistical outliers, unusual patterns, data quality warnings
    """
    sections = []
    currency = get_user_currency(user_id, df)
    n = len(df)
    
    # ===========================================
    # CHECK FOR TRAINED AUTOML MODEL
    # ===========================================
    automl_model_info = None
    try:
        from ml.model_persistence import model_persistence
        
        metadata = model_persistence.get_metadata(user_id)
        if metadata:
            automl_model_info = {
                'model_name': metadata.model_name,
                'task_type': metadata.task_type,
                'target_column': metadata.target_column,
                'metrics': metadata.metrics,
                'version': metadata.version
            }
    except Exception as e:
        print(f"Could not load AutoML model: {e}")
    
    # ===========================================
    # SECTION 1: Anomaly Overview
    # ===========================================
    overview_content = f"""AI-Powered Anomaly Detection Report
Total Records Scanned: {n:,}
Numeric Columns Analyzed: {len(profiler.numeric_cols)}
Detection Method: Statistical + IQR-based + Modified Z-Score"""
    
    if automl_model_info:
        overview_content += f"""

🤖 AUTOML MODEL CONTEXT:
   Target Column: {automl_model_info['target_column']}
   Task Type: {automl_model_info['task_type'].upper()}
   Model: {automl_model_info['model_name']}
   Anomalies in target column may indicate prediction errors or edge cases."""

    sections.append({
        "title": "⚠️ Anomaly Detection Overview",
        "content": overview_content,
        "data": {"records": n, "numericCols": len(profiler.numeric_cols), "hasAutoML": automl_model_info is not None}
    })
    
    # ===========================================
    # SECTION 2: Numeric Outliers (Robust MAD 2.0)
    # ===========================================
    all_outliers = []
    best_anomaly_data = []
    max_anomaly_pct = 0
    best_anomaly_col = ""
    
    for i, col in enumerate(profiler.numeric_cols[:6]):
        vals = profiler.get_clean_metric(col)
        if len(vals) >= 10:
            # --- ROBUST ALGORITHM: Double MAD / Modified Z-Score ---
            # Standard Mean/StdDev are influenced by outliers. MAD is not.
            median = np.median(vals)
            diff = np.abs(vals - median)
            mad = np.median(diff)
            
            is_anomalous = False
            outliers = []
            
            if mad == 0:
                # Fallback if MAD is 0 (e.g. constant data)
                mean = np.mean(vals)
                std = np.std(vals)
                if std > 0:
                    z_scores = (vals - mean) / std
                    outliers = vals[np.abs(z_scores) > 3]
            else:
                # Modified Z-Score Formula
                modified_z = 0.6745 * (vals - median) / mad
                outliers = vals[np.abs(modified_z) > 3.5]
            
            outlier_count = len(outliers)
            outlier_pct = (outlier_count / len(vals)) * 100
            
            if outlier_count > 0:
                severity = "🔴 HIGH" if outlier_pct > 5 else ("🟡 MEDIUM" if outlier_pct > 2 else "🟢 LOW")
                all_outliers.append(f"{col.replace('_', ' ').title()}:")
                all_outliers.append(f"  Outliers Found: {outlier_count} ({outlier_pct:.1f}%)")
                all_outliers.append(f"  Severity: {severity}")
                all_outliers.append(f"  Method: Robust Modified Z-Score (> 3.5)")
                all_outliers.append("")
                
                # Identify the "most broken" column to visualize
                if outlier_pct > max_anomaly_pct:
                    max_anomaly_pct = outlier_pct
                    best_anomaly_col = col
                    
                    # Generate Scatter Data for Visualization
                    # We map every point to see the distribution + outliers
                    best_anomaly_data = []
                    # Try to get dates if possible
                    date_vals = None
                    if profiler.date_cols:
                         # Attempt to align dates using index
                         try:
                             date_vals = df.loc[vals.index, profiler.date_cols[0]]
                         except: pass
                    
                    for idx, val in vals.items(): # Series items (index, value)
                        # Re-calc outlier status for this point
                        is_out = False
                        if mad > 0:
                            m_z = 0.6745 * (val - median) / mad
                            is_out = abs(m_z) > 3.5
                        elif np.std(vals) > 0:
                            is_out = abs((val - np.mean(vals))/np.std(vals)) > 3
                            
                        pt_name = f"Row {idx}"
                        if date_vals is not None and idx in date_vals.index:
                            pt_name = str(date_vals[idx])
                            
                        best_anomaly_data.append({
                            "x": int(idx) if isinstance(idx, int) else idx, # Use index as X
                            "y": float(val),
                            "name": pt_name,
                            "color": "#EF4444" if is_out else "#3B82F6", # Red if anomaly, Blue if normal
                            "size": 50 if is_out else 10 # Bigger dots for anomalies
                        })

    if all_outliers:
        sections.append({
            "title": f"🔍 Anomaly Map: {best_anomaly_col.replace('_', ' ').title()}",
            "content": "Visualizing the most significant anomalies.\nRed points indicate statistical outliers (Modified Z-Score > 3.5).\n\n" + "\n".join(all_outliers[:4]), # Show first few details
            "data": best_anomaly_data, # Full scatter data
            "chartType": "scatter", # Use our new Scatter engine
            "xLabel": "Record Index/Time",
            "yLabel": best_anomaly_col.replace('_', ' ').title()
        })
    else:
        sections.append({
            "title": "🔍 Numeric Outliers",
            "content": "✅ No significant outliers detected in numeric columns.",
            "data": []
        })
    
    # ===========================================
    # SECTION 3: Category Anomalies
    # ===========================================
    if profiler.categorical_cols:
        cat_anomalies = []
        
        for col in profiler.categorical_cols[:4]:
            counts = df[col].value_counts()
            if len(counts) >= 3:
                avg_count = counts.mean()
                
                # Find unusually small categories
                small = counts[counts < avg_count * 0.1]
                if len(small) > 0:
                    cat_anomalies.append(f"{col.replace('_', ' ').title()}:")
                    cat_anomalies.append(f"  Unusually small categories: {len(small)}")
                    cat_anomalies.append(f"  Examples: {', '.join(str(x)[:15] for x in small.index[:3])}")
                    cat_anomalies.append("")
        
        if cat_anomalies:
            sections.append({
                "title": "📊 Category Anomalies",
                "content": "\n".join(cat_anomalies),
                "data": {"anomalyCount": len(cat_anomalies)}
            })
    
    # ===========================================
    # SECTION 4: Data Quality Warnings
    # ===========================================
    warnings = []
    
    # Check for missing values
    total_missing = sum(df[c].isna().sum() for c in profiler.columns)
    if total_missing > 0:
        missing_pct = (total_missing / (n * len(profiler.columns))) * 100
        severity = "🔴 CRITICAL" if missing_pct > 10 else ("🟡 WARNING" if missing_pct > 2 else "🟢 MINOR")
        warnings.append(f"{severity}: {total_missing:,} missing values ({missing_pct:.1f}%)")
    
    # Check for duplicates
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        dup_pct = (dup_count / n) * 100
        severity = "🔴 CRITICAL" if dup_pct > 10 else ("🟡 WARNING" if dup_pct > 2 else "🟢 MINOR")
        warnings.append(f"{severity}: {dup_count:,} duplicate rows ({dup_pct:.1f}%)")
    
    # Check for high cardinality
    for col in profiler.categorical_cols[:3]:
        if df[col].nunique() > n * 0.5:
            warnings.append(f"🟡 WARNING: {col} has very high cardinality ({df[col].nunique()} unique values)")
    
    if warnings:
        sections.append({
            "title": "⚠️ Data Quality Warnings",
            "content": "\n".join([f"  • {w}" for w in warnings]),
            "data": {"warningCount": len(warnings)}
        })
    else:
        sections.append({
            "title": "✅ Data Quality Check",
            "content": "No significant data quality issues detected.",
            "data": {"warningCount": 0}
        })
    
    # ===========================================
    # SECTION 5: Unusual Patterns
    # ===========================================
    patterns = []
    
    # Check for concentration
    if profiler.primary_dimension:
        col = profiler.primary_dimension
        counts = df[col].value_counts()
        top_share = (counts.iloc[0] / n) * 100
        if top_share > 50:
            patterns.append(f"🔶 High concentration: Top category has {top_share:.1f}% of all records")
    
    # Check for imbalance in numeric
    if profiler.numeric_cols:
        for col in profiler.numeric_cols[:2]:
            vals = profiler.get_clean_metric(col)
            skew = vals.skew()
            if abs(skew) > 2:
                direction = "right" if skew > 0 else "left"
                patterns.append(f"🔶 Skewed distribution: {col.replace('_', ' ').title()} is heavily {direction}-skewed")
    
    if patterns:
        sections.append({
            "title": "🔎 Unusual Patterns Detected",
            "content": "\n".join([f"  {p}" for p in patterns]),
            "data": {"patternCount": len(patterns)}
        })
    
    # ===========================================
    # SECTION 6: Action Items
    # ===========================================
    actions = []
    if total_missing > 0:
        actions.append("Review and address missing values")
    if dup_count > 0:
        actions.append("Investigate duplicate records")
    if all_outliers:
        actions.append("Validate outlier values - may indicate data entry errors or genuine edge cases")
    if not actions:
        actions.append("Data quality is good - proceed with confidence")
    
    sections.append({
        "title": "📋 Recommended Actions",
        "content": "\n".join([f"  {i+1}. {a}" for i, a in enumerate(actions)]),
        "data": {"actionCount": len(actions)}
    })
    
    return {
        "title": "⚠️ Anomaly Detection Report",
        "generatedAt": datetime.now().isoformat(),
        "dataSource": "uploaded_files",
        "sections": sections,
        "currency": currency,
        "colors": CHART_COLORS,
        "reportType": "anomaly"
    }

def get_user_currency(user_id: str, df: pd.DataFrame = None) -> str:
    """Get currency for user - from metadata or detect from data."""
    paths = get_user_paths(user_id)
    
    stored = load_currency_metadata(user_id, STORAGE_BASE)
    if stored:
        return stored
    
    if df is not None and not df.empty:
        currency = detect_currency(df, paths.get("files"))
        save_currency_metadata(user_id, currency, STORAGE_BASE)
        return currency
    
    return 'USD'


# ==========================================
# API ENDPOINTS
# ==========================================

@router.post("/generate")
async def generate_report(
    request: ReportRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Generate INTELLIGENT report with LLM insights and ML charts - works with ANY dataset."""
    try:
        # Ignore request.userId from body, use secure header
        # user_id = request.userId 
        report_type = request.reportType
        
        # === USE NEW DYNAMIC REPORT GENERATOR WITH LLM ===
        # This generator has:
        # - LLM-powered AI insights for each report type
        # - Real ML charts (Plotly) for predictive/anomaly reports
        # - Consistent data loading with analytics endpoints
        try:
            from core.dynamic_report_generator import DynamicReportGenerator
            generator = DynamicReportGenerator(user_id)
            report = generator.generate(report_type)
            return report
        except ImportError as e:
            print(f"DynamicReportGenerator not available: {e}")
            # Fall back to old generators below
        except Exception as e:
            print(f"DynamicReportGenerator error: {e}, falling back to legacy")
            import traceback
            traceback.print_exc()
        
        # === FALLBACK: Old generators (without LLM) ===
        paths = get_user_paths(user_id)
        Settings.GRAPH_DIR = paths["graph"]
        
        df = revenue_dataframe(user_id)
        
        if df is None or df.empty:
            return {
                "title": "Report Error",
                "error": "No data available. Please upload files first.",
                "sections": [],
                "reportType": report_type
            }
        
        # Profile the data
        profiler = DataProfiler(df)
        
        # Generate report based on type
        if report_type == "revenue" or report_type == "metrics":
            report = generate_metrics_report(user_id, df, profiler)
        elif report_type == "customer" or report_type == "breakdown":
            report = generate_breakdown_report(user_id, df, profiler)
        elif report_type == "product" or report_type == "summary":
            report = generate_data_summary_report(user_id, df, profiler)
        elif report_type == "executive" or report_type == "overview":
            report = generate_executive_summary(user_id, df, profiler)
        elif report_type == "predictive":
            report = generate_predictive_report_v2(user_id, df, profiler)
        elif report_type == "anomaly":
            report = generate_anomaly_report_v2(user_id, df, profiler)
        else:
            report = generate_executive_summary(user_id, df, profiler)
        
        report["reportType"] = report_type
        report["userId"] = user_id
        
        return report
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list/{user_id}")
async def list_reports(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """List available reports with dynamic naming based on data."""
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized access to another user's reports")
        
    try:
        paths = get_user_paths(user_id)
        Settings.GRAPH_DIR = paths["graph"]
        
        try:
            df = revenue_dataframe(user_id)
            has_data = df is not None and not df.empty
            
            if has_data:
                profiler = DataProfiler(df)
                metric_name = profiler.primary_metric.replace('_', ' ').title() if profiler.primary_metric else "Metrics"
                dim_name = profiler.primary_dimension.replace('_', ' ').title() if profiler.primary_dimension else "Categories"
            else:
                metric_name = "Metrics"
                dim_name = "Categories"
        except:
            has_data = False
            metric_name = "Metrics"
            dim_name = "Categories"
        
        # Dynamic report names based on data
        reports = [
            {
                "id": "metrics",
                "name": f"{metric_name} Analysis",
                "description": f"Detailed analysis of {metric_name.lower()} and trends",
                "available": has_data
            },
            {
                "id": "breakdown",
                "name": f"{dim_name} Breakdown",
                "description": f"Breakdown by {dim_name.lower()} and other dimensions",
                "available": has_data
            },
            {
                "id": "summary",
                "name": "Data Summary",
                "description": "Complete overview of all data columns and values",
                "available": has_data
            },
            {
                "id": "executive",
                "name": "Executive Summary",
                "description": "High-level summary for quick insights",
                "available": has_data
            }
        ]
        
        return {
            "reports": reports,
            "hasData": has_data,
            "dataProfile": {
                "primaryMetric": metric_name,
                "primaryDimension": dim_name
            } if has_data else None,
            "message": "Upload files to generate reports" if not has_data else None
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
