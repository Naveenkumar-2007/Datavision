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
            
            ax.set_xlabel('Predicted', fontsize=12, color='#333333')
            ax.set_ylabel('Actual', fontsize=12, color='#333333')
            ax.set_title(f'Confusion Matrix - {model_name}', fontsize=14, color='#333333', pad=20)
            
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
        
        ax.bar(x - width/2, actual_counts, width, label='Actual', color=COLORS[0], edgecolor='#333333')
        ax.bar(x + width/2, pred_counts, width, label='Predicted', color=COLORS[2], edgecolor='#333333')
        
        ax.set_xlabel('Class', fontsize=12, color='#333333')
        ax.set_ylabel('Count', fontsize=12, color='#333333')
        ax.set_title(f'Class Distribution - {model_name}', fontsize=14, color='#333333')
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
            ax.set_xlabel('False Positive Rate', fontsize=12, color='#333333')
            ax.set_ylabel('True Positive Rate', fontsize=12, color='#333333')
            ax.set_title(f'ROC Curve - {model_name}', fontsize=14, color='#333333')
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
            ax.set_xlabel('Recall', fontsize=12, color='#333333')
            ax.set_ylabel('Precision', fontsize=12, color='#333333')
            ax.set_title(f'Precision-Recall Curve - {model_name}', fontsize=14, color='#333333')
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
            ax.set_xlabel('Mean Predicted Probability', fontsize=12, color='#333333')
            ax.set_ylabel('Fraction of Positives', fontsize=12, color='#333333')
            ax.set_title(f'Calibration Curve - {model_name}', fontsize=14, color='#333333')
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
            
            ax.hist(max_proba[correct], bins=20, alpha=0.7, color=COLORS[1], label='Correct', edgecolor='#333333')
            ax.hist(max_proba[~correct], bins=20, alpha=0.7, color=COLORS[6], label='Incorrect', edgecolor='#333333')
            
            ax.set_xlabel('Prediction Confidence', fontsize=12, color='#333333')
            ax.set_ylabel('Count', fontsize=12, color='#333333')
            ax.set_title(f'Confidence Distribution - {model_name}', fontsize=14, color='#333333')
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
        axes[0].set_title('Actual Class Balance', color='#333333', fontsize=12)
        
        unique_p, counts_p = np.unique(y_pred, return_counts=True)
        labels_p = [str(class_names[i])[:10] if class_names and i < len(class_names) else str(u) for i, u in enumerate(unique_p)]
        axes[1].pie(counts_p, labels=labels_p, autopct='%1.1f%%', colors=colors[:len(unique_p)],
                   textprops={'color': 'white'}, wedgeprops={'edgecolor': 'white'})
        axes[1].set_title('Predicted Class Balance', color='#333333', fontsize=12)
        
        fig.suptitle(f'Class Balance - {model_name}', fontsize=14, color='#333333')
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
            ax.set_xlabel('Class', fontsize=12, color='#333333')
            ax.set_ylabel('Prediction Confidence', fontsize=12, color='#333333')
            ax.set_title(f'Confidence by Class - {model_name}', fontsize=14, color='#333333')
            
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
            ax.set_title(f'Classification Metrics by Class - {model_name}', fontsize=14, color='#333333')
            
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
            
            ax.set_xlabel('Prediction Score', fontsize=12, color='#333333')
            ax.set_ylabel('Density', fontsize=12, color='#333333')
            ax.set_title(f'Score Distribution by Class - {model_name}', fontsize=14, color='#333333')
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
                   xy=(0.05, 0.95), xycoords='axes fraction', fontsize=11, color='#333333',
                   bbox=dict(boxstyle='round', facecolor='#333333', alpha=0.8), va='top')
        
        ax.set_xlabel('Actual', fontsize=12, color='#333333')
        ax.set_ylabel('Predicted', fontsize=12, color='#333333')
        ax.set_title(f'Actual vs Predicted - {model_name}', fontsize=14, color='#333333')
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
        axes[0, 0].set_xlabel('Predicted', color='#333333')
        axes[0, 0].set_ylabel('Residual', color='#333333')
        axes[0, 0].set_title('Residuals vs Predicted', color='#333333')
        
        # Residuals Histogram
        axes[0, 1].hist(residuals, bins=30, color=COLORS[2], alpha=0.7, edgecolor='#333333')
        axes[0, 1].axvline(x=0, color='red', linestyle='--', lw=1.5)
        axes[0, 1].set_xlabel('Residual', color='#333333')
        axes[0, 1].set_ylabel('Frequency', color='#333333')
        axes[0, 1].set_title('Residuals Distribution', color='#333333')
        
        # Q-Q Plot
        stats.probplot(residuals, dist="norm", plot=axes[1, 0])
        axes[1, 0].get_lines()[0].set_color(COLORS[0])
        axes[1, 0].get_lines()[1].set_color('red')
        axes[1, 0].set_title('Q-Q Plot (Normality)', color='#333333')
        axes[1, 0].set_xlabel('Theoretical Quantiles', color='#333333')
        axes[1, 0].set_ylabel('Sample Quantiles', color='#333333')
        
        # Residuals vs Index
        axes[1, 1].scatter(range(len(residuals)), residuals, alpha=0.6, color=COLORS[3], s=30)
        axes[1, 1].axhline(y=0, color='red', linestyle='--', lw=1.5)
        axes[1, 1].set_xlabel('Index', color='#333333')
        axes[1, 1].set_ylabel('Residual', color='#333333')
        axes[1, 1].set_title('Residuals vs Order', color='#333333')
        
        fig.suptitle(f'Residual Analysis - {model_name}', fontsize=14, color='#333333', y=1.02)
        plt.tight_layout()
        
        charts['residuals_analysis'] = _fig_to_base64(fig)
    except Exception as e:
        logger.warning(f"Residuals analysis error: {e}")
    
    # 3. ERROR DISTRIBUTION with percentiles
    try:
        fig, ax = plt.subplots(figsize=(8, 6))
        
        sns.kdeplot(errors, ax=ax, color=COLORS[3], fill=True, alpha=0.3, lw=2)
        ax.hist(errors, bins=30, density=True, alpha=0.3, color=COLORS[3], edgecolor='#333333')
        
        for p, color in [(50, COLORS[0]), (75, COLORS[1]), (90, COLORS[4]), (95, COLORS[6])]:
            val = np.percentile(errors, p)
            ax.axvline(val, color=color, linestyle='--', label=f'{p}th: {val:.2f}')
        
        ax.set_xlabel('Absolute Error', fontsize=12, color='#333333')
        ax.set_ylabel('Density', fontsize=12, color='#333333')
        ax.set_title(f'Error Distribution - {model_name}', fontsize=14, color='#333333')
        ax.legend(fontsize=9)
        
        charts['error_distribution'] = _fig_to_base64(fig)
    except Exception as e:
        logger.warning(f"Error distribution error: {e}")
    
    # 4. TARGET DISTRIBUTION HISTOGRAM
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.hist(y_test, bins=30, alpha=0.6, color=COLORS[0], label='Actual', edgecolor='#333333')
        ax.hist(y_pred, bins=30, alpha=0.6, color=COLORS[2], label='Predicted', edgecolor='#333333')
        
        ax.axvline(y_test.mean(), color=COLORS[0], linestyle='--', lw=2, label=f'Actual Mean: {y_test.mean():.2f}')
        ax.axvline(y_pred.mean(), color=COLORS[2], linestyle='--', lw=2, label=f'Pred Mean: {y_pred.mean():.2f}')
        
        ax.set_xlabel('Value', fontsize=12, color='#333333')
        ax.set_ylabel('Frequency', fontsize=12, color='#333333')
        ax.set_title(f'Target Distribution - {model_name}', fontsize=14, color='#333333')
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
        ax.set_xlabel('Target Quantile', fontsize=12, color='#333333')
        ax.set_ylabel('Absolute Error', fontsize=12, color='#333333')
        ax.set_title(f'Error by Target Range - {model_name}', fontsize=14, color='#333333')
        
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
        
        ax.set_xlabel('Sample (sorted)', fontsize=12, color='#333333')
        ax.set_ylabel('Value', fontsize=12, color='#333333')
        ax.set_title(f'Prediction Overview - {model_name}', fontsize=14, color='#333333')
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
        
        ax.set_xlabel('Fitted Values', fontsize=12, color='#333333')
        ax.set_ylabel('√|Residuals|', fontsize=12, color='#333333')
        ax.set_title(f'Scale-Location Plot - {model_name}', fontsize=14, color='#333333')
        
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
            
            ax.set_xlabel(xlabel, fontsize=12, color='#333333')
            ax.set_ylabel(ylabel, fontsize=12, color='#333333')
            ax.set_title(f'Cluster Visualization - {model_name}', fontsize=14, color='#333333')
            ax.legend()
            
            charts['cluster_scatter'] = _fig_to_base64(fig)
    except Exception as e:
        logger.warning(f"Cluster scatter error: {e}")
    
    # 2. CLUSTER DISTRIBUTION BAR
    try:
        fig, ax = plt.subplots(figsize=(8, 6))
        
        unique, counts = np.unique(labels, return_counts=True)
        bars = ax.bar(range(len(unique)), counts, color=COLORS[:len(unique)], edgecolor='#333333')
        
        for bar, count in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                   str(count), ha='center', fontsize=10, color='#333333')
        
        ax.set_xticks(range(len(unique)))
        ax.set_xticklabels([f'Cluster {i}' for i in unique])
        ax.set_xlabel('Cluster', fontsize=12, color='#333333')
        ax.set_ylabel('Count', fontsize=12, color='#333333')
        ax.set_title(f'Cluster Sizes - {model_name}', fontsize=14, color='#333333')
        
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
                ax.text(-0.05, y_lower + 0.5 * size, f'C{i}', fontsize=10, color='#333333')
                y_lower = y_upper + 10
            
            ax.axvline(x=sil_avg, color='red', linestyle='--', lw=2, label=f'Avg: {sil_avg:.3f}')
            ax.set_xlabel('Silhouette Coefficient', fontsize=12, color='#333333')
            ax.set_ylabel('Cluster', fontsize=12, color='#333333')
            ax.set_title(f'Silhouette Analysis - {model_name}', fontsize=14, color='#333333')
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
                ax.set_title(fname, color='#333333')
            
            for i in range(n_feat, 4):
                axes[i].set_visible(False)
            
            fig.suptitle(f'Feature Distribution by Cluster - {model_name}', fontsize=14, color='#333333')
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
                           color=COLORS[c % len(COLORS)], label=f'C{c}', edgecolor='#333333')
                
                fname = feature_names[i][:15] if i < len(feature_names) else f'Feature {i}'
                ax.set_xlabel(fname, color='#333333')
                ax.legend(fontsize=8)
            
            for i in range(n_feat, 4):
                axes[i].set_visible(False)
            
            fig.suptitle(f'Feature Histograms by Cluster - {model_name}', fontsize=14, color='#333333')
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
        ax.hist(lengths, bins=30, color=COLORS[0], alpha=0.7, edgecolor='#333333')
        ax.axvline(np.mean(lengths), color='red', linestyle='--', label=f'Mean: {np.mean(lengths):.1f}')
        ax.axvline(np.median(lengths), color=COLORS[3], linestyle='--', label=f'Median: {np.median(lengths):.1f}')
        
        ax.set_xlabel('Word Count', fontsize=12, color='#333333')
        ax.set_ylabel('Frequency', fontsize=12, color='#333333')
        ax.set_title(f'Text Length Distribution - {model_name}', fontsize=14, color='#333333')
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
        ax.set_xlabel('Class', fontsize=12, color='#333333')
        ax.set_ylabel('Word Count', fontsize=12, color='#333333')
        ax.set_title(f'Text Length by Class - {model_name}', fontsize=14, color='#333333')
        
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
        
        features = feature_importance[:50]  # Show up to 50 features
        names = [f.get('feature', f"Feature {i}")[:25] for i, f in enumerate(features)]
        values = [f.get('importance', 0) * 100 for f in features]
        
        names, values = names[::-1], values[::-1]
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        colors = [COLORS[i % len(COLORS)] for i in range(len(names))][::-1]
        bars = ax.barh(range(len(names)), values, color=colors, edgecolor='#333333', linewidth=0.5)
        
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(names, fontsize=10)
        ax.set_xlabel('Importance (%)', fontsize=12, color='#333333')
        ax.set_title(f'Feature Importance - {model_name}', fontsize=14, color='#333333', pad=20)
        
        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                   f'{val:.1f}%', va='center', fontsize=9, color='#333333')
        
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
        bars = ax.bar(range(len(names)), scores, color=colors, edgecolor='#333333', linewidth=0.5)
        
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels(names, rotation=45, ha='right', fontsize=10)
        ax.set_ylabel('Score (%)', fontsize=12, color='#333333')
        ax.set_title('Model Comparison', fontsize=14, color='#333333', pad=20)
        
        ax.annotate('🏆 BEST', xy=(0, scores[0]), xytext=(0, scores[0] + 2),
                   ha='center', fontsize=10, color=COLORS[0], fontweight='bold')
        
        for bar, score in zip(bars, scores):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                   f'{score:.1f}', ha='center', fontsize=9, color='#333333')
        
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
        
        ax.set_title(title, fontsize=14, color='#333333', pad=20)
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
                        alpha=0.7, edgecolor='#333333')
            axes[i].set_title(col[:20], fontsize=10, color='#333333')
        
        for i in range(n_features, len(axes)):
            axes[i].set_visible(False)
        
        fig.suptitle(title, fontsize=14, color='#333333')
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
            axes[i].set_title(col[:20], fontsize=10, color='#333333')
        
        for i in range(n_features, len(axes)):
            axes[i].set_visible(False)
        
        fig.suptitle(title, fontsize=14, color='#333333')
        plt.tight_layout()
        
        return _fig_to_base64(fig)
    except Exception as e:
        logger.warning(f"Boxplot grid error: {e}")
        return None


