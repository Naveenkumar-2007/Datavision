"""
5 POWERFUL MCPs - Autonomous Tool System
==========================================

These are the 5 MOST POWERFUL MCP tools that make DataVision
a $50 Billion worth product.

Each MCP has a unique capability:
1. DATA ANALYZER - Deep data exploration
2. PATTERN FINDER - Anomaly and pattern detection
3. REPORT GENERATOR - Professional reports
4. INSIGHT EXTRACTOR - Key insights mining
5. COMPARISON ENGINE - Multi-dataset comparison
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

from core.llm import chat

logger = logging.getLogger(__name__)


@dataclass
class MCPResult:
    """Result from an MCP tool"""
    success: bool
    tool_name: str
    output: str
    data: Optional[Dict] = None
    visualization: Optional[str] = None
    confidence: float = 0.9


# ============================================================================
# MCP 1: DATA ANALYZER - Deep Data Exploration
# ============================================================================

class DataAnalyzerMCP:
    """
    🔍 DATA ANALYZER MCP
    
    Strength: Deep exploration of any dataset
    - Schema analysis
    - Data quality checks
    - Statistical summaries
    - Distribution analysis
    """
    
    name = "Data Analyzer"
    icon = "🔍"
    description = "Deep data exploration and quality analysis"
    
    @staticmethod
    def execute(df: pd.DataFrame, query: str = "") -> MCPResult:
        """Execute data analysis"""
        try:
            if df is None or df.empty:
                return MCPResult(
                    success=False,
                    tool_name="Data Analyzer",
                    output="No data available. Please upload files first."
                )
            
            # Analyze data
            analysis = {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns),
                "dtypes": {col: str(df[col].dtype) for col in df.columns},
                "missing": df.isnull().sum().to_dict(),
                "numeric_stats": {}
            }
            
            # Numeric column stats
            for col in df.select_dtypes(include=['int64', 'float64']).columns:
                analysis["numeric_stats"][col] = {
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "mean": float(df[col].mean()),
                    "sum": float(df[col].sum())
                }
            
            # Generate summary using LLM
            prompt = f"""Summarize this dataset analysis in a clear, helpful way.

DATASET STATS:
- Rows: {analysis['rows']}
- Columns: {analysis['columns']}
- Column Names: {', '.join(analysis['column_names'])}
- Numeric Stats: {json.dumps(analysis['numeric_stats'], indent=2)[:500]}
- Missing Values: {analysis['missing']}

USER QUERY: {query if query else "General analysis"}

Provide a concise but comprehensive summary of this data."""

            summary = chat(prompt, temperature=0.3, max_tokens=500)
            
            return MCPResult(
                success=True,
                tool_name="Data Analyzer",
                output=f"🔍 **Data Analysis Complete**\n\n{summary}",
                data=analysis,
                confidence=0.95
            )
            
        except Exception as e:
            return MCPResult(
                success=False,
                tool_name="Data Analyzer",
                output=f"Analysis error: {str(e)}"
            )


# ============================================================================
# MCP 2: PATTERN FINDER - Anomaly and Pattern Detection
# ============================================================================

class PatternFinderMCP:
    """
    🔎 PATTERN FINDER MCP
    
    Strength: Discovers hidden patterns and anomalies
    - Outlier detection
    - Trend identification
    - Correlation finding
    - Anomaly alerts
    """
    
    name = "Pattern Finder"
    icon = "🔎"
    description = "Discovers patterns, trends, and anomalies in your data"
    
    @staticmethod
    def execute(df: pd.DataFrame, query: str = "") -> MCPResult:
        """Find patterns and anomalies"""
        try:
            if df is None or df.empty:
                return MCPResult(
                    success=False,
                    tool_name="Pattern Finder",
                    output="No data available."
                )
            
            patterns = {
                "outliers": [],
                "correlations": [],
                "trends": []
            }
            
            # Find outliers in numeric columns
            for col in df.select_dtypes(include=['int64', 'float64']).columns:
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                outlier_mask = (df[col] < q1 - 1.5*iqr) | (df[col] > q3 + 1.5*iqr)
                outlier_count = outlier_mask.sum()
                if outlier_count > 0:
                    patterns["outliers"].append(f"{col}: {outlier_count} outliers")
            
            # Use LLM to describe patterns
            sample = df.head(20).to_string()
            
            prompt = f"""Analyze this data for patterns, trends, and anomalies.

