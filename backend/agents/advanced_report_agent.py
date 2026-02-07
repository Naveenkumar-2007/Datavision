"""
Advanced Report Generation Agent
================================
Fully dynamic, AI-powered report generation with zero hardcoded content.
Every chart, insight, and recommendation is derived from actual data analysis.

Features:
- Intelligent data profiling and pattern detection
- Dynamic chart selection based on data characteristics
- AI-powered narrative generation
- Multi-domain support (Sales, Finance, HR, Operations, etc.)
- Real-time anomaly detection and highlighting
- Predictive insights when ML models are available
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import json

logger = logging.getLogger(__name__)

# Import ML Chart Generator for real charts
try:
    from ml.ml_chart_generator import MLChartGenerator
    ML_CHARTS_AVAILABLE = True
except ImportError:
    ML_CHARTS_AVAILABLE = False
    logger.warning("MLChartGenerator not available")

# ============================================================================
# DATA PROFILER - Analyzes data characteristics for smart report generation
# ============================================================================

class DataProfiler:
    """Profiles dataset to determine optimal report structure and visualizations."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.profile = self._generate_profile()
    
    def _generate_profile(self) -> Dict[str, Any]:
        """Generate comprehensive data profile."""
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime_cols = self.df.select_dtypes(include=['datetime64']).columns.tolist()
        
        # Detect potential datetime columns stored as strings
        for col in categorical_cols[:]:
            try:
                sample = self.df[col].dropna().head(100)
                if len(sample) > 0:
                    pd.to_datetime(sample, errors='raise')
                    datetime_cols.append(col)
                    categorical_cols.remove(col)
            except:
                pass
        
        # Identify column roles
        id_cols = self._detect_id_columns()
        metric_cols = self._detect_metric_columns(numeric_cols)
        dimension_cols = self._detect_dimension_columns(categorical_cols)
        
        # Detect data domain
        domain = self._detect_domain()
        
        # Calculate data quality metrics
        quality = self._calculate_quality()
        
        # Detect patterns
        patterns = self._detect_patterns(numeric_cols, datetime_cols)
        
        return {
            "shape": {"rows": len(self.df), "columns": len(self.df.columns)},
            "column_types": {
                "numeric": numeric_cols,
                "categorical": categorical_cols,
                "datetime": datetime_cols,
                "id": id_cols
            },
            "roles": {
                "metrics": metric_cols,
                "dimensions": dimension_cols
            },
            "domain": domain,
            "quality": quality,
            "patterns": patterns,
            "columns": list(self.df.columns)
        }
    
    def _detect_id_columns(self) -> List[str]:
        """Detect columns that are likely IDs."""
        id_cols = []
        for col in self.df.columns:
            col_lower = col.lower()
            if any(x in col_lower for x in ['id', 'key', 'code', 'number', 'no.']):
                if self.df[col].nunique() > len(self.df) * 0.8:
                    id_cols.append(col)
        return id_cols
    
    def _detect_metric_columns(self, numeric_cols: List[str]) -> List[Dict]:
        """Identify and rank metric columns by importance."""
        metrics = []
        
        logger.info(f"📊 [REPORT DATA] Analyzing {len(numeric_cols)} numeric columns")
        
        for col in numeric_cols:
            col_lower = col.lower()
            
            # Calculate column statistics from ACTUAL data
            col_data = self.df[col].dropna()  # Clean data
            if len(col_data) == 0:
                logger.warning(f"⚠️ [REPORT DATA] Column '{col}' has no valid data, skipping")
                continue
                
            total = col_data.sum()
            mean = col_data.mean()
            std = col_data.std() if len(col_data) > 1 else 0
            min_val = col_data.min()
            max_val = col_data.max()
            non_null = len(col_data)
            
            # Log actual values for debugging
            logger.info(f"📈 [REPORT DATA] {col}: total={total:.2f}, mean={mean:.2f}, min={min_val:.2f}, max={max_val:.2f}, rows={non_null}")
            
            # Determine metric type
            metric_type = "numeric"
            if any(x in col_lower for x in ['revenue', 'sales', 'amount', 'price', 'cost', 'total', 'value', 'income']):
                metric_type = "monetary"
            elif any(x in col_lower for x in ['count', 'quantity', 'qty', 'number', 'units', 'num']):
                metric_type = "count"
            elif any(x in col_lower for x in ['rate', 'percent', 'ratio', 'pct', '%']):
                metric_type = "rate"
            elif any(x in col_lower for x in ['score', 'rating', 'rank', 'grade']):
                metric_type = "score"
            
            # Calculate importance score
            importance = 0
            if metric_type == "monetary":
                importance += 50
            elif metric_type == "count":
                importance += 30
            importance += min(20, abs(total) / 1000000)  # Higher totals = more important
            importance += (non_null / len(self.df)) * 20  # Completeness bonus
            
            metrics.append({
                "name": col,
                "type": metric_type,
                "total": float(total) if pd.notna(total) else 0,
                "mean": float(mean) if pd.notna(mean) else 0,
                "std": float(std) if pd.notna(std) else 0,
                "min": float(min_val) if pd.notna(min_val) else 0,
                "max": float(max_val) if pd.notna(max_val) else 0,
                "importance": importance,
                "count": non_null
            })
        
        sorted_metrics = sorted(metrics, key=lambda x: x["importance"], reverse=True)
        logger.info(f"✅ [REPORT DATA] Detected {len(sorted_metrics)} metrics, top: {[m['name'] for m in sorted_metrics[:3]]}")
        return sorted_metrics
    
    def _detect_dimension_columns(self, categorical_cols: List[str]) -> List[Dict]:
        """Identify and characterize dimension columns."""
        dimensions = []
        for col in categorical_cols:
            unique_count = self.df[col].nunique()
            value_counts = self.df[col].value_counts()
            
            # Skip if too many unique values (likely an ID)
            if unique_count > len(self.df) * 0.5:
                continue
            
            # Determine cardinality category
            if unique_count <= 5:
                cardinality = "low"
            elif unique_count <= 20:
                cardinality = "medium"
            else:
                cardinality = "high"
            
            dimensions.append({
                "name": col,
                "unique_count": unique_count,
                "cardinality": cardinality,
                "top_values": value_counts.head(10).to_dict(),
                "coverage": (self.df[col].notna().sum() / len(self.df)) * 100
            })
        
        return sorted(dimensions, key=lambda x: x["coverage"], reverse=True)
    
    def _detect_domain(self) -> Dict[str, Any]:
        """Detect the business domain of the data."""
        col_names = ' '.join(self.df.columns).lower()
        
        domain_scores = {
            "sales": sum(1 for x in ['revenue', 'sales', 'customer', 'order', 'product', 'quantity', 'discount'] if x in col_names),
            "finance": sum(1 for x in ['amount', 'balance', 'transaction', 'payment', 'invoice', 'account', 'credit', 'debit'] if x in col_names),
            "hr": sum(1 for x in ['employee', 'salary', 'department', 'hire', 'position', 'manager', 'attendance'] if x in col_names),
            "marketing": sum(1 for x in ['campaign', 'click', 'impression', 'conversion', 'lead', 'channel', 'roi'] if x in col_names),
            "operations": sum(1 for x in ['inventory', 'stock', 'supplier', 'warehouse', 'delivery', 'shipment'] if x in col_names),
            "ecommerce": sum(1 for x in ['cart', 'checkout', 'sku', 'category', 'brand', 'review', 'rating'] if x in col_names)
        }
        
        detected = max(domain_scores, key=domain_scores.get)
        confidence = domain_scores[detected] / max(sum(domain_scores.values()), 1)
        
        return {
            "detected": detected if domain_scores[detected] > 0 else "general",
            "confidence": confidence,
            "scores": domain_scores
        }
    
    def _calculate_quality(self) -> Dict[str, Any]:
        """Calculate data quality metrics."""
        total_cells = len(self.df) * len(self.df.columns)
        missing_cells = self.df.isna().sum().sum()
        duplicates = self.df.duplicated().sum()
        
        # Column-level quality
        col_quality = {}
        for col in self.df.columns:
            col_quality[col] = {
                "missing_pct": (self.df[col].isna().sum() / len(self.df)) * 100,
                "unique_pct": (self.df[col].nunique() / len(self.df)) * 100
            }
        
        # Overall score
        completeness = ((total_cells - missing_cells) / total_cells) * 100
        uniqueness = ((len(self.df) - duplicates) / len(self.df)) * 100
        score = (completeness * 0.6 + uniqueness * 0.4)
        
        return {
            "score": score,
            "completeness": completeness,
            "uniqueness": uniqueness,
            "missing_cells": missing_cells,
            "duplicate_rows": duplicates,
            "total_cells": total_cells,
            "column_quality": col_quality
        }
    
    def _detect_patterns(self, numeric_cols: List[str], datetime_cols: List[str]) -> Dict[str, Any]:
        """Detect data patterns and trends."""
        patterns = {
            "trends": [],
            "correlations": [],
            "seasonality": None,
            "outliers": {}
        }
        
        # Detect trends in numeric columns
        for col in numeric_cols[:5]:
            values = self.df[col].dropna()
            if len(values) > 10:
                first_half = values.iloc[:len(values)//2].mean()
                second_half = values.iloc[len(values)//2:].mean()
                if first_half != 0:
                    change = ((second_half - first_half) / abs(first_half)) * 100
                    if abs(change) > 5:
                        patterns["trends"].append({
                            "column": col,
                            "direction": "increasing" if change > 0 else "decreasing",
                            "change_pct": change
                        })
        
        # Detect correlations
        if len(numeric_cols) >= 2:
            try:
                corr_matrix = self.df[numeric_cols[:10]].corr()
                for i, col1 in enumerate(corr_matrix.columns):
                    for j, col2 in enumerate(corr_matrix.columns):
                        if i < j:
                            corr = corr_matrix.iloc[i, j]
                            if pd.notna(corr) and abs(corr) > 0.7:
                                patterns["correlations"].append({
                                    "columns": [col1, col2],
                                    "correlation": corr,
                                    "strength": "strong" if abs(corr) > 0.9 else "moderate"
                                })
            except:
                pass
        
        # Detect outliers using IQR method
        for col in numeric_cols[:5]:
            try:
                Q1 = self.df[col].quantile(0.25)
                Q3 = self.df[col].quantile(0.75)
                IQR = Q3 - Q1
                outlier_count = ((self.df[col] < Q1 - 1.5*IQR) | (self.df[col] > Q3 + 1.5*IQR)).sum()
                if outlier_count > 0:
                    patterns["outliers"][col] = int(outlier_count)
            except:
                pass
        
        return patterns


# ============================================================================
# CHART SELECTOR - Intelligently selects best visualizations
# ============================================================================

class ChartSelector:
    """Selects optimal chart types based on data characteristics."""
    
    @staticmethod
    def select_charts(profile: Dict, report_type: str, max_charts: int = 8) -> List[Dict]:
        """Select best charts for the given data profile and report type."""
        charts = []
        
        metrics = profile.get("roles", {}).get("metrics", [])
        dimensions = profile.get("roles", {}).get("dimensions", [])
        numeric_cols = profile.get("column_types", {}).get("numeric", [])
        categorical_cols = profile.get("column_types", {}).get("categorical", [])
        
        if report_type == "metrics":
            charts = ChartSelector._select_metrics_charts(metrics, numeric_cols, dimensions)
        elif report_type == "breakdown":
            charts = ChartSelector._select_breakdown_charts(dimensions, metrics)
        elif report_type == "summary":
            charts = ChartSelector._select_summary_charts(profile, metrics, dimensions)
        elif report_type == "executive":
            charts = ChartSelector._select_executive_charts(profile, metrics, dimensions)
        elif report_type == "predictive":
            charts = ChartSelector._select_predictive_charts(metrics, numeric_cols)
        elif report_type == "anomaly":
            charts = ChartSelector._select_anomaly_charts(profile, metrics, numeric_cols)
        
        return charts[:max_charts]
    
    @staticmethod
    def _select_metrics_charts(metrics: List, numeric_cols: List, dimensions: List) -> List[Dict]:
        """Charts for metrics analysis."""
        charts = []
        
        # Top metrics comparison bar chart
        if len(metrics) >= 2:
            charts.append({
                "type": "bar",
                "purpose": "metric_comparison",
                "columns": [m["name"] for m in metrics[:6]],
                "title": "Key Metrics Comparison",
                "description": "Comparing average values across numeric columns"
            })
        
        # Distribution histogram for top metric
        if metrics:
            top_metric = metrics[0]
            charts.append({
                "type": "histogram",
                "purpose": "distribution",
                "column": top_metric["name"],
                "title": f"Distribution of {top_metric['name']}",
                "description": f"Value distribution analysis"
            })
        
        # Trend line if there's sequential data
        if len(metrics) >= 1:
            charts.append({
                "type": "area",
                "purpose": "trend",
                "column": metrics[0]["name"],
                "title": f"{metrics[0]['name']} Trend",
                "description": "Sequential trend analysis"
            })
        
        # Metric by dimension if available
        if metrics and dimensions:
            charts.append({
                "type": "grouped_bar",
                "purpose": "metric_by_dimension",
                "metric": metrics[0]["name"],
                "dimension": dimensions[0]["name"],
                "title": f"{metrics[0]['name']} by {dimensions[0]['name']}",
                "description": "Performance breakdown"
            })
        
        # Correlation heatmap
        if len(numeric_cols) >= 3:
            charts.append({
                "type": "heatmap",
                "purpose": "correlation",
                "columns": numeric_cols[:8],
                "title": "Correlation Matrix",
                "description": "Relationships between metrics"
            })
        
        return charts
    
    @staticmethod
    def _select_breakdown_charts(dimensions: List, metrics: List) -> List[Dict]:
        """Charts for category breakdown."""
        charts = []
        
        for dim in dimensions[:3]:
            if dim["cardinality"] == "low":
                charts.append({
                    "type": "pie",
                    "purpose": "distribution",
                    "column": dim["name"],
                    "title": f"{dim['name']} Distribution",
                    "description": f"{dim['unique_count']} categories"
                })
            elif dim["cardinality"] == "medium":
                charts.append({
                    "type": "horizontal_bar",
                    "purpose": "ranking",
                    "column": dim["name"],
                    "title": f"Top {dim['name']} Categories",
                    "description": "Ranked by frequency"
                })
            else:
                charts.append({
                    "type": "treemap",
                    "purpose": "hierarchy",
                    "column": dim["name"],
                    "title": f"{dim['name']} Treemap",
                    "description": "Visual size by count"
                })
        
        # Metric by dimension
        if dimensions and metrics:
            charts.append({
                "type": "stacked_bar",
                "purpose": "composition",
                "dimension": dimensions[0]["name"],
                "metric": metrics[0]["name"] if metrics else None,
                "title": f"{metrics[0]['name'] if metrics else 'Values'} by {dimensions[0]['name']}",
                "description": "Composition breakdown"
            })
        
        return charts
    
    @staticmethod
    def _select_summary_charts(profile: Dict, metrics: List, dimensions: List) -> List[Dict]:
        """Charts for data summary."""
        charts = []
        quality = profile.get("quality", {})
        
        # Data quality gauge
        charts.append({
            "type": "gauge",
            "purpose": "quality_score",
            "value": quality.get("score", 0),
            "title": "Data Quality Score",
            "description": f"{quality.get('completeness', 0):.1f}% complete"
        })
        
        # Column type distribution
        col_types = profile.get("column_types", {})
        charts.append({
            "type": "donut",
            "purpose": "column_types",
            "data": {
                "Numeric": len(col_types.get("numeric", [])),
                "Categorical": len(col_types.get("categorical", [])),
                "DateTime": len(col_types.get("datetime", []))
            },
            "title": "Column Types",
            "description": "Data type distribution"
        })
        
        # Missing values by column
        if quality.get("missing_cells", 0) > 0:
            charts.append({
                "type": "horizontal_bar",
                "purpose": "missing_data",
                "title": "Missing Values by Column",
                "description": "Data completeness analysis"
            })
        
        # Top metrics summary
        if len(metrics) >= 2:
            charts.append({
                "type": "bar",
                "purpose": "metrics_summary",
                "columns": [m["name"] for m in metrics[:5]],
                "title": "Metrics Overview",
                "description": "Key numeric columns"
            })
        
        return charts
    
    @staticmethod
    def _select_executive_charts(profile: Dict, metrics: List, dimensions: List) -> List[Dict]:
        """Charts for executive summary."""
        charts = []
        
        # KPI cards (represented as special chart type)
        if metrics:
            charts.append({
                "type": "kpi_cards",
                "purpose": "key_metrics",
                "metrics": [m["name"] for m in metrics[:4]],
                "title": "Key Performance Indicators",
                "description": "Critical business metrics"
            })
        
        # Main performance chart
        if metrics and dimensions:
            charts.append({
                "type": "combo",
                "purpose": "performance_overview",
                "metric": metrics[0]["name"],
                "dimension": dimensions[0]["name"],
                "title": "Performance Overview",
                "description": "Key metric analysis"
            })
        
        # Trend chart
        if metrics:
            charts.append({
                "type": "area",
                "purpose": "trend_overview",
                "column": metrics[0]["name"],
                "title": "Trend Analysis",
                "description": "Performance trajectory"
            })
        
        return charts
    
    @staticmethod
    def _select_predictive_charts(metrics: List, numeric_cols: List) -> List[Dict]:
        """Charts for predictive analysis."""
        charts = []
        
        # These will be populated from ML model if available
        charts.append({
            "type": "feature_importance",
            "purpose": "ml_features",
            "title": "Feature Importance",
            "description": "Key prediction drivers"
        })
        
        charts.append({
            "type": "performance_metrics",
            "purpose": "ml_performance",
            "title": "Model Performance",
            "description": "Prediction accuracy"
        })
        
        if metrics:
            charts.append({
                "type": "scatter",
                "purpose": "prediction_scatter",
                "column": metrics[0]["name"],
                "title": "Actual vs Predicted",
                "description": "Model accuracy visualization"
            })
        
        return charts
    
    @staticmethod
    def _select_anomaly_charts(profile: Dict, metrics: List, numeric_cols: List) -> List[Dict]:
        """Charts for anomaly detection."""
        charts = []
        outliers = profile.get("patterns", {}).get("outliers", {})
        
        # Anomaly count by column
        if outliers:
            charts.append({
                "type": "bar",
                "purpose": "anomaly_count",
                "title": "Anomalies by Column",
                "description": "Outlier distribution"
            })
        
        # Box plot for outlier visualization
        if len(numeric_cols) >= 1:
            charts.append({
                "type": "box",
                "purpose": "outlier_detection",
                "columns": numeric_cols[:5],
                "title": "Statistical Outliers",
                "description": "IQR-based detection"
            })
        
        # Z-score distribution
        if metrics:
            charts.append({
                "type": "histogram",
                "purpose": "zscore_distribution",
                "column": metrics[0]["name"],
                "title": f"Z-Score Distribution: {metrics[0]['name']}",
                "description": "Anomaly threshold analysis"
            })
        
        return charts


# ============================================================================
# ADVANCED REPORT AGENT - Main orchestrator
# ============================================================================

class AdvancedReportAgent:
    """
    Advanced AI-powered report generation agent.
    Generates fully dynamic reports with zero hardcoded content.
    """
    
    def __init__(
        self,
        df: pd.DataFrame,
        user_id: str = "default",
        ml_model: Optional[Dict] = None,
        ml_training_data: Optional[Dict] = None,
        llm_client: Optional[Any] = None
    ):
        self.df = df
        self.user_id = user_id
        self.ml_model = ml_model
        self.ml_training_data = ml_training_data
        self.llm_client = llm_client
        
        # Profile the data
        self.profiler = DataProfiler(df)
        self.profile = self.profiler.profile
        
        # Chart colors
        self.colors = [
            "#6366F1", "#22C55E", "#F59E0B", "#EF4444", "#8B5CF6",
            "#06B6D4", "#EC4899", "#14B8A6", "#F97316", "#3B82F6"
        ]
        
        logger.info(f"AdvancedReportAgent initialized: {self.profile['shape']['rows']:,} rows, {self.profile['shape']['columns']} columns")
        logger.info(f"Detected domain: {self.profile['domain']['detected']} (confidence: {self.profile['domain']['confidence']:.2f})")
    
    def generate_report_sync(self, report_type: str) -> Dict[str, Any]:
        """Generate a fully dynamic report based on type (SYNCHRONOUS version)."""
        generators = {
            "metrics": self._generate_metrics_report_sync,
            "breakdown": self._generate_breakdown_report_sync,
            "summary": self._generate_summary_report_sync,
            "executive": self._generate_executive_report_sync,
            "predictive": self._generate_predictive_report_sync,
            "anomaly": self._generate_anomaly_report_sync
        }
        
        generator = generators.get(report_type)
        if not generator:
            return {"error": f"Unknown report type: {report_type}"}
        
        try:
            report = generator()
            return self._finalize_report(report, report_type)
        except Exception as e:
            logger.error(f"Error generating {report_type} report: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    async def generate_report(self, report_type: str) -> Dict[str, Any]:
        """Generate a fully dynamic report based on type (ASYNC version)."""
        generators = {
            "metrics": self._generate_metrics_report,
            "breakdown": self._generate_breakdown_report,
            "summary": self._generate_summary_report,
            "executive": self._generate_executive_report,
            "predictive": self._generate_predictive_report,
            "anomaly": self._generate_anomaly_report
        }
        
        generator = generators.get(report_type)
        if not generator:
            return {"error": f"Unknown report type: {report_type}"}
        
        try:
            report = await generator()
            return self._finalize_report(report, report_type)
        except Exception as e:
            logger.error(f"Error generating {report_type} report: {e}")
            return {"error": str(e)}
    
    def _finalize_report(self, report: Dict, report_type: str) -> Dict[str, Any]:
        """Finalize report with metadata."""
        final_report = {
            "success": True,
            "report": {
                **report,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "report_type": report_type,
                    "data_source": f"user_{self.user_id}",
                    "rows_analyzed": self.profile["shape"]["rows"],
                    "columns_analyzed": self.profile["shape"]["columns"],
                    "domain_detected": self.profile["domain"]["detected"],
                    "data_quality_score": self.profile["quality"]["score"]
                }
            }
        }
        
        # Log final report summary
        try:
            section_titles = [s.get("title", "Untitled") for s in report.get("sections", [])]
            logger.info(f"✅ [REPORT GENERATED] Type: {report_type}")
            logger.info(f"   Shape: {self.profile['shape']['rows']} rows x {self.profile['shape']['columns']} cols")
            logger.info(f"   Sections ({len(section_titles)}): {section_titles}")
        except Exception as e:
            logger.error(f"Error logging report summary: {e}")
            
        return final_report
    
    # =========================================================================
    # SYNCHRONOUS REPORT GENERATORS (for reliable sync execution)
    # =========================================================================
    
    def _generate_metrics_report_sync(self) -> Dict[str, Any]:
        """Generate metrics analysis report - SYNC version with REAL data."""
        sections = []
        metrics = self.profile["roles"]["metrics"]
        numeric_cols = self.profile["column_types"]["numeric"]
        dimensions = self.profile["roles"]["dimensions"]
        
        # Section 1: Key Metrics Overview (from REAL data)
        overview_content = f"**Dataset**: {self.profile['shape']['rows']:,} rows × {self.profile['shape']['columns']} columns\n\n"
        overview_content += f"**Numeric Columns Analyzed**: {len(metrics)}\n\n"
        if metrics:
            overview_content += "**Key Statistics:**\n"
            for m in metrics[:5]:
                overview_content += f"• **{m['name']}**: Mean={m['mean']:,.2f}, Min={m['min']:,.2f}, Max={m['max']:,.2f}\n"
        sections.append({"title": "Key Metrics Overview", "content": overview_content})
        
        # Section 2: Metrics Comparison Chart (REAL data)
        if len(metrics) >= 2:
            chart_data = [{"name": m["name"][:15], "value": round(m["mean"], 2)} for m in metrics[:8]]
            sections.append({
                "title": "Metrics Comparison",
                "content": f"Average values across {len(metrics)} numeric columns in your dataset.",
                "chartType": "bar",
                "data": chart_data
            })
        
        # Section 3: Distribution of Top Metric (REAL data)
        if metrics:
            top_metric = metrics[0]
            hist_data = self._create_histogram_data(top_metric["name"])
            sections.append({
                "title": f"Distribution: {top_metric['name']}",
                "content": f"Value distribution. Mean: {top_metric['mean']:,.2f}, Std: {top_metric['std']:,.2f}",
                "chartType": "bar",
                "data": hist_data
            })
        
        # Section 4: Trend Analysis (REAL patterns)
        trends = self.profile["patterns"]["trends"]
        if trends:
            trend_content = "**Detected Trends:**\n\n"
            for t in trends[:5]:
                emoji = "📈" if t["direction"] == "increasing" else "📉"
                trend_content += f"• **{t['column']}**: {emoji} {abs(t['change_pct']):.1f}% {t['direction']}\n"
            sections.append({"title": "Trend Analysis", "content": trend_content})
        
        # Section 5: Correlation Analysis (REAL correlations)
        correlations = self.profile["patterns"]["correlations"]
        if correlations:
            corr_content = "**Strong Correlations Found:**\n\n"
            for c in correlations[:5]:
                strength = "🔴 Strong" if abs(c["correlation"]) > 0.9 else "🟠 Moderate"
                direction = "positive" if c["correlation"] > 0 else "negative"
                corr_content += f"• **{c['columns'][0]}** ↔ **{c['columns'][1]}**: {strength} {direction} ({c['correlation']:.2f})\n"
            sections.append({"title": "Correlation Analysis", "content": corr_content})
        
        # Section 6: Metric by Dimension (REAL grouping)
        if metrics and dimensions:
            grouped_data = self._create_grouped_data(metrics[0]["name"], dimensions[0]["name"])
            if grouped_data:
                sections.append({
                    "title": f"{metrics[0]['name']} by {dimensions[0]['name']}",
                    "content": f"Breakdown across {dimensions[0]['unique_count']} categories.",
                    "chartType": "horizontal_bar",
                    "data": grouped_data
                })
        
        # Section 7: Statistical Variability (REAL std dev)
        if len(metrics) >= 2:
            std_data = [{"name": m["name"][:12], "value": round(m["std"], 2)} for m in metrics[:8]]
            sections.append({
                "title": "Variability Analysis",
                "content": "Standard deviation comparison - higher values indicate more spread.",
                "chartType": "horizontal_bar",
                "data": std_data
            })
        
        return {"title": self._generate_dynamic_title("Metrics Analysis", metrics), "type": "metrics", "sections": sections}
    
    def _generate_breakdown_report_sync(self) -> Dict[str, Any]:
        """Generate category breakdown report - SYNC version with REAL data."""
        sections = []
        dimensions = self.profile["roles"]["dimensions"]
        metrics = self.profile["roles"]["metrics"]
        
        # Section 1: Category Overview (REAL data)
        overview = f"**Categorical Columns**: {len(dimensions)}\n\n"
        for dim in dimensions[:5]:
            overview += f"• **{dim['name']}**: {dim['unique_count']} unique values ({dim['cardinality']} cardinality)\n"
        sections.append({"title": "Category Overview", "content": overview})
        
        # Sections 2-4: Distribution charts for each dimension (REAL data)
        for i, dim in enumerate(dimensions[:3]):
            dist = self.df[dim["name"]].value_counts().head(10)
            chart_data = [{"name": str(k)[:20], "value": int(v)} for k, v in dist.items()]
            chart_type = "pie" if dim["cardinality"] == "low" else "horizontal_bar"
            sections.append({
                "title": f"{dim['name']} Breakdown",
                "content": f"Distribution across {dim['unique_count']} categories.",
                "chartType": chart_type,
                "data": chart_data
            })
        
        # Section 5: Metric by Category (REAL grouping)
        if dimensions and metrics:
            try:
                grouped = self.df.groupby(dimensions[0]["name"])[metrics[0]["name"]].mean().nlargest(10)
                chart_data = [{"name": str(k)[:15], "value": round(v, 2)} for k, v in grouped.items()]
                sections.append({
                    "title": f"Average {metrics[0]['name']} by {dimensions[0]['name']}",
                    "content": f"Performance comparison across categories.",
                    "chartType": "bar",
                    "data": chart_data
                })
            except:
                pass
        
        # Section 6: Concentration Analysis (REAL calculation)
        if dimensions:
            dim = dimensions[0]
            dist = self.df[dim["name"]].value_counts()
            total = dist.sum()
            top1_pct = (dist.iloc[0] / total * 100) if len(dist) > 0 else 0
            top3_pct = (dist.head(3).sum() / total * 100) if len(dist) >= 3 else top1_pct
            concentration = f"**Concentration Analysis for {dim['name']}:**\n\n"
            concentration += f"• Top 1 category: {top1_pct:.1f}% of data\n"
            concentration += f"• Top 3 categories: {top3_pct:.1f}% of data\n"
            concentration += f"• Total categories: {len(dist)}\n"
            sections.append({"title": "Concentration Analysis", "content": concentration})
        
        return {"title": self._generate_dynamic_title("Data Breakdown", dimensions), "type": "breakdown", "sections": sections}
    
    def _generate_summary_report_sync(self) -> Dict[str, Any]:
        """Generate data summary report - SYNC version with REAL data."""
        sections = []
        quality = self.profile["quality"]
        col_types = self.profile["column_types"]
        
        # Section 1: Dataset Overview (REAL data)
        overview = f"""**Dataset Statistics:**
• Total Records: {self.profile['shape']['rows']:,}
• Total Columns: {self.profile['shape']['columns']}
• Numeric Columns: {len(col_types['numeric'])}
• Categorical Columns: {len(col_types['categorical'])}
• DateTime Columns: {len(col_types['datetime'])}
• Missing Values: {quality['missing_cells']:,} ({100 - quality['completeness']:.1f}%)
• Duplicate Rows: {quality['duplicate_rows']:,}

**Columns:** {', '.join(self.profile['columns'][:15])}{'...' if len(self.profile['columns']) > 15 else ''}"""
        sections.append({"title": "Dataset Overview", "content": overview})
        
        # Section 2: Column Types Chart (REAL data)
        type_data = [
            {"name": "Numeric", "value": len(col_types["numeric"])},
            {"name": "Categorical", "value": len(col_types["categorical"])},
            {"name": "DateTime", "value": len(col_types["datetime"])}
        ]
        type_data = [d for d in type_data if d["value"] > 0]
        if type_data:
            sections.append({
                "title": "Column Type Distribution",
                "content": "Breakdown of data types in your dataset.",
                "chartType": "pie",
                "data": type_data
            })
        
        # Section 3: Statistical Summary (REAL stats)
        metrics = self.profile["roles"]["metrics"]
        stats_content = "**Statistical Summary:**\n\n"
        for m in metrics[:6]:
            stats_content += f"• **{m['name']}**: Mean={m['mean']:,.2f}, Min={m['min']:,.2f}, Max={m['max']:,.2f}\n"
        sections.append({"title": "Statistical Summary", "content": stats_content})
        
        # Section 4: Data Quality (REAL assessment)
        grade = "A" if quality["score"] >= 90 else "B" if quality["score"] >= 75 else "C" if quality["score"] >= 60 else "D"
        quality_content = f"""**Data Quality Score: {quality['score']:.0f}/100 (Grade: {grade})**

• **Completeness**: {quality['completeness']:.1f}%
• **Uniqueness**: {quality['uniqueness']:.1f}%
• **Missing Values**: {quality['missing_cells']:,} cells
• **Duplicate Rows**: {quality['duplicate_rows']:,}"""
        sections.append({"title": "Data Quality Assessment", "content": quality_content})
        
        # Section 5: Quality Donut Chart (REAL data)
        quality_data = [
            {"name": "Complete", "value": int(quality["completeness"])},
            {"name": "Missing", "value": int(100 - quality["completeness"])}
        ]
        sections.append({
            "title": "Data Completeness",
            "content": f"Overall quality score: {quality['score']:.0f}/100",
            "chartType": "donut",
            "data": quality_data
        })
        
        # Section 6: Missing Values by Column (REAL data)
        missing = self.df.isna().sum()
        missing = missing[missing > 0].sort_values(ascending=False).head(10)
        if len(missing) > 0:
            missing_data = [{"name": col[:12], "value": int(val)} for col, val in missing.items()]
            sections.append({
                "title": "Missing Values by Column",
                "content": "Columns with incomplete data.",
                "chartType": "horizontal_bar",
                "data": missing_data
            })
        
        return {"title": "Comprehensive Data Summary Report", "type": "summary", "sections": sections}
    
    def _generate_executive_report_sync(self) -> Dict[str, Any]:
        """Generate executive summary report - SYNC version with REAL data."""
        sections = []
        metrics = self.profile["roles"]["metrics"]
        dimensions = self.profile["roles"]["dimensions"]
        domain = self.profile["domain"]["detected"]
        patterns = self.profile["patterns"]
        quality = self.profile["quality"]
        
        # Section 1: Executive Summary (REAL data)
        exec_summary = f"""This {domain} dataset contains **{self.profile['shape']['rows']:,} records** across **{self.profile['shape']['columns']} columns**.

Key metrics analyzed include {', '.join([m['name'] for m in metrics[:3]])}. The data has a quality score of **{quality['score']:.0f}/100** with {quality['completeness']:.1f}% completeness.

{len(dimensions)} categorical dimensions were identified for segmentation analysis."""
        sections.append({"title": "Executive Summary", "content": exec_summary})
        
        # Section 2: KPI Dashboard (REAL metrics)
        if metrics:
            kpi_content = "**Key Performance Indicators:**\n\n"
            for m in metrics[:4]:
                emoji = "💰" if m["type"] == "monetary" else "📊" if m["type"] == "count" else "📈"
                kpi_content += f"| {emoji} **{m['name']}** | Total: {m['total']:,.2f} | Avg: {m['mean']:,.2f} |\n"
            sections.append({"title": "Key Performance Indicators", "content": kpi_content})
        
        # Section 3: Performance Chart (REAL data)
        if metrics and dimensions:
            try:
                grouped = self.df.groupby(dimensions[0]["name"])[metrics[0]["name"]].sum().nlargest(8)
                chart_data = [{"name": str(k)[:15], "value": round(v, 2)} for k, v in grouped.items()]
                sections.append({
                    "title": f"{metrics[0]['name']} by {dimensions[0]['name']}",
                    "content": "Top performing categories.",
                    "chartType": "bar",
                    "data": chart_data
                })
            except:
                pass
        
        # Section 4: Trend Overview (REAL data)
        if metrics:
            trend_data = self._create_trend_data(metrics[0]["name"])
            sections.append({
                "title": f"{metrics[0]['name']} Trend",
                "content": "Performance trajectory showing overall trend.",
                "chartType": "area",
                "data": trend_data
            })
        
        # Section 5: Key Findings (REAL patterns)
        findings = []
        if metrics:
            findings.append(f"📊 **Primary Metric**: {metrics[0]['name']} with total value of {metrics[0]['total']:,.2f}")
        for trend in patterns.get("trends", [])[:2]:
            emoji = "📈" if trend["direction"] == "increasing" else "📉"
            findings.append(f"{emoji} **{trend['column']}** shows {abs(trend['change_pct']):.1f}% {trend['direction']} trend")
        for corr in patterns.get("correlations", [])[:1]:
            findings.append(f"🔗 Strong correlation between **{corr['columns'][0]}** and **{corr['columns'][1]}** ({corr['correlation']:.2f})")
        if quality["completeness"] < 95:
            findings.append(f"⚠️ Data completeness at {quality['completeness']:.1f}%")
        
        findings_content = "\n".join(f"• {f}" for f in findings) if findings else "No significant findings."
        sections.append({"title": "Key Findings", "content": findings_content})
        
        # Section 6: Strategic Recommendations (based on REAL data)
        recommendations = []
        if quality["completeness"] < 95:
            recommendations.append(f"📌 **Improve Data Quality**: Address {quality['missing_cells']:,} missing values.")
        if patterns.get("trends"):
            trend = patterns["trends"][0]
            recommendations.append(f"📈 **Monitor {trend['column']}**: Shows {trend['change_pct']:.1f}% {trend['direction']} trend.")
        if patterns.get("correlations"):
            corr = patterns["correlations"][0]
            recommendations.append(f"🔗 **Leverage Relationship**: {corr['columns'][0]} and {corr['columns'][1]} are correlated.")
        if not recommendations:
            recommendations.append("✅ Data quality is good. Continue monitoring key metrics.")
        
        rec_content = "\n".join(recommendations)
        sections.append({"title": "Strategic Recommendations", "content": rec_content})
        
        return {"title": f"Executive Report: {domain.title()} Analysis", "type": "executive", "sections": sections}
    
    def _generate_predictive_report_sync(self) -> Dict[str, Any]:
        """Generate predictive analysis report - SYNC version with REAL ML data."""
        sections = []
        
        if not self.ml_model:
            sections.append({
                "title": "No ML Model Available",
                "content": "**Please train a model first!**\n\nGo to the Predict tab and train a model to unlock predictive analytics."
            })
            return {"title": "Predictive Analysis Report", "type": "predictive", "sections": sections}
        
        model_info = self.ml_model
        metrics = model_info.get("metrics", {})
        task_type = model_info.get("task_type", "classification")
        model_name = model_info.get("model_name", "ML Model")
        target_col = model_info.get("target_column", "target")
        features = model_info.get("features", model_info.get("feature_columns", []))
        feature_importance = model_info.get("feature_importance", {})
        
        # Section 1: Model Overview (REAL model data)
        model_content = f"""**Trained Model Details:**

• **Algorithm**: {model_name}
• **Task Type**: {task_type.upper()}
• **Target Variable**: `{target_col}`
• **Input Features**: {len(features)} columns"""
        if features and len(features) <= 10:
            model_content += f"\n• **Features**: {', '.join(features[:10])}"
        sections.append({"title": f"Model Overview: {model_name}", "content": model_content})
        
        # Section 2: Performance Metrics (REAL metrics)
        if task_type == "classification":
            accuracy = metrics.get("accuracy", metrics.get("f1_score", 0))
            assessment = "🟢 **Excellent**" if accuracy >= 0.9 else "🟡 **Good**" if accuracy >= 0.75 else "🟠 **Moderate**" if accuracy >= 0.6 else "🔴 **Needs Improvement**"
            perf_content = f"""**Classification Performance on `{target_col}`:**

{assessment}

| Metric | Score |
|--------|-------|
| **Accuracy** | {metrics.get('accuracy', 0) * 100:.1f}% |
| **Precision** | {metrics.get('precision', 0) * 100:.1f}% |
| **Recall** | {metrics.get('recall', 0) * 100:.1f}% |
| **F1 Score** | {metrics.get('f1_score', metrics.get('f1', 0)) * 100:.1f}% |"""
        else:
            r2 = metrics.get("r2", metrics.get("r2_score", 0))
            assessment = "🟢 **Excellent**" if r2 >= 0.9 else "🟡 **Good**" if r2 >= 0.7 else "🟠 **Moderate**" if r2 >= 0.5 else "🔴 **Limited**"
            perf_content = f"""**Regression Performance on `{target_col}`:**

{assessment}

| Metric | Value |
|--------|-------|
| **R² Score** | {r2 * 100:.1f}% |
| **MAE** | {metrics.get('mae', 0):,.4f} |
| **RMSE** | {metrics.get('rmse', 0):,.4f} |"""
        sections.append({"title": f"Performance: Predicting {target_col}", "content": perf_content})
        
        # Section 3: Performance Chart (REAL metrics)
        if task_type == "classification":
            chart_data = []
            for name, key in [("Accuracy", "accuracy"), ("Precision", "precision"), ("Recall", "recall"), ("F1", "f1_score")]:
                value = metrics.get(key, metrics.get(key.replace("_score", ""), 0))
                if value > 0:
                    chart_data.append({"name": name, "value": round(value * 100, 1)})
        else:
            r2 = max(metrics.get("r2", metrics.get("r2_score", 0)), 0)
            chart_data = [
                {"name": "R² Score", "value": round(r2 * 100, 1)},
                {"name": "Explained Var", "value": round(metrics.get("explained_variance", r2) * 100, 1)}
            ]
        if chart_data:
            sections.append({
                "title": f"{task_type.title()} Metrics",
                "content": f"Model performance on `{target_col}`.",
                "chartType": "bar",
                "data": chart_data
            })
        
        # Section 4: Feature Importance (REAL from model)
        if feature_importance:
            sorted_fi = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]
            fi_data = [{"name": k[:15], "value": round(v * 100, 1)} for k, v in sorted_fi]
            top_feature = sorted_fi[0][0] if sorted_fi else "Unknown"
            sections.append({
                "title": f"Feature Importance for {target_col}",
                "content": f"Top predictor: `{top_feature}` drives predictions.",
                "chartType": "horizontal_bar",
                "data": fi_data
            })
            
            # Also generate Plotly feature importance chart if available
            if ML_CHARTS_AVAILABLE and len(sorted_fi) > 0:
                try:
                    features_list = [f[0] for f in sorted_fi]
                    importances_list = [f[1] for f in sorted_fi]
                    fi_plotly = MLChartGenerator.feature_importance_chart(features_list, importances_list)
                    if fi_plotly:
                        sections.append({
                            "title": f"📊 Feature Importance (Plotly)",
                            "content": "Interactive visualization of feature contributions.",
                            "chartType": "plotly",
                            "data": fi_plotly
                        })
                except Exception as e:
                    logger.debug(f"Could not generate FI chart: {e}")
        
        # Section 5: Generate REAL ML Charts from training data (y_test, y_pred)
        if self.ml_training_data and ML_CHARTS_AVAILABLE:
            y_test = self.ml_training_data.get('y_test')
            y_pred = self.ml_training_data.get('y_pred')
            
            if y_test is not None and y_pred is not None:
                try:
                    if task_type == "classification":
                        # Confusion Matrix Chart
                        cm_chart = MLChartGenerator.confusion_matrix_chart(y_test, y_pred)
                        if cm_chart:
                            sections.append({
                                "title": f"📊 Confusion Matrix: {target_col}",
                                "content": "Classification results. Diagonal = correct predictions.",
                                "chartType": "plotly",
                                "data": cm_chart
                            })
                        
                        # ROC Curve (if binary or limited classes)
                        try:
                            unique_classes = len(np.unique(y_test))
                            if unique_classes <= 5:
                                roc_chart = MLChartGenerator.roc_curve_chart(y_test, y_pred)
                                if roc_chart:
                                    sections.append({
                                        "title": f"📈 ROC Curve",
                                        "content": "True positive vs false positive trade-off.",
                                        "chartType": "plotly",
                                        "data": roc_chart
                                    })
                        except:
                            pass
                    else:
                        # Regression: Actual vs Predicted
                        avp_chart = MLChartGenerator.actual_vs_predicted_chart(y_test, y_pred)
                        if avp_chart:
                            sections.append({
                                "title": f"📉 Actual vs Predicted: {target_col}",
                                "content": "Points near diagonal = accurate predictions.",
                                "chartType": "plotly",
                                "data": avp_chart
                            })
                        
                        # Residuals Chart
                        res_chart = MLChartGenerator.residuals_chart(y_test, y_pred)
                        if res_chart:
                            sections.append({
                                "title": f"📊 Residuals Distribution",
                                "content": "Prediction errors. Centered at 0 = unbiased model.",
                                "chartType": "plotly",
                                "data": res_chart
                            })
                    
                    logger.info(f"✅ Generated real ML charts for predictive report")
                except Exception as e:
                    logger.warning(f"Could not generate ML charts: {e}")
        
        # Section 6: Saved base64 charts (fallback)
        saved_charts = self.ml_training_data.get("saved_charts", {}) if self.ml_training_data else {}
        if saved_charts:
            for chart_key, base64_img in saved_charts.items():
                if base64_img and chart_key not in ['confusion_matrix', 'actual_vs_predicted', 'residuals_analysis']:
                    chart_info = self._get_ml_chart_info(chart_key, target_col, metrics)
                    sections.append({
                        "title": chart_info["title"],
                        "content": chart_info["description"],
                        "chartType": "image",
                        "data": {"image": base64_img}
                    })
        
        # Section 7: Target Distribution (REAL data)
        if target_col in self.df.columns:
            if task_type == "classification":
                dist = self.df[target_col].value_counts().head(8)
                chart_data = [{"name": str(k), "value": int(v)} for k, v in dist.items()]
                sections.append({
                    "title": f"Target Distribution: {target_col}",
                    "content": f"Class distribution. Most common: `{dist.index[0]}`",
                    "chartType": "pie",
                    "data": chart_data
                })
            else:
                data = self.df[target_col].dropna()
                stat_content = f"""**`{target_col}` Statistics:**
• Mean: {data.mean():,.2f}
• Std Dev: {data.std():,.2f}
• Range: {data.min():,.2f} to {data.max():,.2f}
• Records: {len(data):,}"""
                sections.append({"title": f"Target Statistics: {target_col}", "content": stat_content})
        
        return {"title": f"Predictive Analysis: {target_col} using {model_name}", "type": "predictive", "sections": sections}
    
    def _generate_anomaly_report_sync(self) -> Dict[str, Any]:
        """Generate anomaly detection report - SYNC version with REAL ML data and charts."""
        sections = []
        numeric_cols = self.profile["column_types"]["numeric"]
        outliers = self.profile["patterns"]["outliers"]
        
        # Section 1: Anomaly Summary (REAL detection)
        total_anomalies = sum(outliers.values()) if outliers else 0
        summary = f"""**Anomaly Detection Summary:**

• **Total Anomalies Found**: {total_anomalies:,}
• **Detection Method**: IQR (Interquartile Range) + Z-Score
• **Columns Analyzed**: {len(numeric_cols)}

"""
        if outliers:
            summary += "**Anomalies by Column:**\n"
            for col, count in sorted(outliers.items(), key=lambda x: x[1], reverse=True)[:5]:
                summary += f"• **{col}**: {count:,} anomalies detected\n"
        else:
            summary += "✅ **No significant anomalies detected!**"
        sections.append({"title": "Anomaly Detection Summary", "content": summary})
        
        # Section 2: Anomaly Count Chart (REAL data)
        if outliers:
            outlier_data = [{"name": k[:12], "value": v} for k, v in sorted(outliers.items(), key=lambda x: x[1], reverse=True)[:10]]
            sections.append({
                "title": "Anomalies by Column",
                "content": "Number of outliers detected using IQR method.",
                "chartType": "bar",
                "data": outlier_data
            })
        
        # Section 3: Statistical Outlier Analysis (REAL calculation)
        for col in numeric_cols[:2]:
            data = self.df[col].dropna()
            q1, q3 = data.quantile(0.25), data.quantile(0.75)
            iqr = q3 - q1
            lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            outliers_low = (data < lower).sum()
            outliers_high = (data > upper).sum()
            
            analysis = f"""**IQR Analysis for {col}:**

• **Q1 (25th percentile)**: {q1:,.2f}
• **Q3 (75th percentile)**: {q3:,.2f}
• **IQR**: {iqr:,.2f}
• **Lower Bound**: {lower:,.2f}
• **Upper Bound**: {upper:,.2f}
• **Below Lower Bound**: {outliers_low:,} records
• **Above Upper Bound**: {outliers_high:,} records"""
            sections.append({"title": f"Outlier Analysis: {col}", "content": analysis})
        
        # Section 4: Distribution Chart (REAL data)
        if numeric_cols:
            col = numeric_cols[0]
            data = self.df[col].dropna()
            dist_data = [
                {"name": "Min", "value": round(data.min(), 2)},
                {"name": "Q1", "value": round(data.quantile(0.25), 2)},
                {"name": "Median", "value": round(data.median(), 2)},
                {"name": "Q3", "value": round(data.quantile(0.75), 2)},
                {"name": "Max", "value": round(data.max(), 2)}
            ]
            sections.append({
                "title": f"Distribution: {col}",
                "content": "Statistical distribution showing outlier ranges.",
                "chartType": "bar",
                "data": dist_data
            })
        
        # Section 5: Z-Score Analysis (REAL calculation)
        zscore_content = "**Z-Score Analysis (|z| > 3 = Anomaly):**\n\n"
        for col in numeric_cols[:3]:
            data = self.df[col].dropna()
            mean, std = data.mean(), data.std()
            if std > 0:
                z_scores = np.abs((data - mean) / std)
                anomalies = (z_scores > 3).sum()
                max_z = z_scores.max()
                zscore_content += f"• **{col}**: {anomalies} anomalies (max z-score: {max_z:.2f})\n"
        sections.append({"title": "Z-Score Analysis", "content": zscore_content})
        
        # Section 6: Generate REAL ML Charts from training data
        if self.ml_training_data and ML_CHARTS_AVAILABLE:
            y_test = self.ml_training_data.get('y_test')
            y_pred = self.ml_training_data.get('y_pred')
            task_type = self.ml_training_data.get('task_type', 'classification')
            target_col = self.ml_training_data.get('target_column', 'target')
            
            if y_test is not None and y_pred is not None:
                try:
                    if task_type == "classification":
                        # Confusion Matrix for anomaly analysis
                        cm_chart = MLChartGenerator.confusion_matrix_chart(y_test, y_pred)
                        if cm_chart:
                            sections.append({
                                "title": f"📊 ML Confusion Matrix",
                                "content": f"Model predictions for `{target_col}`. Misclassifications may indicate anomalies.",
                                "chartType": "plotly",
                                "data": cm_chart
                            })
                    else:
                        # Residuals chart shows anomalous predictions
                        res_chart = MLChartGenerator.residuals_chart(y_test, y_pred)
                        if res_chart:
                            sections.append({
                                "title": f"📊 Prediction Residuals",
                                "content": f"Residual distribution for `{target_col}`. Large residuals = potential anomalies.",
                                "chartType": "plotly",
                                "data": res_chart
                            })
                        
                        # Actual vs Predicted
                        avp_chart = MLChartGenerator.actual_vs_predicted_chart(y_test, y_pred)
                        if avp_chart:
                            sections.append({
                                "title": f"📉 Actual vs Predicted",
                                "content": "Points far from diagonal indicate anomalous predictions.",
                                "chartType": "plotly",
                                "data": avp_chart
                            })
                    
                    logger.info(f"✅ Generated real ML charts for anomaly report")
                except Exception as e:
                    logger.warning(f"Could not generate ML anomaly charts: {e}")
        
        # Section 7: Saved base64 charts (fallback if Plotly failed)
        if self.ml_training_data:
            saved_charts = self.ml_training_data.get("saved_charts", {})
            for chart_key in ["confusion_matrix", "residuals_analysis", "actual_vs_predicted"]:
                # Only use saved charts if we didn't already generate Plotly versions
                if chart_key in saved_charts and saved_charts[chart_key]:
                    chart_info = self._get_ml_chart_info(chart_key, "target", {})
                    sections.append({
                        "title": f"ML {chart_info['title']}",
                        "content": chart_info["description"],
                        "chartType": "image",
                        "data": {"image": saved_charts[chart_key]}
                    })
        
        # Section 8: Anomaly Patterns (REAL detection)
        if outliers and len(outliers) >= 2:
            pattern_content = "**Detected Patterns:**\n\n"
            total_anomalies = sum(outliers.values())
            anomaly_rate = (total_anomalies / len(self.df)) * 100
            pattern_content += f"• Overall anomaly rate: {anomaly_rate:.2f}%\n"
            if anomaly_rate > 5:
                pattern_content += "• ⚠️ High anomaly rate suggests data quality issues\n"
            else:
                pattern_content += "• ✅ Anomaly rate within normal range\n"
            sections.append({"title": "Anomaly Patterns", "content": pattern_content})
        
        # Section 9: Recommendations (based on REAL findings)
        rec_content = "**Recommendations:**\n\n"
        if total_anomalies > 0:
            rec_content += f"1. **Review {total_anomalies:,} flagged records** - manually inspect anomalous values\n"
            rec_content += "2. **Investigate root cause** - determine if outliers are errors or genuine\n"
            rec_content += "3. **Consider data cleaning** - remove or correct erroneous data\n"
        else:
            rec_content += "✅ No significant anomalies found. Data appears consistent.\n"
        sections.append({"title": "Recommendations", "content": rec_content})
        
        return {"title": "Anomaly Detection Report", "type": "anomaly", "sections": sections}
    
    # =========================================================================
    # ASYNC REPORT GENERATORS (use these if you need AI insights)
    # =========================================================================
    
    async def _generate_breakdown_report(self) -> Dict[str, Any]:
        """Generate category breakdown report - fully dynamic."""
        sections = []
        dimensions = self.profile["roles"]["dimensions"]
        metrics = self.profile["roles"]["metrics"]
        
        # Section 1: Category Overview
        overview = self._build_category_overview(dimensions)
        sections.append({
            "title": "Category Overview",
            "content": overview
        })
        
        # Section 2-4: Dynamic charts for each dimension
        for i, dim in enumerate(dimensions[:3]):
            dist = self.df[dim["name"]].value_counts().head(10)
            chart_data = [{"name": str(k)[:20], "value": int(v)} for k, v in dist.items()]
            
            # Select chart type based on cardinality
            if dim["cardinality"] == "low":
                chart_type = "pie"
                desc = f"Distribution across {dim['unique_count']} categories"
            else:
                chart_type = "horizontal_bar"
                desc = f"Top 10 of {dim['unique_count']} categories"
            
            sections.append({
                "title": f"{dim['name']} Breakdown",
                "content": desc,
                "chartType": chart_type,
                "data": chart_data
            })
        
        # Section 5: Cross-tabulation
        if len(dimensions) >= 2 and metrics:
            cross_data = self._create_crosstab_data(dimensions[0]["name"], dimensions[1]["name"], metrics[0]["name"] if metrics else None)
            if cross_data:
                sections.append({
                    "title": f"{dimensions[0]['name']} vs {dimensions[1]['name']}",
                    "content": f"Cross-tabulation showing relationship between dimensions.",
                    "chartType": "stacked_bar",
                    "data": cross_data
                })
        
        # Section 6: Concentration Analysis
        if dimensions:
            concentration = self._calculate_concentration(dimensions[0]["name"])
            sections.append({
                "title": "Concentration Analysis",
                "content": concentration
            })
        
        # Section 7: AI Insights
        ai_insight = await self._generate_ai_insight("breakdown", dimensions, sections)
        if ai_insight:
            sections.append({
                "title": "AI Category Insights",
                "content": ai_insight
            })
        
        return {
            "title": self._generate_dynamic_title("Data Breakdown", dimensions),
            "type": "breakdown",
            "sections": sections
        }
    
    # =========================================================================
    # SUMMARY REPORT
    # =========================================================================
    
    async def _generate_summary_report(self) -> Dict[str, Any]:
        """Generate data summary report - fully dynamic."""
        sections = []
        quality = self.profile["quality"]
        
        # Section 1: Dataset Overview
        overview = self._build_dataset_overview()
        sections.append({
            "title": "Dataset Overview",
            "content": overview
        })
        
        # Section 2: Column Types Chart
        col_types = self.profile["column_types"]
        type_data = [
            {"name": "Numeric", "value": len(col_types["numeric"])},
            {"name": "Categorical", "value": len(col_types["categorical"])},
            {"name": "DateTime", "value": len(col_types["datetime"])}
        ]
        type_data = [d for d in type_data if d["value"] > 0]
        
        if type_data:
            sections.append({
                "title": "Column Type Distribution",
                "content": "Breakdown of data types in your dataset.",
                "chartType": "pie",
                "data": type_data
            })
        
        # Section 3: Statistical Summary
        stats_content = self._build_statistical_summary()
        sections.append({
            "title": "Statistical Summary",
            "content": stats_content
        })
        
        # Section 4: Data Quality
        quality_content = self._build_quality_summary(quality)
        sections.append({
            "title": "Data Quality Assessment",
            "content": quality_content
        })
        
        # Section 5: Quality Score Visualization
        quality_data = [
            {"name": "Complete", "value": int(quality["completeness"])},
            {"name": "Missing", "value": int(100 - quality["completeness"])}
        ]
        sections.append({
            "title": "Data Completeness",
            "content": f"Overall data quality score: {quality['score']:.0f}/100",
            "chartType": "donut",
            "data": quality_data
        })
        
        # Section 6: Missing Values Analysis
        missing_data = self._get_missing_values_data()
        if missing_data:
            sections.append({
                "title": "Missing Values by Column",
                "content": "Columns with incomplete data that may need attention.",
                "chartType": "horizontal_bar",
                "data": missing_data
            })
        
        # Section 7: AI Recommendations
        ai_insight = await self._generate_ai_insight("summary", quality, sections)
        if ai_insight:
            sections.append({
                "title": "AI Data Quality Recommendations",
                "content": ai_insight
            })
        
        return {
            "title": "Comprehensive Data Summary Report",
            "type": "summary",
            "sections": sections
        }
    
    # =========================================================================
    # EXECUTIVE REPORT
    # =========================================================================
    
    async def _generate_executive_report(self) -> Dict[str, Any]:
        """Generate executive summary report - fully dynamic."""
        sections = []
        metrics = self.profile["roles"]["metrics"]
        dimensions = self.profile["roles"]["dimensions"]
        domain = self.profile["domain"]["detected"]
        
        # Section 1: Executive Summary
        exec_summary = await self._build_executive_summary()
        sections.append({
            "title": "Executive Summary",
            "content": exec_summary
        })
        
        # Section 2: KPI Dashboard
        if metrics:
            kpi_content = self._build_kpi_dashboard(metrics[:4])
            sections.append({
                "title": "Key Performance Indicators",
                "content": kpi_content
            })
        
        # Section 3: Performance Overview Chart
        if metrics and dimensions:
            grouped = self.df.groupby(dimensions[0]["name"])[metrics[0]["name"]].sum().nlargest(8)
            chart_data = [{"name": str(k)[:15], "value": round(v, 2)} for k, v in grouped.items()]
            
            sections.append({
                "title": f"{metrics[0]['name']} by {dimensions[0]['name']}",
                "content": f"Top performing {dimensions[0]['name']} categories by {metrics[0]['name']}.",
                "chartType": "bar",
                "data": chart_data
            })
        
        # Section 4: Trend Overview
        if metrics:
            trend_data = self._create_trend_data(metrics[0]["name"])
            sections.append({
                "title": f"{metrics[0]['name']} Trend",
                "content": "Performance trajectory showing overall trend direction.",
                "chartType": "area",
                "data": trend_data
            })
        
        # Section 5: Key Findings
        findings = self._extract_key_findings()
        sections.append({
            "title": "Key Findings",
            "content": findings
        })
        
        # Section 6: Strategic Recommendations
        recommendations = await self._generate_strategic_recommendations()
        sections.append({
            "title": "Strategic Recommendations",
            "content": recommendations
        })
        
        return {
            "title": f"Executive Report: {domain.title()} Analysis",
            "type": "executive",
            "sections": sections
        }
    
    # =========================================================================
    # PREDICTIVE REPORT
    # =========================================================================
    
    async def _generate_predictive_report(self) -> Dict[str, Any]:
        """Generate predictive analysis report - fully dynamic with ML integration."""
        sections = []
        
        # Check for ML model
        if not self.ml_model:
            sections.append({
                "title": "No ML Model Available",
                "content": "**Please train a model first!**\n\nGo to the Predict tab and train a model to unlock predictive analytics and forecasting capabilities."
            })
            return {
                "title": "Predictive Analysis Report",
                "type": "predictive",
                "sections": sections
            }
        
        model_info = self.ml_model
        metrics = model_info.get("metrics", {})
        task_type = model_info.get("task_type", "classification")
        model_name = model_info.get("model_name", "ML Model")
        target_col = model_info.get("target_column", "target")
        features = model_info.get("features", model_info.get("feature_columns", []))
        feature_importance = model_info.get("feature_importance", {})
        
        # Section 1: Model Overview
        model_overview = self._build_model_overview(model_info)
        sections.append({
            "title": f"Model Overview: {model_name}",
            "content": model_overview
        })
        
        # Section 2: Performance Metrics
        perf_content = self._build_performance_section(metrics, task_type, target_col)
        sections.append({
            "title": f"Performance: Predicting {target_col}",
            "content": perf_content
        })
        
        # Section 3: Performance Chart
        perf_chart = self._create_performance_chart(metrics, task_type)
        if perf_chart:
            sections.append({
                "title": f"{task_type.title()} Metrics",
                "content": f"Visual representation of model performance on `{target_col}`.",
                "chartType": "bar",
                "data": perf_chart
            })
        
        # Section 4: Feature Importance
        if feature_importance:
            sorted_fi = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]
            fi_data = [{"name": k[:15], "value": round(v * 100, 1)} for k, v in sorted_fi]
            
            top_feature = sorted_fi[0][0] if sorted_fi else "Unknown"
            sections.append({
                "title": f"Feature Importance for {target_col}",
                "content": f"Key predictive drivers. Top feature: `{top_feature}` contributes most to predictions.",
                "chartType": "horizontal_bar",
                "data": fi_data
            })
        
        # Section 5: Saved ML Charts (from training)
        saved_charts = self.ml_training_data.get("saved_charts", {}) if self.ml_training_data else {}
        for chart_key, base64_img in saved_charts.items():
            if base64_img:
                chart_info = self._get_ml_chart_info(chart_key, target_col, metrics)
                sections.append({
                    "title": chart_info["title"],
                    "content": chart_info["description"],
                    "chartType": "image",
                    "data": {"image": base64_img}
                })
        
        # Section 6: Target Distribution
        if target_col in self.df.columns:
            target_section = self._build_target_distribution(target_col, task_type)
            sections.append(target_section)
        
        # Section 7: AI Model Interpretation
        ai_insight = await self._generate_ml_insight(model_info, feature_importance)
        if ai_insight:
            sections.append({
                "title": f"AI Analysis: {model_name}",
                "content": ai_insight
            })
        
        return {
            "title": f"Predictive Analysis: {target_col} using {model_name}",
            "type": "predictive",
            "sections": sections
        }
    
    # =========================================================================
    # ANOMALY REPORT
    # =========================================================================
    
    async def _generate_anomaly_report(self) -> Dict[str, Any]:
        """Generate anomaly detection report - fully dynamic."""
        sections = []
        numeric_cols = self.profile["column_types"]["numeric"]
        outliers = self.profile["patterns"]["outliers"]
        
        # Section 1: Anomaly Summary
        summary = self._build_anomaly_summary(outliers)
        sections.append({
            "title": "Anomaly Detection Summary",
            "content": summary
        })
        
        # Section 2: Anomaly Count Chart
        if outliers:
            outlier_data = [{"name": k[:12], "value": v} for k, v in sorted(outliers.items(), key=lambda x: x[1], reverse=True)[:10]]
            sections.append({
                "title": "Anomalies by Column",
                "content": "Number of outliers detected in each numeric column using IQR method.",
                "chartType": "bar",
                "data": outlier_data
            })
        
        # Section 3: Statistical Outlier Analysis
        for col in numeric_cols[:2]:
            outlier_analysis = self._build_outlier_analysis(col)
            sections.append({
                "title": f"Outlier Analysis: {col}",
                "content": outlier_analysis
            })
        
        # Section 4: Distribution with Outliers
        if numeric_cols:
            col = numeric_cols[0]
            dist_data = self._create_distribution_data(col)
            sections.append({
                "title": f"Distribution: {col}",
                "content": "Value distribution showing potential outlier ranges.",
                "chartType": "bar",
                "data": dist_data
            })
        
        # Section 5: Z-Score Analysis
        if numeric_cols:
            zscore_content = self._build_zscore_analysis(numeric_cols[:3])
            sections.append({
                "title": "Z-Score Analysis",
                "content": zscore_content
            })
        
        # Section 6: Anomaly Patterns
        patterns = self._detect_anomaly_patterns()
        if patterns:
            sections.append({
                "title": "Anomaly Patterns",
                "content": patterns
            })
        
        # Section 7: AI Interpretation
        ai_insight = await self._generate_anomaly_insight(outliers)
        if ai_insight:
            sections.append({
                "title": "AI Anomaly Interpretation",
                "content": ai_insight
            })
        
        return {
            "title": "Anomaly Detection Report",
            "type": "anomaly",
            "sections": sections
        }
    
    # =========================================================================
    # HELPER METHODS - Content Builders
    # =========================================================================
    
    def _build_metrics_overview(self, metrics: List[Dict]) -> str:
        """Build metrics overview content dynamically."""
        content = f"**Dataset**: {self.profile['shape']['rows']:,} rows × {self.profile['shape']['columns']} columns\n\n"
        content += f"**Numeric Columns Analyzed**: {len(metrics)}\n\n"
        
        if metrics:
            content += "**Key Statistics:**\n"
            for m in metrics[:5]:
                content += f"• **{m['name']}**: Mean={m['mean']:,.2f}, Min={m['min']:,.2f}, Max={m['max']:,.2f}\n"
        
        return content
    
    def _build_category_overview(self, dimensions: List[Dict]) -> str:
        """Build category overview content."""
        content = f"**Categorical Columns**: {len(dimensions)}\n\n"
        
        for dim in dimensions[:5]:
            content += f"• **{dim['name']}**: {dim['unique_count']} unique values ({dim['cardinality']} cardinality)\n"
        
        return content
    
    def _build_dataset_overview(self) -> str:
        """Build comprehensive dataset overview."""
        shape = self.profile["shape"]
        col_types = self.profile["column_types"]
        quality = self.profile["quality"]
        
        content = f"""**Dataset Statistics:**
• Total Records: {shape['rows']:,}
• Total Columns: {shape['columns']}
• Numeric Columns: {len(col_types['numeric'])}
• Categorical Columns: {len(col_types['categorical'])}
• DateTime Columns: {len(col_types['datetime'])}
• Missing Values: {quality['missing_cells']:,} ({100 - quality['completeness']:.1f}%)
• Duplicate Rows: {quality['duplicate_rows']:,}

**Columns:** {', '.join(self.profile['columns'][:15])}{'...' if len(self.profile['columns']) > 15 else ''}"""
        
        return content
    
    def _build_statistical_summary(self) -> str:
        """Build statistical summary for numeric columns."""
        metrics = self.profile["roles"]["metrics"]
        content = "**Statistical Summary:**\n\n"
        
        for m in metrics[:6]:
            content += f"• **{m['name']}**: Mean={m['mean']:,.2f}, Min={m['min']:,.2f}, Max={m['max']:,.2f}\n"
        
        return content
    
    def _build_quality_summary(self, quality: Dict) -> str:
        """Build data quality summary."""
        grade = "A" if quality["score"] >= 90 else "B" if quality["score"] >= 75 else "C" if quality["score"] >= 60 else "D"
        
        content = f"""**Data Quality Score: {quality['score']:.0f}/100 (Grade: {grade})**

• **Completeness**: {quality['completeness']:.1f}%
• **Uniqueness**: {quality['uniqueness']:.1f}%
• **Missing Values**: {quality['missing_cells']:,} cells
• **Duplicate Rows**: {quality['duplicate_rows']:,}"""
        
        return content
    
    def _build_kpi_dashboard(self, metrics: List[Dict]) -> str:
        """Build KPI dashboard content."""
        content = "**Key Performance Indicators:**\n\n"
        
        for m in metrics:
            emoji = "💰" if m["type"] == "monetary" else "📊" if m["type"] == "count" else "📈"
            content += f"| {emoji} **{m['name']}** | Total: {m['total']:,.2f} | Avg: {m['mean']:,.2f} |\n"
        
        return content
    
    def _build_model_overview(self, model_info: Dict) -> str:
        """Build ML model overview."""
        features = model_info.get("features", model_info.get("feature_columns", []))
        
        content = f"""**Trained Model Details:**

• **Algorithm**: {model_info.get('model_name', 'Unknown')}
• **Task Type**: {model_info.get('task_type', 'classification').upper()}
• **Target Variable**: `{model_info.get('target_column', 'target')}`
• **Input Features**: {len(features)} columns
• **Model Version**: v{model_info.get('version', 1)}"""
        
        if features and len(features) <= 10:
            content += f"\n• **Features**: {', '.join(features[:10])}"
        
        return content
    
    def _build_performance_section(self, metrics: Dict, task_type: str, target_col: str) -> str:
        """Build performance metrics section."""
        if task_type == "classification":
            accuracy = metrics.get("accuracy", metrics.get("f1_score", 0))
            assessment = "🟢 **Excellent**" if accuracy >= 0.9 else "🟡 **Good**" if accuracy >= 0.75 else "🟠 **Moderate**" if accuracy >= 0.6 else "🔴 **Needs Improvement**"
            
            content = f"""**Classification Performance on `{target_col}`:**

{assessment}

| Metric | Score |
|--------|-------|
| **Accuracy** | {metrics.get('accuracy', 0) * 100:.1f}% |
| **Precision** | {metrics.get('precision', 0) * 100:.1f}% |
| **Recall** | {metrics.get('recall', 0) * 100:.1f}% |
| **F1 Score** | {metrics.get('f1_score', metrics.get('f1', 0)) * 100:.1f}% |"""
        else:
            r2 = metrics.get("r2", metrics.get("r2_score", 0))
            assessment = "🟢 **Excellent**" if r2 >= 0.9 else "🟡 **Good**" if r2 >= 0.7 else "🟠 **Moderate**" if r2 >= 0.5 else "🔴 **Limited**"
            
            content = f"""**Regression Performance on `{target_col}`:**

{assessment}

| Metric | Value |
|--------|-------|
| **R² Score** | {r2 * 100:.1f}% |
| **MAE** | {metrics.get('mae', 0):,.4f} |
| **RMSE** | {metrics.get('rmse', 0):,.4f} |"""
        
        return content
    
    def _build_anomaly_summary(self, outliers: Dict) -> str:
        """Build anomaly detection summary."""
        total = sum(outliers.values())
        
        content = f"""**Anomaly Detection Summary:**

• **Total Anomalies Found**: {total:,}
• **Detection Method**: IQR (Interquartile Range)
• **Columns Analyzed**: {len(self.profile['column_types']['numeric'])}

"""
        if outliers:
            content += "**Anomalies by Column:**\n"
            for col, count in sorted(outliers.items(), key=lambda x: x[1], reverse=True)[:5]:
                content += f"• **{col}**: {count:,} anomalies detected\n"
        else:
            content += "✅ **No significant anomalies detected!**"
        
        return content
    
    def _build_outlier_analysis(self, col: str) -> str:
        """Build detailed outlier analysis for a column."""
        data = self.df[col].dropna()
        q1 = data.quantile(0.25)
        q3 = data.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        
        outliers_low = (data < lower).sum()
        outliers_high = (data > upper).sum()
        
        content = f"""**IQR Analysis for {col}:**

• **Q1 (25th percentile)**: {q1:,.2f}
• **Q3 (75th percentile)**: {q3:,.2f}
• **IQR**: {iqr:,.2f}
• **Lower Bound**: {lower:,.2f}
• **Upper Bound**: {upper:,.2f}
• **Below Lower Bound**: {outliers_low:,} records
• **Above Upper Bound**: {outliers_high:,} records"""
        
        return content
    
    def _build_zscore_analysis(self, columns: List[str]) -> str:
        """Build Z-score analysis content."""
        content = "**Z-Score Analysis (|z| > 3 = Anomaly):**\n\n"
        
        for col in columns:
            data = self.df[col].dropna()
            mean = data.mean()
            std = data.std()
            if std > 0:
                z_scores = np.abs((data - mean) / std)
                anomalies = (z_scores > 3).sum()
                max_z = z_scores.max()
                content += f"• **{col}**: {anomalies} anomalies (max z-score: {max_z:.2f})\n"
        
        return content
    
    def _build_target_distribution(self, target_col: str, task_type: str) -> Dict:
        """Build target variable distribution section."""
        if task_type == "classification":
            dist = self.df[target_col].value_counts().head(8)
            chart_data = [{"name": str(k), "value": int(v)} for k, v in dist.items()]
            most_common = dist.index[0] if len(dist) > 0 else "N/A"
            
            return {
                "title": f"Target Distribution: {target_col}",
                "content": f"Class distribution in your data. Most common: `{most_common}`",
                "chartType": "pie",
                "data": chart_data
            }
        else:
            data = self.df[target_col].dropna()
            return {
                "title": f"Target Statistics: {target_col}",
                "content": f"""**Statistics:**
• Mean: {data.mean():,.2f}
• Std Dev: {data.std():,.2f}
• Range: {data.min():,.2f} to {data.max():,.2f}
• Records: {len(data):,}"""
            }
    
    # =========================================================================
    # HELPER METHODS - Chart Data Creators
    # =========================================================================
    
    def _create_histogram_data(self, column: str, bins: int = 10) -> List[Dict]:
        """Create histogram data for a column - VALIDATES data from DataFrame."""
        if column not in self.df.columns:
            logger.warning(f"⚠️ [CHART] Column '{column}' not in DataFrame")
            return []
            
        data = self.df[column].dropna()
        if len(data) == 0:
            logger.warning(f"⚠️ [CHART] No valid data for histogram: {column}")
            return []
            
        hist, bin_edges = np.histogram(data, bins=bins)
        
        result = [
            {"name": f"{bin_edges[i]:,.0f}-{bin_edges[i+1]:,.0f}", "value": int(hist[i])}
            for i in range(len(hist))
        ]
        
        logger.info(f"📊 [CHART] Created histogram for '{column}': {len(result)} bins, total count={sum(hist)}")
        return result
    
    def _create_grouped_data(self, metric: str, dimension: str, top_n: int = 10) -> List[Dict]:
        """Create grouped bar chart data - VALIDATES grouping from DataFrame."""
        if metric not in self.df.columns or dimension not in self.df.columns:
            logger.warning(f"⚠️ [CHART] Missing columns for grouping: metric={metric}, dimension={dimension}")
            return []
            
        try:
            # Group and aggregate with validation
            grouped = self.df.groupby(dimension)[metric].agg(['mean', 'sum', 'count']).reset_index()
            grouped = grouped.dropna(subset=['mean'])
            
            if len(grouped) == 0:
                logger.warning(f"⚠️ [CHART] No valid groups for {metric} by {dimension}")
                return []
            
            # Sort by mean and get top N
            grouped = grouped.nlargest(top_n, 'mean')
            
            result = [
                {"name": str(row[dimension])[:15], "value": round(row['mean'], 2)} 
                for _, row in grouped.iterrows()
            ]
            
            logger.info(f"📊 [CHART] Created grouped data: {metric} by {dimension}, {len(result)} groups")
            return result
        except Exception as e:
            logger.error(f"❌ [CHART] Error creating grouped data: {e}")
            return []

    
    def _create_crosstab_data(self, dim1: str, dim2: str, metric: Optional[str] = None) -> List[Dict]:
        """Create cross-tabulation data."""
        try:
            if metric:
                pivot = pd.pivot_table(self.df, values=metric, index=dim1, columns=dim2, aggfunc='sum').head(5)
            else:
                pivot = pd.crosstab(self.df[dim1], self.df[dim2]).head(5)
            
            data = []
            for idx in pivot.index[:5]:
                row = {"name": str(idx)[:15]}
                for col in pivot.columns[:5]:
                    row[str(col)[:10]] = float(pivot.loc[idx, col]) if pd.notna(pivot.loc[idx, col]) else 0
                data.append(row)
            return data
        except:
            return []
    
    def _create_trend_data(self, column: str, points: int = 30) -> List[Dict]:
        """Create trend data for area chart."""
        data = self.df[column].dropna()
        if len(data) > points:
            # Sample evenly
            indices = np.linspace(0, len(data) - 1, points, dtype=int)
            values = data.iloc[indices].tolist()
        else:
            values = data.tolist()
        
        return [{"name": f"P{i+1}", "value": round(v, 2)} for i, v in enumerate(values)]
    
    def _create_distribution_data(self, column: str) -> List[Dict]:
        """Create distribution data showing quartiles."""
        data = self.df[column].dropna()
        return [
            {"name": "Min", "value": round(data.min(), 2)},
            {"name": "Q1", "value": round(data.quantile(0.25), 2)},
            {"name": "Median", "value": round(data.median(), 2)},
            {"name": "Q3", "value": round(data.quantile(0.75), 2)},
            {"name": "Max", "value": round(data.max(), 2)}
        ]
    
    def _create_performance_chart(self, metrics: Dict, task_type: str) -> List[Dict]:
        """Create performance metrics chart data."""
        if task_type == "classification":
            data = []
            for name, key in [("Accuracy", "accuracy"), ("Precision", "precision"), ("Recall", "recall"), ("F1", "f1_score")]:
                value = metrics.get(key, metrics.get(key.replace("_score", ""), 0))
                if value > 0:
                    data.append({"name": name, "value": round(value * 100, 1)})
            return data
        else:
            r2 = max(metrics.get("r2", metrics.get("r2_score", 0)), 0)
            return [
                {"name": "R² Score", "value": round(r2 * 100, 1)},
                {"name": "Explained Var", "value": round(metrics.get("explained_variance", r2) * 100, 1)}
            ]
    
    def _get_missing_values_data(self) -> List[Dict]:
        """Get missing values by column for chart."""
        missing = self.df.isna().sum()
        missing = missing[missing > 0].sort_values(ascending=False).head(10)
        
        if len(missing) == 0:
            return []
        
        return [{"name": col[:12], "value": int(val)} for col, val in missing.items()]
    
    def _calculate_concentration(self, dimension: str) -> str:
        """Calculate concentration analysis for a dimension."""
        dist = self.df[dimension].value_counts()
        total = dist.sum()
        
        # Calculate top N concentration
        top1_pct = (dist.iloc[0] / total * 100) if len(dist) > 0 else 0
        top3_pct = (dist.head(3).sum() / total * 100) if len(dist) >= 3 else top1_pct
        top5_pct = (dist.head(5).sum() / total * 100) if len(dist) >= 5 else top3_pct
        
        content = f"""**Concentration Analysis for {dimension}:**

• Top 1 category: {top1_pct:.1f}% of data
• Top 3 categories: {top3_pct:.1f}% of data
• Top 5 categories: {top5_pct:.1f}% of data
• Total categories: {len(dist)}

"""
        if top1_pct > 50:
            content += "⚠️ **High concentration**: Single category dominates the data."
        elif top3_pct > 80:
            content += "⚠️ **Moderate concentration**: Top 3 categories dominate."
        else:
            content += "✅ **Well distributed**: Data is spread across categories."
        
        return content
    
    def _extract_key_findings(self) -> str:
        """Extract key findings from data analysis."""
        findings = []
        metrics = self.profile["roles"]["metrics"]
        dimensions = self.profile["roles"]["dimensions"]
        patterns = self.profile["patterns"]
        
        # Metric findings
        if metrics:
            top_metric = metrics[0]
            findings.append(f"📊 **Primary Metric**: {top_metric['name']} with total value of {top_metric['total']:,.2f}")
        
        # Trend findings
        for trend in patterns.get("trends", [])[:2]:
            emoji = "📈" if trend["direction"] == "increasing" else "📉"
            findings.append(f"{emoji} **{trend['column']}** shows {abs(trend['change_pct']):.1f}% {trend['direction']} trend")
        
        # Correlation findings
        for corr in patterns.get("correlations", [])[:1]:
            findings.append(f"🔗 Strong correlation found between **{corr['columns'][0]}** and **{corr['columns'][1]}** ({corr['correlation']:.2f})")
        
        # Dimension findings
        if dimensions:
            top_dim = dimensions[0]
            findings.append(f"📋 **{top_dim['name']}** has {top_dim['unique_count']} unique categories")
        
        # Quality findings
        quality = self.profile["quality"]
        if quality["completeness"] < 95:
            findings.append(f"⚠️ Data completeness at {quality['completeness']:.1f}% - {quality['missing_cells']:,} missing values")
        
        return "\n".join(f"• {f}" for f in findings) if findings else "No significant findings detected."
    
    def _detect_anomaly_patterns(self) -> str:
        """Detect patterns in anomalies."""
        outliers = self.profile["patterns"]["outliers"]
        if not outliers:
            return ""
        
        content = "**Detected Patterns:**\n\n"
        
        # Check if outliers correlate
        if len(outliers) >= 2:
            cols = list(outliers.keys())[:2]
            try:
                # Check if same rows have outliers in multiple columns
                mask1 = np.abs((self.df[cols[0]] - self.df[cols[0]].mean()) / self.df[cols[0]].std()) > 3
                mask2 = np.abs((self.df[cols[1]] - self.df[cols[1]].mean()) / self.df[cols[1]].std()) > 3
                overlap = (mask1 & mask2).sum()
                
                if overlap > 0:
                    content += f"• {overlap} records have anomalies in both **{cols[0]}** and **{cols[1]}**\n"
            except:
                pass
        
        # Calculate anomaly density
        total_anomalies = sum(outliers.values())
        anomaly_rate = (total_anomalies / len(self.df)) * 100
        content += f"• Overall anomaly rate: {anomaly_rate:.2f}%\n"
        
        if anomaly_rate > 5:
            content += "• ⚠️ High anomaly rate suggests potential data quality issues\n"
        
        return content
    
    def _get_ml_chart_info(self, chart_key: str, target_col: str, metrics: Dict) -> Dict:
        """Get title and description for ML charts."""
        chart_info = {
            "confusion_matrix": {
                "title": f"📊 Confusion Matrix: {target_col}",
                "description": f"Classification results for `{target_col}`. Diagonal = correct predictions."
            },
            "roc_curve": {
                "title": f"📈 ROC Curve (AUC: {metrics.get('auc', metrics.get('roc_auc', 'N/A'))})",
                "description": f"Trade-off between true/false positives for `{target_col}`."
            },
            "feature_importance": {
                "title": f"🎯 Feature Importance",
                "description": f"Features that most influence `{target_col}` predictions."
            },
            "actual_vs_predicted": {
                "title": f"📉 Actual vs Predicted: {target_col}",
                "description": f"Comparison of real vs predicted values. Points near diagonal = accurate."
            },
            "residuals_analysis": {
                "title": f"📊 Residuals Distribution",
                "description": f"Prediction error distribution. Centered at 0 = unbiased model."
            },
            "class_distribution": {
                "title": f"📊 Class Distribution",
                "description": f"Actual vs predicted class frequencies for `{target_col}`."
            },
            "precision_recall": {
                "title": f"🎯 Precision-Recall Curve",
                "description": f"Trade-off between precision and recall for `{target_col}`."
            }
        }
        
        return chart_info.get(chart_key, {
            "title": f"📊 {chart_key.replace('_', ' ').title()}",
            "description": f"Visualization for `{target_col}` analysis."
        })
    
    def _generate_dynamic_title(self, base_title: str, context: List) -> str:
        """Generate dynamic report title based on context."""
        domain = self.profile["domain"]["detected"]
        
        if context and len(context) > 0:
            if isinstance(context[0], dict) and "name" in context[0]:
                key_item = context[0]["name"]
                return f"{base_title}: {key_item} ({domain.title()})"
        
        return f"{base_title}: {domain.title()} Data"
    
    # =========================================================================
    # AI INSIGHT GENERATORS
    # =========================================================================
    
    async def _build_executive_summary(self) -> str:
        """Build AI-powered executive summary."""
        metrics = self.profile["roles"]["metrics"]
        dimensions = self.profile["roles"]["dimensions"]
        quality = self.profile["quality"]
        domain = self.profile["domain"]["detected"]
        
        if self.llm_client:
            prompt = f"""Write a brief executive summary (3-4 sentences) for this {domain} dataset:

- Records: {self.profile['shape']['rows']:,}
- Columns: {self.profile['shape']['columns']}
- Key Metrics: {', '.join([m['name'] for m in metrics[:3]])}
- Key Dimensions: {', '.join([d['name'] for d in dimensions[:3]])}
- Data Quality: {quality['score']:.0f}/100

Be specific and data-driven. Focus on business value."""
            
            return await self._call_llm(prompt)
        
        # Fallback without LLM
        return f"""This {domain} dataset contains **{self.profile['shape']['rows']:,} records** across **{self.profile['shape']['columns']} columns**. 

Key metrics analyzed include {', '.join([m['name'] for m in metrics[:3]])}. The data has a quality score of **{quality['score']:.0f}/100** with {quality['completeness']:.1f}% completeness.

{len(dimensions)} categorical dimensions were identified for segmentation analysis."""
    
    async def _generate_strategic_recommendations(self) -> str:
        """Generate strategic recommendations."""
        metrics = self.profile["roles"]["metrics"]
        patterns = self.profile["patterns"]
        quality = self.profile["quality"]
        
        if self.llm_client:
            prompt = f"""Based on this data analysis, provide 3 strategic recommendations:

Trends: {json.dumps(patterns.get('trends', [])[:3])}
Correlations: {json.dumps(patterns.get('correlations', [])[:2])}
Data Quality: {quality['score']:.0f}%
Top Metrics: {[m['name'] for m in metrics[:3]]}

Be specific, actionable, and business-focused."""
            
            return await self._call_llm(prompt)
        
        # Fallback recommendations
        recommendations = ["📌 **Focus on data quality**: Address missing values to improve analysis accuracy."]
        
        if patterns.get("trends"):
            trend = patterns["trends"][0]
            recommendations.append(f"📈 **Monitor {trend['column']}**: Shows {trend['change_pct']:.1f}% {trend['direction']} trend.")
        
        if patterns.get("correlations"):
            corr = patterns["correlations"][0]
            recommendations.append(f"🔗 **Leverage correlation**: {corr['columns'][0]} and {corr['columns'][1]} are strongly related.")
        
        return "\n".join(recommendations)
    
    async def _generate_ai_insight(self, report_type: str, context: Any, sections: List) -> Optional[str]:
        """Generate AI-powered insights for any report type."""
        if not self.llm_client:
            return None
        
        prompt = f"""Analyze this {report_type} report data and provide 3 key insights:

Dataset: {self.profile['shape']['rows']:,} records, {self.profile['shape']['columns']} columns
Domain: {self.profile['domain']['detected']}
Quality: {self.profile['quality']['score']:.0f}%

Context: {json.dumps(context[:3] if isinstance(context, list) else context, default=str)[:500]}

Provide 3 bullet points with specific, data-driven insights. Be concise."""
        
        return await self._call_llm(prompt)
    
    async def _generate_ml_insight(self, model_info: Dict, feature_importance: Dict) -> Optional[str]:
        """Generate AI-powered ML model interpretation."""
        if not self.llm_client:
            return None
        
        metrics = model_info.get("metrics", {})
        top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5] if feature_importance else []
        
        prompt = f"""Interpret this ML model's performance and provide business insights:

Model: {model_info.get('model_name', 'Unknown')}
Task: {model_info.get('task_type', 'classification')}
Target: {model_info.get('target_column', 'target')}
Metrics: {json.dumps({k: v for k, v in metrics.items() if isinstance(v, (int, float))})}
Top Features: {top_features}

Provide:
1. Performance assessment (is this model production-ready?)
2. Feature interpretation (what do top features tell us?)
3. Improvement recommendations

Keep response under 200 words."""
        
        return await self._call_llm(prompt)
    
    async def _generate_anomaly_insight(self, outliers: Dict) -> Optional[str]:
        """Generate AI-powered anomaly interpretation."""
        if not self.llm_client:
            return None
        
        total = sum(outliers.values())
        
        prompt = f"""Analyze these data anomalies and provide recommendations:

Dataset: {self.profile['shape']['rows']:,} records
Total Anomalies: {total}
Anomalies by Column: {json.dumps(outliers)}
Detection Method: IQR (Interquartile Range)

Provide:
1. What might cause these anomalies?
2. Are they data errors or genuine outliers?
3. Recommended actions

Be specific and actionable."""
        
        return await self._call_llm(prompt)
    
    async def _call_llm(self, prompt: str, max_tokens: int = 300) -> Optional[str]:
        """Call LLM for insight generation."""
        try:
            if hasattr(self.llm_client, 'generate'):
                response = await self.llm_client.generate(prompt, max_tokens=max_tokens)
                return response
            elif hasattr(self.llm_client, 'chat'):
                response = await self.llm_client.chat([{"role": "user", "content": prompt}], max_tokens=max_tokens)
                return response.get("content", response.get("message", ""))
            else:
                # Try direct call
                from backend.ai.openrouter import generate_response
                return await generate_response(prompt, max_tokens=max_tokens)
        except Exception as e:
            logger.warning(f"LLM call failed: {e}")
            return None


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

async def generate_advanced_report(
    df: pd.DataFrame,
    report_type: str,
    user_id: str = "default",
    ml_model: Optional[Dict] = None,
    ml_training_data: Optional[Dict] = None,
    llm_client: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Factory function to generate an advanced report.
    
    Args:
        df: The DataFrame to analyze
        report_type: One of 'metrics', 'breakdown', 'summary', 'executive', 'predictive', 'anomaly'
        user_id: User identifier
        ml_model: ML model info (for predictive reports)
        ml_training_data: ML training data with saved charts
        llm_client: LLM client for AI insights
    
    Returns:
        Dict with report data
    """
    agent = AdvancedReportAgent(
        df=df,
        user_id=user_id,
        ml_model=ml_model,
        ml_training_data=ml_training_data,
        llm_client=llm_client
    )
    
    return await agent.generate_report(report_type)
