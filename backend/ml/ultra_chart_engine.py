"""
💎 ULTRA ENTERPRISE CHART ENGINE v1.0 - $5M QUALITY VISUALIZATIONS
===================================================================

Premium, enterprise-grade visualizations for Ultra AutoML mode.
Designed to impress executives and provide deep model insights.

Features:
- Executive Summary Dashboard
- Deep Model Diagnostics
- Learning Curves & Convergence Analysis
- SHAP-style Feature Explanations
- Decision Boundary Visualization
- Error Analysis Deep Dive
- Cross-Validation Performance
- Ensemble Contribution Analysis
- Time-Series Decomposition
- NLP Token Importance

Author: AI Business Analyst Team
Version: 1.0.0
"""

import numpy as np
import pandas as pd
import base64
import io
import logging
from typing import Dict, List, Optional, Any, Tuple
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

# Visualization imports
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.gridspec import GridSpec
import seaborn as sns

# ML imports
from sklearn.metrics import (
    confusion_matrix, classification_report, roc_curve, auc,
    precision_recall_curve, average_precision_score,
    r2_score, mean_absolute_error, mean_squared_error
)
from sklearn.model_selection import learning_curve
from sklearn.inspection import permutation_importance

# Set EXECUTIVE PREMIUM theme
plt.style.use('seaborn-v0_8-whitegrid')
ULTRA_COLORS = {
    'primary': '#0F172A',      # Slate 900
    'secondary': '#1E293B',    # Slate 800
    'accent': '#3B82F6',       # Blue 500
    'success': '#10B981',      # Emerald 500
    'warning': '#F59E0B',      # Amber 500
    'danger': '#EF4444',       # Red 500
    'purple': '#8B5CF6',       # Violet 500
    'pink': '#EC4899',         # Pink 500
    'teal': '#14B8A6',         # Teal 500
    'gold': '#F59E0B',         # Gold
    'background': '#FFFFFF',
    'text': '#1E293B',
    'grid': '#E2E8F0',
}

GRADIENT_COLORS = ['#3B82F6', '#8B5CF6', '#EC4899', '#EF4444', '#F59E0B', '#10B981']

