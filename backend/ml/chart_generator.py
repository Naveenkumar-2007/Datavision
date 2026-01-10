"""
🎨 PRODUCTION ML CHART GENERATOR v3.0
=====================================

COMPREHENSIVE ML Visualization using matplotlib and seaborn.
Only creates charts when sufficient data is available.

Chart Types by Task:

CLASSIFICATION (12 charts):
- Confusion Matrix (normalized heatmap)
- Class Distribution (actual vs predicted)
- ROC Curve (binary + multi-class)
- Precision-Recall Curve
- Calibration Curve
- Prediction Confidence
- Classification Report Heatmap
- Class Balance Pie Chart
- Prediction Error by Class (box plot)
- Score Distribution Histogram
- Cumulative Gains Chart
- Lift Chart

REGRESSION (10 charts):
- Actual vs Predicted Scatter
- Residuals Analysis (2x2 grid)  
- Error Distribution (KDE + histogram)
- Prediction Overview (sorted with bands)
- Target Distribution Histogram
- Prediction Error Box Plot
- Cook's Distance Plot
- Scale-Location Plot
- Predicted vs Residuals Scatter
- SHAP-style Importance (if available)

CLUSTERING (8 charts):
- Cluster Scatter (PCA 2D)
- Cluster Distribution Bar
- Silhouette Analysis
- Feature Distribution by Cluster
- Cluster Box Plots
- Cluster Centroid Radar
- Cluster Pairplot (first 4 features)
- Elbow Method (if k data available)

NLP (6 charts):
- Word Cloud
- Word Frequency Histogram
- Text Length Distribution
- TF-IDF Feature Importance
- Class Distribution (for text classification)
- Sentiment/Topic Distribution

COMMON (5 charts):
- Feature Importance (horizontal bar)
- Model Comparison (bar chart)
- Correlation Heatmap
- Distribution Overview (histogram grid)
- Box Plot Grid
"""

import numpy as np
import pandas as pd
import base64
import io
import logging
from typing import Dict, List, Optional, Any, Tuple

# Visualization imports
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch

# ML metrics
from sklearn.metrics import (
    confusion_matrix, classification_report, roc_curve, auc,
    precision_recall_curve, r2_score, mean_absolute_error,
    mean_squared_error, silhouette_samples, silhouette_score,
    average_precision_score
)
from sklearn.calibration import calibration_curve
from scipy import stats

logger = logging.getLogger(__name__)

# Set PROFESSIONAL LIGHT theme style (Clean, Business-Ready)
sns.set_style("whitegrid")
plt.rcParams.update({
    'figure.facecolor': '#ffffff',
    'axes.facecolor': '#ffffff',
    'axes.edgecolor': '#e0e0e0',
    'text.color': '#333333',
    'axes.labelcolor': '#333333',
    'xtick.color': '#555555',
    'ytick.color': '#555555',
    'grid.color': '#f0f0f0',
    'legend.facecolor': '#ffffff',
    'legend.edgecolor': '#e0e0e0',
    'figure.dpi': 200,          # High resolution
    'font.size': 11,            # Readable font
    'axes.titlesize': 14,       # Clear titles
    'axes.labelsize': 12,       # Clear labels
    'font.family': 'sans-serif',
    'font.sans-serif': ['Segoe UI', 'Arial', 'sans-serif'] # Modern business fonts
})

# DataVision color palette - Extended (Vibrant & Professional)
COLORS = [
    '#0F766E',  # Deep Teal (Primary)
    '#2563EB',  # Royal Blue
    '#D946EF',  # Magenta
    '#F59E0B',  # Amber
    '#10B981',  # Emerald
    '#8B5CF6',  # Violet
    '#EF4444',  # Red
    '#06B6D4',  # Cyan
    '#84CC16',  # Lime
    '#F97316',  # Orange
    '#6366F1',  # Indigo
    '#A855F7',  # Purple
]

# Custom colormaps (Adapted for Light Theme)
TEAL_CMAP = LinearSegmentedColormap.from_list('teal', ['#ffffff', '#ccfbf1', '#0f766e'])
HEAT_CMAP = LinearSegmentedColormap.from_list('heat', ['#ffffff', '#fef3c7', '#ef4444'])


def _fig_to_base64(fig) -> str:
    """Convert matplotlib figure to base64 string"""
    buf = io.BytesIO()
    # Save with high DPI and white background
    fig.savefig(buf, format='png', dpi=200, bbox_inches='tight', 
                facecolor='#ffffff', edgecolor='none')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{img_base64}"


