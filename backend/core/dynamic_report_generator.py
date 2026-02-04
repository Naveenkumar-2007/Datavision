"""
📊 DYNAMIC REPORT GENERATOR - All 6 Report Types (V2 with Advanced Agent)
==========================================================================

Generates all 6 report types based on real user data:
1. Metrics Analysis - Numeric trends and statistics
2. Data Breakdown - Category distributions
3. Data Summary - Complete overview
4. Executive Summary - High-level insights
5. Predictive Report - ML forecasts (AutoML) with REAL ML CHARTS
6. Anomaly Report - Outlier detection (AutoML) with REAL ML CHARTS

V2 FEATURES:
- Advanced Report Agent with intelligent data profiling
- Zero hardcoded content - everything from actual data analysis
- Dynamic chart selection based on data characteristics
- AI-powered insights and recommendations
- Multi-domain support (Sales, Finance, HR, etc.)

NO HARDCODED DATA - Everything from user's actual uploaded files.
"""

import logging
import json
import os
import glob
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Advanced Report Agent for V2 generation
try:
    from agents.advanced_report_agent import AdvancedReportAgent, generate_advanced_report
    ADVANCED_AGENT_AVAILABLE = True
    logger.info("✅ Advanced Report Agent loaded")
except ImportError:
    ADVANCED_AGENT_AVAILABLE = False
    logger.warning("Advanced Report Agent not available, using legacy generator")

# LLM for intelligent summaries
try:
    from core.llm import chat as llm_chat
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

# ML Chart Generator for REAL ML visualizations
try:
    from ml.ml_chart_generator import MLChartGenerator
    ML_CHARTS_AVAILABLE = True
    logger.info("✅ ML Chart Generator loaded for reports")
except ImportError:
    ML_CHARTS_AVAILABLE = False
    logger.warning("ML Chart Generator not available")

# AutoML Engine for loading saved model data
try:
    from ml.automl_engine import ProductionMLEngine
    AUTOML_AVAILABLE = True
except ImportError:
    AUTOML_AVAILABLE = False