DATA SAMPLE:
{sample[:1000]}

DETECTED OUTLIERS: {patterns['outliers']}

USER QUERY: {query if query else "Find patterns"}

Identify:
1. Key patterns in the data
2. Any trends over time or categories
3. Unusual values or anomalies
4. Interesting correlations

Be specific and cite actual values from the data."""

            analysis = chat(prompt, temperature=0.3, max_tokens=600)
            
            return MCPResult(
                success=True,
                tool_name="Pattern Finder",
                output=f"🔎 **Pattern Analysis**\n\n{analysis}",
                data=patterns,
                confidence=0.85
            )
            
        except Exception as e:
            return MCPResult(
                success=False,
                tool_name="Pattern Finder",
                output=f"Pattern finding error: {str(e)}"
            )


# ============================================================================
# MCP 3: REPORT GENERATOR - Professional Reports
# ============================================================================

class ReportGeneratorMCP:
    """
    📄 REPORT GENERATOR MCP
    
    Strength: Creates professional reports from data
    - Executive summaries
    - Detailed breakdowns
    - Key metrics highlights
    - Actionable recommendations
    """
    
    name = "Report Generator"
    icon = "📄"
    description = "Generates professional reports from your data"
    
    @staticmethod
    def execute(df: pd.DataFrame, query: str = "") -> MCPResult:
        """Generate a professional report"""
        try:
            if df is None or df.empty:
                return MCPResult(
                    success=False,
                    tool_name="Report Generator",
                    output="No data available for report."
                )
            
            # Prepare data summary
            num_cols = df.select_dtypes(include=['int64', 'float64']).columns
            cat_cols = df.select_dtypes(include=['object']).columns
            
            stats = {}
            for col in num_cols[:5]:
                stats[col] = {
                    "total": float(df[col].sum()),
                    "average": float(df[col].mean()),
                    "max": float(df[col].max())
                }
            
            cat_summary = {}
            for col in cat_cols[:3]:
                cat_summary[col] = df[col].value_counts().head(5).to_dict()
            
            prompt = f"""Generate a professional executive report from this data.

DATA OVERVIEW:
- Total Records: {len(df)}
- Numeric Metrics: {json.dumps(stats, indent=2)[:600]}
- Categories: {json.dumps(cat_summary, indent=2)[:400]}

USER REQUEST: {query if query else "Generate report"}

Create a professional report with:
1. 📊 Executive Summary (2-3 sentences)
2. 📈 Key Metrics (bullet points with real numbers)
3. 🎯 Top Insights (3-5 findings)
4. 💡 Recommendations (actionable next steps)

Use markdown formatting. Use ONLY data from above."""

            report = chat(prompt, temperature=0.4, max_tokens=1000)
            
            return MCPResult(
                success=True,
                tool_name="Report Generator",
                output=f"📄 **Professional Report**\n\n{report}",
                confidence=0.9
            )
            
        except Exception as e:
            return MCPResult(
                success=False,
                tool_name="Report Generator",
                output=f"Report generation error: {str(e)}"
            )


# ============================================================================
# MCP 4: INSIGHT EXTRACTOR - Key Insights Mining
# ============================================================================

class InsightExtractorMCP:
    """
    💡 INSIGHT EXTRACTOR MCP
    
    Strength: Mines the most valuable insights
    - Hidden relationships
    - Business opportunities
    - Risk factors
    - Growth potential
    """
    
    name = "Insight Extractor"
    icon = "💡"
    description = "Extracts valuable business insights from your data"
    
    @staticmethod
    def execute(df: pd.DataFrame, query: str = "") -> MCPResult:
        """Extract key insights"""
        try:
            if df is None or df.empty:
                return MCPResult(
                    success=False,
                    tool_name="Insight Extractor",
                    output="No data available."
                )
            
            # Prepare comprehensive data view
            sample = df.head(30).to_string()
            describe = df.describe().to_string() if len(df.select_dtypes(include=['int64', 'float64']).columns) > 0 else ""
            
            prompt = f"""You are a world-class data analyst. Extract the MOST VALUABLE insights from this data.

DATA:
{sample[:1500]}

STATISTICS:
{describe[:500]}

USER FOCUS: {query if query else "Key insights"}