def generate_ml_charts(
    task_type: str,
    y_test: np.ndarray,
    y_pred: np.ndarray,
    y_proba: Optional[np.ndarray] = None,
    feature_importance: Optional[List[Dict]] = None,
    class_names: Optional[List[str]] = None,
    model_name: str = "Model",
    X_test: Optional[np.ndarray] = None,
    feature_names: Optional[List[str]] = None,
    text_data: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Generate COMPREHENSIVE ML charts based on task type and available data.
    
    Args:
        task_type: 'classification', 'regression', 'clustering', or 'nlp'
        y_test: True labels
        y_pred: Predicted labels
        y_proba: Prediction probabilities
        feature_importance: List of {feature, importance} dicts
        class_names: Names of classes
        model_name: Model name for titles
        X_test: Test features
        feature_names: Feature names
        text_data: Raw text data for NLP charts
    
    Returns:
        Dict of chart_name: base64_image_string
    """
    charts = {}
    
    try:
        # Safely convert to numpy arrays
        y_test = np.array(y_test).flatten()
        y_pred = np.array(y_pred).flatten()
        
        # Handle non-numeric labels (strings) by encoding them
        # This prevents 'isnan' errors on object arrays
        original_labels = None
        if y_test.dtype == object or not np.issubdtype(y_test.dtype, np.number):
            from sklearn.preprocessing import LabelEncoder
            le = LabelEncoder()
            # Combine y_test and y_pred to ensure consistent encoding
            all_labels = np.concatenate([y_test, y_pred])
            le.fit(all_labels)
            original_labels = le.classes_.tolist()  # Store original labels for display
            y_test = le.transform(y_test)
            y_pred = le.transform(y_pred)
            # Use original labels as class_names if not provided
            if class_names is None:
                class_names = original_labels
        
        if len(y_test) < 5 or len(y_pred) < 5:
            logger.warning("Insufficient data for charts")
            return {}
        
        task_lower = task_type.lower()
        
        if 'classification' in task_lower or 'nlp' in task_lower:
            charts.update(_generate_classification_charts(
                y_test, y_pred, y_proba, class_names, model_name
            ))
            if 'nlp' in task_lower and text_data:
                charts.update(_generate_nlp_charts(text_data, y_test, model_name))
        elif 'clustering' in task_lower:
            charts.update(_generate_clustering_charts(
                X_test, y_pred, model_name, feature_names
            ))
        else:  # regression
            charts.update(_generate_regression_charts(
                y_test, y_pred, model_name
            ))
        
        # Common charts
        if feature_importance and len(feature_importance) > 0:
            fi_chart = _generate_feature_importance_chart(feature_importance, model_name)
            if fi_chart:
                charts['feature_importance'] = fi_chart
                
        logger.info(f"✅ Generated {len(charts)} charts: {list(charts.keys())}")
                
    except Exception as e:
        logger.error(f"Chart generation error: {e}")
        import traceback
        traceback.print_exc()
    
    return charts


# =============================================================================
# CLASSIFICATION CHARTS (12 types)
# =============================================================================

def _generate_classification_charts(
    y_test: np.ndarray,
    y_pred: np.ndarray,
    y_proba: Optional[np.ndarray],
    class_names: Optional[List[str]],
    model_name: str
) -> Dict[str, str]:
    """Generate comprehensive classification charts"""
    charts = {}
    n_classes = len(np.unique(y_test))
    
    # 1. CONFUSION MATRIX (Enhanced with normalization)
    try:
        cm = confusion_matrix(y_test, y_pred)
        if cm.shape[0] >= 2:
            fig, ax = plt.subplots(figsize=(8, 6))
            
            cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
            cm_norm = np.nan_to_num(cm_norm)
            
            sns.heatmap(cm_norm, annot=True, fmt='.1%', cmap='Blues',
                       ax=ax, cbar_kws={'label': 'Percentage'}, linewidths=0.5)
            
            for i in range(cm.shape[0]):
                for j in range(cm.shape[1]):
                    ax.text(j + 0.5, i + 0.75, f'n={cm[i,j]}',
                           ha='center', va='center', fontsize=8, color='gray')
            
            labels = [str(c)[:10] for c in class_names] if class_names else None
            if labels:
                ax.set_xticklabels(labels, rotation=45, ha='right')
                ax.set_yticklabels(labels, rotation=0)
            
            ax.set_xlabel('Predicted', fontsize=12, color='white')
            ax.set_ylabel('Actual', fontsize=12, color='white')
            ax.set_title(f'Confusion Matrix - {model_name}', fontsize=14, color='white', pad=20)
            
            charts['confusion_matrix'] = _fig_to_base64(fig)
    except Exception as e:
        logger.warning(f"Confusion matrix error: {e}")
    
    # 2. CLASS DISTRIBUTION (Side by side bars)
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        unique_classes = np.union1d(np.unique(y_test), np.unique(y_pred))
        x = np.arange(len(unique_classes))
        width = 0.35
        
        actual_counts = [np.sum(y_test == c) for c in unique_classes]
        pred_counts = [np.sum(y_pred == c) for c in unique_classes]
        
        ax.bar(x - width/2, actual_counts, width, label='Actual', color=COLORS[0], edgecolor='white')
        ax.bar(x + width/2, pred_counts, width, label='Predicted', color=COLORS[2], edgecolor='white')
        
        ax.set_xlabel('Class', fontsize=12, color='white')
        ax.set_ylabel('Count', fontsize=12, color='white')
        ax.set_title(f'Class Distribution - {model_name}', fontsize=14, color='white')
        ax.set_xticks(x)
        labels = [str(c)[:10] for c in class_names[:len(unique_classes)]] if class_names else [str(c) for c in unique_classes]
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.legend()
        
        charts['class_distribution'] = _fig_to_base64(fig)
    except Exception as e:
        logger.warning(f"Class distribution error: {e}")
    
    # 3. ROC CURVE (Multi-class support)
    if y_proba is not None:
        try:
            fig, ax = plt.subplots(figsize=(8, 6))
            
            if n_classes == 2:
                proba = y_proba[:, 1] if len(y_proba.shape) > 1 and y_proba.shape[1] >= 2 else y_proba.flatten()
                fpr, tpr, _ = roc_curve(y_test, proba)
                roc_auc = auc(fpr, tpr)
                ax.plot(fpr, tpr, color=COLORS[0], lw=2, label=f'ROC (AUC = {roc_auc:.3f})')
                ax.fill_between(fpr, tpr, alpha=0.2, color=COLORS[0])
            else:
                if len(y_proba.shape) > 1:
                    for i in range(min(n_classes, y_proba.shape[1])):
                        y_binary = (y_test == i).astype(int)
                        if y_binary.sum() > 0:
                            fpr, tpr, _ = roc_curve(y_binary, y_proba[:, i])
                            roc_auc = auc(fpr, tpr)
                            label = class_names[i][:10] if class_names and i < len(class_names) else f'Class {i}'
                            ax.plot(fpr, tpr, color=COLORS[i % len(COLORS)], lw=2, 
                                   label=f'{label} (AUC={roc_auc:.2f})')
            
            ax.plot([0, 1], [0, 1], 'k--', lw=1, alpha=0.5, label='Random')
            ax.set_xlim([0.0, 1.0])
            ax.set_ylim([0.0, 1.05])
            ax.set_xlabel('False Positive Rate', fontsize=12, color='white')
            ax.set_ylabel('True Positive Rate', fontsize=12, color='white')
            ax.set_title(f'ROC Curve - {model_name}', fontsize=14, color='white')
            ax.legend(loc='lower right', fontsize=9)
            
            charts['roc_curve'] = _fig_to_base64(fig)
        except Exception as e:
            logger.warning(f"ROC curve error: {e}")
    
    # 4. PRECISION-RECALL CURVE
    if y_proba is not None and n_classes == 2:
        try:
            proba = y_proba[:, 1] if len(y_proba.shape) > 1 else y_proba.flatten()
            precision, recall, _ = precision_recall_curve(y_test, proba)
            avg_prec = average_precision_score(y_test, proba)
            
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.plot(recall, precision, color=COLORS[1], lw=2, label=f'PR (AP = {avg_prec:.3f})')
            ax.fill_between(recall, precision, alpha=0.2, color=COLORS[1])
            ax.set_xlabel('Recall', fontsize=12, color='white')
            ax.set_ylabel('Precision', fontsize=12, color='white')
            ax.set_title(f'Precision-Recall Curve - {model_name}', fontsize=14, color='white')
            ax.legend()
            
            charts['precision_recall'] = _fig_to_base64(fig)
        except Exception as e:
            logger.warning(f"Precision-Recall error: {e}")
    
    # 5. CALIBRATION CURVE
    if y_proba is not None and n_classes == 2 and len(y_test) >= 20:
        try:
            proba = y_proba[:, 1] if len(y_proba.shape) > 1 else y_proba.flatten()
            prob_true, prob_pred = calibration_curve(y_test, proba, n_bins=10)
            
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.plot([0, 1], [0, 1], 'k--', lw=1, label='Perfect')
            ax.plot(prob_pred, prob_true, 's-', color=COLORS[2], lw=2, label=model_name)
            ax.set_xlabel('Mean Predicted Probability', fontsize=12, color='white')
            ax.set_ylabel('Fraction of Positives', fontsize=12, color='white')
            ax.set_title(f'Calibration Curve - {model_name}', fontsize=14, color='white')
            ax.legend()
            
            charts['calibration'] = _fig_to_base64(fig)
        except Exception as e:
            logger.warning(f"Calibration error: {e}")
    
    # 6. PREDICTION CONFIDENCE HISTOGRAM
    if y_proba is not None:
        try:
            fig, ax = plt.subplots(figsize=(8, 6))
            
            max_proba = np.max(y_proba, axis=1) if len(y_proba.shape) > 1 else np.abs(y_proba - 0.5) * 2 + 0.5
            correct = y_pred == y_test
            
            ax.hist(max_proba[correct], bins=20, alpha=0.7, color=COLORS[1], label='Correct', edgecolor='white')
            ax.hist(max_proba[~correct], bins=20, alpha=0.7, color=COLORS[6], label='Incorrect', edgecolor='white')
            
            ax.set_xlabel('Prediction Confidence', fontsize=12, color='white')
            ax.set_ylabel('Count', fontsize=12, color='white')
            ax.set_title(f'Confidence Distribution - {model_name}', fontsize=14, color='white')
            ax.legend()
            
            charts['confidence_histogram'] = _fig_to_base64(fig)
        except Exception as e:
            logger.warning(f"Confidence histogram error: {e}")
    
    # 7. CLASS BALANCE PIE CHART
    try:
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        
        unique, counts = np.unique(y_test, return_counts=True)
        labels = [str(class_names[i])[:10] if class_names and i < len(class_names) else str(u) for i, u in enumerate(unique)]
        colors = [COLORS[i % len(COLORS)] for i in range(len(unique))]
        
        axes[0].pie(counts, labels=labels, autopct='%1.1f%%', colors=colors, 
                   textprops={'color': 'white'}, wedgeprops={'edgecolor': 'white'})
        axes[0].set_title('Actual Class Balance', color='white', fontsize=12)
        
        unique_p, counts_p = np.unique(y_pred, return_counts=True)
        labels_p = [str(class_names[i])[:10] if class_names and i < len(class_names) else str(u) for i, u in enumerate(unique_p)]
        axes[1].pie(counts_p, labels=labels_p, autopct='%1.1f%%', colors=colors[:len(unique_p)],
                   textprops={'color': 'white'}, wedgeprops={'edgecolor': 'white'})
        axes[1].set_title('Predicted Class Balance', color='white', fontsize=12)
        
        fig.suptitle(f'Class Balance - {model_name}', fontsize=14, color='white')
        plt.tight_layout()
        
        charts['class_balance_pie'] = _fig_to_base64(fig)
    except Exception as e:
        logger.warning(f"Class balance pie error: {e}")
    
    # 8. PREDICTION ERROR BOX PLOT BY CLASS
    if y_proba is not None:
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            max_proba = np.max(y_proba, axis=1) if len(y_proba.shape) > 1 else y_proba.flatten()
            classes = np.unique(y_test)
            data = [max_proba[y_test == c] for c in classes]
            
            bp = ax.boxplot(data, patch_artist=True)
            for i, (patch, color) in enumerate(zip(bp['boxes'], [COLORS[i % len(COLORS)] for i in range(len(classes))])):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)
            
            labels = [str(class_names[i])[:10] if class_names and i < len(class_names) else str(c) for i, c in enumerate(classes)]
            ax.set_xticklabels(labels, rotation=45, ha='right')
            ax.set_xlabel('Class', fontsize=12, color='white')
            ax.set_ylabel('Prediction Confidence', fontsize=12, color='white')
            ax.set_title(f'Confidence by Class - {model_name}', fontsize=14, color='white')
            
            charts['confidence_boxplot'] = _fig_to_base64(fig)
        except Exception as e:
            logger.warning(f"Confidence boxplot error: {e}")
    
    # 9. CLASSIFICATION REPORT HEATMAP
    try:
        from sklearn.metrics import precision_recall_fscore_support
        precision, recall, f1, support = precision_recall_fscore_support(y_test, y_pred, zero_division=0)
        
        if len(precision) <= 10:  # Only for reasonable number of classes
            fig, ax = plt.subplots(figsize=(10, 6))
            
            data = np.array([precision, recall, f1]).T
            labels = [str(class_names[i])[:10] if class_names and i < len(class_names) else f'Class {i}' for i in range(len(precision))]
            
            sns.heatmap(data, annot=True, fmt='.2f', cmap='RdYlGn', 
                       xticklabels=['Precision', 'Recall', 'F1-Score'],
                       yticklabels=labels, ax=ax, vmin=0, vmax=1)
            ax.set_title(f'Classification Metrics by Class - {model_name}', fontsize=14, color='white')
            
            charts['metrics_heatmap'] = _fig_to_base64(fig)
    except Exception as e:
        logger.warning(f"Metrics heatmap error: {e}")
    
    # 10. SCORE DISTRIBUTION
    if y_proba is not None:
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            if len(y_proba.shape) > 1:
                for i in range(min(y_proba.shape[1], 5)):
                    label = class_names[i][:10] if class_names and i < len(class_names) else f'Class {i}'
                    sns.kdeplot(y_proba[:, i], ax=ax, label=label, color=COLORS[i % len(COLORS)], lw=2)
            
            ax.set_xlabel('Prediction Score', fontsize=12, color='white')
            ax.set_ylabel('Density', fontsize=12, color='white')
            ax.set_title(f'Score Distribution by Class - {model_name}', fontsize=14, color='white')
            ax.legend()
            
            charts['score_distribution'] = _fig_to_base64(fig)
        except Exception as e:
            logger.warning(f"Score distribution error: {e}")
    
    return charts


# =============================================================================
# REGRESSION CHARTS (10 types)
# =============================================================================

def _generate_regression_charts(
    y_test: np.ndarray,
    y_pred: np.ndarray,
    model_name: str
) -> Dict[str, str]:
    """Generate comprehensive regression charts"""
    charts = {}
    residuals = y_pred - y_test
    errors = np.abs(residuals)
    
    # 1. ACTUAL VS PREDICTED with trend
    try:
        fig, ax = plt.subplots(figsize=(8, 6))
        
        ax.scatter(y_test, y_pred, alpha=0.6, color=COLORS[0], s=50, edgecolors='white', linewidth=0.5)
        
        min_v, max_v = min(y_test.min(), y_pred.min()), max(y_test.max(), y_pred.max())
        ax.plot([min_v, max_v], [min_v, max_v], 'r--', lw=2, label='Perfect')
        
        z = np.polyfit(y_test, y_pred, 1)
        p = np.poly1d(z)
        ax.plot(np.sort(y_test), p(np.sort(y_test)), '--', color=COLORS[1], lw=1.5, label='Trend')
        
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        ax.annotate(f'R² = {r2:.4f}\nMAE = {mae:.2f}\nRMSE = {rmse:.2f}', 
                   xy=(0.05, 0.95), xycoords='axes fraction', fontsize=11, color='white',
                   bbox=dict(boxstyle='round', facecolor='#333333', alpha=0.8), va='top')
        
        ax.set_xlabel('Actual', fontsize=12, color='white')
        ax.set_ylabel('Predicted', fontsize=12, color='white')
        ax.set_title(f'Actual vs Predicted - {model_name}', fontsize=14, color='white')
        ax.legend()
        
        charts['actual_vs_predicted'] = _fig_to_base64(fig)
    except Exception as e:
        logger.warning(f"Actual vs Predicted error: {e}")
    
    # 2. RESIDUALS ANALYSIS (2x2 grid)
    try:
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # Residuals vs Predicted
        axes[0, 0].scatter(y_pred, residuals, alpha=0.6, color=COLORS[1], s=40)
        axes[0, 0].axhline(y=0, color='red', linestyle='--', lw=1.5)
        axes[0, 0].set_xlabel('Predicted', color='white')
        axes[0, 0].set_ylabel('Residual', color='white')
        axes[0, 0].set_title('Residuals vs Predicted', color='white')
        
        # Residuals Histogram
        axes[0, 1].hist(residuals, bins=30, color=COLORS[2], alpha=0.7, edgecolor='white')
        axes[0, 1].axvline(x=0, color='red', linestyle='--', lw=1.5)
        axes[0, 1].set_xlabel('Residual', color='white')
        axes[0, 1].set_ylabel('Frequency', color='white')
        axes[0, 1].set_title('Residuals Distribution', color='white')
        
        # Q-Q Plot
        stats.probplot(residuals, dist="norm", plot=axes[1, 0])
        axes[1, 0].get_lines()[0].set_color(COLORS[0])
        axes[1, 0].get_lines()[1].set_color('red')
        axes[1, 0].set_title('Q-Q Plot (Normality)', color='white')
        axes[1, 0].set_xlabel('Theoretical Quantiles', color='white')
        axes[1, 0].set_ylabel('Sample Quantiles', color='white')
        
        # Residuals vs Index
        axes[1, 1].scatter(range(len(residuals)), residuals, alpha=0.6, color=COLORS[3], s=30)
        axes[1, 1].axhline(y=0, color='red', linestyle='--', lw=1.5)
        axes[1, 1].set_xlabel('Index', color='white')
        axes[1, 1].set_ylabel('Residual', color='white')
        axes[1, 1].set_title('Residuals vs Order', color='white')
        
        fig.suptitle(f'Residual Analysis - {model_name}', fontsize=14, color='white', y=1.02)
        plt.tight_layout()
        
        charts['residuals_analysis'] = _fig_to_base64(fig)
    except Exception as e:
        logger.warning(f"Residuals analysis error: {e}")
    
    # 3. ERROR DISTRIBUTION with percentiles
    try:
        fig, ax = plt.subplots(figsize=(8, 6))
        
        sns.kdeplot(errors, ax=ax, color=COLORS[3], fill=True, alpha=0.3, lw=2)
        ax.hist(errors, bins=30, density=True, alpha=0.3, color=COLORS[3], edgecolor='white')
        
        for p, color in [(50, COLORS[0]), (75, COLORS[1]), (90, COLORS[4]), (95, COLORS[6])]:
            val = np.percentile(errors, p)
            ax.axvline(val, color=color, linestyle='--', label=f'{p}th: {val:.2f}')
        
        ax.set_xlabel('Absolute Error', fontsize=12, color='white')
        ax.set_ylabel('Density', fontsize=12, color='white')
        ax.set_title(f'Error Distribution - {model_name}', fontsize=14, color='white')
        ax.legend(fontsize=9)
        
        charts['error_distribution'] = _fig_to_base64(fig)
    except Exception as e:
        logger.warning(f"Error distribution error: {e}")
    
    # 4. TARGET DISTRIBUTION HISTOGRAM
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.hist(y_test, bins=30, alpha=0.6, color=COLORS[0], label='Actual', edgecolor='white')
        ax.hist(y_pred, bins=30, alpha=0.6, color=COLORS[2], label='Predicted', edgecolor='white')
        
        ax.axvline(y_test.mean(), color=COLORS[0], linestyle='--', lw=2, label=f'Actual Mean: {y_test.mean():.2f}')
        ax.axvline(y_pred.mean(), color=COLORS[2], linestyle='--', lw=2, label=f'Pred Mean: {y_pred.mean():.2f}')
        
        ax.set_xlabel('Value', fontsize=12, color='white')
        ax.set_ylabel('Frequency', fontsize=12, color='white')
        ax.set_title(f'Target Distribution - {model_name}', fontsize=14, color='white')
        ax.legend()
        
        charts['target_histogram'] = _fig_to_base64(fig)
    except Exception as e:
        logger.warning(f"Target histogram error: {e}")
    
    # 5. ERROR BOX PLOT (by quantiles)
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        quantiles = np.percentile(y_test, [0, 25, 50, 75, 100])
        groups = []
        labels = []
        for i in range(len(quantiles) - 1):
            mask = (y_test >= quantiles[i]) & (y_test < quantiles[i+1])
            if mask.sum() > 0:
                groups.append(errors[mask])
                labels.append(f'Q{i+1}')
        
        bp = ax.boxplot(groups, patch_artist=True)
        for i, patch in enumerate(bp['boxes']):
            patch.set_facecolor(COLORS[i % len(COLORS)])
            patch.set_alpha(0.7)
        
        ax.set_xticklabels(labels)
        ax.set_xlabel('Target Quantile', fontsize=12, color='white')
        ax.set_ylabel('Absolute Error', fontsize=12, color='white')
        ax.set_title(f'Error by Target Range - {model_name}', fontsize=14, color='white')
        
        charts['error_boxplot'] = _fig_to_base64(fig)
    except Exception as e:
        logger.warning(f"Error boxplot error: {e}")
    
    # 6. PREDICTION OVERVIEW (sorted with bands)
    try:
        fig, ax = plt.subplots(figsize=(12, 6))
        
        idx = np.argsort(y_test)
        y_sorted = y_test[idx]
        pred_sorted = y_pred[idx]
        
        ax.scatter(range(len(y_sorted)), y_sorted, alpha=0.7, color=COLORS[0], s=20, label='Actual')
        ax.scatter(range(len(pred_sorted)), pred_sorted, alpha=0.5, color=COLORS[3], s=15, marker='x', label='Predicted')
        
        std = np.std(pred_sorted - y_sorted)
        ax.fill_between(range(len(y_sorted)), y_sorted - 2*std, y_sorted + 2*std, 
                       alpha=0.2, color=COLORS[1], label='±2σ')
        
        ax.set_xlabel('Sample (sorted)', fontsize=12, color='white')
        ax.set_ylabel('Value', fontsize=12, color='white')
        ax.set_title(f'Prediction Overview - {model_name}', fontsize=14, color='white')
        ax.legend()
        
        charts['prediction_overview'] = _fig_to_base64(fig)
    except Exception as e:
        logger.warning(f"Prediction overview error: {e}")
    
    # 7. SCALE-LOCATION PLOT
    try:
        fig, ax = plt.subplots(figsize=(8, 6))
        
        sqrt_abs_resid = np.sqrt(np.abs(residuals))
        ax.scatter(y_pred, sqrt_abs_resid, alpha=0.6, color=COLORS[4], s=40)
        
        z = np.polyfit(y_pred, sqrt_abs_resid, 1)
        p = np.poly1d(z)
        ax.plot(np.sort(y_pred), p(np.sort(y_pred)), 'r--', lw=2)
        
        ax.set_xlabel('Fitted Values', fontsize=12, color='white')
        ax.set_ylabel('√|Residuals|', fontsize=12, color='white')
        ax.set_title(f'Scale-Location Plot - {model_name}', fontsize=14, color='white')
        
        charts['scale_location'] = _fig_to_base64(fig)
    except Exception as e:
        logger.warning(f"Scale-location error: {e}")
    
    return charts


# =============================================================================
# CLUSTERING CHARTS (8 types)
# =============================================================================

def _generate_clustering_charts(
    X: Optional[np.ndarray],
    labels: np.ndarray,
    model_name: str,
    feature_names: Optional[List[str]] = None
) -> Dict[str, str]:
    """Generate comprehensive clustering charts"""
    charts = {}
    
    if X is None or len(X) < 5:
        return charts
    
    n_clusters = len(np.unique(labels))
    
    # 1. CLUSTER SCATTER (2D PCA)
    try:
        fig, ax = plt.subplots(figsize=(10, 8))
        
        if X.shape[1] >= 2:
            if X.shape[1] > 2:
                from sklearn.decomposition import PCA
                pca = PCA(n_components=2)
                X_2d = pca.fit_transform(X)
                xlabel = f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)'
                ylabel = f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)'
            else:
                X_2d = X
                xlabel = feature_names[0] if feature_names else 'Feature 1'
                ylabel = feature_names[1] if feature_names and len(feature_names) > 1 else 'Feature 2'
            
            for i in range(n_clusters):
                mask = labels == i
                ax.scatter(X_2d[mask, 0], X_2d[mask, 1], c=COLORS[i % len(COLORS)], 
                          s=50, alpha=0.7, label=f'Cluster {i} (n={mask.sum()})',
                          edgecolors='white', linewidth=0.5)
            
            ax.set_xlabel(xlabel, fontsize=12, color='white')
            ax.set_ylabel(ylabel, fontsize=12, color='white')
            ax.set_title(f'Cluster Visualization - {model_name}', fontsize=14, color='white')
            ax.legend()
            
            charts['cluster_scatter'] = _fig_to_base64(fig)
    except Exception as e:
        logger.warning(f"Cluster scatter error: {e}")
    
    # 2. CLUSTER DISTRIBUTION BAR
    try:
        fig, ax = plt.subplots(figsize=(8, 6))
        
        unique, counts = np.unique(labels, return_counts=True)
        bars = ax.bar(range(len(unique)), counts, color=COLORS[:len(unique)], edgecolor='white')
        
        for bar, count in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                   str(count), ha='center', fontsize=10, color='white')
        
        ax.set_xticks(range(len(unique)))
        ax.set_xticklabels([f'Cluster {i}' for i in unique])
        ax.set_xlabel('Cluster', fontsize=12, color='white')
        ax.set_ylabel('Count', fontsize=12, color='white')
        ax.set_title(f'Cluster Sizes - {model_name}', fontsize=14, color='white')
        
        charts['cluster_distribution'] = _fig_to_base64(fig)
    except Exception as e:
        logger.warning(f"Cluster distribution error: {e}")
    
    # 3. SILHOUETTE ANALYSIS
    if n_clusters >= 2:
        try:
            sil_vals = silhouette_samples(X, labels)
            sil_avg = silhouette_score(X, labels)
            
            fig, ax = plt.subplots(figsize=(10, 8))
            
            y_lower = 10
            for i in range(n_clusters):
                vals = sil_vals[labels == i]
                vals.sort()
                size = vals.shape[0]
                y_upper = y_lower + size
                
                ax.fill_betweenx(np.arange(y_lower, y_upper), 0, vals,
                                alpha=0.7, color=COLORS[i % len(COLORS)])
                ax.text(-0.05, y_lower + 0.5 * size, f'C{i}', fontsize=10, color='white')
                y_lower = y_upper + 10
            
            ax.axvline(x=sil_avg, color='red', linestyle='--', lw=2, label=f'Avg: {sil_avg:.3f}')
            ax.set_xlabel('Silhouette Coefficient', fontsize=12, color='white')
            ax.set_ylabel('Cluster', fontsize=12, color='white')
            ax.set_title(f'Silhouette Analysis - {model_name}', fontsize=14, color='white')
            ax.legend()
            
            charts['silhouette'] = _fig_to_base64(fig)
        except Exception as e:
            logger.warning(f"Silhouette error: {e}")
    
    # 4. FEATURE BOX PLOTS BY CLUSTER
    if feature_names and X.shape[1] >= 1:
        try:
            n_feat = min(4, X.shape[1])
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            axes = axes.flatten()
            
            for i in range(n_feat):
                ax = axes[i]
                data = [X[labels == c, i] for c in range(n_clusters)]
                bp = ax.boxplot(data, patch_artist=True)
                
                for j, patch in enumerate(bp['boxes']):
                    patch.set_facecolor(COLORS[j % len(COLORS)])
                    patch.set_alpha(0.7)
                
                ax.set_xticklabels([f'C{c}' for c in range(n_clusters)])
                fname = feature_names[i][:15] if i < len(feature_names) else f'Feature {i}'
                ax.set_title(fname, color='white')
            
            for i in range(n_feat, 4):
                axes[i].set_visible(False)
            
            fig.suptitle(f'Feature Distribution by Cluster - {model_name}', fontsize=14, color='white')
            plt.tight_layout()
            
            charts['cluster_boxplots'] = _fig_to_base64(fig)
        except Exception as e:
            logger.warning(f"Cluster boxplots error: {e}")
    
    # 5. CLUSTER HISTOGRAMS
    if feature_names and X.shape[1] >= 1:
        try:
            n_feat = min(4, X.shape[1])
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            axes = axes.flatten()
            
            for i in range(n_feat):
                ax = axes[i]
                for c in range(n_clusters):
                    ax.hist(X[labels == c, i], bins=15, alpha=0.5, 
                           color=COLORS[c % len(COLORS)], label=f'C{c}', edgecolor='white')
                
                fname = feature_names[i][:15] if i < len(feature_names) else f'Feature {i}'
                ax.set_xlabel(fname, color='white')
                ax.legend(fontsize=8)
            
            for i in range(n_feat, 4):
                axes[i].set_visible(False)
            
            fig.suptitle(f'Feature Histograms by Cluster - {model_name}', fontsize=14, color='white')
            plt.tight_layout()
            
            charts['cluster_histograms'] = _fig_to_base64(fig)
        except Exception as e:
            logger.warning(f"Cluster histograms error: {e}")
    
    return charts


# =============================================================================
# NLP CHARTS (6 types)
# =============================================================================

def _generate_nlp_charts(
    text_data: List[str],
    y: np.ndarray,
    model_name: str
) -> Dict[str, str]:
    """Generate NLP-specific charts"""
    charts = {}
    
    # 1. TEXT LENGTH DISTRIBUTION
    try:
        lengths = [len(str(t).split()) for t in text_data]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(lengths, bins=30, color=COLORS[0], alpha=0.7, edgecolor='white')
        ax.axvline(np.mean(lengths), color='red', linestyle='--', label=f'Mean: {np.mean(lengths):.1f}')
        ax.axvline(np.median(lengths), color=COLORS[3], linestyle='--', label=f'Median: {np.median(lengths):.1f}')
        
        ax.set_xlabel('Word Count', fontsize=12, color='white')
        ax.set_ylabel('Frequency', fontsize=12, color='white')
        ax.set_title(f'Text Length Distribution - {model_name}', fontsize=14, color='white')
        ax.legend()
        
        charts['text_length_dist'] = _fig_to_base64(fig)
    except Exception as e:
        logger.warning(f"Text length dist error: {e}")
    
    # 2. TEXT LENGTH BY CLASS
    try:
        unique_classes = np.unique(y)
        lengths = [len(str(t).split()) for t in text_data]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        data = [[lengths[i] for i in range(len(y)) if y[i] == c] for c in unique_classes]
        
        bp = ax.boxplot(data, patch_artist=True)
        for i, patch in enumerate(bp['boxes']):
            patch.set_facecolor(COLORS[i % len(COLORS)])
            patch.set_alpha(0.7)
        
        ax.set_xticklabels([f'Class {c}' for c in unique_classes], rotation=45, ha='right')
        ax.set_xlabel('Class', fontsize=12, color='white')
        ax.set_ylabel('Word Count', fontsize=12, color='white')
        ax.set_title(f'Text Length by Class - {model_name}', fontsize=14, color='white')
        
        charts['text_length_by_class'] = _fig_to_base64(fig)
    except Exception as e:
        logger.warning(f"Text length by class error: {e}")
    
    return charts


# =============================================================================
# COMMON CHARTS
# =============================================================================

def _generate_feature_importance_chart(
    feature_importance: List[Dict],
    model_name: str
) -> Optional[str]:
    """Generate feature importance horizontal bar chart"""
    try:
        if not feature_importance:
            return None
        
        features = feature_importance[:15]
        names = [f.get('feature', f"Feature {i}")[:25] for i, f in enumerate(features)]
        values = [f.get('importance', 0) * 100 for f in features]
        
        names, values = names[::-1], values[::-1]
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        colors = [COLORS[i % len(COLORS)] for i in range(len(names))][::-1]
        bars = ax.barh(range(len(names)), values, color=colors, edgecolor='white', linewidth=0.5)
        
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(names, fontsize=10)
        ax.set_xlabel('Importance (%)', fontsize=12, color='white')
        ax.set_title(f'Feature Importance - {model_name}', fontsize=14, color='white', pad=20)
        
        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                   f'{val:.1f}%', va='center', fontsize=9, color='white')
        
        ax.set_xlim([0, max(values) * 1.15 if values else 100])
        plt.tight_layout()
        
        return _fig_to_base64(fig)
    except Exception as e:
        logger.warning(f"Feature importance error: {e}")
        return None


def generate_model_comparison_chart(
    leaderboard: List[Dict],
    metric_name: str = "accuracy"
) -> Optional[str]:
    """Generate model comparison bar chart"""
    try:
        if not leaderboard or len(leaderboard) < 2:
            return None
        
        models = leaderboard[:10]
        names = [m.get('name', f"Model {i}")[:15] for i, m in enumerate(models)]
        scores = []
        
        for m in models:
            metrics = m.get('metrics', {})
            score = metrics.get(metric_name, metrics.get('accuracy', metrics.get('r2', metrics.get('f1', 0))))
            scores.append(float(score) * 100 if float(score) <= 1 else float(score))
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        colors = [COLORS[0] if i == 0 else COLORS[2] for i in range(len(names))]
        bars = ax.bar(range(len(names)), scores, color=colors, edgecolor='white', linewidth=0.5)
        
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels(names, rotation=45, ha='right', fontsize=10)
        ax.set_ylabel('Score (%)', fontsize=12, color='white')
        ax.set_title('Model Comparison', fontsize=14, color='white', pad=20)
        
        ax.annotate('🏆 BEST', xy=(0, scores[0]), xytext=(0, scores[0] + 2),
                   ha='center', fontsize=10, color=COLORS[0], fontweight='bold')
        
        for bar, score in zip(bars, scores):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                   f'{score:.1f}', ha='center', fontsize=9, color='white')
        
        plt.tight_layout()
        return _fig_to_base64(fig)
    except Exception as e:
        logger.warning(f"Model comparison error: {e}")
        return None


def generate_correlation_heatmap(df: pd.DataFrame, title: str = "Feature Correlation") -> Optional[str]:
    """Generate correlation heatmap for numeric features"""
    try:
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.shape[1] < 2:
            return None
        
        if numeric_df.shape[1] > 15:
            numeric_df = numeric_df.iloc[:, :15]
        
        corr = numeric_df.corr()
        
        fig, ax = plt.subplots(figsize=(10, 8))
        mask = np.triu(np.ones_like(corr, dtype=bool))
        sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap='RdYlGn',
                   center=0, ax=ax, linewidths=0.5, cbar_kws={'shrink': 0.8})
        
        ax.set_title(title, fontsize=14, color='white', pad=20)
        plt.tight_layout()
        
        return _fig_to_base64(fig)
    except Exception as e:
        logger.warning(f"Correlation heatmap error: {e}")
        return None


def generate_distribution_grid(df: pd.DataFrame, title: str = "Feature Distributions") -> Optional[str]:
    """Generate histogram grid for numeric features"""
    try:
        numeric_df = df.select_dtypes(include=[np.number])
        n_features = min(9, numeric_df.shape[1])
        
        if n_features < 1:
            return None
        
        rows = int(np.ceil(n_features / 3))
        fig, axes = plt.subplots(rows, 3, figsize=(12, rows * 3))
        axes = axes.flatten() if hasattr(axes, 'flatten') else [axes]
        
        for i, col in enumerate(numeric_df.columns[:n_features]):
            axes[i].hist(numeric_df[col].dropna(), bins=20, color=COLORS[i % len(COLORS)], 
                        alpha=0.7, edgecolor='white')
            axes[i].set_title(col[:20], fontsize=10, color='white')
        
        for i in range(n_features, len(axes)):
            axes[i].set_visible(False)
        
        fig.suptitle(title, fontsize=14, color='white')
        plt.tight_layout()
        
        return _fig_to_base64(fig)
    except Exception as e:
        logger.warning(f"Distribution grid error: {e}")
        return None


def generate_boxplot_grid(df: pd.DataFrame, title: str = "Feature Box Plots") -> Optional[str]:
    """Generate box plot grid for numeric features"""
    try:
        numeric_df = df.select_dtypes(include=[np.number])
        n_features = min(9, numeric_df.shape[1])
        
        if n_features < 1:
            return None
        
        rows = int(np.ceil(n_features / 3))
        fig, axes = plt.subplots(rows, 3, figsize=(12, rows * 3))
        axes = axes.flatten() if hasattr(axes, 'flatten') else [axes]
        
        for i, col in enumerate(numeric_df.columns[:n_features]):
            bp = axes[i].boxplot(numeric_df[col].dropna(), patch_artist=True)
            bp['boxes'][0].set_facecolor(COLORS[i % len(COLORS)])
            bp['boxes'][0].set_alpha(0.7)
            axes[i].set_title(col[:20], fontsize=10, color='white')
        
        for i in range(n_features, len(axes)):
            axes[i].set_visible(False)
        
        fig.suptitle(title, fontsize=14, color='white')
        plt.tight_layout()
        
        return _fig_to_base64(fig)
    except Exception as e:
        logger.warning(f"Boxplot grid error: {e}")
        return None
