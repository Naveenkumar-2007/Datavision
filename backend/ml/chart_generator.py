"""
📊 ML CHART GENERATOR v3.0
===========================

THEME-AWARE Charts that work in both dark and light modes:
- Light gray background (#f8f9fa) - visible in both themes
- High contrast colors
- More chart variety
"""

import io
import base64
from typing import Dict, List, Optional
import warnings

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

warnings.filterwarnings('ignore')

# High-contrast colors visible in both themes
COLORS = {
    'blue': '#2563eb',
    'green': '#16a34a',
    'red': '#dc2626',
    'orange': '#ea580c',
    'purple': '#9333ea',
    'cyan': '#0891b2',
    'pink': '#db2777',
    'amber': '#d97706',
    'teal': '#0d9488',
    'indigo': '#4f46e5',
}

PALETTE = list(COLORS.values())

# Background that works in both themes
BG_COLOR = '#f8f9fa'  # Very light gray - visible on dark and light


def setup_theme_aware_style():
    """Style that works in both dark and light themes"""
    plt.rcParams.update({
        'figure.facecolor': BG_COLOR,
        'axes.facecolor': '#ffffff',
        'axes.edgecolor': '#d1d5db',
        'axes.labelcolor': '#1f2937',
        'axes.labelsize': 12,
        'axes.titlesize': 14,
        'axes.titleweight': 'bold',
        'text.color': '#1f2937',
        'xtick.color': '#4b5563',
        'ytick.color': '#4b5563',
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'grid.color': '#e5e7eb',
        'grid.alpha': 0.7,
        'grid.linewidth': 0.8,
        'legend.fontsize': 10,
        'legend.framealpha': 1,
        'legend.edgecolor': '#d1d5db',
        'legend.facecolor': '#ffffff',
        'font.family': 'sans-serif',
    })


def fig_to_base64(fig) -> str:
    """Convert figure to base64"""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=BG_COLOR, edgecolor='none')
    buf.seek(0)
    img = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{img}"