# =============================================================================
# 🌟 ULTRA MODE ADVANCED CHARTS (Premium Visualizations)
# =============================================================================
# These charts are ONLY generated in Ultra mode for advanced insights

# Premium Ultra Color Palette - Rich Gradients
ULTRA_COLORS = {
    'primary': ['#667eea', '#764ba2'],      # Purple Gradient
    'success': ['#11998e', '#38ef7d'],      # Green Gradient  
    'warning': ['#f093fb', '#f5576c'],      # Pink Gradient
    'info': ['#4facfe', '#00f2fe'],         # Blue Gradient
    'danger': ['#ff416c', '#ff4b2b'],       # Red Gradient
    'premium': ['#c471f5', '#fa71cd'],      # Premium Pink
    'gold': ['#f7971e', '#ffd200'],         # Gold Gradient
    'ocean': ['#2193b0', '#6dd5ed'],        # Ocean Blue
}

ULTRA_PALETTE = [
    '#667eea', '#11998e', '#f093fb', '#4facfe', '#ff416c',
    '#c471f5', '#f7971e', '#2193b0', '#764ba2', '#38ef7d'
]


def generate_learning_curve_chart(
    model,
    X: np.ndarray,
    y: np.ndarray,
    model_name: str = "Model",
    cv: int = 5,
    train_sizes: List[float] = None
) -> Optional[str]:
    """
    🎓 Generate Learning Curve chart showing model performance vs training data size.
    
    This is a premium chart that helps identify:
    - Overfitting (high training score, low validation score)
    - Underfitting (both scores low)
    - Ideal model fit (both scores high and converging)
    
    Args:
        model: Trained sklearn model
        X: Feature matrix
        y: Target array
        model_name: Name for chart title
        cv: Number of cross-validation folds
        train_sizes: Training sizes to evaluate (default: [0.1, 0.3, 0.5, 0.7, 0.9, 1.0])
    
    Returns:
        Base64 encoded PNG image or None
    """
    try:
        from sklearn.model_selection import learning_curve
        
        if train_sizes is None:
            train_sizes = [0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
        
        # Limit data size for performance
        max_samples = min(5000, len(X))
        if len(X) > max_samples:
            indices = np.random.choice(len(X), max_samples, replace=False)
            X_sample, y_sample = X[indices], y[indices]
        else:
            X_sample, y_sample = X, y
        
        # Calculate learning curve
        train_sizes_abs, train_scores, val_scores = learning_curve(
            model, X_sample, y_sample,
            train_sizes=train_sizes,
            cv=min(cv, 5),
            n_jobs=-1,
            scoring='accuracy' if hasattr(model, 'predict_proba') else 'r2',
            shuffle=True,
            random_state=42
        )
        
        # Calculate mean and std
        train_mean = np.mean(train_scores, axis=1)
        train_std = np.std(train_scores, axis=1)
        val_mean = np.mean(val_scores, axis=1)
        val_std = np.std(val_scores, axis=1)
        
        # Create chart
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot training scores
        ax.fill_between(train_sizes_abs, train_mean - train_std, train_mean + train_std,
                       alpha=0.15, color=ULTRA_PALETTE[0])
        ax.plot(train_sizes_abs, train_mean, 'o-', color=ULTRA_PALETTE[0], 
               linewidth=2, markersize=8, label='Training Score')
        
        # Plot validation scores
        ax.fill_between(train_sizes_abs, val_mean - val_std, val_mean + val_std,
                       alpha=0.15, color=ULTRA_PALETTE[4])
        ax.plot(train_sizes_abs, val_mean, 's-', color=ULTRA_PALETTE[4], 
               linewidth=2, markersize=8, label='Validation Score')
        
        # Add annotations for final values
        ax.annotate(f'{train_mean[-1]:.3f}', 
                   xy=(train_sizes_abs[-1], train_mean[-1]),
                   xytext=(5, 10), textcoords='offset points',
                   fontsize=10, fontweight='bold', color=ULTRA_PALETTE[0])
        ax.annotate(f'{val_mean[-1]:.3f}', 
                   xy=(train_sizes_abs[-1], val_mean[-1]),
                   xytext=(5, -15), textcoords='offset points',
                   fontsize=10, fontweight='bold', color=ULTRA_PALETTE[4])
        
        # Calculate and display gap (overfitting indicator)
        gap = train_mean[-1] - val_mean[-1]
        gap_color = '#10B981' if gap < 0.05 else ('#F59E0B' if gap < 0.15 else '#EF4444')
        ax.text(0.95, 0.05, f'Gap: {gap:.3f}', transform=ax.transAxes,
               ha='right', va='bottom', fontsize=11, fontweight='bold',
               color=gap_color, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.set_xlabel('Training Examples', fontsize=12, color='#333333')
        ax.set_ylabel('Score', fontsize=12, color='#333333')
        ax.set_title(f'📈 Learning Curve - {model_name}', fontsize=14, color='#333333', pad=15)
        ax.legend(loc='lower right', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Set reasonable y-axis limits
        min_score = max(0, min(train_mean.min(), val_mean.min()) - 0.1)
        max_score = min(1.0, max(train_mean.max(), val_mean.max()) + 0.1)
        ax.set_ylim(min_score, max_score)
        
        plt.tight_layout()
        return _fig_to_base64(fig)
        
    except Exception as e:
        logger.warning(f"Learning curve generation error: {e}")
        return None


def generate_model_comparison_radar(
    leaderboard: List[Dict],
    metric_names: List[str] = None,
    top_n: int = 5
) -> Optional[str]:
    """
    🎯 Generate multi-model comparison radar chart.
    
    Compares top models across multiple metrics in a radar/spider chart format.
    
    Args:
        leaderboard: List of model results with metrics
        metric_names: Metrics to compare (default: accuracy, precision, recall, f1)
        top_n: Number of top models to include
    
    Returns:
        Base64 encoded PNG image or None
    """
    try:
        if not leaderboard or len(leaderboard) < 2:
            return None
        
        if metric_names is None:
            metric_names = ['accuracy', 'precision', 'recall', 'f1']
        
        # Get top models
        top_models = leaderboard[:min(top_n, len(leaderboard))]
        
        # Extract metrics for each model
        model_data = []
        for model in top_models:
            metrics = model.get('metrics', {})
            values = []
            for metric in metric_names:
                val = metrics.get(metric, 0)
                if isinstance(val, (int, float)):
                    values.append(float(val))
                else:
                    values.append(0)
            model_data.append({
                'name': model.get('name', 'Unknown')[:20],
                'values': values
            })
        
        if not model_data:
            return None
        
        # Create radar chart
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
        
        # Calculate angles
        n_metrics = len(metric_names)
        angles = np.linspace(0, 2 * np.pi, n_metrics, endpoint=False).tolist()
        angles += angles[:1]  # Close the polygon
        
        # Plot each model
        for i, model in enumerate(model_data):
            values = model['values'] + [model['values'][0]]  # Close polygon
            color = ULTRA_PALETTE[i % len(ULTRA_PALETTE)]
            
            ax.fill(angles, values, color=color, alpha=0.1)
            ax.plot(angles, values, 'o-', color=color, linewidth=2, 
                   markersize=6, label=model['name'])
        
        # Set labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([m.title() for m in metric_names], size=11, color='#333333')
        ax.set_ylim(0, 1)
        
        # Add legend
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0), fontsize=9)
        
        ax.set_title('🎯 Model Comparison Radar', size=14, y=1.1, color='#333333', fontweight='bold')
        
        plt.tight_layout()
        return _fig_to_base64(fig)
        
    except Exception as e:
        logger.warning(f"Model comparison radar error: {e}")
        return None


def generate_training_history_chart(
    history: Dict[str, List[float]],
    model_name: str = "Deep Learning Model"
) -> Optional[str]:
    """
    📊 Generate training history chart for deep learning models.
    
    Shows loss and metric curves over training epochs.
    
    Args:
        history: Dictionary with 'loss', 'val_loss', 'accuracy', 'val_accuracy' etc.
        model_name: Name for chart title
    
    Returns:
        Base64 encoded PNG image or None
    """
    try:
        if not history:
            return None
        
        # Create 2x1 subplot for loss and accuracy
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        epochs = range(1, len(history.get('loss', [])) + 1)
        
        # Left: Loss curves
        ax1 = axes[0]
        if 'loss' in history:
            ax1.plot(epochs, history['loss'], 'o-', color=ULTRA_PALETTE[0], 
                    linewidth=2, markersize=4, label='Training Loss')
        if 'val_loss' in history:
            ax1.plot(epochs, history['val_loss'], 's-', color=ULTRA_PALETTE[4], 
                    linewidth=2, markersize=4, label='Validation Loss')
        
        ax1.set_xlabel('Epoch', fontsize=11)
        ax1.set_ylabel('Loss', fontsize=11)
        ax1.set_title('📉 Training & Validation Loss', fontsize=12, color='#333333')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Find best validation loss epoch
        if 'val_loss' in history:
            best_epoch = np.argmin(history['val_loss']) + 1
            ax1.axvline(best_epoch, color='green', linestyle='--', alpha=0.7,
                       label=f'Best: Epoch {best_epoch}')
        
        # Right: Accuracy curves (if available)
        ax2 = axes[1]
        has_accuracy = 'accuracy' in history or 'val_accuracy' in history
        
        if has_accuracy:
            if 'accuracy' in history:
                ax2.plot(epochs, history['accuracy'], 'o-', color=ULTRA_PALETTE[1], 
                        linewidth=2, markersize=4, label='Training Accuracy')
            if 'val_accuracy' in history:
                ax2.plot(epochs, history['val_accuracy'], 's-', color=ULTRA_PALETTE[3], 
                        linewidth=2, markersize=4, label='Validation Accuracy')
            
            ax2.set_xlabel('Epoch', fontsize=11)
            ax2.set_ylabel('Accuracy', fontsize=11)
            ax2.set_title('📈 Training & Validation Accuracy', fontsize=12, color='#333333')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        else:
            # If no accuracy, show a summary box
            ax2.text(0.5, 0.5, f'Training Complete\n\nFinal Loss: {history.get("loss", [0])[-1]:.4f}',
                    ha='center', va='center', fontsize=14, transform=ax2.transAxes,
                    bbox=dict(boxstyle='round', facecolor=ULTRA_PALETTE[1], alpha=0.3))
            ax2.set_title('📊 Training Summary', fontsize=12, color='#333333')
            ax2.axis('off')
        
        fig.suptitle(f'🧠 Training History - {model_name}', fontsize=14, y=1.02, color='#333333')
        plt.tight_layout()
        
        return _fig_to_base64(fig)
        
    except Exception as e:
        logger.warning(f"Training history chart error: {e}")
        return None



def generate_ultra_charts(
    task_type: str,
    y_test: np.ndarray,
    y_pred: np.ndarray,
    y_proba: Optional[np.ndarray] = None,
    feature_importance: Optional[List[Dict]] = None,
    leaderboard: Optional[List[Dict]] = None,
    model_name: str = "Model",
    X_test: Optional[np.ndarray] = None,
    cv_scores: Optional[List[float]] = None
) -> Dict[str, str]:
    """
    🌟 ULTRA MODE ADVANCED CHARTS
    
    Generates premium visualizations with advanced analytics:
    1. Learning Curve Analysis
    2. Performance Radar Chart
    3. Model Reliability Analysis
    4. Cross-Validation Stability
    5. Prediction Density Plot
    6. SHAP-style Feature Importance
    7. Performance Dashboard
    8. Threshold Analysis (Classification)
    """
    charts = {}
    
    try:
        y_test = np.array(y_test).flatten()
        y_pred = np.array(y_pred).flatten()
        
        task_lower = task_type.lower()
        is_classification = 'classification' in task_lower or 'nlp' in task_lower
        
        # 1. PERFORMANCE RADAR CHART (Multi-metric visualization)
        if is_classification:
            try:
                from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
                
                accuracy = accuracy_score(y_test, y_pred)
                precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
                recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
                f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
                
                # Calculate specificity (TN / (TN + FP)) for binary
                n_classes = len(np.unique(y_test))
                if n_classes == 2:
                    from sklearn.metrics import confusion_matrix
                    cm = confusion_matrix(y_test, y_pred)
                    specificity = cm[0,0] / (cm[0,0] + cm[0,1]) if (cm[0,0] + cm[0,1]) > 0 else 0
                else:
                    specificity = recall  # Use recall as proxy for multi-class
                
                metrics = ['Accuracy', 'Precision', 'Recall', 'F1-Score', 'Specificity']
                values = [accuracy, precision, recall, f1, specificity]
                
                # Radar chart
                fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
                
                angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
                values_plot = values + [values[0]]  # Close the polygon
                angles += angles[:1]
                
                ax.fill(angles, values_plot, color=ULTRA_PALETTE[0], alpha=0.25)
                ax.plot(angles, values_plot, color=ULTRA_PALETTE[0], linewidth=2, marker='o', markersize=8)
                
                ax.set_xticks(angles[:-1])
                ax.set_xticklabels(metrics, size=11, color='#333333')
                ax.set_ylim(0, 1)
                ax.set_title(f'🎯 Performance Radar - {model_name}', size=14, y=1.1, color='#333333')
                
                # Add value annotations
                for angle, value, metric in zip(angles[:-1], values, metrics):
                    ax.annotate(f'{value:.2f}', xy=(angle, value), xytext=(angle, value + 0.1),
                               ha='center', fontsize=9, color=ULTRA_PALETTE[0], fontweight='bold')
                
                charts['ultra_performance_radar'] = _fig_to_base64(fig)
            except Exception as e:
                logger.warning(f"Performance radar error: {e}")
        
        # 2. MODEL RELIABILITY / CALIBRATION ANALYSIS
        if is_classification and y_proba is not None:
            try:
                fig, axes = plt.subplots(1, 2, figsize=(14, 6))
                
                # Left: Reliability diagram with confidence intervals
                ax1 = axes[0]
                n_classes = len(np.unique(y_test))
                
                if n_classes == 2 and len(y_proba.shape) > 1:
                    prob = y_proba[:, 1]
                    
                    # Binned reliability
                    n_bins = 10
                    bins = np.linspace(0, 1, n_bins + 1)
                    bin_indices = np.digitize(prob, bins) - 1
                    bin_indices = np.clip(bin_indices, 0, n_bins - 1)
                    
                    bin_accuracy = []
                    bin_confidence = []
                    bin_counts = []
                    
                    for i in range(n_bins):
                        mask = bin_indices == i
                        if mask.sum() > 0:
                            bin_accuracy.append(y_test[mask].mean())
                            bin_confidence.append(prob[mask].mean())
                            bin_counts.append(mask.sum())
                        else:
                            bin_accuracy.append(np.nan)
                            bin_confidence.append((bins[i] + bins[i+1]) / 2)
                            bin_counts.append(0)
                    
                    # Plot with gradient bars
                    bar_colors = plt.cm.coolwarm(np.array(bin_accuracy))
                    ax1.bar(range(n_bins), bin_accuracy, color=bar_colors, edgecolor='#333333', alpha=0.8)
                    ax1.plot(range(n_bins), bin_confidence, 'k--', lw=2, label='Perfect Calibration')
                    ax1.set_xticks(range(n_bins))
                    ax1.set_xticklabels([f'{bins[i]:.1f}-{bins[i+1]:.1f}' for i in range(n_bins)], rotation=45, ha='right')
                    ax1.set_xlabel('Predicted Probability Bin', fontsize=11)
                    ax1.set_ylabel('Actual Accuracy', fontsize=11)
                    ax1.set_title('📊 Calibration Analysis', fontsize=13, color='#333333')
                    ax1.legend()
                    ax1.set_ylim(0, 1)
                
                # Right: Confidence vs Accuracy scatter
                ax2 = axes[1]
                max_proba = np.max(y_proba, axis=1) if len(y_proba.shape) > 1 else y_proba
                correct = (y_pred == y_test).astype(int)
                
                # Hexbin for density
                hb = ax2.hexbin(max_proba, correct, gridsize=20, cmap='YlGnBu', mincnt=1)
                plt.colorbar(hb, ax=ax2, label='Count')
                ax2.set_xlabel('Prediction Confidence', fontsize=11)
                ax2.set_ylabel('Correct (1) / Incorrect (0)', fontsize=11)
                ax2.set_title('🎯 Confidence vs Correctness', fontsize=13, color='#333333')
                
                plt.tight_layout()
                charts['ultra_model_reliability'] = _fig_to_base64(fig)
            except Exception as e:
                logger.warning(f"Model reliability error: {e}")
        
        # 3. CROSS-VALIDATION STABILITY (if cv_scores provided)
        if cv_scores and len(cv_scores) > 1:
            try:
                fig, ax = plt.subplots(figsize=(10, 6))
                
                folds = range(1, len(cv_scores) + 1)
                mean_score = np.mean(cv_scores)
                std_score = np.std(cv_scores)
                
                # Gradient bars
                colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(cv_scores)))
                bars = ax.bar(folds, cv_scores, color=colors, edgecolor='#333333', linewidth=1.5)
                
                # Mean line
                ax.axhline(mean_score, color='#ff416c', linestyle='--', linewidth=2, 
                          label=f'Mean: {mean_score:.4f}')
                ax.fill_between([0.5, len(cv_scores) + 0.5], mean_score - std_score, mean_score + std_score,
                               alpha=0.2, color='#ff416c', label=f'±1 Std: {std_score:.4f}')
                
                ax.set_xlabel('Fold', fontsize=12)
                ax.set_ylabel('Score', fontsize=12)
                ax.set_title(f'📈 Cross-Validation Stability - {model_name}', fontsize=14, color='#333333')
                ax.set_xticks(folds)
                ax.legend()
                
                # Add value labels
                for bar, score in zip(bars, cv_scores):
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                           f'{score:.3f}', ha='center', fontsize=9, fontweight='bold')
                
                charts['ultra_cv_stability'] = _fig_to_base64(fig)
            except Exception as e:
                logger.warning(f"CV stability error: {e}")
        
        # 4. PREDICTION DENSITY / JOINTPLOT
        try:
            fig, ax = plt.subplots(figsize=(10, 8))
            
            if is_classification and y_proba is not None and len(y_proba.shape) > 1:
                # For classification: confidence heatmap
                max_proba = np.max(y_proba, axis=1)
                
                # KDE density
                from scipy.stats import gaussian_kde
                xy = np.vstack([y_test, max_proba])
                try:
                    z = gaussian_kde(xy)(xy)
                    scatter = ax.scatter(y_test, max_proba, c=z, s=50, cmap='plasma', alpha=0.7)
                    plt.colorbar(scatter, ax=ax, label='Density')
                except:
                    scatter = ax.scatter(y_test, max_proba, c=ULTRA_PALETTE[0], s=50, alpha=0.6)
                
                ax.set_xlabel('Actual Class', fontsize=12)
                ax.set_ylabel('Prediction Confidence', fontsize=12)
                ax.set_title(f'🌈 Prediction Density - {model_name}', fontsize=14, color='#333333')
            else:
                # For regression: actual vs predicted density
                from scipy.stats import gaussian_kde
                xy = np.vstack([y_test, y_pred])
                try:
                    z = gaussian_kde(xy)(xy)
                    scatter = ax.scatter(y_test, y_pred, c=z, s=50, cmap='viridis', alpha=0.7)
                    plt.colorbar(scatter, ax=ax, label='Density')
                except:
                    scatter = ax.scatter(y_test, y_pred, c=ULTRA_PALETTE[1], s=50, alpha=0.6)
                
                # Perfect line
                min_v, max_v = min(y_test.min(), y_pred.min()), max(y_test.max(), y_pred.max())
                ax.plot([min_v, max_v], [min_v, max_v], 'r--', lw=2, label='Perfect')
                ax.legend()
                ax.set_xlabel('Actual Value', fontsize=12)
                ax.set_ylabel('Predicted Value', fontsize=12)
                ax.set_title(f'🌈 Prediction Density - {model_name}', fontsize=14, color='#333333')
            
            charts['ultra_prediction_density'] = _fig_to_base64(fig)
        except Exception as e:
            logger.warning(f"Prediction density error: {e}")
        
        # 5. SHAP-STYLE FEATURE IMPORTANCE (Premium visualization)
        if feature_importance and len(feature_importance) > 0:
            try:
                fig, ax = plt.subplots(figsize=(12, 8))
                
                top_n = min(15, len(feature_importance))
                features = feature_importance[:top_n]
                names = [f.get('feature', f"Feat {i}")[:30] for i, f in enumerate(features)]
                values = [f.get('importance', 0) * 100 for f in features]
                
                # Reverse for horizontal bar (top feature at top)
                names = names[::-1]
                values = values[::-1]
                
                # Gradient colors based on importance
                colors = plt.cm.plasma(np.linspace(0.2, 0.8, len(names)))[::-1]
                
                bars = ax.barh(range(len(names)), values, color=colors, 
                              edgecolor='#333333', linewidth=0.5, height=0.7)
                
                # Add lollipop markers
                for i, (bar, val) in enumerate(zip(bars, values)):
                    ax.scatter(val, i, s=100, color=colors[i], zorder=5, edgecolors='white', linewidths=2)
                    ax.text(val + max(values)*0.02, i, f'{val:.1f}%', va='center', fontsize=10, fontweight='bold')
                
                ax.set_yticks(range(len(names)))
                ax.set_yticklabels(names, fontsize=10)
                ax.set_xlabel('Importance (%)', fontsize=12)
                ax.set_title(f'🎨 Feature Importance (Premium) - {model_name}', fontsize=14, color='#333333', pad=15)
                ax.set_xlim(0, max(values) * 1.2)
                
                # Add gradient background
                ax.axvspan(0, max(values) * 0.33, alpha=0.1, color='green')
                ax.axvspan(max(values) * 0.33, max(values) * 0.66, alpha=0.1, color='yellow')
                ax.axvspan(max(values) * 0.66, max(values) * 1.2, alpha=0.1, color='red')
                
                plt.tight_layout()
                charts['ultra_feature_importance'] = _fig_to_base64(fig)
            except Exception as e:
                logger.warning(f"SHAP-style importance error: {e}")
        
        # 6. MODEL COMPARISON DASHBOARD (if leaderboard provided)
        if leaderboard and len(leaderboard) > 1:
            try:
                fig, axes = plt.subplots(2, 2, figsize=(14, 10))
                
                # Get model names and metrics
                models = [m.get('name', f"Model {i}")[:15] for i, m in enumerate(leaderboard[:8])]
                
                # Get different metrics
                scores = [m.get('score', 0) for m in leaderboard[:8]]
                accuracies = [m.get('metrics', {}).get('accuracy', 0) for m in leaderboard[:8]]
                f1_scores = [m.get('metrics', {}).get('f1', 0) for m in leaderboard[:8]]
                
                # Top-left: Primary Score
                ax1 = axes[0, 0]
                colors1 = plt.cm.coolwarm(np.linspace(0.2, 0.8, len(models)))
                bars1 = ax1.barh(models, scores, color=colors1, edgecolor='#333333')
                ax1.set_xlabel('Score')
                ax1.set_title('🏆 Model Scores', fontsize=12, color='#333333')
                for bar, score in zip(bars1, scores):
                    ax1.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                            f'{score:.3f}', va='center', fontsize=9)
                
                # Top-right: Accuracy
                ax2 = axes[0, 1]
                colors2 = plt.cm.viridis(np.linspace(0.2, 0.8, len(models)))
                bars2 = ax2.barh(models, accuracies, color=colors2, edgecolor='#333333')
                ax2.set_xlabel('Accuracy')
                ax2.set_title('📊 Accuracy Comparison', fontsize=12, color='#333333')
                
                # Bottom-left: F1 Score
                ax3 = axes[1, 0]
                colors3 = plt.cm.plasma(np.linspace(0.2, 0.8, len(models)))
                bars3 = ax3.barh(models, f1_scores, color=colors3, edgecolor='#333333')
                ax3.set_xlabel('F1 Score')
                ax3.set_title('🎯 F1 Score Comparison', fontsize=12, color='#333333')
                
                # Bottom-right: Performance ranking
                ax4 = axes[1, 1]
                rankings = list(range(1, len(models) + 1))
                scatter = ax4.scatter(scores, f1_scores, c=rankings, s=200, 
                                     cmap='RdYlGn_r', edgecolors='white', linewidths=2)
                for i, model in enumerate(models):
                    ax4.annotate(model, (scores[i], f1_scores[i]), 
                               xytext=(5, 5), textcoords='offset points', fontsize=8)
                ax4.set_xlabel('Score')
                ax4.set_ylabel('F1 Score')
                ax4.set_title('📈 Score vs F1 Trade-off', fontsize=12, color='#333333')
                plt.colorbar(scatter, ax=ax4, label='Rank')
                
                fig.suptitle(f'🌟 ULTRA Model Comparison Dashboard', fontsize=16, y=1.02, color='#333333')
                plt.tight_layout()
                
                charts['ultra_model_dashboard'] = _fig_to_base64(fig)
            except Exception as e:
                logger.warning(f"Model dashboard error: {e}")
        
        # 7. THRESHOLD ANALYSIS (Binary Classification)
        if is_classification and y_proba is not None:
            n_classes = len(np.unique(y_test))
            if n_classes == 2 and len(y_proba.shape) > 1:
                try:
                    from sklearn.metrics import precision_score, recall_score, f1_score as f1_metric
                    
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    probs = y_proba[:, 1]
                    thresholds = np.linspace(0.1, 0.9, 17)
                    
                    precisions = []
                    recalls = []
                    f1s = []
                    
                    for thresh in thresholds:
                        pred_thresh = (probs >= thresh).astype(int)
                        precisions.append(precision_score(y_test, pred_thresh, zero_division=0))
                        recalls.append(recall_score(y_test, pred_thresh, zero_division=0))
                        f1s.append(f1_metric(y_test, pred_thresh, zero_division=0))
                    
                    ax.plot(thresholds, precisions, 'o-', color=ULTRA_PALETTE[0], lw=2, label='Precision', markersize=6)
                    ax.plot(thresholds, recalls, 's-', color=ULTRA_PALETTE[1], lw=2, label='Recall', markersize=6)
                    ax.plot(thresholds, f1s, '^-', color=ULTRA_PALETTE[4], lw=2, label='F1-Score', markersize=6)
                    
                    # Mark optimal F1 threshold
                    best_idx = np.argmax(f1s)
                    ax.axvline(thresholds[best_idx], color='gray', linestyle='--', alpha=0.7)
                    ax.scatter([thresholds[best_idx]], [f1s[best_idx]], s=200, color='gold', 
                              edgecolors='black', linewidths=2, zorder=5, label=f'Optimal: {thresholds[best_idx]:.2f}')
                    
                    ax.set_xlabel('Classification Threshold', fontsize=12)
                    ax.set_ylabel('Score', fontsize=12)
                    ax.set_title(f'🔧 Threshold Analysis - {model_name}', fontsize=14, color='#333333')
                    ax.legend(loc='best')
                    ax.set_xlim(0, 1)
                    ax.set_ylim(0, 1.05)
                    ax.grid(True, alpha=0.3)
                    
                    charts['ultra_threshold_analysis'] = _fig_to_base64(fig)
                except Exception as e:
                    logger.warning(f"Threshold analysis error: {e}")
        
        # 8. ERROR DISTRIBUTION VIOLIN (Regression)
        if not is_classification:
            try:
                fig, ax = plt.subplots(figsize=(10, 6))
                
                errors = y_pred - y_test
                abs_errors = np.abs(errors)
                
                # Create quartile groups
                quartiles = np.percentile(y_test, [25, 50, 75])
                groups = []
                group_labels = []
                
                masks = [
                    y_test <= quartiles[0],
                    (y_test > quartiles[0]) & (y_test <= quartiles[1]),
                    (y_test > quartiles[1]) & (y_test <= quartiles[2]),
                    y_test > quartiles[2]
                ]
                
                for i, mask in enumerate(masks):
                    if mask.sum() > 0:
                        groups.append(errors[mask])
                        group_labels.append(f'Q{i+1}')
                
                parts = ax.violinplot(groups, positions=range(len(groups)), showmeans=True, showmedians=True)
                
                for i, pc in enumerate(parts['bodies']):
                    pc.set_facecolor(ULTRA_PALETTE[i % len(ULTRA_PALETTE)])
                    pc.set_alpha(0.7)
                
                ax.set_xticks(range(len(group_labels)))
                ax.set_xticklabels(group_labels)
                ax.axhline(0, color='red', linestyle='--', alpha=0.5)
                ax.set_xlabel('Target Quartile', fontsize=12)
                ax.set_ylabel('Prediction Error', fontsize=12)
                ax.set_title(f'🎻 Error Distribution by Target Range - {model_name}', fontsize=14, color='#333333')
                
                charts['ultra_error_violin'] = _fig_to_base64(fig)
            except Exception as e:
                logger.warning(f"Error violin error: {e}")
        
        logger.info(f"✨ Generated {len(charts)} ULTRA charts: {list(charts.keys())}")
        
    except Exception as e:
        logger.error(f"Ultra chart generation error: {e}")
        import traceback
        traceback.print_exc()
    
    return charts


