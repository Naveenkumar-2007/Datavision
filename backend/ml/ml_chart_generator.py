"""
🎨 ML CHART GENERATOR - Production-Level ML Visualizations
============================================================

Generates beautiful, interactive Plotly charts for:
- Classification: Confusion Matrix, ROC Curve, Precision-Recall
- Regression: Actual vs Predicted, Residuals
- Clustering: PCA Scatter, Silhouette, Elbow
- General: Feature Importance, Correlation Heatmap, Learning Curves

All charts generated dynamically from actual model data - NO HARDCODING!
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MLChartGenerator:
    """
    🎨 PRODUCTION ML CHART GENERATOR
    
    Generates all ML visualizations from actual model data.
    Returns Plotly JSON for frontend rendering.
    """
    
    # Professional color palette
    COLORS = {
        'primary': '#3b82f6',
        'secondary': '#8b5cf6',
        'success': '#22c55e',
        'warning': '#f59e0b',
        'danger': '#ef4444',
        'info': '#06b6d4',
        'gradient': ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#22c55e', '#06b6d4', '#ef4444', '#14b8a6'],
        'heatmap': [[0, '#f0fdf4'], [0.5, '#22c55e'], [1, '#14532d']]
    }
    
    LAYOUT_BASE = {
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'font': {'color': '#f8fafc', 'family': 'Inter, -apple-system, sans-serif'},
        'margin': {'l': 60, 'r': 40, 't': 60, 'b': 60}
    }
    
    # =========================================================================
    # CLASSIFICATION CHARTS
    # =========================================================================
    
    @classmethod
    def confusion_matrix_chart(cls, y_true, y_pred, labels: List[str] = None) -> Dict:
        """Generate confusion matrix heatmap"""
        from sklearn.metrics import confusion_matrix
        
        cm = confusion_matrix(y_true, y_pred)
        n_classes = len(cm)
        
        if labels is None:
            labels = [f'Class {i}' for i in range(n_classes)]
        
        # Calculate percentages
        cm_pct = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis] * 100
        
        # Text annotations
        text = [[f'{cm[i][j]}<br>({cm_pct[i][j]:.1f}%)' for j in range(n_classes)] for i in range(n_classes)]
        
        chart = {
            "data": [{
                "type": "heatmap",
                "z": cm.tolist(),
                "x": labels,
                "y": labels,
                "colorscale": [[0, '#1e3a5f'], [0.5, '#3b82f6'], [1, '#60a5fa']],
                "showscale": True,
                "text": text,
                "texttemplate": "%{text}",
                "textfont": {"size": 14, "color": "#fff"},
                "hoverongaps": False,
                "colorbar": {"title": "Count", "titlefont": {"size": 12, "color": "#f8fafc"}}
            }],
            "layout": {
                **cls.LAYOUT_BASE,
                "title": {"text": "📊 Confusion Matrix", "font": {"size": 18, "color": "#f8fafc"}},
                "xaxis": {"title": "Predicted", "tickfont": {"size": 12}, "side": "bottom", "gridcolor": "rgba(255,255,255,0.1)"},
                "yaxis": {"title": "Actual", "autorange": "reversed", "tickfont": {"size": 12}, "gridcolor": "rgba(255,255,255,0.1)"},
                "height": 450,
                "width": 500
            }
        }
        return chart
    
    @classmethod
    def roc_curve_chart(cls, y_true, y_proba) -> Dict:
        """Generate ROC curve with AUC"""
        from sklearn.metrics import roc_curve, auc
        
        try:
            fpr, tpr, _ = roc_curve(y_true, y_proba)
            roc_auc = auc(fpr, tpr)
        except:
            return cls._empty_chart("ROC Curve not available")
        
        chart = {
            "data": [
                {
                    "type": "scatter",
                    "mode": "lines",
                    "x": fpr.tolist(),
                    "y": tpr.tolist(),
                    "name": f"ROC (AUC = {roc_auc:.3f})",
                    "line": {"color": cls.COLORS['primary'], "width": 3},
                    "fill": "tozeroy",
                    "fillcolor": "rgba(59, 130, 246, 0.2)"
                },
                {
                    "type": "scatter",
                    "mode": "lines",
                    "x": [0, 1],
                    "y": [0, 1],
                    "name": "Random",
                    "line": {"color": "#94a3b8", "dash": "dash", "width": 2}
                }
            ],
            "layout": {
                **cls.LAYOUT_BASE,
                "title": {"text": f"📈 ROC Curve (AUC = {roc_auc:.3f})", "font": {"size": 18}},
                "xaxis": {"title": "False Positive Rate", "range": [0, 1], "gridcolor": "rgba(255,255,255,0.1)"},
                "yaxis": {"title": "True Positive Rate", "range": [0, 1], "gridcolor": "rgba(255,255,255,0.1)"},
                "showlegend": True,
                "legend": {"x": 0.6, "y": 0.1, "bgcolor": "rgba(0,0,0,0.5)"},
                "height": 400
            }
        }
        return chart
    
    @classmethod
    def precision_recall_chart(cls, y_true, y_proba) -> Dict:
        """Generate Precision-Recall curve"""
        from sklearn.metrics import precision_recall_curve, average_precision_score
        
        try:
            precision, recall, _ = precision_recall_curve(y_true, y_proba)
            ap = average_precision_score(y_true, y_proba)
        except:
            return cls._empty_chart("Precision-Recall not available")
        
        chart = {
            "data": [{
                "type": "scatter",
                "mode": "lines",
                "x": recall.tolist(),
                "y": precision.tolist(),
                "name": f"PR (AP = {ap:.3f})",
                "line": {"color": cls.COLORS['secondary'], "width": 3},
                "fill": "tozeroy",
                "fillcolor": "rgba(139, 92, 246, 0.2)"
            }],
            "layout": {
                **cls.LAYOUT_BASE,
                "title": {"text": f"🎯 Precision-Recall (AP = {ap:.3f})", "font": {"size": 18}},
                "xaxis": {"title": "Recall", "range": [0, 1], "gridcolor": "rgba(255,255,255,0.1)"},
                "yaxis": {"title": "Precision", "range": [0, 1], "gridcolor": "rgba(255,255,255,0.1)"},
                "height": 400
            }
        }
        return chart
    
    # =========================================================================
    # REGRESSION CHARTS
    # =========================================================================
    
    @classmethod
    def actual_vs_predicted_chart(cls, y_true, y_pred, title: str = "Actual vs Predicted") -> Dict:
        """Generate actual vs predicted scatter plot"""
        y_true_list = list(y_true) if hasattr(y_true, '__iter__') else [y_true]
        y_pred_list = list(y_pred) if hasattr(y_pred, '__iter__') else [y_pred]
        
        min_val = min(min(y_true_list), min(y_pred_list))
        max_val = max(max(y_true_list), max(y_pred_list))
        
        chart = {
            "data": [
                {
                    "type": "scatter",
                    "mode": "markers",
                    "x": y_true_list,
                    "y": y_pred_list,
                    "marker": {"color": cls.COLORS['primary'], "opacity": 0.7, "size": 8},
                    "name": "Predictions"
                },
                {
                    "type": "scatter",
                    "mode": "lines",
                    "x": [min_val, max_val],
                    "y": [min_val, max_val],
                    "line": {"color": cls.COLORS['danger'], "dash": "dash", "width": 2},
                    "name": "Perfect Fit"
                }
            ],
            "layout": {
                **cls.LAYOUT_BASE,
                "title": {"text": f"📊 {title}", "font": {"size": 18}},
                "xaxis": {"title": "Actual Values", "gridcolor": "rgba(255,255,255,0.1)"},
                "yaxis": {"title": "Predicted Values", "gridcolor": "rgba(255,255,255,0.1)"},
                "showlegend": True,
                "legend": {"bgcolor": "rgba(0,0,0,0.5)"},
                "height": 400
            }
        }
        return chart
    
    @classmethod
    def residuals_chart(cls, y_true, y_pred) -> Dict:
        """Generate residual distribution histogram"""
        residuals = np.array(y_true) - np.array(y_pred)
        
        chart = {
            "data": [{
                "type": "histogram",
                "x": residuals.tolist(),
                "nbinsx": 30,
                "marker": {"color": cls.COLORS['secondary'], "line": {"color": "#6d28d9", "width": 1}},
                "name": "Residuals"
            }],
            "layout": {
                **cls.LAYOUT_BASE,
                "title": {"text": "📊 Residual Distribution", "font": {"size": 18}},
                "xaxis": {"title": "Residual (Actual - Predicted)", "gridcolor": "rgba(255,255,255,0.1)"},
                "yaxis": {"title": "Frequency", "gridcolor": "rgba(255,255,255,0.1)"},
                "shapes": [{
                    "type": "line",
                    "x0": 0, "x1": 0,
                    "y0": 0, "y1": 1,
                    "yref": "paper",
                    "line": {"color": cls.COLORS['danger'], "dash": "dash", "width": 2}
                }],
                "height": 350
            }
        }
        return chart
    
    # =========================================================================
    # CLUSTERING CHARTS
    # =========================================================================
    
    @classmethod
    def cluster_scatter_chart(cls, X_2d: np.ndarray, labels: np.ndarray, title: str = "Cluster Analysis") -> Dict:
        """Generate 2D PCA cluster scatter plot"""
        unique_labels = np.unique(labels)
        n_clusters = len(unique_labels)
        
        data = []
        for i, label in enumerate(unique_labels):
            mask = labels == label
            cluster_name = f"Cluster {label}" if label >= 0 else "Noise"
            color = cls.COLORS['gradient'][i % len(cls.COLORS['gradient'])] if label >= 0 else '#6b7280'
            
            data.append({
                "type": "scatter",
                "mode": "markers",
                "x": X_2d[mask, 0].tolist(),
                "y": X_2d[mask, 1].tolist(),
                "marker": {"color": color, "size": 8, "opacity": 0.7, "line": {"width": 1, "color": "#fff"}},
                "name": cluster_name
            })
        
        chart = {
            "data": data,
            "layout": {
                **cls.LAYOUT_BASE,
                "title": {"text": f"🔮 {title} ({n_clusters} Clusters)", "font": {"size": 18}},
                "xaxis": {"title": "PCA Component 1", "gridcolor": "rgba(255,255,255,0.1)"},
                "yaxis": {"title": "PCA Component 2", "gridcolor": "rgba(255,255,255,0.1)"},
                "showlegend": True,
                "legend": {"bgcolor": "rgba(0,0,0,0.5)"},
                "height": 450
            }
        }
        return chart
    
    @classmethod
    def elbow_chart(cls, k_range: List[int], inertias: List[float], optimal_k: int = None) -> Dict:
        """Generate elbow method chart for optimal k"""
        chart = {
            "data": [
                {
                    "type": "scatter",
                    "mode": "lines+markers",
                    "x": k_range,
                    "y": inertias,
                    "line": {"color": cls.COLORS['primary'], "width": 3},
                    "marker": {"size": 10},
                    "name": "Inertia"
                }
            ],
            "layout": {
                **cls.LAYOUT_BASE,
                "title": {"text": "📉 Elbow Method for Optimal K", "font": {"size": 18}},
                "xaxis": {"title": "Number of Clusters (K)", "gridcolor": "rgba(255,255,255,0.1)"},
                "yaxis": {"title": "Inertia (WCSS)", "gridcolor": "rgba(255,255,255,0.1)"},
                "height": 350
            }
        }
        
        # Add vertical line at optimal k
        if optimal_k:
            chart["layout"]["shapes"] = [{
                "type": "line",
                "x0": optimal_k, "x1": optimal_k,
                "y0": 0, "y1": 1,
                "yref": "paper",
                "line": {"color": cls.COLORS['success'], "dash": "dash", "width": 2}
            }]
            chart["layout"]["annotations"] = [{
                "x": optimal_k,
                "y": 1,
                "yref": "paper",
                "text": f"Optimal K = {optimal_k}",
                "showarrow": True,
                "arrowhead": 2,
                "ax": 40,
                "ay": -30,
                "font": {"color": cls.COLORS['success']}
            }]
        
        return chart
    
    @classmethod
    def silhouette_chart(cls, k_range: List[int], scores: List[float]) -> Dict:
        """Generate silhouette score chart"""
        best_k = k_range[np.argmax(scores)]
        
        chart = {
            "data": [{
                "type": "bar",
                "x": k_range,
                "y": scores,
                "marker": {
                    "color": [cls.COLORS['success'] if k == best_k else cls.COLORS['primary'] for k in k_range]
                },
                "text": [f"{s:.3f}" for s in scores],
                "textposition": "outside"
            }],
            "layout": {
                **cls.LAYOUT_BASE,
                "title": {"text": f"🎯 Silhouette Score (Best K = {best_k})", "font": {"size": 18}},
                "xaxis": {"title": "Number of Clusters (K)", "gridcolor": "rgba(255,255,255,0.1)"},
                "yaxis": {"title": "Silhouette Score", "range": [0, 1], "gridcolor": "rgba(255,255,255,0.1)"},
                "height": 350
            }
        }
        return chart
    
    # =========================================================================
    # GENERAL CHARTS
    # =========================================================================
    
    @classmethod
    def feature_importance_chart(cls, features: List[str], importances: List[float], title: str = "Feature Importance") -> Dict:
        """Generate horizontal bar chart for feature importance"""
        # Sort by importance
        sorted_idx = np.argsort(importances)
        features = [features[i] for i in sorted_idx]
        importances = [importances[i] for i in sorted_idx]
        
        # Take top 15
        features = features[-15:]
        importances = importances[-15:]
        
        # Gradient colors
        n = len(features)
        colors = [f'hsl(220, 80%, {40 + i * 3}%)' for i in range(n)]
        
        chart = {
            "data": [{
                "type": "bar",
                "x": [imp * 100 for imp in importances],
                "y": features,
                "orientation": "h",
                "marker": {"color": colors, "line": {"color": "#1e40af", "width": 1}},
                "text": [f"{imp*100:.1f}%" for imp in importances],
                "textposition": "outside",
                "textfont": {"size": 11}
            }],
            "layout": {
                **cls.LAYOUT_BASE,
                "title": {"text": f"🔑 {title}", "font": {"size": 18}},
                "xaxis": {"title": "Importance (%)", "gridcolor": "rgba(255,255,255,0.1)"},
                "yaxis": {"tickfont": {"size": 11}},
                "margin": {"l": 150, "r": 80, "t": 60, "b": 50},
                "height": max(350, n * 30)
            }
        }
        return chart
    
    @classmethod
    def correlation_heatmap(cls, df: pd.DataFrame, max_cols: int = 12) -> Dict:
        """Generate correlation heatmap for numeric columns"""
        numeric_df = df.select_dtypes(include=[np.number])
        
        if numeric_df.empty or len(numeric_df.columns) < 2:
            return cls._empty_chart("Not enough numeric columns for correlation")
        
        cols = numeric_df.columns[:max_cols]
        corr = numeric_df[cols].corr()
        
        chart = {
            "data": [{
                "type": "heatmap",
                "z": corr.values.tolist(),
                "x": [c[:12] for c in corr.columns],
                "y": [c[:12] for c in corr.index],
                "colorscale": "RdBu",
                "zmin": -1,
                "zmax": 1,
                "text": [[f"{v:.2f}" for v in row] for row in corr.values],
                "texttemplate": "%{text}",
                "textfont": {"size": 10, "color": "#fff"},
                "colorbar": {"title": "Correlation"}
            }],
            "layout": {
                **cls.LAYOUT_BASE,
                "title": {"text": "🔗 Feature Correlation Matrix", "font": {"size": 18}},
                "xaxis": {"tickangle": -45, "tickfont": {"size": 10}},
                "yaxis": {"tickfont": {"size": 10}},
                "height": max(400, len(cols) * 35)
            }
        }
        return chart
    
    @classmethod
    def learning_curve_chart(cls, train_sizes: List, train_scores: List, val_scores: List) -> Dict:
        """Generate learning curve chart"""
        chart = {
            "data": [
                {
                    "type": "scatter",
                    "mode": "lines+markers",
                    "x": list(train_sizes),
                    "y": list(train_scores),
                    "name": "Training Score",
                    "line": {"color": cls.COLORS['primary'], "width": 2},
                    "marker": {"size": 8}
                },
                {
                    "type": "scatter",
                    "mode": "lines+markers",
                    "x": list(train_sizes),
                    "y": list(val_scores),
                    "name": "Validation Score",
                    "line": {"color": cls.COLORS['success'], "width": 2},
                    "marker": {"size": 8}
                }
            ],
            "layout": {
                **cls.LAYOUT_BASE,
                "title": {"text": "📈 Learning Curves", "font": {"size": 18}},
                "xaxis": {"title": "Training Set Size", "gridcolor": "rgba(255,255,255,0.1)"},
                "yaxis": {"title": "Score", "gridcolor": "rgba(255,255,255,0.1)"},
                "showlegend": True,
                "legend": {"bgcolor": "rgba(0,0,0,0.5)"},
                "height": 400
            }
        }
        return chart
    
    @classmethod
    def model_comparison_chart(cls, models: List[Dict], metric_key: str = 'f1') -> Dict:
        """Generate model comparison bar chart"""
        names = [m.get('name', f'Model {i}') for i, m in enumerate(models)]
        scores = [m.get('metrics', {}).get(metric_key, 0) for m in models]
        best_idx = np.argmax(scores)
        
        colors = [cls.COLORS['success'] if i == best_idx else cls.COLORS['primary'] for i in range(len(models))]
        
        chart = {
            "data": [{
                "type": "bar",
                "x": scores,
                "y": names,
                "orientation": "h",
                "marker": {"color": colors, "line": {"width": 1, "color": "#fff"}},
                "text": [f"{s:.3f}" for s in scores],
                "textposition": "outside"
            }],
            "layout": {
                **cls.LAYOUT_BASE,
                "title": {"text": f"🏆 Model Comparison ({metric_key.upper()})", "font": {"size": 18}},
                "xaxis": {"title": metric_key.upper(), "range": [0, 1.1], "gridcolor": "rgba(255,255,255,0.1)"},
                "yaxis": {"automargin": True},
                "margin": {"l": 150, "r": 60, "t": 60, "b": 50},
                "height": max(300, len(models) * 50)
            }
        }
        return chart
    
    @classmethod
    def _empty_chart(cls, message: str) -> Dict:
        """Return empty chart with message"""
        return {
            "data": [],
            "layout": {
                **cls.LAYOUT_BASE,
                "title": {"text": message, "font": {"size": 14}},
                "annotations": [{
                    "text": message,
                    "x": 0.5, "y": 0.5,
                    "xref": "paper", "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 16, "color": "#94a3b8"}
                }],
                "height": 300
            }
        }


# Convenience function
def generate_ml_chart(chart_type: str, **kwargs) -> Dict:
    """Generate any ML chart by type"""
    chart_map = {
        'confusion_matrix': MLChartGenerator.confusion_matrix_chart,
        'roc_curve': MLChartGenerator.roc_curve_chart,
        'precision_recall': MLChartGenerator.precision_recall_chart,
        'actual_vs_predicted': MLChartGenerator.actual_vs_predicted_chart,
        'residuals': MLChartGenerator.residuals_chart,
        'cluster_scatter': MLChartGenerator.cluster_scatter_chart,
        'elbow': MLChartGenerator.elbow_chart,
        'silhouette': MLChartGenerator.silhouette_chart,
        'feature_importance': MLChartGenerator.feature_importance_chart,
        'correlation': MLChartGenerator.correlation_heatmap,
        'learning_curve': MLChartGenerator.learning_curve_chart,
        'model_comparison': MLChartGenerator.model_comparison_chart,
    }
    
    generator = chart_map.get(chart_type)
    if generator:
        return generator(**kwargs)
    return MLChartGenerator._empty_chart(f"Unknown chart type: {chart_type}")