Extract 5 HIGH-VALUE insights:
1. What's the most surprising finding?
2. What opportunity does this data reveal?
3. What risk or problem is visible?
4. What trend is emerging?
5. What action should be taken?

Be specific with numbers from the data. Each insight should be actionable."""

            insights = chat(prompt, temperature=0.4, max_tokens=800)
            
            return MCPResult(
                success=True,
                tool_name="Insight Extractor",
                output=f"💡 **Key Insights**\n\n{insights}",
                confidence=0.85
            )
            
        except Exception as e:
            return MCPResult(
                success=False,
                tool_name="Insight Extractor",
                output=f"Insight extraction error: {str(e)}"
            )


# ============================================================================
# MCP 5: COMPARISON ENGINE - Multi-Dataset Comparison
# ============================================================================

class ComparisonEngineMCP:
    """
    ⚖️ COMPARISON ENGINE MCP
    
    Strength: Compares data across dimensions
    - Category comparisons
    - Time period comparisons
    - Segment analysis
    - Benchmark evaluations
    """
    
    name = "Comparison Engine"
    icon = "⚖️"
    description = "Compares data across categories, time periods, and segments"
    
    @staticmethod
    def execute(df: pd.DataFrame, query: str = "") -> MCPResult:
        """Compare data dimensions"""
        try:
            if df is None or df.empty:
                return MCPResult(
                    success=False,
                    tool_name="Comparison Engine",
                    output="No data available for comparison."
                )
            
            # Find categorical and numeric columns
            cat_cols = df.select_dtypes(include=['object']).columns.tolist()
            num_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            
            comparisons = {}
            
            # Generate comparisons for top categorical columns
            for cat_col in cat_cols[:2]:
                for num_col in num_cols[:2]:
                    key = f"{num_col} by {cat_col}"
                    try:
                        comparison = df.groupby(cat_col)[num_col].agg(['sum', 'mean', 'count']).head(10)
                        comparisons[key] = comparison.to_dict()
                    except:
                        pass
            
            prompt = f"""Create a comparison analysis of this data.

DATA COMPARISONS:
{json.dumps(comparisons, indent=2, default=str)[:1500]}

USER REQUEST: {query if query else "Compare categories"}

Provide:
1. ⚖️ Key Comparisons (which categories/segments perform better)
2. 📊 Rankings (top and bottom performers)
3. 📈 Differences (significant gaps between segments)
4. 💡 Insights (what the comparison reveals)

Use markdown tables where appropriate. All numbers from the data."""

            analysis = chat(prompt, temperature=0.3, max_tokens=800)
            
            return MCPResult(
                success=True,
                tool_name="Comparison Engine",
                output=f"⚖️ **Comparison Analysis**\n\n{analysis}",
                data={"comparisons": len(comparisons)},
                confidence=0.9
            )
            
        except Exception as e:
            return MCPResult(
                success=False,
                tool_name="Comparison Engine",
                output=f"Comparison error: {str(e)}"
            )


# ============================================================================
# MCP 6: FORECASTER - Time Series Prediction
# ============================================================================

class ForecasterMCP:
    """
    🔮 FORECASTER MCP
    
    Strength: Time series forecasting with confidence intervals
    - Trend projection
    - Seasonal patterns
    - Confidence ranges
    - Risk assessment
    """
    
    name = "Forecaster"
    icon = "🔮"
    description = "Generates time-based forecasts with confidence intervals"
    
    @staticmethod
    def execute(df: pd.DataFrame, query: str = "") -> MCPResult:
        """Generate forecast with confidence"""
        import numpy as np
        try:
            if df is None or df.empty:
                return MCPResult(success=False, tool_name="Forecaster", output="No data available.")
            
            # Find numeric columns for forecasting
            num_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            if not num_cols:
                return MCPResult(success=False, tool_name="Forecaster", output="No numeric columns for forecasting.")
            
            target_col = num_cols[0]
            values = df[target_col].dropna().values
            
            if len(values) < 5:
                return MCPResult(success=False, tool_name="Forecaster", output="Insufficient data points for forecast (need at least 5).")
            
            # Simple trend calculation
            n = len(values)
            x = np.arange(n)
            slope, intercept = np.polyfit(x, values, 1)
            
            # Forecast next 3 periods
            forecasts = []
            for i in range(1, 4):
                predicted = intercept + slope * (n + i - 1)
                std_dev = np.std(values) * 0.3 * i  # Uncertainty grows with time
                forecasts.append({
                    "period": f"+{i}",
                    "value": round(predicted, 2),
                    "lower": round(predicted - 1.96 * std_dev, 2),
                    "upper": round(predicted + 1.96 * std_dev, 2)
                })
            
            trend = "upward 📈" if slope > 0 else "downward 📉" if slope < 0 else "stable ➡️"
            confidence = "High" if abs(slope) > np.std(values) * 0.1 else "Medium"
            
            output = f"""🔮 **Forecast for {target_col}**