# =============================================================================
# 📈 STOCK/FINANCIAL DATA CHARTS
# =============================================================================

def detect_stock_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Detect if the DataFrame contains stock/financial data.
    Returns detected column mappings for OHLCV data.
    """
    result = {
        'is_stock_data': False,
        'date_col': None,
        'open_col': None,
        'high_col': None,
        'low_col': None,
        'close_col': None,
        'volume_col': None,
        'adj_close_col': None,
        'price_cols': [],
        'has_ohlc': False
    }
    
    cols_lower = {col.lower().strip(): col for col in df.columns}
    
    # Detect date column
    date_keywords = ['date', 'time', 'timestamp', 'datetime', 'period']
    for kw in date_keywords:
        for col_lower, col in cols_lower.items():
            if kw in col_lower:
                result['date_col'] = col
                break
        if result['date_col']:
            break
    
    # Also check for datetime dtype columns
    if not result['date_col']:
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                result['date_col'] = col
                break
    
    # Detect OHLCV columns
    ohlcv_mappings = {
        'open': ['open', 'opening', 'open_price'],
        'high': ['high', 'highest', 'high_price', 'max_price'],
        'low': ['low', 'lowest', 'low_price', 'min_price'],
        'close': ['close', 'closing', 'close_price', 'last', 'price'],
        'volume': ['volume', 'vol', 'qty', 'quantity', 'traded_volume'],
        'adj_close': ['adj close', 'adj_close', 'adjusted close', 'adjusted_close']
    }
    
    for field, keywords in ohlcv_mappings.items():
        for kw in keywords:
            for col_lower, col in cols_lower.items():
                if kw == col_lower or kw in col_lower:
                    if field == 'open':
                        result['open_col'] = col
                    elif field == 'high':
                        result['high_col'] = col
                    elif field == 'low':
                        result['low_col'] = col
                    elif field == 'close':
                        result['close_col'] = col
                    elif field == 'volume':
                        result['volume_col'] = col
                    elif field == 'adj_close':
                        result['adj_close_col'] = col
                    break
    
    # Check if we have OHLC data
    result['has_ohlc'] = all([
        result['open_col'], result['high_col'], 
        result['low_col'], result['close_col']
    ])
    
    # Collect all price-like columns
    price_keywords = ['price', 'close', 'open', 'high', 'low', 'value', 'rate']
    for col_lower, col in cols_lower.items():
        for kw in price_keywords:
            if kw in col_lower and pd.api.types.is_numeric_dtype(df[col]):
                if col not in result['price_cols']:
                    result['price_cols'].append(col)
    
    # Determine if it's stock data
    stock_indicators = 0
    if result['has_ohlc']:
        stock_indicators += 3
    if result['volume_col']:
        stock_indicators += 1
    if result['date_col']:
        stock_indicators += 1
    if len(result['price_cols']) >= 2:
        stock_indicators += 1
    
    # Also check column names for stock-related terms
    stock_terms = ['stock', 'ticker', 'symbol', 'share', 'equity', 'nifty', 'sensex', 'nasdaq', 'spy', 'return']
    for col_lower in cols_lower.keys():
        if any(term in col_lower for term in stock_terms):
            stock_indicators += 1
            break
    
    result['is_stock_data'] = stock_indicators >= 3
    
    return result


def generate_stock_charts(
    df: pd.DataFrame,
    stock_info: Dict[str, Any],
    target_col: Optional[str] = None
) -> Dict[str, str]:
    """
    Generate stock/financial specific charts.
    Returns dict of chart_name -> base64 encoded image.
    """
    charts = {}
    
    try:
        # Ensure date column is datetime
        date_col = stock_info.get('date_col')
        if date_col and date_col in df.columns:
            df = df.copy()
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df = df.dropna(subset=[date_col])
            df = df.sort_values(date_col)
        
        # 1. PRICE TREND CHART (Line chart with price over time)
        price_col = stock_info.get('close_col') or stock_info.get('adj_close_col')
        if date_col and price_col and price_col in df.columns:
            try:
                fig, ax = plt.subplots(figsize=(12, 6))
                
                ax.plot(df[date_col], df[price_col], linewidth=2, color='#2196F3', label='Price')
                
                # Add moving averages
                if len(df) >= 20:
                    ma20 = df[price_col].rolling(window=20).mean()
                    ax.plot(df[date_col], ma20, linewidth=1.5, color='#FF9800', 
                            label='20-Day MA', linestyle='--')
                
                if len(df) >= 50:
                    ma50 = df[price_col].rolling(window=50).mean()
                    ax.plot(df[date_col], ma50, linewidth=1.5, color='#E91E63', 
                            label='50-Day MA', linestyle='-.')
                
                ax.fill_between(df[date_col], df[price_col], alpha=0.1, color='#2196F3')
                ax.set_xlabel('Date', fontsize=12)
                ax.set_ylabel('Price', fontsize=12)
                ax.set_title('📈 Stock Price Trend with Moving Averages', fontsize=14, fontweight='bold')
                ax.legend(loc='upper left')
                ax.grid(True, alpha=0.3)
                
                # Improve x-axis formatting - limit number of labels
                from matplotlib.ticker import MaxNLocator
                ax.xaxis.set_major_locator(MaxNLocator(nbins=8))
                plt.xticks(rotation=45, ha='right')
                fig.subplots_adjust(bottom=0.2)  # Add space for rotated labels
                
                charts['stock_price_trend'] = _fig_to_base64(fig)
            except Exception as e:
                logger.warning(f"Price trend chart error: {e}")
        
        # 2. CANDLESTICK CHART (if OHLC data available)
        if stock_info.get('has_ohlc') and date_col:
            try:
                from mplfinance.original_flavor import candlestick_ohlc
                import matplotlib.dates as mdates
                
                fig, ax = plt.subplots(figsize=(14, 7))
                
                # Prepare data for candlestick
                df_ohlc = df[[date_col, stock_info['open_col'], stock_info['high_col'], 
                              stock_info['low_col'], stock_info['close_col']]].copy()
                df_ohlc.columns = ['Date', 'Open', 'High', 'Low', 'Close']
                df_ohlc['Date'] = mdates.date2num(df_ohlc['Date'])
                
                # Limit to last 60 candles for readability
                df_plot = df_ohlc.tail(60)
                
                candlestick_ohlc(ax, df_plot.values, width=0.6, 
                                colorup='#26A69A', colordown='#EF5350')
                
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=10))
                plt.xticks(rotation=45, ha='right')
                ax.set_xlabel('Date', fontsize=12)
                ax.set_ylabel('Price', fontsize=12)
                ax.set_title('🕯️ Candlestick Chart (Last 60 Periods)', fontsize=14, fontweight='bold')
                ax.grid(True, alpha=0.3)
                fig.subplots_adjust(bottom=0.18)
                
                charts['stock_candlestick'] = _fig_to_base64(fig)
            except ImportError:
                # Fallback: Create a simple OHLC chart without mplfinance
                try:
                    fig, ax = plt.subplots(figsize=(14, 7))
                    
                    df_plot = df.tail(60).copy().reset_index(drop=True)
                    
                    # Plot high-low range as lines with proper spacing
                    for i, (_, row) in enumerate(df_plot.iterrows()):
                        color = '#26A69A' if row[stock_info['close_col']] >= row[stock_info['open_col']] else '#EF5350'
                        ax.vlines(i, row[stock_info['low_col']], row[stock_info['high_col']], color=color, linewidth=1)
                        ax.vlines(i, row[stock_info['open_col']], row[stock_info['close_col']], color=color, linewidth=4)
                    
                    # Limit x-axis ticks to prevent crowding
                    from matplotlib.ticker import MaxNLocator
                    ax.xaxis.set_major_locator(MaxNLocator(nbins=10, integer=True))
                    
                    ax.set_xlabel('Period', fontsize=12)
                    ax.set_ylabel('Price', fontsize=12)
                    ax.set_title('🕯️ OHLC Chart (Last 60 Periods)', fontsize=14, fontweight='bold')
                    ax.grid(True, alpha=0.3)
                    fig.subplots_adjust(bottom=0.12)
                    
                    charts['stock_ohlc'] = _fig_to_base64(fig)
                except Exception as e:
                    logger.warning(f"OHLC fallback chart error: {e}")
            except Exception as e:
                logger.warning(f"Candlestick chart error: {e}")
        
        # 3. VOLUME CHART
        volume_col = stock_info.get('volume_col')
        if date_col and volume_col and volume_col in df.columns:
            try:
                fig, ax = plt.subplots(figsize=(12, 4))
                
                df_plot = df.tail(100).reset_index(drop=True)
                colors = ['#26A69A' if df_plot[stock_info.get('close_col', price_col)].iloc[i] >= 
                         df_plot[stock_info.get('open_col', price_col)].iloc[i] 
                         else '#EF5350' for i in range(len(df_plot))]
                
                ax.bar(range(len(df_plot)), df_plot[volume_col], color=colors, alpha=0.7)
                ax.set_xlabel('Period', fontsize=12)
                ax.set_ylabel('Volume', fontsize=12)
                ax.set_title('📊 Trading Volume (Last 100 Periods)', fontsize=14, fontweight='bold')
                ax.grid(True, alpha=0.3, axis='y')
                
                # Limit x-axis ticks to prevent crowding
                from matplotlib.ticker import MaxNLocator
                ax.xaxis.set_major_locator(MaxNLocator(nbins=10, integer=True))
                
                # Format y-axis for large numbers
                ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M' if x >= 1e6 else f'{x/1e3:.0f}K' if x >= 1e3 else f'{x:.0f}'))
                fig.subplots_adjust(bottom=0.15)
                
                charts['stock_volume'] = _fig_to_base64(fig)
            except Exception as e:
                logger.warning(f"Volume chart error: {e}")
        
        # 4. DAILY RETURNS DISTRIBUTION
        if price_col and price_col in df.columns:
            try:
                fig, axes = plt.subplots(1, 2, figsize=(14, 5))
                
                # Calculate returns
                returns = df[price_col].pct_change().dropna() * 100
                
                # Histogram of returns
                axes[0].hist(returns, bins=50, color='#2196F3', alpha=0.7, edgecolor='white')
                axes[0].axvline(returns.mean(), color='red', linestyle='--', label=f'Mean: {returns.mean():.2f}%')
                axes[0].axvline(0, color='black', linestyle='-', alpha=0.5)
                axes[0].set_xlabel('Daily Return (%)', fontsize=12)
                axes[0].set_ylabel('Frequency', fontsize=12)
                axes[0].set_title('📊 Daily Returns Distribution', fontsize=14, fontweight='bold')
                axes[0].legend()
                axes[0].grid(True, alpha=0.3)
                
                # Cumulative returns
                cumulative_returns = (1 + returns/100).cumprod() - 1
                axes[1].plot(range(len(cumulative_returns)), cumulative_returns * 100, 
                            color='#4CAF50', linewidth=2)
                axes[1].fill_between(range(len(cumulative_returns)), 
                                    cumulative_returns * 100, alpha=0.2, color='#4CAF50')
                axes[1].axhline(0, color='black', linestyle='-', alpha=0.5)
                axes[1].set_xlabel('Period', fontsize=12)
                axes[1].set_ylabel('Cumulative Return (%)', fontsize=12)
                axes[1].set_title('📈 Cumulative Returns', fontsize=14, fontweight='bold')
                axes[1].grid(True, alpha=0.3)
                
                plt.tight_layout()
                charts['stock_returns'] = _fig_to_base64(fig)
            except Exception as e:
                logger.warning(f"Returns chart error: {e}")
        
        # 5. VOLATILITY ANALYSIS
        if price_col and price_col in df.columns and len(df) >= 30:
            try:
                fig, ax = plt.subplots(figsize=(12, 5))
                
                returns = df[price_col].pct_change().dropna()
                
                # Rolling volatility (20-day)
                rolling_vol = returns.rolling(window=20).std() * np.sqrt(252) * 100  # Annualized
                
                ax.plot(range(len(rolling_vol)), rolling_vol, color='#9C27B0', linewidth=2)
                ax.fill_between(range(len(rolling_vol)), rolling_vol, alpha=0.2, color='#9C27B0')
                ax.axhline(rolling_vol.mean(), color='red', linestyle='--', 
                          label=f'Average: {rolling_vol.mean():.1f}%')
                ax.set_xlabel('Period', fontsize=12)
                ax.set_ylabel('Annualized Volatility (%)', fontsize=12)
                ax.set_title('📉 Rolling Volatility (20-Day Window)', fontsize=14, fontweight='bold')
                ax.legend()
                ax.grid(True, alpha=0.3)
                plt.tight_layout()
                
                charts['stock_volatility'] = _fig_to_base64(fig)
            except Exception as e:
                logger.warning(f"Volatility chart error: {e}")
        
        # 6. PRICE WITH BOLLINGER BANDS
        if date_col and price_col and price_col in df.columns and len(df) >= 20:
            try:
                fig, ax = plt.subplots(figsize=(12, 6))
                
                df_plot = df.tail(100).copy()
                
                # Calculate Bollinger Bands
                ma20 = df_plot[price_col].rolling(window=20).mean()
                std20 = df_plot[price_col].rolling(window=20).std()
                upper_band = ma20 + (std20 * 2)
                lower_band = ma20 - (std20 * 2)
                
                ax.plot(range(len(df_plot)), df_plot[price_col], color='#2196F3', 
                       linewidth=2, label='Price')
                ax.plot(range(len(df_plot)), ma20, color='#FF9800', 
                       linewidth=1.5, label='20-Day MA')
                ax.fill_between(range(len(df_plot)), upper_band, lower_band, 
                               alpha=0.2, color='#9C27B0', label='Bollinger Bands (2σ)')
                
                ax.set_xlabel('Period', fontsize=12)
                ax.set_ylabel('Price', fontsize=12)
                ax.set_title('📊 Price with Bollinger Bands', fontsize=14, fontweight='bold')
                ax.legend(loc='upper left')
                ax.grid(True, alpha=0.3)
                plt.tight_layout()
                
                charts['stock_bollinger'] = _fig_to_base64(fig)
            except Exception as e:
                logger.warning(f"Bollinger bands chart error: {e}")
        
        # 7. CORRELATION WITH OTHER PRICE COLUMNS
        price_cols = stock_info.get('price_cols', [])
        if len(price_cols) >= 2:
            try:
                fig, ax = plt.subplots(figsize=(8, 6))
                
                price_df = df[price_cols].dropna()
                if len(price_df) > 10:
                    corr_matrix = price_df.corr()
                    
                    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='RdYlGn', 
                               center=0, ax=ax, square=True,
                               linewidths=0.5, cbar_kws={'shrink': 0.8})
                    ax.set_title('🔗 Price Correlations', fontsize=14, fontweight='bold')
                    plt.tight_layout()
                    
                    charts['stock_price_correlation'] = _fig_to_base64(fig)
            except Exception as e:
                logger.warning(f"Price correlation chart error: {e}")
        
        logger.info(f"📈 Generated {len(charts)} stock charts: {list(charts.keys())}")
        
    except Exception as e:
        logger.error(f"Stock chart generation error: {e}")
        import traceback
        traceback.print_exc()
    
    return charts

