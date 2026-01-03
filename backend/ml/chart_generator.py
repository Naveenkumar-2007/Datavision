"""
🧠 INTELLIGENT ML VISUALIZATION ENGINE
=======================================

Production-ready visualization pipeline that:
- Automatically analyzes dataset and ML task
- Selects only meaningful, decision-oriented charts
- Provides explanations for each visualization
- Helps users decide if ML model is reliable

Library Selection:
- Matplotlib: Static, publication-grade plots
- Seaborn: Statistical plots (KDE, violin, heatmaps)
- Uses appropriate colors based on data patterns
"""

import io
import base64
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

warnings.filterwarnings('ignore')


# =============================================================================
# VISUALIZATION DECISIONS
# =============================================================================

@dataclass
class ChartDecision:
    """Represents a decision about whether to show a chart"""
    name: str
    should_show: bool
    reason: str
    insight: str  # What decision this helps make
    warning: Optional[str] = None


# =============================================================================
# STYLING
# =============================================================================

# Professional, minimal color scheme
COLORS = {
    'primary': '#0ea5e9',      # Sky blue
    'success': '#10b981',      # Emerald
    'warning': '#f59e0b',      # Amber
    'danger': '#ef4444',       # Red
    'purple': '#8b5cf6',       # Purple
    'pink': '#ec4899',         # Pink
    'cyan': '#06b6d4',         # Cyan
    'bg': '#0f172a',           # Dark bg
    'card': '#1e293b',         # Card bg
    'text': '#f8fafc',         # Text
    'muted': '#64748b',        # Muted
    'grid': '#334155',         # Grid
}

# Distinct color palettes for different charts
PALETTE_MODELS = ['#10b981', '#0ea5e9', '#8b5cf6', '#f59e0b', '#ec4899', '#06b6d4']
PALETTE_FEATURES = ['#8b5cf6', '#a855f7', '#d946ef', '#ec4899', '#f43f5e', '#f97316']
PALETTE_COMPARISON = ['#10b981', '#3b82f6']


def setup_style():
    """Set professional dark theme"""
    plt.style.use('dark_background')
    plt.rcParams.update({
        'figure.facecolor': COLORS['card'],
        'axes.facecolor': COLORS['card'],
        'axes.edgecolor': COLORS['muted'],
        'axes.labelcolor': COLORS['text'],
        'axes.labelsize': 11,
        'axes.titlesize': 13,
        'text.color': COLORS['text'],
        'xtick.color': COLORS['muted'],
        'ytick.color': COLORS['muted'],
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'grid.color': COLORS['grid'],
        'grid.alpha': 0.3,
        'legend.fontsize': 9,
        'legend.framealpha': 0.8,
    })


def fig_to_base64(fig) -> str:
    """Convert figure to base64"""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=120, bbox_inches='tight', 
                facecolor=COLORS['card'], edgecolor='none')
    buf.seek(0)
    img = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{img}"


# =============================================================================
# VISUALIZATION INTELLIGENCE
# =============================================================================