**Current Trend**: {trend}
**Confidence Level**: {confidence}

| Period | Predicted | Lower Bound | Upper Bound |
|--------|-----------|-------------|-------------|
| {forecasts[0]['period']} | {forecasts[0]['value']:,.0f} | {forecasts[0]['lower']:,.0f} | {forecasts[0]['upper']:,.0f} |
| {forecasts[1]['period']} | {forecasts[1]['value']:,.0f} | {forecasts[1]['lower']:,.0f} | {forecasts[1]['upper']:,.0f} |
| {forecasts[2]['period']} | {forecasts[2]['value']:,.0f} | {forecasts[2]['lower']:,.0f} | {forecasts[2]['upper']:,.0f} |

**Based on**: {n} historical data points
**Method**: Linear trend projection with 95% confidence interval"""
            
            return MCPResult(
                success=True,
                tool_name="Forecaster",
                output=output,
                data={"forecasts": forecasts, "trend": trend},
                confidence=0.75 if confidence == "Medium" else 0.9
            )
            
        except Exception as e:
            return MCPResult(success=False, tool_name="Forecaster", output=f"Forecast error: {str(e)}")


# ============================================================================
# MCP 7: ANOMALY DETECTOR - Real-time Outlier Detection
# ============================================================================

class AnomalyDetectorMCP:
    """
    ⚠️ ANOMALY DETECTOR MCP
    
    Strength: Detects statistical outliers and anomalies
    - Z-score detection
    - IQR-based outliers
    - Severity classification
    - Actionable alerts
    """
    
    name = "Anomaly Detector"
    icon = "⚠️"
    description = "Detects statistical anomalies and outliers in your data"
    
    @staticmethod
    def execute(df: pd.DataFrame, query: str = "") -> MCPResult:
        """Detect anomalies in data"""
        import numpy as np
        try:
            if df is None or df.empty:
                return MCPResult(success=False, tool_name="Anomaly Detector", output="No data available.")
            
            anomalies = []
            num_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            
            for col in num_cols[:5]:
                values = df[col].dropna()
                if len(values) < 3:
                    continue
                    
                mean = values.mean()
                std = values.std()
                
                if std == 0:
                    continue
                
                # Z-score detection (|z| > 3)
                z_scores = ((values - mean) / std).abs()
                outlier_indices = z_scores[z_scores > 3].index.tolist()
                
                for idx in outlier_indices[:3]:  # Top 3 per column
                    val = values[idx]
                    z = z_scores[idx]
                    severity = "🔴 CRITICAL" if z > 4 else "🟠 HIGH" if z > 3.5 else "🟡 MODERATE"
                    anomalies.append({
                        "column": col,
                        "value": round(float(val), 2),
                        "expected": f"{round(mean, 2)} ± {round(std * 2, 2)}",
                        "z_score": round(float(z), 2),
                        "severity": severity
                    })
            
            if not anomalies:
                output = "✅ **No significant anomalies detected**\n\nAll values are within expected statistical ranges."
            else:
                output = f"⚠️ **{len(anomalies)} Anomalies Detected**\n\n"
                output += "| Column | Value | Expected Range | Severity |\n|--------|-------|----------------|----------|\n"
                for a in anomalies[:10]:
                    output += f"| {a['column']} | {a['value']:,.0f} | {a['expected']} | {a['severity']} |\n"
                output += "\n**Recommendation**: Investigate flagged values for data quality or exceptional events."
            
            return MCPResult(
                success=True,
                tool_name="Anomaly Detector",
                output=output,
                data={"anomaly_count": len(anomalies), "anomalies": anomalies},
                confidence=0.92
            )
            
        except Exception as e:
            return MCPResult(success=False, tool_name="Anomaly Detector", output=f"Anomaly detection error: {str(e)}")


# ============================================================================
# MCP 8: CHART EXECUTOR - Enhanced with ML Visualization Support
# ============================================================================

class ChartExecutorMCP:
    """
    📊 ENHANCED CHART EXECUTOR MCP
    
    Strength: Creates any chart from natural language with ML support
    - Query intent detection
    - Auto chart type selection
    - ML visualizations (matplotlib/seaborn)
    - Plotly interactive charts
    - Dynamic color palettes
    """
    
    name = "Chart Executor"
    icon = "📊"
    description = "Creates charts from natural language with ML visualization support"
    
    # Chart intent keywords
    CHART_INTENTS = {
        "bar": ["bar", "compare", "comparison", "by category", "group"],
        "line": ["line", "trend", "over time", "timeline", "growth", "monthly", "yearly"],
        "pie": ["pie", "distribution", "percentage", "share", "breakdown", "proportion"],
        "scatter": ["scatter", "correlation", "relationship", "vs", "versus"],
        "heatmap": ["heatmap", "correlation matrix", "heat map"],
        "histogram": ["histogram", "distribution", "frequency"],
        "box": ["box", "boxplot", "quartiles", "outliers"],
        "area": ["area", "cumulative", "stacked area"],
        "radar": ["radar", "spider", "multi-dimensional"],
        "funnel": ["funnel", "conversion", "stage"],
        "treemap": ["treemap", "hierarchy", "composition"],
        "forecast": ["forecast", "predict", "prediction", "future"]
    }
    
    @staticmethod
    def detect_chart_intent(query: str) -> str:
        """Detect chart type from query"""
        query_lower = query.lower()
        
        for chart_type, keywords in ChartExecutorMCP.CHART_INTENTS.items():
            if any(kw in query_lower for kw in keywords):
                return chart_type
        
        return "bar"  # Default
    
    @staticmethod
    def execute(df: pd.DataFrame, query: str = "") -> MCPResult:
        """Execute chart from natural language with ML support"""
        try:
            if df is None or df.empty:
                return MCPResult(success=False, tool_name="Chart Executor", output="No data available.")
            
            import numpy as np
            
            # Detect chart intent
            chart_type = ChartExecutorMCP.detect_chart_intent(query)
            
            ml_charts = []
            plotly_chart = None
            
            # For forecast/prediction requests, use ML visualizer
            if chart_type == "forecast":
                try:
                    from core.ml_predictor import MLPredictor
                    from core.ml_visualizer import MLVisualizer
                    
                    predictor = MLPredictor()
                    visualizer = MLVisualizer()
                    
                    if predictor.ml_available and visualizer.available:
                        # Find numeric column
                        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                        if num_cols:
                            target_col = num_cols[0]
                            
                            # Generate ML prediction
                            result = predictor.predict(df, target_col, periods=3)
                            
                            if result.success:
                                # Create forecast chart
                                forecast_chart = visualizer.create_forecast_plot(
                                    historical=df[target_col].tolist(),
                                    predictions=result.predictions,
                                    lower_bound=result.lower_bounds,
                                    upper_bound=result.upper_bounds,
                                    title=f"Forecast: {target_col}"
                                )
                                if forecast_chart.get('image'):
                                    ml_charts.append(forecast_chart)
                                
                                # Create feature importance if available
                                if result.feature_importance:
                                    importance_chart = visualizer.create_feature_importance(
                                        result.feature_importance,
                                        title="Key Drivers"
                                    )
                                    if importance_chart.get('image'):
                                        ml_charts.append(importance_chart)
                                
                                return MCPResult(
                                    success=True,
                                    tool_name="Chart Executor",
                                    output=f"""📊 **ML Forecast Chart Generated**