class MLChartGenerator:
    """Theme-aware ML chart generator with extensive chart variety"""
    
    def generate_all_charts(
        self,
        task_type: str,
        y_test: np.ndarray,
        y_pred: np.ndarray,
        y_proba: Optional[np.ndarray] = None,
        feature_importance: Optional[List[Dict]] = None,
        leaderboard: Optional[List[Dict]] = None
    ) -> Dict[str, str]:
        """Generate comprehensive charts for task type"""
        
        setup_theme_aware_style()
        charts = {}
        
        is_classification = 'classification' in task_type.lower()
        
        print(f"📊 Generating charts for {task_type}...")
        
        # =====================================================================
        # COMMON CHARTS (Both regression and classification)
        # =====================================================================
        
        if leaderboard and len(leaderboard) > 0:
            charts['model_comparison'] = self._model_comparison(leaderboard, is_classification)
            charts['training_time'] = self._training_time(leaderboard)
        
        if feature_importance and len(feature_importance) > 0:
            charts['feature_importance'] = self._feature_importance(feature_importance)
        
        # =====================================================================
        # TASK-SPECIFIC CHARTS
        # =====================================================================
        
        if y_test is not None and y_pred is not None:
            if is_classification:
                # Classification charts
                charts['confusion_matrix'] = self._confusion_matrix(y_test, y_pred)
                charts['class_distribution'] = self._class_distribution(y_test, y_pred)
                charts['classification_metrics'] = self._classification_metrics(y_test, y_pred)
                charts['prediction_accuracy_pie'] = self._prediction_accuracy_pie(y_test, y_pred)
                
                if y_proba is not None:
                    charts['roc_curve'] = self._roc_curve(y_test, y_proba)
                    charts['probability_histogram'] = self._probability_histogram(y_proba)
                    charts['confidence_gauge'] = self._confidence_gauge(y_proba)
            else:
                # Regression charts
                charts['actual_vs_predicted'] = self._actual_vs_predicted(y_test, y_pred)
                charts['residual_plot'] = self._residual_plot(y_test, y_pred)
                charts['error_histogram'] = self._error_histogram(y_test, y_pred)
                charts['prediction_error'] = self._prediction_error(y_test, y_pred)
                charts['qq_plot'] = self._qq_plot(y_test, y_pred)
                charts['regression_metrics'] = self._regression_metrics(y_test, y_pred)
                charts['error_boxplot'] = self._error_boxplot(y_test, y_pred)
        
        print(f"   ✅ Generated {len(charts)} charts")
        return charts
    
    # =========================================================================
    # COMMON CHARTS
    # =========================================================================
    
    def _model_comparison(self, leaderboard: List[Dict], is_classification: bool) -> str:
        """Model performance comparison"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        names = [m['name'] for m in leaderboard[:8]][::-1]
        metric = 'f1' if is_classification else 'r2'
        scores = [m['metrics'].get(metric, m['metrics'].get('accuracy', 0)) for m in leaderboard[:8]][::-1]
        
        colors = [PALETTE[i % len(PALETTE)] for i in range(len(names))]
        
        bars = ax.barh(range(len(names)), scores, color=colors, height=0.65, 
                      edgecolor='white', linewidth=2)
        
        # Value labels
        for bar, score in zip(bars, scores):
            ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2,
                   f'{score:.3f}', va='center', fontsize=11, fontweight='bold')
        
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(names)
        ax.set_xlabel(f'{metric.upper()} Score', fontweight='bold')
        ax.set_title('🏆 Model Performance Comparison', fontweight='bold', pad=15, fontsize=14)
        ax.set_xlim(0, max(scores) * 1.2 if scores else 1)
        ax.grid(axis='x', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _training_time(self, leaderboard: List[Dict]) -> str:
        """Training time comparison"""
        fig, ax = plt.subplots(figsize=(10, 5))
        
        names = [m['name'] for m in leaderboard[:8]]
        times = [m.get('training_time', 0) for m in leaderboard[:8]]
        
        bars = ax.bar(names, times, color=COLORS['cyan'], edgecolor='white', linewidth=2)
        
        for bar, t in zip(bars, times):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                   f'{t:.1f}s', ha='center', fontsize=10, fontweight='bold')
        
        ax.set_ylabel('Time (seconds)', fontweight='bold')
        ax.set_title('⏱️ Training Time by Model', fontweight='bold', pad=15, fontsize=14)
        ax.grid(axis='y', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _feature_importance(self, importance: List[Dict]) -> str:
        """Feature importance chart"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        features = [f['feature'][:20] for f in importance[:10]][::-1]
        values = [f['importance'] for f in importance[:10]][::-1]
        
        colors = [COLORS['indigo'] if v == max(values) else COLORS['blue'] for v in values]
        
        bars = ax.barh(range(len(features)), values, color=colors, height=0.65,
                      edgecolor='white', linewidth=2)
        
        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height()/2,
                   f'{val:.1%}', va='center', fontsize=10, fontweight='bold')
        
        ax.set_yticks(range(len(features)))
        ax.set_yticklabels(features)
        ax.set_xlabel('Importance', fontweight='bold')
        ax.set_title('📊 Feature Importance', fontweight='bold', pad=15, fontsize=14)
        ax.grid(axis='x', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    # =========================================================================
    # REGRESSION CHARTS
    # =========================================================================
    
    def _actual_vs_predicted(self, y_test: np.ndarray, y_pred: np.ndarray) -> str:
        """Actual vs Predicted scatter"""
        fig, ax = plt.subplots(figsize=(8, 8))
        
        r2 = 1 - np.sum((y_test - y_pred)**2) / np.sum((y_test - np.mean(y_test))**2)
        
        ax.scatter(y_test, y_pred, c=COLORS['blue'], alpha=0.6, s=40, 
                  edgecolors='white', linewidth=0.5)
        
        lims = [min(y_test.min(), y_pred.min()), max(y_test.max(), y_pred.max())]
        ax.plot(lims, lims, '--', color=COLORS['green'], linewidth=3, label='Perfect Prediction')
        
        ax.set_xlabel('Actual Values', fontweight='bold', fontsize=12)
        ax.set_ylabel('Predicted Values', fontweight='bold', fontsize=12)
        ax.set_title(f'📈 Actual vs Predicted (R² = {r2:.4f})', fontweight='bold', pad=15, fontsize=14)
        ax.legend(loc='upper left', fontsize=10)
        ax.grid(alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _residual_plot(self, y_test: np.ndarray, y_pred: np.ndarray) -> str:
        """Residual analysis plot"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        residuals = y_test - y_pred
        std = np.std(residuals)
        
        colors = [COLORS['green'] if r >= 0 else COLORS['red'] for r in residuals]
        ax.scatter(y_pred, residuals, c=colors, alpha=0.6, s=35, 
                  edgecolors='white', linewidth=0.3)
        
        ax.axhline(0, color=COLORS['blue'], linewidth=2.5)
        ax.axhline(2*std, color=COLORS['orange'], linewidth=2, linestyle='--', label=f'+2σ ({2*std:.1f})')
        ax.axhline(-2*std, color=COLORS['orange'], linewidth=2, linestyle='--', label=f'-2σ ({-2*std:.1f})')
        ax.fill_between([y_pred.min(), y_pred.max()], -2*std, 2*std, alpha=0.1, color=COLORS['orange'])
        
        ax.set_xlabel('Predicted Values', fontweight='bold', fontsize=12)
        ax.set_ylabel('Residuals (Actual - Predicted)', fontweight='bold', fontsize=12)
        ax.set_title('📉 Residual Analysis', fontweight='bold', pad=15, fontsize=14)
        ax.legend(loc='upper right')
        ax.grid(alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _error_histogram(self, y_test: np.ndarray, y_pred: np.ndarray) -> str:
        """Error distribution"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        errors = y_test - y_pred
        
        ax.hist(errors, bins=40, density=True, alpha=0.7, color=COLORS['blue'],
               edgecolor='white', linewidth=1)
        
        if len(errors) > 10:
            kde = stats.gaussian_kde(errors)
            x = np.linspace(errors.min(), errors.max(), 200)
            ax.plot(x, kde(x), color=COLORS['red'], linewidth=3, label='Density')
        
        ax.axvline(0, color=COLORS['green'], linewidth=2.5, linestyle='-', label='Zero Error')
        ax.axvline(np.mean(errors), color=COLORS['orange'], linewidth=2, linestyle='--',
                  label=f'Mean = {np.mean(errors):.2f}')
        
        ax.set_xlabel('Prediction Error', fontweight='bold', fontsize=12)
        ax.set_ylabel('Density', fontweight='bold', fontsize=12)
        ax.set_title('📊 Error Distribution', fontweight='bold', pad=15, fontsize=14)
        ax.legend(loc='upper right')
        ax.grid(alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _prediction_error(self, y_test: np.ndarray, y_pred: np.ndarray) -> str:
        """Error by value"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        errors = np.abs(y_test - y_pred)
        
        scatter = ax.scatter(y_test, errors, c=errors, cmap='RdYlGn_r',
                           alpha=0.7, s=35, edgecolors='white', linewidth=0.3)
        
        z = np.polyfit(y_test, errors, 1)
        ax.plot(np.sort(y_test), np.poly1d(z)(np.sort(y_test)), 
               color=COLORS['red'], linewidth=2.5, linestyle='--', label='Trend')
        
        plt.colorbar(scatter, ax=ax, label='Absolute Error', shrink=0.8)
        
        ax.set_xlabel('Actual Values', fontweight='bold', fontsize=12)
        ax.set_ylabel('Absolute Error', fontweight='bold', fontsize=12)
        ax.set_title('🎯 Prediction Error by Value', fontweight='bold', pad=15, fontsize=14)
        ax.legend(loc='upper right')
        ax.grid(alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _qq_plot(self, y_test: np.ndarray, y_pred: np.ndarray) -> str:
        """Q-Q plot for residuals"""
        fig, ax = plt.subplots(figsize=(8, 8))
        
        residuals = y_test - y_pred
        stats.probplot(residuals, dist="norm", plot=ax)
        
        ax.get_lines()[0].set_color(COLORS['blue'])
        ax.get_lines()[0].set_markersize(6)
        ax.get_lines()[1].set_color(COLORS['red'])
        ax.get_lines()[1].set_linewidth(2.5)
        
        ax.set_title('📐 Q-Q Plot (Residual Normality)', fontweight='bold', pad=15, fontsize=14)
        ax.grid(alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _regression_metrics(self, y_test: np.ndarray, y_pred: np.ndarray) -> str:
        """Regression metrics summary"""
        fig, ax = plt.subplots(figsize=(10, 5))
        
        r2 = 1 - np.sum((y_test - y_pred)**2) / np.sum((y_test - np.mean(y_test))**2)
        mae = np.mean(np.abs(y_test - y_pred))
        rmse = np.sqrt(np.mean((y_test - y_pred)**2))
        mape = np.mean(np.abs((y_test - y_pred) / np.where(y_test==0, 1, y_test))) * 100
        
        metrics = ['R² Score', 'MAE', 'RMSE', 'MAPE (%)']
        values = [r2, mae, rmse, mape]
        colors = [COLORS['green'] if r2 > 0.7 else COLORS['orange'], 
                 COLORS['blue'], COLORS['purple'], COLORS['cyan']]
        
        bars = ax.bar(metrics, values, color=colors, edgecolor='white', linewidth=2)
        
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.02,
                   f'{val:.3f}', ha='center', fontsize=12, fontweight='bold')
        
        ax.set_ylabel('Value', fontweight='bold', fontsize=12)
        ax.set_title('📋 Regression Metrics Summary', fontweight='bold', pad=15, fontsize=14)
        ax.grid(axis='y', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _error_boxplot(self, y_test: np.ndarray, y_pred: np.ndarray) -> str:
        """Error boxplot"""
        fig, ax = plt.subplots(figsize=(8, 6))
        
        errors = y_test - y_pred
        abs_errors = np.abs(errors)
        
        bp = ax.boxplot([errors, abs_errors], labels=['Signed Error', 'Absolute Error'],
                       patch_artist=True, widths=0.6)
        
        bp['boxes'][0].set_facecolor(COLORS['blue'])
        bp['boxes'][1].set_facecolor(COLORS['orange'])
        
        for element in ['whiskers', 'caps', 'medians']:
            plt.setp(bp[element], color='#374151', linewidth=2)
        
        ax.axhline(0, color=COLORS['green'], linewidth=2, linestyle='--', alpha=0.7)
        
        ax.set_ylabel('Error', fontweight='bold', fontsize=12)
        ax.set_title('📦 Error Distribution (Box Plot)', fontweight='bold', pad=15, fontsize=14)
        ax.grid(axis='y', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    # =========================================================================
    # CLASSIFICATION CHARTS
    # =========================================================================
    
    def _confusion_matrix(self, y_test: np.ndarray, y_pred: np.ndarray) -> str:
        """Confusion matrix heatmap"""
        from sklearn.metrics import confusion_matrix, accuracy_score
        
        fig, ax = plt.subplots(figsize=(8, 7))
        
        cm = confusion_matrix(y_test, y_pred)
        cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        cm_norm = np.nan_to_num(cm_norm)
        
        sns.heatmap(cm_norm, annot=True, fmt='.1%', cmap='Blues', ax=ax,
                   cbar_kws={'label': 'Proportion', 'shrink': 0.8},
                   annot_kws={'size': 12, 'weight': 'bold'},
                   linewidths=2, linecolor='white')
        
        acc = accuracy_score(y_test, y_pred)
        ax.set_xlabel('Predicted', fontweight='bold', fontsize=12)
        ax.set_ylabel('Actual', fontweight='bold', fontsize=12)
        ax.set_title(f'🎯 Confusion Matrix (Accuracy: {acc:.1%})', fontweight='bold', pad=15, fontsize=14)
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _class_distribution(self, y_test: np.ndarray, y_pred: np.ndarray) -> str:
        """Class distribution comparison"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        classes, actual = np.unique(y_test, return_counts=True)
        _, pred = np.unique(y_pred, return_counts=True)
        
        if len(pred) < len(actual):
            pred = np.pad(pred, (0, len(actual) - len(pred)))
        
        x = np.arange(min(len(classes), 10))
        width = 0.4
        
        ax.bar(x - width/2, actual[:10], width, label='Actual', 
              color=COLORS['blue'], edgecolor='white', linewidth=2)
        ax.bar(x + width/2, pred[:10], width, label='Predicted',
              color=COLORS['green'], edgecolor='white', linewidth=2)
        
        ax.set_xlabel('Class', fontweight='bold', fontsize=12)
        ax.set_ylabel('Count', fontweight='bold', fontsize=12)
        ax.set_title('📊 Class Distribution: Actual vs Predicted', fontweight='bold', pad=15, fontsize=14)
        ax.set_xticks(x)
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _classification_metrics(self, y_test: np.ndarray, y_pred: np.ndarray) -> str:
        """Classification metrics summary"""
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        fig, ax = plt.subplots(figsize=(10, 5))
        
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        rec = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        
        metrics = ['Accuracy', 'Precision', 'Recall', 'F1 Score']
        values = [acc, prec, rec, f1]
        colors = [COLORS['blue'], COLORS['green'], COLORS['orange'], COLORS['purple']]
        
        bars = ax.bar(metrics, values, color=colors, edgecolor='white', linewidth=2)
        
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                   f'{val:.1%}', ha='center', fontsize=12, fontweight='bold')
        
        ax.set_ylim(0, 1.15)
        ax.set_ylabel('Score', fontweight='bold', fontsize=12)
        ax.set_title('📋 Classification Metrics', fontweight='bold', pad=15, fontsize=14)
        ax.grid(axis='y', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _prediction_accuracy_pie(self, y_test: np.ndarray, y_pred: np.ndarray) -> str:
        """Correct vs incorrect predictions pie"""
        fig, ax = plt.subplots(figsize=(8, 8))
        
        correct = np.sum(y_test == y_pred)
        incorrect = len(y_test) - correct
        
        sizes = [correct, incorrect]
        labels = [f'Correct\n({correct})', f'Incorrect\n({incorrect})']
        colors = [COLORS['green'], COLORS['red']]
        explode = (0.02, 0.02)
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, 
                                         autopct='%1.1f%%', startangle=90,
                                         explode=explode, shadow=False,
                                         wedgeprops={'edgecolor': 'white', 'linewidth': 3})
        
        plt.setp(autotexts, size=14, weight='bold', color='white')
        plt.setp(texts, size=12, weight='bold')
        
        ax.set_title('✅ Prediction Accuracy', fontweight='bold', pad=15, fontsize=14)
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _roc_curve(self, y_test: np.ndarray, y_proba: np.ndarray) -> str:
        """ROC curve"""
        from sklearn.metrics import roc_curve, auc
        
        fig, ax = plt.subplots(figsize=(8, 8))
        
        try:
            fpr, tpr, _ = roc_curve(y_test, y_proba)
            roc_auc = auc(fpr, tpr)
            
            ax.fill_between(fpr, tpr, alpha=0.2, color=COLORS['blue'])
            ax.plot(fpr, tpr, color=COLORS['blue'], linewidth=3,
                   label=f'ROC (AUC = {roc_auc:.3f})')
            ax.plot([0, 1], [0, 1], '--', color=COLORS['red'], linewidth=2,
                   label='Random (AUC = 0.5)')
            
            ax.set_xlabel('False Positive Rate', fontweight='bold', fontsize=12)
            ax.set_ylabel('True Positive Rate', fontweight='bold', fontsize=12)
            ax.set_title('📈 ROC Curve', fontweight='bold', pad=15, fontsize=14)
            ax.legend(loc='lower right', fontsize=11)
            ax.set_xlim([-0.02, 1.02])
            ax.set_ylim([-0.02, 1.02])
        except:
            ax.text(0.5, 0.5, 'ROC not available\n(multiclass)', ha='center', va='center', fontsize=14)
        
        ax.grid(alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _probability_histogram(self, y_proba: np.ndarray) -> str:
        """Probability distribution"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        proba = y_proba.flatten() if len(y_proba.shape) > 1 else y_proba
        
        ax.hist(proba, bins=50, density=True, alpha=0.7,
               color=COLORS['cyan'], edgecolor='white', linewidth=1)
        
        if len(proba) > 10:
            kde = stats.gaussian_kde(np.clip(proba, 0.01, 0.99))
            x = np.linspace(0, 1, 200)
            ax.plot(x, kde(x), color=COLORS['purple'], linewidth=3, label='Density')
        
        ax.axvline(0.5, color=COLORS['red'], linewidth=2.5, linestyle='--', label='Threshold (0.5)')
        
        ax.set_xlabel('Prediction Probability', fontweight='bold', fontsize=12)
        ax.set_ylabel('Density', fontweight='bold', fontsize=12)
        ax.set_title('🎲 Model Confidence Distribution', fontweight='bold', pad=15, fontsize=14)
        ax.legend(loc='upper right')
        ax.set_xlim([0, 1])
        ax.grid(alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _confidence_gauge(self, y_proba: np.ndarray) -> str:
        """Average confidence gauge"""
        fig, ax = plt.subplots(figsize=(8, 6))
        
        avg_conf = np.mean(np.max(y_proba.reshape(-1, 1) if len(y_proba.shape) == 1 else y_proba, axis=-1) if len(y_proba.shape) > 1 else y_proba)
        
        # Gauge chart
        theta = np.linspace(0, np.pi, 100)
        r = 1
        
        ax.fill_between(theta, 0, r, alpha=0.15, color=COLORS['red'])
        ax.fill_between(theta[50:], 0, r, alpha=0.15, color=COLORS['orange'])
        ax.fill_between(theta[70:], 0, r, alpha=0.15, color=COLORS['green'])
        
        # Needle
        angle = np.pi * (1 - avg_conf)
        ax.annotate('', xy=(angle, 0.85), xytext=(np.pi/2, 0),
                   arrowprops=dict(arrowstyle='->', lw=3, color=COLORS['blue']))
        
        ax.text(np.pi/2, -0.3, f'{avg_conf:.1%}', ha='center', fontsize=24, fontweight='bold', color=COLORS['blue'])
        ax.text(np.pi/2, -0.5, 'Average Confidence', ha='center', fontsize=12, color='#374151')
        
        ax.set_xlim(0, np.pi)
        ax.set_ylim(-0.7, 1.1)
        ax.axis('off')
        ax.set_title('🎯 Model Confidence Level', fontweight='bold', pad=15, fontsize=14)
        
        plt.tight_layout()
        return fig_to_base64(fig)


# Global instance
chart_generator = MLChartGenerator()