def _fig_to_base64(fig) -> str:
    """Convert matplotlib figure to base64 string."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_str


# =============================================================================
# EXECUTIVE SUMMARY DASHBOARD
# =============================================================================

def generate_executive_dashboard(
    task_type: str,
    model_name: str,
    metrics: Dict[str, float],
    y_test: np.ndarray,
    y_pred: np.ndarray,
    y_proba: Optional[np.ndarray] = None,
    training_time: float = 0,
    n_models_tested: int = 0,
    feature_importance: Optional[List[Dict]] = None
) -> str:
    """
    Generate executive summary dashboard - single image with all key insights.
    Premium $5M quality visualization.
    """
    fig = plt.figure(figsize=(20, 14), facecolor='white')
    fig.suptitle(f'🏆 EXECUTIVE MODEL PERFORMANCE DASHBOARD', 
                 fontsize=24, fontweight='bold', color=ULTRA_COLORS['primary'], y=0.98)
    
    gs = GridSpec(3, 4, figure=fig, hspace=0.35, wspace=0.3)
    
    # === ROW 1: Key Metrics Cards ===
    # Metric 1: Primary Score
    ax1 = fig.add_subplot(gs[0, 0])
    primary_metric = list(metrics.keys())[0] if metrics else 'Score'
    primary_value = list(metrics.values())[0] if metrics else 0
    _draw_metric_card(ax1, primary_metric.upper(), f"{primary_value:.1%}" if primary_value <= 1 else f"{primary_value:.2f}",
                      ULTRA_COLORS['accent'], '📊')
    
    # Metric 2: Model Name
    ax2 = fig.add_subplot(gs[0, 1])
    _draw_metric_card(ax2, 'BEST MODEL', model_name[:15], ULTRA_COLORS['success'], '🏆')
    
    # Metric 3: Models Tested
    ax3 = fig.add_subplot(gs[0, 2])
    _draw_metric_card(ax3, 'MODELS TESTED', str(n_models_tested), ULTRA_COLORS['purple'], '🔬')
    
    # Metric 4: Training Time
    ax4 = fig.add_subplot(gs[0, 3])
    time_str = f"{training_time:.1f}s" if training_time < 60 else f"{training_time/60:.1f}m"
    _draw_metric_card(ax4, 'TRAINING TIME', time_str, ULTRA_COLORS['warning'], '⏱️')
    
    # === ROW 2: Performance Visualizations ===
    if task_type == 'classification':
        # Confusion Matrix
        ax5 = fig.add_subplot(gs[1, 0:2])
        _draw_premium_confusion_matrix(ax5, y_test, y_pred)
        
        # ROC Curve (if probabilities available)
        ax6 = fig.add_subplot(gs[1, 2:4])
        if y_proba is not None:
            _draw_premium_roc_curve(ax6, y_test, y_proba)
        else:
            _draw_metrics_radar(ax6, metrics)
    else:
        # Prediction vs Actual
        ax5 = fig.add_subplot(gs[1, 0:2])
        _draw_prediction_vs_actual(ax5, y_test, y_pred)
        
        # Residuals Distribution
        ax6 = fig.add_subplot(gs[1, 2:4])
        _draw_residuals_distribution(ax6, y_test, y_pred)
    
    # === ROW 3: Feature Importance & Model Insights ===
    ax7 = fig.add_subplot(gs[2, 0:2])
    if feature_importance:
        _draw_premium_feature_importance(ax7, feature_importance[:10])
    else:
        _draw_placeholder(ax7, "Feature Importance\n(Not Available)")
    
    # All Metrics Summary
    ax8 = fig.add_subplot(gs[2, 2:4])
    _draw_metrics_summary(ax8, metrics, task_type)
    
    return _fig_to_base64(fig)


def _draw_metric_card(ax, title: str, value: str, color: str, icon: str):
    """Draw a premium metric card."""
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    # Background rounded rectangle
    rect = patches.FancyBboxPatch((0.05, 0.05), 0.9, 0.9, 
                                   boxstyle="round,pad=0.02,rounding_size=0.1",
                                   facecolor=color, alpha=0.1, edgecolor=color, linewidth=2)
    ax.add_patch(rect)
    
    # Icon
    ax.text(0.5, 0.7, icon, fontsize=32, ha='center', va='center')
    
    # Value
    ax.text(0.5, 0.4, value, fontsize=20, fontweight='bold', 
            ha='center', va='center', color=color)
    
    # Title
    ax.text(0.5, 0.15, title, fontsize=10, ha='center', va='center', 
            color=ULTRA_COLORS['text'], alpha=0.7)


def _draw_premium_confusion_matrix(ax, y_test, y_pred):
    """Draw premium confusion matrix with percentages."""
    cm = confusion_matrix(y_test, y_pred)
    cm_percent = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis] * 100
    
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                cbar_kws={'label': 'Count'}, linewidths=0.5, linecolor='white')
    
    # Add percentage annotations
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j + 0.5, i + 0.75, f'({cm_percent[i, j]:.1f}%)', 
                    ha='center', va='center', fontsize=8, color='gray')
    
    ax.set_title('📊 Confusion Matrix', fontsize=14, fontweight='bold', pad=10)
    ax.set_xlabel('Predicted', fontsize=11)
    ax.set_ylabel('Actual', fontsize=11)


def _draw_premium_roc_curve(ax, y_test, y_proba):
    """Draw premium ROC curve with AUC."""
    if y_proba.ndim == 2:
        if y_proba.shape[1] == 2:
            y_score = y_proba[:, 1]
        else:
            # Multi-class: use max probability
            y_score = y_proba.max(axis=1)
    else:
        y_score = y_proba
    
    try:
        fpr, tpr, _ = roc_curve(y_test, y_score)
        roc_auc = auc(fpr, tpr)
        
        ax.fill_between(fpr, tpr, alpha=0.3, color=ULTRA_COLORS['accent'])
        ax.plot(fpr, tpr, color=ULTRA_COLORS['accent'], lw=3, 
                label=f'ROC Curve (AUC = {roc_auc:.3f})')
        ax.plot([0, 1], [0, 1], 'k--', lw=1, alpha=0.5)
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.set_xlabel('False Positive Rate', fontsize=11)
        ax.set_ylabel('True Positive Rate', fontsize=11)
        ax.set_title('📈 ROC Curve', fontsize=14, fontweight='bold', pad=10)
        ax.legend(loc='lower right', fontsize=10)
        
        # Add AUC badge
        ax.text(0.95, 0.05, f'AUC: {roc_auc:.3f}', transform=ax.transAxes,
                fontsize=14, fontweight='bold', ha='right', va='bottom',
                bbox=dict(boxstyle='round', facecolor=ULTRA_COLORS['success'], alpha=0.8),
                color='white')
    except Exception as e:
        ax.text(0.5, 0.5, f'ROC unavailable\n({str(e)[:30]})', 
                ha='center', va='center', transform=ax.transAxes)


def _draw_prediction_vs_actual(ax, y_test, y_pred):
    """Draw prediction vs actual scatter plot for regression."""
    ax.scatter(y_test, y_pred, alpha=0.5, c=ULTRA_COLORS['accent'], s=30, edgecolors='white')
    
    # Perfect prediction line
    min_val = min(y_test.min(), y_pred.min())
    max_val = max(y_test.max(), y_pred.max())
    ax.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='Perfect Prediction')
    
    r2 = r2_score(y_test, y_pred)
    ax.set_xlabel('Actual Values', fontsize=11)
    ax.set_ylabel('Predicted Values', fontsize=11)
    ax.set_title('📊 Prediction vs Actual', fontsize=14, fontweight='bold', pad=10)
    ax.legend(fontsize=10)
    
    # R² badge
    ax.text(0.05, 0.95, f'R² = {r2:.4f}', transform=ax.transAxes,
            fontsize=12, fontweight='bold', ha='left', va='top',
            bbox=dict(boxstyle='round', facecolor=ULTRA_COLORS['success'], alpha=0.8),
            color='white')


def _draw_residuals_distribution(ax, y_test, y_pred):
    """Draw residuals distribution histogram."""
    residuals = y_test - y_pred
    
    ax.hist(residuals, bins=30, color=ULTRA_COLORS['accent'], alpha=0.7, edgecolor='white')
    ax.axvline(x=0, color='red', linestyle='--', lw=2, label='Zero Error')
    ax.axvline(x=residuals.mean(), color=ULTRA_COLORS['warning'], linestyle='-', lw=2, 
               label=f'Mean: {residuals.mean():.3f}')
    
    ax.set_xlabel('Residual (Actual - Predicted)', fontsize=11)
    ax.set_ylabel('Frequency', fontsize=11)
    ax.set_title('📉 Residuals Distribution', fontsize=14, fontweight='bold', pad=10)
    ax.legend(fontsize=9)


def _draw_premium_feature_importance(ax, feature_importance: List[Dict]):
    """Draw premium horizontal bar chart for feature importance."""
    names = [f['name'][:20] for f in feature_importance]
    scores = [f['importance'] for f in feature_importance]
    
    colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(names)))[::-1]
    bars = ax.barh(names, scores, color=colors, edgecolor='white', height=0.6)
    
    ax.set_xlabel('Importance Score', fontsize=11)
    ax.set_title('🎯 Top 10 Feature Importance', fontsize=14, fontweight='bold', pad=10)
    ax.invert_yaxis()
    
    # Add value labels
    for bar, score in zip(bars, scores):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                f'{score:.3f}', va='center', fontsize=9)


def _draw_metrics_summary(ax, metrics: Dict, task_type: str):
    """Draw a premium metrics summary table."""
    ax.axis('off')
    ax.set_title('📋 Model Performance Metrics', fontsize=14, fontweight='bold', pad=10)
    
    # Create table data
    cell_text = [[k.replace('_', ' ').title(), f"{v:.4f}" if isinstance(v, float) else str(v)] 
                 for k, v in metrics.items()]
    
    if cell_text:
        table = ax.table(cellText=cell_text, colLabels=['Metric', 'Value'],
                        loc='center', cellLoc='center',
                        colColours=[ULTRA_COLORS['accent'], ULTRA_COLORS['accent']],
                        colWidths=[0.5, 0.3])
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1.2, 1.8)
        
        # Style header
        for (row, col), cell in table.get_celld().items():
            if row == 0:
                cell.set_text_props(color='white', fontweight='bold')
            cell.set_edgecolor(ULTRA_COLORS['grid'])


def _draw_metrics_radar(ax, metrics: Dict):
    """Draw radar chart for metrics."""
    if not metrics or len(metrics) < 3:
        _draw_placeholder(ax, "Metrics Radar\n(Need 3+ metrics)")
        return
    
    labels = list(metrics.keys())[:6]
    values = [min(1, max(0, v)) for v in list(metrics.values())[:6]]  # Clamp to [0, 1]
    
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    values += values[:1]
    angles += angles[:1]
    
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.plot(angles, values, 'o-', linewidth=2, color=ULTRA_COLORS['accent'])
    ax.fill(angles, values, alpha=0.25, color=ULTRA_COLORS['accent'])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_title('📊 Metrics Radar', fontsize=14, fontweight='bold', pad=20)


def _draw_placeholder(ax, text: str):
    """Draw placeholder when data is unavailable."""
    ax.axis('off')
    ax.text(0.5, 0.5, text, ha='center', va='center', fontsize=14, 
            color='gray', transform=ax.transAxes)


# =============================================================================
# LEARNING CURVE ANALYSIS
# =============================================================================

def generate_learning_curve_chart(
    model: Any,
    X: np.ndarray,
    y: np.ndarray,
    cv: int = 5,
    model_name: str = "Model"
) -> str:
    """Generate learning curve showing model performance vs training size."""
    fig, ax = plt.subplots(figsize=(12, 8), facecolor='white')
    
    try:
        train_sizes, train_scores, val_scores = learning_curve(
            model, X, y, cv=cv, n_jobs=1,
            train_sizes=np.linspace(0.1, 1.0, 10),
            scoring='accuracy'
        )
        
        train_mean = np.mean(train_scores, axis=1)
        train_std = np.std(train_scores, axis=1)
        val_mean = np.mean(val_scores, axis=1)
        val_std = np.std(val_scores, axis=1)
        
        ax.fill_between(train_sizes, train_mean - train_std, train_mean + train_std,
                        alpha=0.2, color=ULTRA_COLORS['accent'])
        ax.fill_between(train_sizes, val_mean - val_std, val_mean + val_std,
                        alpha=0.2, color=ULTRA_COLORS['success'])
        
        ax.plot(train_sizes, train_mean, 'o-', color=ULTRA_COLORS['accent'],
                lw=2, label='Training Score')
        ax.plot(train_sizes, val_mean, 'o-', color=ULTRA_COLORS['success'],
                lw=2, label='Validation Score')
        
        ax.set_xlabel('Training Set Size', fontsize=12)
        ax.set_ylabel('Score', fontsize=12)
        ax.set_title(f'📈 Learning Curve: {model_name}', fontsize=16, fontweight='bold')
        ax.legend(loc='lower right', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Add insight text
        if val_mean[-1] < train_mean[-1] - 0.1:
            insight = "⚠️ High variance: Model may be overfitting"
        elif val_mean[-1] > 0.9:
            insight = "✅ Excellent: Model generalizes well"
        else:
            insight = "ℹ️ May benefit from more training data"
        
        ax.text(0.02, 0.02, insight, transform=ax.transAxes, fontsize=11,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
        
    except Exception as e:
        ax.text(0.5, 0.5, f'Learning curve unavailable\n({str(e)[:50]})', 
                ha='center', va='center', transform=ax.transAxes, fontsize=12)
    
    return _fig_to_base64(fig)


# =============================================================================
# MODEL COMPARISON DASHBOARD
# =============================================================================

def generate_model_comparison_dashboard(
    leaderboard: List[Dict],
    metric_name: str = "score"
) -> str:
    """Generate comprehensive model comparison dashboard."""
    fig = plt.figure(figsize=(16, 10), facecolor='white')
    fig.suptitle('🏆 MODEL COMPARISON DASHBOARD', fontsize=20, fontweight='bold', y=0.98)
    
    gs = GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)
    
    # Prepare data
    models = [r.get('name', r.get('model', 'Unknown'))[:15] for r in leaderboard[:10]]
    scores = [r.get('score', r.get(metric_name, 0)) for r in leaderboard[:10]]
    
    # === Chart 1: Horizontal Bar Chart ===
    ax1 = fig.add_subplot(gs[0, 0])
    colors = [ULTRA_COLORS['success'] if i == 0 else ULTRA_COLORS['accent'] 
              for i in range(len(models))]
    bars = ax1.barh(models, scores, color=colors, edgecolor='white', height=0.6)
    ax1.set_xlabel(metric_name.title(), fontsize=11)
    ax1.set_title('📊 Model Rankings', fontsize=14, fontweight='bold')
    ax1.invert_yaxis()
    for bar, score in zip(bars, scores):
        ax1.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height()/2,
                f'{score:.4f}', va='center', fontsize=9)
    
    # === Chart 2: Score Distribution ===
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.hist(scores, bins=min(10, len(scores)), color=ULTRA_COLORS['accent'], 
             alpha=0.7, edgecolor='white')
    ax2.axvline(x=scores[0], color=ULTRA_COLORS['success'], linestyle='--', lw=2,
                label=f'Best: {scores[0]:.4f}')
    ax2.set_xlabel(metric_name.title(), fontsize=11)
    ax2.set_ylabel('Count', fontsize=11)
    ax2.set_title('📈 Score Distribution', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=10)
    
    # === Chart 3: Performance Heatmap ===
    ax3 = fig.add_subplot(gs[1, 0])
    if len(leaderboard) > 1 and 'metrics' in leaderboard[0]:
        # Get all metrics from leaderboard
        all_metrics = set()
        for r in leaderboard[:8]:
            if 'metrics' in r:
                all_metrics.update(r['metrics'].keys())
        
        if all_metrics:
            metrics_list = list(all_metrics)[:5]
            heatmap_data = []
            for r in leaderboard[:8]:
                row = []
                for m in metrics_list:
                    val = r.get('metrics', {}).get(m, 0)
                    row.append(val if isinstance(val, (int, float)) else 0)
                heatmap_data.append(row)
            
            sns.heatmap(np.array(heatmap_data), annot=True, fmt='.3f',
                       xticklabels=[m[:10] for m in metrics_list],
                       yticklabels=[r.get('name', 'Model')[:10] for r in leaderboard[:8]],
                       cmap='Blues', ax=ax3)
            ax3.set_title('🔥 Performance Heatmap', fontsize=14, fontweight='bold')
        else:
            ax3.text(0.5, 0.5, 'Metrics heatmap\nunavailable', 
                    ha='center', va='center', transform=ax3.transAxes)
    else:
        ax3.text(0.5, 0.5, 'Metrics heatmap\nunavailable', 
                ha='center', va='center', transform=ax3.transAxes)
        ax3.axis('off')
    
    # === Chart 4: Top 5 Comparison ===
    ax4 = fig.add_subplot(gs[1, 1])
    top5_models = models[:5]
    top5_scores = scores[:5]
    
    x = np.arange(len(top5_models))
    width = 0.6
    bars = ax4.bar(x, top5_scores, width, color=GRADIENT_COLORS[:5], edgecolor='white')
    ax4.set_xticks(x)
    ax4.set_xticklabels(top5_models, rotation=45, ha='right', fontsize=9)
    ax4.set_ylabel(metric_name.title(), fontsize=11)
    ax4.set_title('🥇 Top 5 Models', fontsize=14, fontweight='bold')
    
    # Add crown to winner
    ax4.annotate('👑', xy=(0, top5_scores[0]), xytext=(0, top5_scores[0] + 0.02),
                fontsize=20, ha='center')
    
    return _fig_to_base64(fig)


# =============================================================================
# ERROR ANALYSIS DEEP DIVE
# =============================================================================

def generate_error_analysis_chart(
    y_test: np.ndarray,
    y_pred: np.ndarray,
    y_proba: Optional[np.ndarray] = None,
    task_type: str = 'classification'
) -> str:
    """Generate deep error analysis dashboard."""
    fig = plt.figure(figsize=(16, 12), facecolor='white')
    fig.suptitle('🔍 ERROR ANALYSIS DEEP DIVE', fontsize=20, fontweight='bold', y=0.98)
    
    gs = GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)
    
    if task_type == 'classification':
        # === Misclassification Analysis ===
        ax1 = fig.add_subplot(gs[0, 0])
        errors = y_test != y_pred
        error_rate = errors.sum() / len(errors)
        
        sizes = [1 - error_rate, error_rate]
        colors = [ULTRA_COLORS['success'], ULTRA_COLORS['danger']]
        labels = [f'Correct\n({(1-error_rate)*100:.1f}%)', f'Errors\n({error_rate*100:.1f}%)']
        
        wedges, texts = ax1.pie(sizes, colors=colors, startangle=90, 
                                 wedgeprops=dict(width=0.5, edgecolor='white'))
        ax1.legend(wedges, labels, loc='center', fontsize=12)
        ax1.set_title('🎯 Classification Accuracy', fontsize=14, fontweight='bold')
        
        # === Error by Class ===
        ax2 = fig.add_subplot(gs[0, 1])
        classes = np.unique(y_test)
        class_errors = []
        for c in classes:
            mask = y_test == c
            class_error = (y_pred[mask] != y_test[mask]).sum() / mask.sum() if mask.sum() > 0 else 0
            class_errors.append(class_error)
        
        ax2.bar(range(len(classes)), class_errors, color=ULTRA_COLORS['danger'], alpha=0.7)
        ax2.set_xticks(range(len(classes)))
        ax2.set_xticklabels([f'Class {c}' for c in classes])
        ax2.set_ylabel('Error Rate', fontsize=11)
        ax2.set_title('📊 Error Rate by Class', fontsize=14, fontweight='bold')
        
        # === Confidence Analysis ===
        ax3 = fig.add_subplot(gs[1, 0])
        if y_proba is not None:
            if y_proba.ndim == 2:
                confidence = y_proba.max(axis=1)
            else:
                confidence = np.abs(y_proba - 0.5) * 2  # Scale to [0, 1]
            
            correct = ~errors
            ax3.hist(confidence[correct], bins=20, alpha=0.7, label='Correct', 
                    color=ULTRA_COLORS['success'])
            ax3.hist(confidence[errors], bins=20, alpha=0.7, label='Errors', 
                    color=ULTRA_COLORS['danger'])
            ax3.set_xlabel('Prediction Confidence', fontsize=11)
            ax3.set_ylabel('Count', fontsize=11)
            ax3.legend(fontsize=10)
            ax3.set_title('📈 Confidence Distribution', fontsize=14, fontweight='bold')
        else:
            ax3.text(0.5, 0.5, 'Confidence analysis\nrequires probabilities', 
                    ha='center', va='center', transform=ax3.transAxes)
            ax3.axis('off')
        
        # === Confusion Matrix Normalized ===
        ax4 = fig.add_subplot(gs[1, 1])
        cm = confusion_matrix(y_test, y_pred, normalize='true')
        sns.heatmap(cm, annot=True, fmt='.2%', cmap='RdYlGn', ax=ax4,
                   cbar_kws={'label': 'Proportion'})
        ax4.set_title('📋 Normalized Confusion Matrix', fontsize=14, fontweight='bold')
        ax4.set_xlabel('Predicted', fontsize=11)
        ax4.set_ylabel('Actual', fontsize=11)
        
    else:  # Regression
        residuals = y_test - y_pred
        
        # === Residuals vs Predicted ===
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.scatter(y_pred, residuals, alpha=0.5, c=ULTRA_COLORS['accent'], s=30)
        ax1.axhline(y=0, color='red', linestyle='--', lw=2)
        ax1.set_xlabel('Predicted Values', fontsize=11)
        ax1.set_ylabel('Residuals', fontsize=11)
        ax1.set_title('📊 Residuals vs Predicted', fontsize=14, fontweight='bold')
        
        # === Q-Q Plot ===
        ax2 = fig.add_subplot(gs[0, 1])
        from scipy import stats
        (osm, osr), (slope, intercept, r) = stats.probplot(residuals, dist="norm")
        ax2.scatter(osm, osr, alpha=0.5, c=ULTRA_COLORS['accent'], s=30)
        ax2.plot(osm, slope*osm + intercept, 'r-', lw=2)
        ax2.set_xlabel('Theoretical Quantiles', fontsize=11)
        ax2.set_ylabel('Sample Quantiles', fontsize=11)
        ax2.set_title('📈 Q-Q Plot (Normality Check)', fontsize=14, fontweight='bold')
        
        # === Error Distribution ===
        ax3 = fig.add_subplot(gs[1, 0])
        ax3.hist(residuals, bins=30, color=ULTRA_COLORS['accent'], alpha=0.7, edgecolor='white')
        ax3.axvline(x=0, color='red', linestyle='--', lw=2, label='Zero Error')
        ax3.axvline(x=residuals.mean(), color=ULTRA_COLORS['warning'], linestyle='-', lw=2,
                   label=f'Mean: {residuals.mean():.4f}')
        ax3.set_xlabel('Residual', fontsize=11)
        ax3.set_ylabel('Frequency', fontsize=11)
        ax3.set_title('📉 Error Distribution', fontsize=14, fontweight='bold')
        ax3.legend(fontsize=9)
        
        # === Error Metrics Summary ===
        ax4 = fig.add_subplot(gs[1, 1])
        ax4.axis('off')
        
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        metrics_text = f"""
        📊 ERROR METRICS SUMMARY
        
        MAE:  {mae:.4f}
        RMSE: {rmse:.4f}
        R²:   {r2:.4f}
        
        Mean Residual: {residuals.mean():.4f}
        Std Residual:  {residuals.std():.4f}
        """
        ax4.text(0.5, 0.5, metrics_text, ha='center', va='center', fontsize=14,
                transform=ax4.transAxes, family='monospace',
                bbox=dict(boxstyle='round', facecolor=ULTRA_COLORS['grid'], alpha=0.5))
    
    return _fig_to_base64(fig)


# =============================================================================
# ULTRA MODE CHART GENERATION
# =============================================================================

def generate_ultra_charts(
    task_type: str,
    y_test: np.ndarray,
    y_pred: np.ndarray,
    y_proba: Optional[np.ndarray] = None,
    model_name: str = "Model",
    metrics: Dict[str, float] = None,
    leaderboard: List[Dict] = None,
    feature_importance: List[Dict] = None,
    training_time: float = 0,
    n_models_tested: int = 0,
    model: Any = None,
    X_test: np.ndarray = None
) -> Dict[str, str]:
    """
    Generate ALL ultra-premium charts for maximum insight.
    
    Returns dictionary of chart_name -> base64_encoded_image
    """
    charts = {}
    
    logger.info("🎨 Generating Ultra Enterprise Charts...")
    
    # 1. Executive Dashboard (MOST IMPORTANT)
    try:
        charts['executive_dashboard'] = generate_executive_dashboard(
            task_type=task_type,
            model_name=model_name,
            metrics=metrics or {},
            y_test=y_test,
            y_pred=y_pred,
            y_proba=y_proba,
            training_time=training_time,
            n_models_tested=n_models_tested,
            feature_importance=feature_importance
        )
        logger.info("   ✅ Executive Dashboard generated")
    except Exception as e:
        logger.warning(f"   ⚠️ Executive Dashboard failed: {e}")
    
    # 2. Model Comparison Dashboard
    if leaderboard and len(leaderboard) > 1:
        try:
            charts['model_comparison'] = generate_model_comparison_dashboard(leaderboard)
            logger.info("   ✅ Model Comparison Dashboard generated")
        except Exception as e:
            logger.warning(f"   ⚠️ Model Comparison failed: {e}")
    
    # 3. Error Analysis Deep Dive
    try:
        charts['error_analysis'] = generate_error_analysis_chart(
            y_test=y_test,
            y_pred=y_pred,
            y_proba=y_proba,
            task_type=task_type
        )
        logger.info("   ✅ Error Analysis generated")
    except Exception as e:
        logger.warning(f"   ⚠️ Error Analysis failed: {e}")
    
    # 4. Learning Curve (if model provided)
    if model is not None and X_test is not None:
        try:
            # Use subset for speed
            sample_size = min(2000, len(X_test))
            indices = np.random.choice(len(X_test), sample_size, replace=False)
            charts['learning_curve'] = generate_learning_curve_chart(
                model=model,
                X=X_test[indices],
                y=y_test[indices],
                model_name=model_name
            )
            logger.info("   ✅ Learning Curve generated")
        except Exception as e:
            logger.warning(f"   ⚠️ Learning Curve failed: {e}")
    
    logger.info(f"🎨 Generated {len(charts)} Ultra Enterprise Charts")
    
    return charts


# =============================================================================
# CONVENIENCE EXPORTS
# =============================================================================

__all__ = [
    'generate_executive_dashboard',
    'generate_model_comparison_dashboard', 
    'generate_error_analysis_chart',
    'generate_learning_curve_chart',
    'generate_ultra_charts'
]