class VisualizationIntelligence:
    """Decides which charts to show based on data + task"""
    
    def analyze_data(
        self,
        y_test: np.ndarray,
        y_pred: np.ndarray,
        y_proba: Optional[np.ndarray],
        task_type: str,
        leaderboard: List[Dict],
        feature_importance: List[Dict]
    ) -> Dict[str, ChartDecision]:
        """Analyze data and decide which visualizations add value"""
        
        decisions = {}
        
        # MODEL COMPARISON - Always show if multiple models
        if len(leaderboard) > 1:
            decisions['model_comparison'] = ChartDecision(
                name='Model Performance Comparison',
                should_show=True,
                reason=f'Comparing {len(leaderboard)} trained models',
                insight='Helps select the best model and understand performance gaps'
            )
        
        # FEATURE IMPORTANCE - Show if available
        if feature_importance and len(feature_importance) > 0:
            top_features = [f['feature'] for f in feature_importance[:3]]
            decisions['feature_importance'] = ChartDecision(
                name='Feature Importance',
                should_show=True,
                reason=f'Top features: {", ".join(top_features)}',
                insight='Identifies which features drive predictions - useful for feature selection'
            )
        
        # TASK-SPECIFIC DECISIONS
        if task_type == 'regression':
            decisions.update(self._regression_decisions(y_test, y_pred))
        else:
            decisions.update(self._classification_decisions(y_test, y_pred, y_proba))
        
        return decisions
    
    def _regression_decisions(self, y_test: np.ndarray, y_pred: np.ndarray) -> Dict[str, ChartDecision]:
        """Decide which regression charts to show"""
        decisions = {}
        
        if y_test is None or y_pred is None:
            return decisions
        
        residuals = y_test - y_pred
        
        # ACTUAL VS PREDICTED - Always show for regression
        r2 = 1 - np.sum(residuals**2) / np.sum((y_test - np.mean(y_test))**2)
        decisions['actual_vs_predicted'] = ChartDecision(
            name='Actual vs Predicted',
            should_show=True,
            reason=f'R² = {r2:.3f}',
            insight='Shows prediction accuracy - points should cluster around diagonal',
            warning='Model underperforming' if r2 < 0.7 else None
        )
        
        # RESIDUAL PLOT - Show to check for patterns
        decisions['residual_plot'] = ChartDecision(
            name='Residual Analysis',
            should_show=True,
            reason='Checking for systematic errors',
            insight='Residuals should be random with no patterns - patterns indicate model bias'
        )
        
        # ERROR DISTRIBUTION - Show to check normality
        _, p_value = stats.normaltest(residuals) if len(residuals) > 20 else (0, 1)
        decisions['error_distribution'] = ChartDecision(
            name='Error Distribution',
            should_show=True,
            reason=f'Normality p-value = {p_value:.3f}',
            insight='Errors should follow normal distribution for reliable predictions',
            warning='Non-normal errors detected' if p_value < 0.05 else None
        )
        
        # Q-Q PLOT - Show if errors may not be normal
        if p_value < 0.05:
            decisions['qq_plot'] = ChartDecision(
                name='Q-Q Plot',
                should_show=True,
                reason='Errors deviate from normality',
                insight='Helps identify if outliers or heavy tails are affecting model'
            )
        
        return decisions
    
    def _classification_decisions(
        self, 
        y_test: np.ndarray, 
        y_pred: np.ndarray,
        y_proba: Optional[np.ndarray]
    ) -> Dict[str, ChartDecision]:
        """Decide which classification charts to show"""
        decisions = {}
        
        if y_test is None or y_pred is None:
            return decisions
        
        n_classes = len(np.unique(y_test))
        is_binary = n_classes == 2
        
        # Check imbalance
        class_counts = np.bincount(y_test.astype(int))
        imbalance_ratio = min(class_counts) / max(class_counts) if max(class_counts) > 0 else 1
        is_imbalanced = imbalance_ratio < 0.3
        
        # CONFUSION MATRIX - Always show
        decisions['confusion_matrix'] = ChartDecision(
            name='Confusion Matrix',
            should_show=True,
            reason=f'{n_classes} classes detected',
            insight='Shows where model makes mistakes - which classes are confused'
        )
        
        # CLASS DISTRIBUTION - Show if imbalanced
        if is_imbalanced:
            decisions['class_distribution'] = ChartDecision(
                name='Class Distribution',
                should_show=True,
                reason=f'Imbalance ratio: {imbalance_ratio:.2f}',
                insight='Shows class balance - imbalanced data can bias predictions',
                warning='Severe class imbalance detected'
            )
        
        # ROC CURVE - Binary only
        if is_binary and y_proba is not None:
            decisions['roc_curve'] = ChartDecision(
                name='ROC Curve',
                should_show=True,
                reason='Binary classification with probabilities',
                insight='AUC shows overall discriminative ability - higher is better'
            )
        
        # PRECISION-RECALL - Imbalanced binary
        if is_binary and is_imbalanced and y_proba is not None:
            decisions['precision_recall'] = ChartDecision(
                name='Precision-Recall Curve',
                should_show=True,
                reason='Imbalanced binary classification',
                insight='Better metric than ROC for imbalanced data - focuses on positive class'
            )
        
        # PROBABILITY DISTRIBUTION - If probabilities available
        if y_proba is not None:
            decisions['probability_distribution'] = ChartDecision(
                name='Prediction Confidence',
                should_show=True,
                reason='Model outputs probabilities',
                insight='Shows model confidence - bimodal is good, uniform is concerning'
            )
        
        return decisions