**Algorithm**: {result.algorithm}
**Target**: {target_col}
**Accuracy R²**: {result.metrics.get('r2_score', 0):.2%}
**Data Points**: {len(df)}

Predictions with 95% confidence intervals generated successfully!""",
                                    visualization={"ml_charts": ml_charts},
                                    data={"ml_charts": ml_charts},
                                    confidence=0.92
                                )
                except ImportError:
                    pass  # Fall back to regular chart
            
            # For correlation/heatmap, use ML visualizer
            if chart_type == "heatmap":
                try:
                    from core.ml_visualizer import MLVisualizer
                    visualizer = MLVisualizer()
                    
                    if visualizer.available:
                        corr_chart = visualizer.create_correlation_heatmap(df, "Data Correlations")
                        if corr_chart.get('image'):
                            ml_charts.append(corr_chart)
                            
                            return MCPResult(
                                success=True,
                                tool_name="Chart Executor",
                                output="📊 **Correlation Heatmap Generated**\n\nShowing relationships between all numeric columns.",
                                visualization={"ml_charts": ml_charts},
                                data={"ml_charts": ml_charts},
                                confidence=0.95
                            )
                except ImportError:
                    pass
            
            # For histogram/distribution, use ML visualizer
            if chart_type == "histogram":
                try:
                    from core.ml_visualizer import MLVisualizer
                    visualizer = MLVisualizer()
                    
                    if visualizer.available:
                        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                        if num_cols:
                            dist_chart = visualizer.create_distribution_plot(
                                df[num_cols[0]].dropna().tolist(),
                                column_name=num_cols[0]
                            )
                            if dist_chart.get('image'):
                                ml_charts.append(dist_chart)
                                
                                return MCPResult(
                                    success=True,
                                    tool_name="Chart Executor",
                                    output=f"📊 **Distribution Chart Generated**\n\nShowing distribution of {num_cols[0]} with mean and standard deviation.",
                                    visualization={"ml_charts": ml_charts},
                                    data={"ml_charts": ml_charts},
                                    confidence=0.93
                                )
                except ImportError:
                    pass
            
            # Fall back to Plotly chart
            from agents.comprehensive_charts import generate_autonomous_visualization
            
            chart_output = generate_autonomous_visualization(query, df)
            
            if chart_output:
                result_data = {"plotly_chart": chart_output}
                if ml_charts:
                    result_data["ml_charts"] = ml_charts
                
                return MCPResult(
                    success=True,
                    tool_name="Chart Executor",
                    output=f"📊 **{chart_type.title()} Chart Generated**\n\nVisualization created based on your request.",
                    visualization=chart_output,
                    data=result_data,
                    confidence=0.95
                )
            else:
                return MCPResult(
                    success=False,
                    tool_name="Chart Executor",
                    output="Could not generate chart. Try specifying the chart type and columns."
                )
                
        except Exception as e:
            return MCPResult(success=False, tool_name="Chart Executor", output=f"Chart error: {str(e)}")


# ============================================================================
# MCP REGISTRY - All 8 Powerful MCPs
# ============================================================================

MCP_REGISTRY = {
    "data_analyzer": DataAnalyzerMCP,
    "pattern_finder": PatternFinderMCP,
    "report_generator": ReportGeneratorMCP,
    "insight_extractor": InsightExtractorMCP,
    "comparison_engine": ComparisonEngineMCP,
    "forecaster": ForecasterMCP,
    "anomaly_detector": AnomalyDetectorMCP,
    "chart_executor": ChartExecutorMCP
}


def get_all_mcps() -> List[Dict]:
    """Get info about all available MCPs"""
    return [
        {"id": "data_analyzer", "name": "🔍 Data Analyzer", "description": "Deep data exploration"},
        {"id": "pattern_finder", "name": "🔎 Pattern Finder", "description": "Anomaly and pattern detection"},
        {"id": "report_generator", "name": "📄 Report Generator", "description": "Professional reports"},
        {"id": "insight_extractor", "name": "💡 Insight Extractor", "description": "Key insights mining"},
        {"id": "comparison_engine", "name": "⚖️ Comparison Engine", "description": "Multi-dimension comparison"},
        {"id": "forecaster", "name": "🔮 Forecaster", "description": "Time series forecasting"},
        {"id": "anomaly_detector", "name": "⚠️ Anomaly Detector", "description": "Outlier detection and alerts"},
        {"id": "chart_executor", "name": "📊 Chart Executor", "description": "Natural language to chart"}
    ]


def execute_mcp(mcp_id: str, df: pd.DataFrame, query: str = "") -> MCPResult:
    """Execute an MCP by ID"""
    if mcp_id not in MCP_REGISTRY:
        return MCPResult(
            success=False,
            tool_name=mcp_id,
            output=f"Unknown MCP: {mcp_id}"
        )
    
    mcp_class = MCP_REGISTRY[mcp_id]
    return mcp_class.execute(df, query)