class DynamicReportGenerator:
    """
    📊 DYNAMIC REPORT GENERATOR
    
    Generates all 6 report types with real user data.
    No hardcoded values - everything from actual data.
    Predictive/Anomaly reports include REAL ML charts from trained models.
    """
    
    MAX_ROWS = 1000  # Performance limit
    
    def __init__(self, user_id: str = "default", fallback_model: Optional[Dict[str, Any]] = None, df: Optional[pd.DataFrame] = None):
        self.user_id = user_id
        self.fallback_model = fallback_model
        self.df = df  # Can be passed directly for testing
        self.ml_model = None
        self.ml_engine = None
        self.ml_training_data = None  # y_test, y_pred, confusion_matrix
        
        # Only load from files if no df was provided
        if self.df is None:
            self._load_user_data()
        
        self._load_ml_model()
        self._load_ml_training_data()
    
    def _load_user_data(self):
        """Load ALL user's uploaded data files (same logic as schema_api)."""
        try:
            # Use get_user_paths for consistent path resolution (same as analytics endpoints)
            from utils.paths import get_user_paths
            from pathlib import Path
            
            paths = get_user_paths(self.user_id)
            uploads_dir = paths.get("files")
            
            logger.info(f"📂 [REPORT] Looking for files in: {uploads_dir}")
            
            all_data = []
            
            if uploads_dir and Path(uploads_dir).exists():
                for file_path in Path(uploads_dir).glob("*"):
                    if file_path.suffix.lower() in ['.csv', '.xlsx', '.xls']:
                        try:
                            if file_path.suffix.lower() == '.csv':
                                df = pd.read_csv(file_path, low_memory=False)
                            else:
                                df = pd.read_excel(file_path)
                            all_data.append(df)
                            logger.info(f"📄 [REPORT] Loaded {len(df)} rows from {file_path.name}")
                        except Exception as e:
                            logger.error(f"Error loading {file_path}: {e}")
            
            if all_data:
                # Combine all files (same as schema_api)
                self.df = pd.concat(all_data, ignore_index=True)
                
                # Sample if too large
                if len(self.df) > self.MAX_ROWS:
                    self.df = self.df.sample(n=self.MAX_ROWS, random_state=42)
                
                logger.info(f"✅ [REPORT] Loaded TOTAL: {len(self.df)} rows, {len(self.df.columns)} cols from {len(all_data)} files")
                return
            
            # Fallback: search all storage locations
            logger.warning(f"⚠️ [REPORT] Primary path not found, searching all locations...")
            search_paths = [
                f"storage/users/{self.user_id}/files/*.csv",
                f"storage/users/{self.user_id}/**/*.csv",
                "storage/users/*/files/*.csv",
            ]
            
            for pattern in search_paths:
                found = glob.glob(pattern, recursive=True)
                if found:
                    all_data = []
                    for f in found:
                        try:
                            df = pd.read_csv(f, low_memory=False)
                            all_data.append(df)
                        except:
                            pass
                    
                    if all_data:
                        self.df = pd.concat(all_data, ignore_index=True)
                        
                        if len(self.df) > self.MAX_ROWS:
                            self.df = self.df.sample(n=self.MAX_ROWS, random_state=42)
                        
                        logger.info(f"✅ [REPORT] Fallback loaded {len(self.df)} rows from {len(all_data)} files")
                        return
            
            logger.warning(f"❌ [REPORT] No CSV files found for user {self.user_id}")
                
        except Exception as e:
            logger.error(f"Failed to load user data: {e}")
    
    def _load_ml_model(self):
        """Load user's trained AutoML model info from multiple sources."""
        try:
            # 1. Try model_persistence first (recommended)
            try:
                from ml.model_persistence import model_persistence
                metadata = model_persistence.get_metadata(self.user_id)
                if metadata:
                    self.ml_model = {
                        'model_name': metadata.model_name,
                        'task_type': metadata.task_type,
                        'target_column': metadata.target_column,
                        'feature_columns': metadata.feature_columns,
                        'metrics': metadata.metrics or {},
                        'version': metadata.version,
                        'feature_count': len(metadata.feature_columns),
                        'features': metadata.feature_columns
                    }
                    logger.info(f"✅ Loaded ML model from persistence: {metadata.model_name}")
                    return
            except Exception as e:
                logger.debug(f"Model persistence load failed: {e}")
            
            # 2. Try legacy model_info.json
            model_info_path = f"storage/automl/{self.user_id}/model_info.json"
            if os.path.exists(model_info_path):
                with open(model_info_path, 'r') as f:
                    self.ml_model = json.load(f)
                logger.info(f"Loaded ML model from JSON: {self.ml_model.get('model_name', 'Unknown')}")
                return
                
            # 3. Fallback to model provided by frontend
            if self.fallback_model:
                self.ml_model = self.fallback_model
                logger.info(f"Loaded ML model from Fallback: {self.ml_model.get('model_name', 'Unknown')}")
                
        except Exception as e:
            logger.debug(f"No ML model found: {e}")
            if self.fallback_model:
                self.ml_model = self.fallback_model
                logger.info("Used fallback model after error")
    
    def _load_ml_training_data(self):
        """Load saved ML training data (y_test, y_pred, confusion_matrix) for real charts."""
        try:
            # Try to load from AutoML engine (global singleton)
            if AUTOML_AVAILABLE:
                from ml.automl_engine import automl_engine
                
                # Load model for this user
                if automl_engine.load(self.user_id):
                    self.ml_engine = automl_engine
                    
                    # Get y_test and y_pred from the engine's stored attributes
                    y_test = getattr(automl_engine, '_y_test', None)
                    y_pred = getattr(automl_engine, '_y_pred', None)
                    confusion_matrix = getattr(automl_engine, 'confusion_matrix', None)
                    
                    # Also get feature importance
                    feature_importance = {}
                    if hasattr(automl_engine, '_get_importance') and automl_engine.model:
                        try:
                            fi_list = automl_engine._get_importance(automl_engine.model)
                            if fi_list:
                                feature_importance = {item['feature']: item['importance'] for item in fi_list}
                        except Exception as e:
                            logger.debug(f"Could not get feature importance: {e}")
                    
                    # Try to load saved charts from model_persistence
                    saved_charts = {}
                    try:
                        from ml.model_persistence import model_persistence
                        saved_charts = model_persistence.get_charts(self.user_id) or {}
                        if saved_charts:
                            logger.info(f"✅ Loaded {len(saved_charts)} saved ML charts")
                    except Exception as e:
                        logger.debug(f"Could not load saved charts: {e}")
                    
                    # Build training data dict
                    self.ml_training_data = {
                        'y_test': y_test,
                        'y_pred': y_pred,
                        'confusion_matrix': confusion_matrix,
                        'feature_importance': feature_importance,
                        'model_name': getattr(automl_engine, 'model_name', 'Unknown'),
                        'task_type': getattr(automl_engine, 'task_type', 'classification'),
                        'target_column': getattr(automl_engine, 'target_column', ''),
                        'metrics': getattr(automl_engine, 'metrics', {}),
                        'saved_charts': saved_charts  # Include saved base64 chart images
                    }
                    
                    # Update ml_model with additional data if not already loaded
                    if not self.ml_model:
                        self.ml_model = {
                            'model_name': self.ml_training_data['model_name'],
                            'task_type': self.ml_training_data['task_type'],
                            'target_column': self.ml_training_data['target_column'],
                            'metrics': self.ml_training_data['metrics'],
                            'feature_importance': feature_importance
                        }
                    elif feature_importance:
                        self.ml_model['feature_importance'] = feature_importance
                    
                    if y_test is not None:
                        logger.info(f"✅ Loaded ML training data: y_test={len(y_test) if hasattr(y_test, '__len__') else 'N/A'}, y_pred={len(y_pred) if y_pred is not None and hasattr(y_pred, '__len__') else 'N/A'}")
                    else:
                        logger.warning("ML engine loaded but no y_test/y_pred available")
                else:
                    logger.warning(f"Could not load ML engine for user {self.user_id}")
                    
        except Exception as e:
            logger.warning(f"Could not load ML training data: {e}")
            import traceback
            traceback.print_exc()
    
    def generate(self, report_type: str, use_advanced: bool = True) -> Dict[str, Any]:
        """
        Generate a report based on type.
        
        Args:
            report_type: One of 'metrics', 'summary', 'executive', 'predictive', 'anomaly'
            use_advanced: Use the new Advanced Report Agent (default: True)
            
        Returns:
            Report dict with title, sections, and charts
        """
        if self.df is None or self.df.empty:
            return {
                "title": "No Data Available",
                "reportType": report_type,
                "generatedAt": datetime.now().isoformat(),
                "dataSource": "No data uploaded",
                "sections": [{
                    "title": "No Data",
                    "content": "Please upload a CSV file to generate reports."
                }],
                "error": "No data available. Please upload a file first."
            }
        
        # Try Advanced Report Agent first (V2)
        if use_advanced and ADVANCED_AGENT_AVAILABLE:
            try:
                return self._generate_with_advanced_agent(report_type)
            except Exception as e:
                logger.warning(f"Advanced agent failed, falling back to legacy: {e}")
        
        # Fallback to legacy generators
        generators = {
            "metrics": self._generate_metrics_report,
            "summary": self._generate_summary_report,
            "executive": self._generate_executive_report,
            "predictive": self._generate_predictive_report,
            "anomaly": self._generate_anomaly_report
        }
        
        generator = generators.get(report_type, self._generate_summary_report)
        return generator()
    
    def _generate_with_advanced_agent(self, report_type: str) -> Dict[str, Any]:
        """Generate report using the Advanced Report Agent (SYNC version)."""
        logger.info(f"🚀 Using Advanced Report Agent (SYNC) for {report_type} report")
        
        # Get LLM client if available
        llm_client = None
        if LLM_AVAILABLE:
            try:
                from core.llm import get_llm_client
                llm_client = get_llm_client()
            except:
                pass
        
        # Create the agent
        agent = AdvancedReportAgent(
            df=self.df,
            user_id=self.user_id,
            ml_model=self.ml_model,
            ml_training_data=self.ml_training_data,
            llm_client=llm_client
        )
        
        # Use SYNC version for reliable execution
        result = agent.generate_report_sync(report_type)
        
        if result.get("success") and result.get("report"):
            report = result["report"]
            # Add legacy compatibility fields
            report["reportType"] = report_type
            report["generatedAt"] = datetime.now().isoformat()
            report["dataSource"] = f"user_{self.user_id}"
            logger.info(f"✅ Advanced Agent generated {report_type} report with {len(report.get('sections', []))} sections")
            return report
        else:
            raise Exception(result.get("error", "Unknown error"))
    
    # =========================================================================
    # 1. METRICS ANALYSIS REPORT - ENHANCED WITH PLOTLY CHARTS (Legacy)
    # =========================================================================
    
    def _generate_metrics_report(self) -> Dict[str, Any]:
        """Generate metrics analysis report with numeric trends and advanced charts."""
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        sections = []
        
        # Section 1: Key Metrics Overview
        metrics_content = f"**Dataset**: {len(self.df):,} rows × {len(self.df.columns)} columns\n\n"
        metrics_content += f"**Numeric Columns**: {len(numeric_cols)}\n\n"
        
        for col in numeric_cols[:5]:
            mean_val = self.df[col].mean()
            std_val = self.df[col].std()
            metrics_content += f"• **{col}**: Mean={mean_val:,.2f}, Std={std_val:,.2f}\n"
        
        sections.append({
            "title": "Key Metrics Overview",
            "content": metrics_content
        })
        
        # Section 2: Statistical Summary with Chart (Min, Max, Mean comparison)
        if numeric_cols:
            # Create comparison for each column
            stats_data = []
            for col in numeric_cols[:6]:
                stats_data.append({
                    "name": col[:12],
                    "value": round(self.df[col].mean(), 2)
                })
            
            sections.append({
                "title": "Average Values by Column",
                "content": "Comparison of average values across numeric columns.",
                "chartType": "bar",
                "data": stats_data
            })
        
        # Section 3: Correlation Heatmap (Plotly)
        if ML_CHARTS_AVAILABLE and len(numeric_cols) >= 2:
            try:
                corr_chart = MLChartGenerator.correlation_heatmap(self.df, max_cols=8)
                if corr_chart:
                    sections.append({
                        "title": "Correlation Heatmap",
                        "content": "Shows relationships between numeric columns. Values close to 1 or -1 indicate strong correlation.",
                        "chartType": "plotly",
                        "plotlyData": corr_chart
                    })
            except Exception as e:
                logger.debug(f"Could not generate correlation heatmap: {e}")
        
        # Section 4: Trend Analysis
        trend_content = "**Trend Analysis:**\n\n"
        for col in numeric_cols[:3]:
            first_half = self.df[col].iloc[:len(self.df)//2].mean()
            second_half = self.df[col].iloc[len(self.df)//2:].mean()
            change = ((second_half - first_half) / first_half * 100) if first_half != 0 else 0
            direction = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            trend_content += f"• **{col}**: {direction} {abs(change):.1f}% {'increase' if change > 0 else 'decrease' if change < 0 else 'stable'}\n"
        
        sections.append({
            "title": "Trend Analysis",
            "content": trend_content
        })
        
        # Section 5: Distribution Chart (Histogram)
        if numeric_cols:
            col = numeric_cols[0]
            hist_data = []
            hist, bin_edges = np.histogram(self.df[col].dropna(), bins=10)
            for i in range(len(hist)):
                hist_data.append({
                    "name": f"{bin_edges[i]:.0f}-{bin_edges[i+1]:.0f}",
                    "value": int(hist[i])
                })
            
            sections.append({
                "title": f"Distribution of {col}",
                "content": f"Histogram showing the distribution of {col} values.",
                "chartType": "bar",
                "data": hist_data
            })
        
        # Section 6: Standard Deviation Comparison
        if len(numeric_cols) >= 2:
            std_data = []
            for col in numeric_cols[:8]:
                std_data.append({
                    "name": col[:12],
                    "value": round(self.df[col].std(), 2)
                })
            
            sections.append({
                "title": "Standard Deviation by Column",
                "content": "Variability comparison - higher values indicate more spread in data.",
                "chartType": "horizontal_bar",
                "data": std_data
            })
        
        # Section 7: AI-Powered Insights (LLM)
        if LLM_AVAILABLE and len(numeric_cols) > 0:
            insight_prompt = f"""Analyze these metrics and provide 3 key insights:

Data: {len(self.df):,} rows with {len(numeric_cols)} numeric columns.
Key metrics:
"""
            for col in numeric_cols[:5]:
                insight_prompt += f"- {col}: mean={self.df[col].mean():.2f}, min={self.df[col].min():.2f}, max={self.df[col].max():.2f}\n"
            
            insight_prompt += "\nProvide 3 bullet points with specific findings. Be concise and data-driven."
            
            insight = self._generate_llm_insight(insight_prompt, max_tokens=200)
            if insight:
                sections.append({
                    "title": "AI-Powered Insights",
                    "content": insight
                })
        
        return self._build_report("Metrics Analysis Report", "metrics", sections)
    
    # =========================================================================
    # 2. DATA BREAKDOWN REPORT
    # =========================================================================
    
    def _generate_breakdown_report(self) -> Dict[str, Any]:
        """Generate category breakdown report with enhanced analysis."""
        categorical_cols = self.df.select_dtypes(include=['object']).columns.tolist()
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        sections = []
        
        # Section 1: Data Overview - Always show meaningful stats
        overview_content = f"**Dataset Overview**\n\n"
        overview_content += f"• **Total Records**: {len(self.df):,}\n"
        overview_content += f"• **Total Columns**: {len(self.df.columns)}\n"
        overview_content += f"• **Numeric Columns**: {len(numeric_cols)}\n"
        overview_content += f"• **Categorical Columns**: {len(categorical_cols)}\n\n"
        
        if categorical_cols:
            overview_content += "**Categorical Column Details:**\n"
            for col in categorical_cols[:5]:
                unique_count = self.df[col].nunique()
                overview_content += f"• **{col}**: {unique_count} unique values\n"
        else:
            overview_content += "**Key Insight**: This dataset is primarily numeric. "
            overview_content += "Analysis will focus on numeric distributions and patterns.\n"
        
        sections.append({
            "title": "Data Overview",
            "content": overview_content
        })
        
        # Section 2-4: If we have categorical columns, show pie charts
        if categorical_cols:
            for col in categorical_cols[:3]:
                dist = self.df[col].value_counts().head(8)
                chart_data = [{"name": str(k), "value": int(v)} for k, v in dist.items()]
                
                sections.append({
                    "title": f"Distribution of {col}",
                    "content": f"Top {len(chart_data)} categories in {col}.",
                    "chartType": "pie",
                    "data": chart_data
                })
        
        # Section: Numeric Distribution Analysis (when no categorical cols or as additional)
        if numeric_cols:
            # Show distribution for top numeric columns
            for col in numeric_cols[:3 if not categorical_cols else 2]:
                try:
                    col_data = self.df[col].dropna()
                    if len(col_data) > 0:
                        # Create histogram-like data
                        hist_data = []
                        min_val, max_val = col_data.min(), col_data.max()
                        if max_val > min_val:
                            bins = np.linspace(min_val, max_val, 8)
                            for i in range(len(bins) - 1):
                                count = ((col_data >= bins[i]) & (col_data < bins[i+1])).sum()
                                label = f"{bins[i]:.1f}-{bins[i+1]:.1f}"
                                hist_data.append({"name": label, "value": int(count)})
                            
                            sections.append({
                                "title": f"Distribution of {col}",
                                "content": f"Value distribution for {col}. Mean: {col_data.mean():.2f}, Median: {col_data.median():.2f}",
                                "chartType": "bar",
                                "data": hist_data
                            })
                except Exception:
                    pass
        
        # Section: Category vs Numeric Analysis
        if categorical_cols and numeric_cols:
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            
            grouped = self.df.groupby(cat_col)[num_col].mean().nlargest(10)
            chart_data = [{"name": str(k)[:15], "value": round(v, 2)} for k, v in grouped.items()]
            
            sections.append({
                "title": f"Average {num_col} by {cat_col}",
                "content": f"Comparison of {num_col} across different {cat_col} categories.",
                "chartType": "horizontal_bar",
                "data": chart_data
            })
        
        # Section: Numeric Correlations (when primarily numeric data)
        if len(numeric_cols) >= 2:
            # Find top correlations
            try:
                corr_matrix = self.df[numeric_cols].corr()
                correlations = []
                for i in range(len(numeric_cols)):
                    for j in range(i+1, len(numeric_cols)):
                        corr_val = corr_matrix.iloc[i, j]
                        if not np.isnan(corr_val) and abs(corr_val) > 0.3:
                            correlations.append({
                                "name": f"{numeric_cols[i][:8]} vs {numeric_cols[j][:8]}",
                                "value": round(corr_val, 3)
                            })
                
                if correlations:
                    # Sort by absolute value
                    correlations.sort(key=lambda x: abs(x["value"]), reverse=True)
                    sections.append({
                        "title": "Numeric Correlations",
                        "content": "Correlation analysis between numeric columns. Values close to 1 or -1 indicate strong relationships.",
                        "chartType": "horizontal_bar",
                        "data": correlations[:8]
                    })
            except Exception:
                pass
        
        # Section: AI-Powered Insights (LLM)
        if LLM_AVAILABLE:
            insight_prompt = f"""Analyze this data breakdown:

Dataset: {len(self.df):,} records, {len(self.df.columns)} columns
Numeric columns ({len(numeric_cols)}): {', '.join(numeric_cols[:5])}
"""
            if categorical_cols:
                insight_prompt += f"\nCategorical columns ({len(categorical_cols)}):\n"
                for col in categorical_cols[:3]:
                    top_vals = self.df[col].value_counts().head(3)
                    insight_prompt += f"- {col}: {self.df[col].nunique()} unique values. Top: {', '.join([f'{v} ({c})' for v, c in top_vals.items()])}\n"
            else:
                insight_prompt += "\nThis is a purely numeric dataset.\n"
                for col in numeric_cols[:3]:
                    insight_prompt += f"- {col}: Mean={self.df[col].mean():.2f}, Std={self.df[col].std():.2f}\n"
            
            insight_prompt += "\nProvide 3 specific insights about data patterns and distribution. Be actionable."
            
            insight = self._generate_llm_insight(insight_prompt, max_tokens=250)
            if insight:
                sections.append({
                    "title": "AI Data Insights",
                    "content": insight
                })
        
        return self._build_report("Data Breakdown Report", "breakdown", sections)
    
    # =========================================================================
    # 3. DATA SUMMARY REPORT - ENHANCED WITH VISUALIZATIONS
    # =========================================================================
    
    def _generate_summary_report(self) -> Dict[str, Any]:
        """Generate complete data summary report with enhanced visualizations."""
        sections = []
        
        # Section 1: Dataset Overview
        numeric_count = len(self.df.select_dtypes(include=[np.number]).columns)
        categorical_count = len(self.df.select_dtypes(include=['object']).columns)
        datetime_count = len(self.df.select_dtypes(include=['datetime64']).columns)
        
        overview_content = f"""**Dataset Statistics:**
• Total Records: {len(self.df):,}
• Total Columns: {len(self.df.columns)}
• Numeric Columns: {numeric_count}
• Categorical Columns: {categorical_count}
• DateTime Columns: {datetime_count}
• Missing Values: {self.df.isna().sum().sum():,} ({self.df.isna().sum().sum() / self.df.size * 100:.1f}%)

**Columns:** {', '.join(self.df.columns[:15])}{'...' if len(self.df.columns) > 15 else ''}"""
        
        sections.append({
            "title": "Dataset Overview",
            "content": overview_content
        })
        
        # Section 2: Column Type Distribution Pie Chart
        col_type_data = [
            {"name": "Numeric", "value": numeric_count},
            {"name": "Categorical", "value": categorical_count},
            {"name": "DateTime", "value": datetime_count}
        ]
        # Remove zero values
        col_type_data = [d for d in col_type_data if d["value"] > 0]
        
        if col_type_data:
            sections.append({
                "title": "Column Types Distribution",
                "content": "Breakdown of column data types in your dataset.",
                "chartType": "pie",
                "data": col_type_data
            })
        
        # Section 3: Numeric Statistics Table
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        stats_content = "**Statistical Summary:**\n\n"
        for col in numeric_cols[:6]:
            stats_content += f"• **{col}**: Mean={self.df[col].mean():,.2f}, Min={self.df[col].min():,.2f}, Max={self.df[col].max():,.2f}\n"
        
        sections.append({
            "title": "Statistical Summary",
            "content": stats_content
        })
        
        # Section 4: Data Quality Score with Visual
        missing_pct = (self.df.isna().sum().sum() / self.df.size) * 100
        duplicates = self.df.duplicated().sum()
        quality_score = max(0, 100 - missing_pct * 2 - (duplicates / len(self.df) * 50))
        
        quality_content = f"""**Data Quality Score: {quality_score:.0f}/100**

• Missing Values: {self.df.isna().sum().sum():,} ({missing_pct:.1f}%)
• Duplicate Rows: {duplicates:,}
• Completeness: {100 - missing_pct:.1f}%"""
        
        sections.append({
            "title": "Data Quality Assessment",
            "content": quality_content
        })
        
        # Section 5: Data Quality Breakdown Pie
        quality_data = [
            {"name": "Complete", "value": int(100 - missing_pct)},
            {"name": "Missing", "value": int(missing_pct)}
        ]
        
        sections.append({
            "title": "Data Completeness",
            "content": "Percentage of complete vs missing data across all columns.",
            "chartType": "donut",
            "data": quality_data
        })
        
        # Section 6: Column Averages Bar Chart
        if len(numeric_cols) > 0:
            col_data = [{"name": col[:12], "value": round(self.df[col].mean(), 2)} for col in numeric_cols[:10]]
            sections.append({
                "title": "Column Averages",
                "content": "Average values for numeric columns.",
                "chartType": "bar",
                "data": col_data
            })
        
        # Section 7: Missing Values by Column (if any)
        missing_by_col = self.df.isna().sum()
        cols_with_missing = missing_by_col[missing_by_col > 0].sort_values(ascending=False).head(8)
        
        if len(cols_with_missing) > 0:
            missing_data = [{"name": col[:12], "value": int(val)} for col, val in cols_with_missing.items()]
            sections.append({
                "title": "Missing Values by Column",
                "content": "Columns with the most missing values.",
                "chartType": "horizontal_bar",
                "data": missing_data
            })
        
        # Section 8: AI Data Quality Insights (LLM)
        if LLM_AVAILABLE:
            quality_prompt = f"""Analyze this dataset's quality and structure:

Dataset: {len(self.df):,} rows, {len(self.df.columns)} columns
- Numeric: {numeric_count} columns
- Categorical: {categorical_count} columns
- Missing: {missing_pct:.1f}% of cells
- Duplicates: {self.df.duplicated().sum()} rows

Columns: {', '.join(self.df.columns[:10])}

Provide 3 concise recommendations for data quality improvement."""
            
            insight = self._generate_llm_insight(quality_prompt, max_tokens=200)
            if insight:
                sections.append({
                    "title": "AI Data Quality Recommendations",
                    "content": insight
                })
        
        return self._build_report("Data Summary Report", "summary", sections)
    
    # =========================================================================
    # 4. EXECUTIVE SUMMARY REPORT
    # =========================================================================
    
    def _generate_executive_report(self) -> Dict[str, Any]:
        """Generate high-level executive summary with LLM insights."""
        sections = []
        
        # Get data summary for LLM
        data_summary = self._get_data_summary_text()
        
        # Section 1: Executive Summary (LLM)
        if LLM_AVAILABLE:
            prompt = f"""Write a concise executive summary for business leaders based on this data:

{data_summary}

Include:
1. Key findings (2-3 bullet points)
2. Performance highlights
3. One actionable recommendation

Keep it professional and under 200 words."""
            try:
                summary = llm_chat(prompt, temperature=0.5, max_tokens=300)
            except:
                summary = self._fallback_executive_summary()
        else:
            summary = self._fallback_executive_summary()
        
        sections.append({
            "title": "Executive Summary",
            "content": summary
        })
        
        # Section 2: Key Performance Indicators
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        kpi_data = []
        for col in numeric_cols[:6]:
            kpi_data.append({
                "name": col[:12],
                "value": round(self.df[col].sum(), 0)
            })
        
        sections.append({
            "title": "Key Performance Indicators",
            "content": "Total values for key metrics.",
            "chartType": "bar",
            "data": kpi_data
        })
        
        # Section 3: LLM-Powered Strategic Recommendations
        if LLM_AVAILABLE:
            rec_prompt = f"""Based on this business data, provide 4 specific strategic recommendations:

{data_summary}

Format as numbered list with bold titles. Be specific to the data columns and values shown."""
            
            rec_content = self._generate_llm_insight(rec_prompt, max_tokens=300)
            if not rec_content:
                rec_content = """**Recommendations:**

1. **Monitor Key Metrics** - Set up dashboards for real-time tracking
2. **Address Data Quality** - Fix missing values for more accurate analysis
3. **Explore Patterns** - Use AI assistant to discover hidden trends
4. **Automate Reports** - Schedule weekly report generation"""
        else:
            rec_content = """**Recommendations:**

1. **Monitor Key Metrics** - Set up dashboards for real-time tracking
2. **Address Data Quality** - Fix missing values for more accurate analysis
3. **Explore Patterns** - Use AI assistant to discover hidden trends
4. **Automate Reports** - Schedule weekly report generation"""
        
        sections.append({
            "title": "Strategic Recommendations",
            "content": rec_content
        })
        
        return self._build_report("Executive Summary Report", "executive", sections)
    
    # =========================================================================
    # 5. PREDICTIVE REPORT (AutoML) - WITH REAL ML CHARTS (FULLY DYNAMIC)
    # =========================================================================
    
    def _generate_predictive_report(self) -> Dict[str, Any]:
        """Generate predictive report using AutoML model with REAL ML charts - fully dynamic based on data."""
        sections = []
        
        # Check if ML model exists
        if not self.ml_model:
            sections.append({
                "title": "No ML Model Available",
                "content": "**Please train a model first!**\n\nGo to Predict mode and train a model to generate predictive reports."
            })
            return self._build_report("Predictive Report", "predictive", sections)
        
        model_info = self.ml_model
        metrics = model_info.get('metrics', {})
        task_type = model_info.get('task_type', 'classification')
        model_name = model_info.get('model_name', 'Unknown Model')
        target_col = model_info.get('target_column', 'target')
        features = model_info.get('features', model_info.get('feature_columns', []))
        feature_count = len(features) if features else model_info.get('feature_count', 0)
        
        # Get feature importance
        feature_importance = model_info.get('feature_importance', {})
        if not feature_importance and self.ml_training_data:
            feature_importance = self.ml_training_data.get('feature_importance', {})
        
        # Determine top features for dynamic descriptions
        top_features = []
        if feature_importance:
            sorted_fi = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
            top_features = [f[0] for f in sorted_fi]
        
        # =====================================================================
        # Section 1: Model Overview (Dynamic based on actual model)
        # =====================================================================
        model_content = f"""**Trained Model Details:**

• **Algorithm**: {model_name}
• **Task Type**: {task_type.upper()} {'(Predicting categories)' if task_type == 'classification' else '(Predicting numeric values)'}
• **Target Variable**: `{target_col}`
• **Input Features**: {feature_count} columns used for prediction
• **Model Version**: v{model_info.get('version', 1)}"""
        
        if features and len(features) <= 10:
            model_content += f"\n• **Feature Names**: {', '.join(features[:10])}"
        
        sections.append({
            "title": f"Model Overview: {model_name}",
            "content": model_content
        })
        
        # =====================================================================
        # Section 2: Model Performance (Dynamic metrics based on task type)
        # =====================================================================
        if task_type == 'classification':
            accuracy = metrics.get('accuracy', metrics.get('f1_score', 0))
            precision = metrics.get('precision', 0)
            recall = metrics.get('recall', 0)
            f1 = metrics.get('f1_score', metrics.get('f1', 0))
            
            # Dynamic performance assessment
            if accuracy >= 0.9:
                perf_assessment = "🟢 **Excellent** - Model performs very well on this data"
            elif accuracy >= 0.75:
                perf_assessment = "🟡 **Good** - Model shows solid predictive capability"
            elif accuracy >= 0.6:
                perf_assessment = "🟠 **Moderate** - Model has room for improvement"
            else:
                perf_assessment = "🔴 **Needs Improvement** - Consider more data or feature engineering"
            
            perf_content = f"""**Classification Performance on `{target_col}`:**

{perf_assessment}

| Metric | Score | Description |
|--------|-------|-------------|
| **Accuracy** | {accuracy * 100:.1f}% | Percentage of correct predictions |
| **Precision** | {precision * 100:.1f}% | How many positive predictions were correct |
| **Recall** | {recall * 100:.1f}% | How many actual positives were found |
| **F1 Score** | {f1 * 100:.1f}% | Balance between precision and recall |"""
            
            # Add class-specific insight if available
            if 'class_report' in metrics:
                perf_content += f"\n\n**Per-Class Performance**: Available in detailed metrics."
        else:
            # Regression metrics
            r2 = metrics.get('r2', metrics.get('r2_score', 0))
            mae = metrics.get('mae', 0)
            rmse = metrics.get('rmse', 0)
            mape = metrics.get('mape', None)
            
            # Dynamic assessment for regression
            if r2 >= 0.9:
                perf_assessment = "🟢 **Excellent** - Model explains most of the variance"
            elif r2 >= 0.7:
                perf_assessment = "🟡 **Good** - Model captures the main patterns"
            elif r2 >= 0.5:
                perf_assessment = "🟠 **Moderate** - Model has predictive value but limited"
            else:
                perf_assessment = "🔴 **Limited** - Consider feature engineering or more data"
            
            perf_content = f"""**Regression Performance on `{target_col}`:**

{perf_assessment}

| Metric | Value | Description |
|--------|-------|-------------|
| **R² Score** | {r2 * 100:.1f}% | Variance explained by model |
| **MAE** | {mae:,.4f} | Average prediction error |
| **RMSE** | {rmse:,.4f} | Root mean squared error |"""
            
            if mape is not None:
                perf_content += f"\n| **MAPE** | {mape:.2f}% | Mean absolute percentage error |"
        
        sections.append({
            "title": f"Model Performance: Predicting {target_col}",
            "content": perf_content
        })
        
        # =====================================================================
        # Section 3: Performance Metrics Chart (Dynamic)
        # =====================================================================
        if task_type == 'classification':
            chart_data = []
            for metric_name, metric_key in [('Accuracy', 'accuracy'), ('Precision', 'precision'), ('Recall', 'recall'), ('F1 Score', 'f1_score')]:
                value = metrics.get(metric_key, metrics.get(metric_key.replace('_score', ''), 0))
                if value > 0:
                    chart_data.append({"name": metric_name, "value": round(value * 100, 1)})
            
            if chart_data:
                sections.append({
                    "title": f"Classification Metrics for {target_col}",
                    "content": f"Performance breakdown for predicting `{target_col}` categories.",
                    "chartType": "bar",
                    "data": chart_data
                })
        else:
            # Regression - show R² as primary metric
            r2 = metrics.get('r2', metrics.get('r2_score', 0))
            explained_var = metrics.get('explained_variance', r2)
            chart_data = [
                {"name": "R² Score", "value": round(max(r2 * 100, 0), 1)},
                {"name": "Explained Var", "value": round(max(explained_var * 100, 0), 1)}
            ]
            sections.append({
                "title": f"Regression Performance for {target_col}",
                "content": f"How well the model predicts `{target_col}` values.",
                "chartType": "bar",
                "data": chart_data
            })
        
        # =====================================================================
        # Section 4: ML Charts (Saved or Generated - Dynamic)
        # =====================================================================
        charts_added = False
        saved_charts = self.ml_training_data.get('saved_charts', {}) if self.ml_training_data else {}
        
        # Add saved charts (base64 images from training) with dynamic descriptions
        if saved_charts:
            for chart_key, base64_img in saved_charts.items():
                if not base64_img:
                    continue
                    
                # Generate dynamic title and description based on chart type and model
                if chart_key == 'confusion_matrix':
                    title = f"📊 Confusion Matrix: {target_col} Predictions"
                    desc = f"Shows how well the model classifies each `{target_col}` category. Diagonal cells = correct predictions."
                elif chart_key == 'roc_curve':
                    auc = metrics.get('auc', metrics.get('roc_auc', 'N/A'))
                    title = f"📈 ROC Curve (AUC: {auc if isinstance(auc, str) else f'{auc:.3f}'})"
                    desc = f"Trade-off between true positives and false positives for `{target_col}`. Higher curve = better model."
                elif chart_key == 'feature_importance':
                    title = f"🎯 Feature Importance for {target_col}"
                    top_feat = top_features[0] if top_features else 'features'
                    desc = f"Which features most influence `{target_col}` predictions. Top driver: `{top_feat}`"
                elif chart_key == 'actual_vs_predicted':
                    title = f"📉 Actual vs Predicted: {target_col}"
                    desc = f"Compares real `{target_col}` values to model predictions. Points near diagonal = accurate."
                elif chart_key == 'residuals_analysis':
                    title = f"📊 Residuals: {target_col} Prediction Errors"
                    desc = f"Distribution of prediction errors for `{target_col}`. Centered at 0 = unbiased model."
                elif chart_key == 'class_distribution':
                    title = f"📊 Class Distribution: {target_col}"
                    desc = f"Comparison of actual vs predicted `{target_col}` class frequencies."
                elif chart_key == 'precision_recall':
                    title = f"🎯 Precision-Recall: {target_col}"
                    desc = f"Trade-off between precision and recall for `{target_col}`. Important for imbalanced data."
                elif chart_key == 'model_comparison':
                    title = f"🏆 Model Comparison for {target_col}"
                    desc = f"Performance of different algorithms tested for predicting `{target_col}`."
                elif chart_key == 'learning_curve':
                    title = f"📈 Learning Curve: {model_name}"
                    desc = f"Shows if model would benefit from more training data for `{target_col}`."
                else:
                    # Generic chart - use key as title
                    title = f"📊 {chart_key.replace('_', ' ').title()}"
                    desc = f"Visualization for `{target_col}` prediction analysis."
                
                sections.append({
                    "title": title,
                    "content": desc,
                    "data": {"image": base64_img},
                    "chartType": "image"
                })
                charts_added = True
                logger.info(f"✅ Added saved chart: {chart_key}")
        
        # Fallback: Generate Plotly charts dynamically if no saved charts
        if not charts_added and ML_CHARTS_AVAILABLE and self.ml_training_data:
            try:
                y_test = self.ml_training_data.get('y_test')
                y_pred = self.ml_training_data.get('y_pred')
                
                if y_test is not None and y_pred is not None:
                    if task_type == 'classification':
                        cm_chart = MLChartGenerator.confusion_matrix_chart(y_test, y_pred)
                        if cm_chart:
                            sections.append({
                                "title": f"📊 Confusion Matrix: {target_col}",
                                "content": f"Classification results for `{target_col}`. Diagonal = correct, off-diagonal = errors.",
                                "chartType": "plotly",
                                "plotlyData": cm_chart
                            })
                            charts_added = True
                    else:
                        avp_chart = MLChartGenerator.actual_vs_predicted_chart(y_test, y_pred)
                        if avp_chart:
                            sections.append({
                                "title": f"📉 Actual vs Predicted: {target_col}",
                                "content": f"Scatter plot of real vs predicted `{target_col}` values.",
                                "chartType": "plotly",
                                "plotlyData": avp_chart
                            })
                            charts_added = True
                        
                        residuals_chart = MLChartGenerator.residuals_chart(y_test, y_pred)
                        if residuals_chart:
                            sections.append({
                                "title": f"📊 Residuals: {target_col}",
                                "content": f"Distribution of `{target_col}` prediction errors.",
                                "chartType": "plotly",
                                "plotlyData": residuals_chart
                            })
            except Exception as e:
                logger.warning(f"Could not generate ML charts: {e}")
        
        # =====================================================================
        # Section 5: Feature Importance (Dynamic)
        # =====================================================================
        if feature_importance:
            sorted_fi = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]
            
            if ML_CHARTS_AVAILABLE:
                try:
                    features_list = [f[0] for f in sorted_fi]
                    importances_list = [f[1] for f in sorted_fi]
                    fi_chart = MLChartGenerator.feature_importance_chart(features_list, importances_list)
                    if fi_chart:
                        top_feat = features_list[0] if features_list else 'Unknown'
                        top_imp = importances_list[0] * 100 if importances_list else 0
                        sections.append({
                            "title": f"🎯 Feature Importance for {target_col}",
                            "content": f"Top predictor: `{top_feat}` ({top_imp:.1f}% importance). These features drive `{target_col}` predictions.",
                            "chartType": "plotly",
                            "plotlyData": fi_chart
                        })
                except Exception as e:
                    logger.warning(f"Could not generate feature importance chart: {e}")
                    fi_data = [{"name": k[:15], "value": round(v * 100, 1)} for k, v in sorted_fi[:8]]
                    sections.append({
                        "title": f"Feature Importance for {target_col}",
                        "content": f"Key drivers of `{target_col}` predictions.",
                        "chartType": "horizontal_bar",
                        "data": fi_data
                    })
            else:
                fi_data = [{"name": k[:15], "value": round(v * 100, 1)} for k, v in sorted_fi[:8]]
                sections.append({
                    "title": f"Feature Importance for {target_col}",
                    "content": f"Key drivers of `{target_col}` predictions.",
                    "chartType": "horizontal_bar",
                    "data": fi_data
                })
        
        # =====================================================================
        # Section 6: Target Distribution from Data (Dynamic)
        # =====================================================================
        if target_col and self.df is not None and target_col in self.df.columns:
            if task_type == 'classification':
                dist = self.df[target_col].value_counts().head(5)
                total = dist.sum()
                pred_data = [{"name": str(k), "value": int(v)} for k, v in dist.items()]
                most_common = dist.index[0] if len(dist) > 0 else 'N/A'
                most_common_pct = (dist.iloc[0] / total * 100) if total > 0 else 0
                
                sections.append({
                    "title": f"Target Distribution: {target_col}",
                    "content": f"Your data has {len(dist)} unique `{target_col}` values. Most common: `{most_common}` ({most_common_pct:.1f}%).",
                    "chartType": "pie",
                    "data": pred_data
                })
            else:
                # Regression - show statistics and trend
                col_data = self.df[target_col].dropna()
                mean_val = col_data.mean()
                std_val = col_data.std()
                min_val = col_data.min()
                max_val = col_data.max()
                
                stat_content = f"""**`{target_col}` Statistics:**

• **Mean**: {mean_val:,.2f}
• **Std Dev**: {std_val:,.2f}
• **Range**: {min_val:,.2f} to {max_val:,.2f}
• **Records**: {len(col_data):,}"""
                
                sections.append({
                    "title": f"Target Statistics: {target_col}",
                    "content": stat_content
                })
                
                # Add trend chart
                values = col_data.head(50).tolist()
                trend_data = [{"name": f"P{i+1}", "value": round(v, 2)} for i, v in enumerate(values)]
                sections.append({
                    "title": f"Target Trend: {target_col}",
                    "content": f"First 50 values of `{target_col}` showing data distribution.",
                    "chartType": "area",
                    "data": trend_data
                })
        
        # =====================================================================
        # Section 7: AI Model Interpretation (LLM - Fully Dynamic)
        # =====================================================================
        if LLM_AVAILABLE and model_info:
            # Build dynamic prompt with all actual data
            ml_prompt = f"""Analyze this machine learning model's performance and provide business insights:

**Model Details:**
- Algorithm: {model_name}
- Task: {task_type.upper()} (predicting '{target_col}')
- Features Used: {feature_count}

**Performance Metrics:**
"""
            for k, v in metrics.items():
                if isinstance(v, (int, float)):
                    if k in ['accuracy', 'precision', 'recall', 'f1_score', 'f1', 'r2', 'r2_score', 'auc']:
                        ml_prompt += f"- {k.replace('_', ' ').title()}: {v * 100:.1f}%\n"
                    else:
                        ml_prompt += f"- {k.replace('_', ' ').title()}: {v:.4f}\n"
            
            if top_features:
                ml_prompt += f"\n**Key Predictive Features (by importance):**\n"
                for i, feat in enumerate(top_features, 1):
                    imp = feature_importance.get(feat, 0) * 100
                    ml_prompt += f"{i}. {feat} ({imp:.1f}%)\n"
            
            ml_prompt += f"""
Based on this data, provide:
1. **Performance Summary**: Is this model good enough for production use on {target_col}?
2. **Key Insights**: What do the important features tell us about {target_col}?
3. **Recommendations**: How can predictions for {target_col} be improved?

Be specific to THIS model and data. Keep response under 200 words."""
            
            insight = self._generate_llm_insight(ml_prompt, max_tokens=300)
            if insight:
                sections.append({
                    "title": f"AI Analysis: {model_name} for {target_col}",
                    "content": insight
                })
        
        # Build report with dynamic title
        report_title = f"Predictive Analysis: {target_col} using {model_name}"
        return self._build_report(report_title, "predictive", sections)
    
    # =========================================================================
    # 6. ANOMALY REPORT (AutoML)
    # =========================================================================
    
    def _generate_anomaly_report(self) -> Dict[str, Any]:
        """Generate anomaly detection report."""
        sections = []
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Section 1: Anomaly Detection Summary
        total_anomalies = 0
        anomaly_details = []
        
        for col in numeric_cols[:5]:
            mean = self.df[col].mean()
            std = self.df[col].std()
            if std > 0:
                z_scores = np.abs((self.df[col] - mean) / std)
                outliers = (z_scores > 3).sum()
                total_anomalies += outliers
                if outliers > 0:
                    anomaly_details.append(f"• **{col}**: {outliers} anomalies detected")
        
        anomaly_content = f"""**Anomaly Detection Summary:**

• **Total Anomalies Found**: {total_anomalies}
• **Detection Method**: Z-Score (threshold: 3 std)
• **Columns Analyzed**: {len(numeric_cols)}

"""
        if anomaly_details:
            anomaly_content += "**Anomalies by Column:**\n" + "\n".join(anomaly_details)
        else:
            anomaly_content += "✅ **No significant anomalies detected!**"
        
        sections.append({
            "title": "Anomaly Detection Summary",
            "content": anomaly_content
        })
        
        # Section 2: Anomaly Count Chart
        anomaly_chart = []
        for col in numeric_cols[:8]:
            mean = self.df[col].mean()
            std = self.df[col].std()
            if std > 0:
                z_scores = np.abs((self.df[col] - mean) / std)
                outliers = (z_scores > 3).sum()
                anomaly_chart.append({"name": col[:12], "value": int(outliers)})
        
        if anomaly_chart:
            sections.append({
                "title": "Anomalies by Column",
                "content": "Number of anomalies detected in each column.",
                "chartType": "bar",
                "data": anomaly_chart
            })
        
        # Section 3: Statistical Outliers
        if numeric_cols:
            col = numeric_cols[0]
            q1 = self.df[col].quantile(0.25)
            q3 = self.df[col].quantile(0.75)
            iqr = q3 - q1
            
            outlier_content = f"""**Outlier Analysis for {col}:**

• **Q1 (25th percentile)**: {q1:,.2f}
• **Q3 (75th percentile)**: {q3:,.2f}
• **IQR**: {iqr:,.2f}
• **Lower Bound**: {q1 - 1.5*iqr:,.2f}
• **Upper Bound**: {q3 + 1.5*iqr:,.2f}

Values outside these bounds are potential outliers."""
            
            sections.append({
                "title": "Statistical Outlier Analysis",
                "content": outlier_content
            })
        
        # Section 4: Data Distribution (Box-like)
        if numeric_cols:
            col = numeric_cols[0]
            dist_data = [
                {"name": "Min", "value": round(self.df[col].min(), 2)},
                {"name": "Q1", "value": round(self.df[col].quantile(0.25), 2)},
                {"name": "Median", "value": round(self.df[col].median(), 2)},
                {"name": "Q3", "value": round(self.df[col].quantile(0.75), 2)},
                {"name": "Max", "value": round(self.df[col].max(), 2)}
            ]
            
            sections.append({
                "title": f"Distribution of {col}",
                "content": "Statistical distribution showing potential outlier ranges.",
                "chartType": "bar",
                "data": dist_data
            })
        
        # Section 5: REAL Confusion Matrix (if ML model is a classifier)
        if ML_CHARTS_AVAILABLE and self.ml_training_data and self.ml_model and self.ml_model.get('task_type') == 'classification':
            try:
                y_test = self.ml_training_data.get('y_test')
                y_pred = self.ml_training_data.get('y_pred')
                
                if y_test is not None and y_pred is not None:
                    cm_chart = MLChartGenerator.confusion_matrix_chart(y_test, y_pred)
                    if cm_chart:
                        sections.append({
                            "title": "ML Classification Performance",
                            "content": "Confusion matrix from trained model - useful for detecting prediction anomalies.",
                            "chartType": "plotly",
                            "plotlyData": cm_chart
                        })
            except Exception as e:
                logger.debug(f"Could not generate confusion matrix for anomaly report: {e}")
        
        # Section 6: AI Anomaly Interpretation (LLM)
        if LLM_AVAILABLE and total_anomalies > 0:
            anomaly_prompt = f"""Analyze these data anomalies and provide business-relevant insights:

Dataset: {len(self.df):,} records analyzed
Total anomalies found: {total_anomalies}
Detection method: Z-Score (3 std threshold)

Anomalies by column:
"""
            for col in numeric_cols[:5]:
                mean = self.df[col].mean()
                std = self.df[col].std()
                if std > 0:
                    z_scores = np.abs((self.df[col] - mean) / std)
                    outliers = (z_scores > 3).sum()
                    if outliers > 0:
                        anomaly_prompt += f"- {col}: {outliers} anomalies (mean={mean:.2f})\n"
            
            anomaly_prompt += "\nProvide 3 specific recommendations: what the anomalies might indicate and how to address them."
            
            insight = self._generate_llm_insight(anomaly_prompt, max_tokens=250)
            if insight:
                sections.append({
                    "title": "AI Anomaly Interpretation",
                    "content": insight
                })
        else:
            # Fallback recommendations
            rec_content = """**Recommendations for Anomalies:**

1. **Review flagged records** - Manually inspect rows with anomalous values
2. **Investigate root cause** - Determine if anomalies are errors or genuine outliers
3. **Consider data cleaning** - Remove or correct erroneous data points
4. **Set up monitoring** - Create alerts for future anomalies"""
            
            sections.append({
                "title": "Recommendations",
                "content": rec_content
            })
        
        return self._build_report("Anomaly Detection Report", "anomaly", sections)
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _make_json_serializable(self, obj):
        """Recursively convert numpy types to native Python types for JSON serialization."""
        if obj is None:
            return None
        if isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if hasattr(obj, 'isoformat'):  # datetime
            return obj.isoformat()
        return obj
    
    def _build_report(self, title: str, report_type: str, sections: List[Dict]) -> Dict[str, Any]:
        """Build final report structure with JSON-safe data."""
        data_source = f"user_{self.user_id}" if self.df is not None else "No data"
        
        # Ensure all sections are JSON-serializable (convert numpy types)
        safe_sections = self._make_json_serializable(sections)
        
        return {
            "title": title,
            "reportType": report_type,
            "generatedAt": datetime.now().isoformat(),
            "dataSource": data_source,
            "sections": safe_sections
        }
    
    def _get_data_summary_text(self) -> str:
        """Get comprehensive text summary of data for LLM."""
        summary = f"""📊 DATASET OVERVIEW:
- Total Records: {len(self.df):,}
- Total Columns: {len(self.df.columns)}
- Column Names: {', '.join(self.df.columns[:15])}{'...' if len(self.df.columns) > 15 else ''}
"""
        
        # Numeric columns
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            summary += f"\n📈 NUMERIC METRICS ({len(numeric_cols)} columns):\n"
            for col in numeric_cols[:8]:
                summary += f"  • {col}: min={self.df[col].min():.2f}, mean={self.df[col].mean():.2f}, max={self.df[col].max():.2f}\n"
        
        # Categorical columns
        cat_cols = self.df.select_dtypes(include=['object']).columns
        if len(cat_cols) > 0:
            summary += f"\n📋 CATEGORICAL DIMENSIONS ({len(cat_cols)} columns):\n"
            for col in cat_cols[:5]:
                top_values = self.df[col].value_counts().head(3)
                summary += f"  • {col}: {self.df[col].nunique()} unique - Top: {', '.join([str(v) for v in top_values.index[:3]])}\n"
        
        # Data quality
        missing_pct = (self.df.isna().sum().sum() / self.df.size) * 100
        summary += f"\n✅ DATA QUALITY:\n  • Missing Values: {missing_pct:.1f}%\n  • Completeness: {100 - missing_pct:.1f}%\n"
        
        # ML model if available
        if self.ml_model:
            summary += f"\n🤖 ML MODEL:\n"
            summary += f"  • Model: {self.ml_model.get('model_name', 'Unknown')}\n"
            summary += f"  • Task: {self.ml_model.get('task_type', 'Unknown').upper()}\n"
            summary += f"  • Target: {self.ml_model.get('target_column', 'Unknown')}\n"
            metrics = self.ml_model.get('metrics', {})
            if metrics:
                primary = metrics.get('accuracy', metrics.get('r2', metrics.get('f1_score', 0)))
                summary += f"  • Performance: {primary * 100:.1f}%\n"
        
        return summary
    
    def _generate_llm_insight(self, prompt: str, max_tokens: int = 350) -> str:
        """Generate LLM-powered insight for report sections."""
        if not LLM_AVAILABLE:
            return None
        try:
            response = llm_chat(prompt, temperature=0.6, max_tokens=max_tokens)
            return response
        except Exception as e:
            logger.warning(f"LLM insight generation failed: {e}")
            return None
    
    def _fallback_executive_summary(self) -> str:
        """Fallback executive summary without LLM."""
        return f"""**Executive Summary**

This report analyzes {len(self.df):,} records across {len(self.df.columns)} data fields.

**Key Findings:**
• Dataset contains {len(self.df.select_dtypes(include=[np.number]).columns)} numeric metrics
• {len(self.df.select_dtypes(include=['object']).columns)} categorical dimensions available
• Data completeness: {(1 - self.df.isna().sum().sum() / self.df.size) * 100:.1f}%

**Recommendation:** Use the AI Analyst chat to explore patterns and gain deeper insights."""


def generate_dynamic_report(user_id: str, report_type: str, use_advanced: bool = True) -> Dict[str, Any]:
    """
    Quick function to generate report.
    
    Args:
        user_id: User identifier
        report_type: One of 'metrics', 'breakdown', 'summary', 'executive', 'predictive', 'anomaly'
        use_advanced: Use the new Advanced Report Agent (default: True)
    """
    generator = DynamicReportGenerator(user_id)
    return generator.generate(report_type, use_advanced=use_advanced)


async def generate_dynamic_report_async(user_id: str, report_type: str) -> Dict[str, Any]:
    """
    Async version for generating reports with Advanced Agent.
    Use this in async contexts for better performance.
    """
    if not ADVANCED_AGENT_AVAILABLE:
        return generate_dynamic_report(user_id, report_type, use_advanced=False)
    
    generator = DynamicReportGenerator(user_id)
    
    if generator.df is None or generator.df.empty:
        return {
            "title": "No Data Available",
            "reportType": report_type,
            "generatedAt": datetime.now().isoformat(),
            "dataSource": "No data uploaded",
            "sections": [{
                "title": "No Data",
                "content": "Please upload a CSV file to generate reports."
            }],
            "error": "No data available. Please upload a file first."
        }
    
    # Get LLM client
    llm_client = None
    if LLM_AVAILABLE:
        try:
            from core.llm import get_llm_client
            llm_client = get_llm_client()
        except:
            pass
    
    result = await generate_advanced_report(
        df=generator.df,
        report_type=report_type,
        user_id=user_id,
        ml_model=generator.ml_model,
        ml_training_data=generator.ml_training_data,
        llm_client=llm_client
    )
    
    if result.get("success") and result.get("report"):
        report = result["report"]
        report["reportType"] = report_type
        report["generatedAt"] = datetime.now().isoformat()
        report["dataSource"] = f"user_{user_id}"
        return report
    
    # Fallback to sync legacy
    return generator.generate(report_type, use_advanced=False)


__all__ = ['DynamicReportGenerator', 'generate_dynamic_report', 'generate_dynamic_report_async']