# =============================================================================
# CHART GENERATORS
# =============================================================================

class ProductionChartGenerator:
    """Generates production-ready ML visualizations"""
    
    def __init__(self):
        self.intelligence = VisualizationIntelligence()
    
    def generate_all_charts(
        self,
        task_type: str,
        y_test: np.ndarray,
        y_pred: np.ndarray,
        y_proba: Optional[np.ndarray] = None,
        feature_importance: Optional[List[Dict]] = None,
        leaderboard: Optional[List[Dict]] = None,
        cv_scores: Optional[Dict[str, List[float]]] = None
    ) -> Dict[str, str]:
        """Generate all applicable charts with intelligent selection"""
        
        setup_style()
        charts = {}
        
        print(f"📊 Analyzing visualization needs for {task_type}...")
        
        # Get intelligent decisions
        decisions = self.intelligence.analyze_data(
            y_test, y_pred, y_proba, task_type, 
            leaderboard or [], feature_importance or []
        )
        
        # Show decisions
        for key, decision in decisions.items():
            if decision.should_show:
                symbol = "⚠️" if decision.warning else "✅"
                print(f"   {symbol} {decision.name}: {decision.reason}")
        
        # Generate selected charts
        if decisions.get('model_comparison', ChartDecision('', False, '', '')).should_show:
            charts['model_comparison'] = self._model_comparison(leaderboard, task_type)
        
        if decisions.get('feature_importance', ChartDecision('', False, '', '')).should_show:
            charts['feature_importance'] = self._feature_importance(feature_importance)
        
        # Task-specific charts
        if task_type == 'regression':
            if decisions.get('actual_vs_predicted', ChartDecision('', False, '', '')).should_show:
                charts['actual_vs_predicted'] = self._actual_vs_predicted(y_test, y_pred)
            
            if decisions.get('residual_plot', ChartDecision('', False, '', '')).should_show:
                charts['residual_plot'] = self._residual_plot(y_test, y_pred)
            
            if decisions.get('error_distribution', ChartDecision('', False, '', '')).should_show:
                charts['error_distribution'] = self._error_distribution(y_test, y_pred)
            
            if decisions.get('qq_plot', ChartDecision('', False, '', '')).should_show:
                charts['qq_plot'] = self._qq_plot(y_test, y_pred)
        
        else:  # Classification
            if decisions.get('confusion_matrix', ChartDecision('', False, '', '')).should_show:
                charts['confusion_matrix'] = self._confusion_matrix(y_test, y_pred)
            
            if decisions.get('class_distribution', ChartDecision('', False, '', '')).should_show:
                charts['class_distribution'] = self._class_distribution(y_test, y_pred)
            
            if decisions.get('roc_curve', ChartDecision('', False, '', '')).should_show:
                charts['roc_curve'] = self._roc_curve(y_test, y_proba)
            
            if decisions.get('precision_recall', ChartDecision('', False, '', '')).should_show:
                charts['precision_recall'] = self._precision_recall(y_test, y_proba)
            
            if decisions.get('probability_distribution', ChartDecision('', False, '', '')).should_show:
                charts['probability_distribution'] = self._probability_distribution(y_proba)
        
        # CV Stability (if available)
        if cv_scores:
            charts['cv_stability'] = self._cv_stability(cv_scores)
        
        print(f"   📈 Generated {len(charts)} decision-oriented charts")
        
        return charts
    
    # =========================================================================
    # COMMON CHARTS
    # =========================================================================
    
    def _model_comparison(self, leaderboard: List[Dict], task_type: str) -> str:
        """Leaderboard bar chart"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        names = [m['name'] for m in leaderboard[:8]]
        metric = 'r2' if task_type == 'regression' else 'f1'
        scores = [m['metrics'].get(metric, m['metrics'].get('accuracy', 0)) for m in leaderboard[:8]]
        
        # Color by performance (best = green, worst = orange)
        colors = [PALETTE_MODELS[i % len(PALETTE_MODELS)] for i in range(len(names))]
        
        bars = ax.barh(names[::-1], scores[::-1], color=colors[::-1], 
                      edgecolor='white', linewidth=0.5, height=0.7)
        
        # Value labels
        for bar, score in zip(bars, scores[::-1]):
            ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                   f'{score:.3f}', va='center', fontsize=10, fontweight='bold')
        
        ax.set_xlabel(f'{metric.upper()} Score', fontweight='bold')
        ax.set_title('Model Performance Ranking', fontweight='bold', pad=15)
        ax.set_xlim(0, max(scores) * 1.12)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Add insight text
        best = names[0]
        ax.text(0.02, -0.12, f"⭐ Best: {best} | Consider deployment readiness",
               transform=ax.transAxes, fontsize=9, color=COLORS['muted'])
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _feature_importance(self, importance: List[Dict]) -> str:
        """Feature importance with gradient colors"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        features = [f['feature'] for f in importance[:10]]
        values = [f['importance'] for f in importance[:10]]
        
        # Gradient from purple to pink
        colors = [PALETTE_FEATURES[i % len(PALETTE_FEATURES)] for i in range(len(features))]
        
        bars = ax.barh(features[::-1], values[::-1], color=colors[::-1],
                      edgecolor='white', linewidth=0.5, height=0.7)
        
        for bar, val in zip(bars, values[::-1]):
            ax.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height()/2,
                   f'{val:.1%}', va='center', fontsize=10, fontweight='bold')
        
        ax.set_xlabel('Relative Importance', fontweight='bold')
        ax.set_title('Feature Importance Analysis', fontweight='bold', pad=15)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Insight
        top3 = ', '.join(features[:3])
        ax.text(0.02, -0.12, f"🎯 Key drivers: {top3}",
               transform=ax.transAxes, fontsize=9, color=COLORS['muted'])
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    # =========================================================================
    # REGRESSION CHARTS
    # =========================================================================
    
    def _actual_vs_predicted(self, y_test: np.ndarray, y_pred: np.ndarray) -> str:
        """Actual vs Predicted with R² annotation"""
        fig, ax = plt.subplots(figsize=(9, 8))
        
        # Calculate R²
        ss_res = np.sum((y_test - y_pred)**2)
        ss_tot = np.sum((y_test - np.mean(y_test))**2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        
        # Scatter with transparency
        ax.scatter(y_test, y_pred, c=COLORS['primary'], alpha=0.4, s=25, 
                  edgecolors='white', linewidth=0.3)
        
        # Perfect prediction line
        lims = [min(y_test.min(), y_pred.min()), max(y_test.max(), y_pred.max())]
        ax.plot(lims, lims, '--', color=COLORS['success'], linewidth=2.5, 
               label='Perfect Prediction', zorder=10)
        
        ax.set_xlabel('Actual Values', fontweight='bold')
        ax.set_ylabel('Predicted Values', fontweight='bold')
        ax.set_title('Prediction Accuracy', fontweight='bold', pad=15)
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.2)
        
        # Add R² annotation
        ax.text(0.95, 0.05, f'R² = {r2:.4f}', transform=ax.transAxes,
               fontsize=14, fontweight='bold', ha='right',
               bbox=dict(boxstyle='round', facecolor=COLORS['success'], alpha=0.3))
        
        # Insight
        quality = "Excellent" if r2 > 0.95 else "Good" if r2 > 0.8 else "Fair" if r2 > 0.5 else "Poor"
        ax.text(0.02, -0.1, f"📊 Model quality: {quality} | Closer to diagonal = better",
               transform=ax.transAxes, fontsize=9, color=COLORS['muted'])
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _residual_plot(self, y_test: np.ndarray, y_pred: np.ndarray) -> str:
        """Residual analysis plot"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        residuals = y_test - y_pred
        
        # Color by sign (positive = underpredict, negative = overpredict)
        colors = np.where(residuals >= 0, COLORS['success'], COLORS['danger'])
        
        ax.scatter(y_pred, residuals, c=colors, alpha=0.5, s=20, 
                  edgecolors='white', linewidth=0.2)
        
        # Zero line
        ax.axhline(y=0, color=COLORS['primary'], linewidth=2.5, label='Zero Error')
        
        # Confidence bands (±2σ)
        std = np.std(residuals)
        ax.axhline(y=2*std, color=COLORS['warning'], linestyle='--', alpha=0.7, label=f'±2σ = ±{2*std:.1f}')
        ax.axhline(y=-2*std, color=COLORS['warning'], linestyle='--', alpha=0.7)
        
        # Fill band
        ax.fill_between([y_pred.min(), y_pred.max()], -2*std, 2*std,
                       alpha=0.1, color=COLORS['warning'])
        
        ax.set_xlabel('Predicted Values', fontweight='bold')
        ax.set_ylabel('Residuals (Actual - Predicted)', fontweight='bold')
        ax.set_title('Residual Analysis', fontweight='bold', pad=15)
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.2)
        
        # Insight
        outliers = np.sum(np.abs(residuals) > 2*std)
        ax.text(0.02, -0.1, f"⚠️ {outliers} predictions outside ±2σ | Look for patterns",
               transform=ax.transAxes, fontsize=9, color=COLORS['muted'])
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _error_distribution(self, y_test: np.ndarray, y_pred: np.ndarray) -> str:
        """Error distribution with normality check"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        errors = y_test - y_pred
        
        # Histogram
        n, bins, patches = ax.hist(errors, bins=40, density=True, alpha=0.7,
                                  color=COLORS['primary'], edgecolor='white', linewidth=0.5)
        
        # KDE overlay
        kde = stats.gaussian_kde(errors)
        x = np.linspace(errors.min(), errors.max(), 200)
        ax.plot(x, kde(x), color=COLORS['pink'], linewidth=3, label='Density')
        
        # Normal distribution overlay
        mean, std = np.mean(errors), np.std(errors)
        normal = stats.norm.pdf(x, mean, std)
        ax.plot(x, normal, '--', color=COLORS['warning'], linewidth=2, label='Normal Dist.')
        
        # Mean line
        ax.axvline(mean, color=COLORS['success'], linewidth=2, label=f'Mean = {mean:.2f}')
        
        ax.set_xlabel('Prediction Error', fontweight='bold')
        ax.set_ylabel('Density', fontweight='bold')
        ax.set_title('Error Distribution Analysis', fontweight='bold', pad=15)
        ax.legend(loc='upper right')
        
        # Normality test
        _, p_val = stats.normaltest(errors) if len(errors) > 20 else (0, 1)
        normal_label = "✅ Normal" if p_val > 0.05 else "⚠️ Non-normal"
        ax.text(0.02, -0.1, f"{normal_label} (p={p_val:.3f}) | Ideal: centered at 0, bell-shaped",
               transform=ax.transAxes, fontsize=9, color=COLORS['muted'])
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _qq_plot(self, y_test: np.ndarray, y_pred: np.ndarray) -> str:
        """Q-Q plot for residual normality"""
        fig, ax = plt.subplots(figsize=(8, 8))
        
        residuals = y_test - y_pred
        
        # Q-Q plot
        stats.probplot(residuals, dist="norm", plot=ax)
        
        # Style the plot
        ax.get_lines()[0].set_markerfacecolor(COLORS['primary'])
        ax.get_lines()[0].set_markeredgecolor('white')
        ax.get_lines()[0].set_markersize(6)
        ax.get_lines()[1].set_color(COLORS['success'])
        ax.get_lines()[1].set_linewidth(2)
        
        ax.set_title('Q-Q Plot (Normality Check)', fontweight='bold', pad=15)
        ax.grid(True, alpha=0.2)
        
        ax.text(0.02, -0.1, "📈 Points on line = normal errors | Deviations = outliers/heavy tails",
               transform=ax.transAxes, fontsize=9, color=COLORS['muted'])
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    # =========================================================================
    # CLASSIFICATION CHARTS
    # =========================================================================
    
    def _confusion_matrix(self, y_test: np.ndarray, y_pred: np.ndarray) -> str:
        """Normalized confusion matrix"""
        from sklearn.metrics import confusion_matrix, accuracy_score
        
        fig, ax = plt.subplots(figsize=(8, 7))
        
        cm = confusion_matrix(y_test, y_pred)
        cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        
        # Heatmap
        sns.heatmap(cm_normalized, annot=True, fmt='.1%', cmap='Blues', ax=ax,
                   cbar_kws={'label': 'Proportion'},
                   annot_kws={'size': 12, 'weight': 'bold'},
                   linewidths=2, linecolor=COLORS['card'])
        
        acc = accuracy_score(y_test, y_pred)
        ax.set_xlabel('Predicted Class', fontweight='bold')
        ax.set_ylabel('Actual Class', fontweight='bold')
        ax.set_title(f'Confusion Matrix (Accuracy: {acc:.1%})', fontweight='bold', pad=15)
        
        ax.text(0.02, -0.1, "🎯 Diagonal = correct | Off-diagonal = errors to investigate",
               transform=ax.transAxes, fontsize=9, color=COLORS['muted'])
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _class_distribution(self, y_test: np.ndarray, y_pred: np.ndarray) -> str:
        """Actual vs Predicted class distribution"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        classes, actual_counts = np.unique(y_test, return_counts=True)
        _, pred_counts = np.unique(y_pred, return_counts=True)
        
        # Ensure same length
        if len(pred_counts) < len(actual_counts):
            pred_counts = np.pad(pred_counts, (0, len(actual_counts) - len(pred_counts)))
        
        x = np.arange(len(classes))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, actual_counts, width, label='Actual',
                      color=COLORS['success'], edgecolor='white', linewidth=1)
        bars2 = ax.bar(x + width/2, pred_counts, width, label='Predicted',
                      color=COLORS['primary'], edgecolor='white', linewidth=1)
        
        ax.set_xlabel('Class', fontweight='bold')
        ax.set_ylabel('Count', fontweight='bold')
        ax.set_title('Class Distribution Comparison', fontweight='bold', pad=15)
        ax.set_xticks(x)
        ax.set_xticklabels([f'Class {c}' for c in classes])
        ax.legend()
        
        # Calculate imbalance
        ratio = min(actual_counts) / max(actual_counts) if max(actual_counts) > 0 else 1
        warning = "⚠️ Imbalanced" if ratio < 0.3 else "✅ Balanced"
        ax.text(0.02, -0.12, f"{warning} (ratio: {ratio:.2f}) | Similar bars = model respects class balance",
               transform=ax.transAxes, fontsize=9, color=COLORS['muted'])
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _roc_curve(self, y_test: np.ndarray, y_proba: np.ndarray) -> str:
        """ROC curve with AUC"""
        from sklearn.metrics import roc_curve, auc
        
        fig, ax = plt.subplots(figsize=(9, 8))
        
        try:
            fpr, tpr, _ = roc_curve(y_test, y_proba)
            roc_auc = auc(fpr, tpr)
            
            # Fill area
            ax.fill_between(fpr, tpr, alpha=0.3, color=COLORS['primary'])
            
            # Main curve
            ax.plot(fpr, tpr, color=COLORS['primary'], linewidth=3,
                   label=f'ROC Curve (AUC = {roc_auc:.3f})')
            
            # Random baseline
            ax.plot([0, 1], [0, 1], '--', color=COLORS['danger'], linewidth=2,
                   label='Random Classifier')
            
            ax.set_xlabel('False Positive Rate', fontweight='bold')
            ax.set_ylabel('True Positive Rate', fontweight='bold')
            ax.set_title('ROC Curve Analysis', fontweight='bold', pad=15)
            ax.legend(loc='lower right')
            ax.grid(True, alpha=0.2)
            ax.set_xlim([0, 1])
            ax.set_ylim([0, 1.02])
            
            # Quality assessment
            quality = "Excellent" if roc_auc > 0.9 else "Good" if roc_auc > 0.8 else "Fair" if roc_auc > 0.7 else "Poor"
            ax.text(0.02, -0.1, f"📊 Discriminative ability: {quality} | AUC > 0.8 is typically good",
                   transform=ax.transAxes, fontsize=9, color=COLORS['muted'])
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Could not generate ROC\n{str(e)[:40]}',
                   ha='center', va='center')
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _precision_recall(self, y_test: np.ndarray, y_proba: np.ndarray) -> str:
        """Precision-Recall curve for imbalanced data"""
        from sklearn.metrics import precision_recall_curve, average_precision_score
        
        fig, ax = plt.subplots(figsize=(9, 8))
        
        try:
            precision, recall, _ = precision_recall_curve(y_test, y_proba)
            ap = average_precision_score(y_test, y_proba)
            
            ax.fill_between(recall, precision, alpha=0.3, color=COLORS['purple'])
            ax.plot(recall, precision, color=COLORS['purple'], linewidth=3,
                   label=f'PR Curve (AP = {ap:.3f})')
            
            ax.set_xlabel('Recall', fontweight='bold')
            ax.set_ylabel('Precision', fontweight='bold')
            ax.set_title('Precision-Recall Curve', fontweight='bold', pad=15)
            ax.legend(loc='lower left')
            ax.grid(True, alpha=0.2)
            ax.set_xlim([0, 1])
            ax.set_ylim([0, 1.02])
            
            ax.text(0.02, -0.1, "📊 Better than ROC for imbalanced data | Higher curve = better",
                   transform=ax.transAxes, fontsize=9, color=COLORS['muted'])
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Could not generate PR curve', ha='center', va='center')
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _probability_distribution(self, y_proba: np.ndarray) -> str:
        """Prediction probability distribution"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        proba = y_proba.flatten() if len(y_proba.shape) > 1 else y_proba
        
        ax.hist(proba, bins=50, density=True, alpha=0.7,
               color=COLORS['cyan'], edgecolor='white', linewidth=0.5)
        
        # KDE
        if len(proba) > 10:
            kde = stats.gaussian_kde(proba)
            x = np.linspace(0, 1, 200)
            ax.plot(x, kde(x), color=COLORS['pink'], linewidth=3, label='Density')
        
        # Decision threshold
        ax.axvline(0.5, color=COLORS['danger'], linewidth=2, linestyle='--',
                  label='Decision Threshold')
        
        ax.set_xlabel('Prediction Probability', fontweight='bold')
        ax.set_ylabel('Density', fontweight='bold')
        ax.set_title('Model Confidence Distribution', fontweight='bold', pad=15)
        ax.legend()
        ax.set_xlim([0, 1])
        
        # Check if bimodal (good) or uniform (concerning)
        ax.text(0.02, -0.1, "🎯 Bimodal (peaks at 0 and 1) = confident model | Uniform = uncertain",
               transform=ax.transAxes, fontsize=9, color=COLORS['muted'])
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _cv_stability(self, cv_scores: Dict[str, List[float]]) -> str:
        """Cross-validation stability visualization"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        models = list(cv_scores.keys())
        means = [np.mean(scores) for scores in cv_scores.values()]
        stds = [np.std(scores) for scores in cv_scores.values()]
        
        x = np.arange(len(models))
        colors = [PALETTE_MODELS[i % len(PALETTE_MODELS)] for i in range(len(models))]
        
        bars = ax.bar(x, means, yerr=stds, color=colors, edgecolor='white',
                     capsize=5, error_kw={'linewidth': 2})
        
        ax.set_xlabel('Model', fontweight='bold')
        ax.set_ylabel('CV Score', fontweight='bold')
        ax.set_title('Model Stability (CV Variance)', fontweight='bold', pad=15)
        ax.set_xticks(x)
        ax.set_xticklabels(models, rotation=45, ha='right')
        
        ax.text(0.02, -0.2, "📊 Small error bars = stable model | Large bars = high variance",
               transform=ax.transAxes, fontsize=9, color=COLORS['muted'])
        
        plt.tight_layout()
        return fig_to_base64(fig)


# Global instance
chart_generator = ProductionChartGenerator()
