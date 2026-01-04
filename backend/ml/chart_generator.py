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
        leaderboard: Optional[List[Dict]] = None,
        model = None,
        X_train: Optional[np.ndarray] = None
    ) -> Dict[str, str]:
        """Generate comprehensive charts for task type - ENHANCED for TOP 1%"""
        
        setup_theme_aware_style()
        charts = {}
        
        is_classification = 'classification' in task_type.lower()
        
        print(f"📊 Generating TOP 1% charts for {task_type}...")
        
        # =====================================================================
        # COMMON CHARTS (Both regression and classification)
        # =====================================================================
        
        if leaderboard and len(leaderboard) > 0:
            charts['model_comparison'] = self._model_comparison(leaderboard, is_classification)
            charts['training_time'] = self._training_time(leaderboard)
            # NEW: Radar comparison chart
            try:
                charts['model_radar'] = self._model_radar_comparison(leaderboard, is_classification)
            except Exception as e:
                print(f"   ⚠️ Radar chart skipped: {e}")
        
        if feature_importance and len(feature_importance) > 0:
            charts['feature_importance'] = self._feature_importance(feature_importance)
            # NEW: SHAP-style importance
            try:
                charts['shap_importance'] = self._shap_importance(feature_importance)
            except Exception as e:
                print(f"   ⚠️ SHAP chart skipped: {e}")
        
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
                    # NEW: Advanced classification charts
                    try:
                        charts['calibration_curve'] = self._calibration_curve(y_test, y_proba)
                    except Exception as e:
                        print(f"   ⚠️ Calibration curve skipped: {e}")
                    try:
                        charts['lift_gain_curves'] = self._lift_gain_curves(y_test, y_proba)
                    except Exception as e:
                        print(f"   ⚠️ Lift/Gain curves skipped: {e}")
                    try:
                        charts['confidence_distribution'] = self._confidence_distribution(y_proba)
                    except Exception as e:
                        print(f"   ⚠️ Confidence distribution skipped: {e}")
            else:
                # Regression charts
                charts['actual_vs_predicted'] = self._actual_vs_predicted(y_test, y_pred)
                charts['residual_plot'] = self._residual_plot(y_test, y_pred)
                charts['error_histogram'] = self._error_histogram(y_test, y_pred)
                charts['prediction_error'] = self._prediction_error(y_test, y_pred)
                charts['qq_plot'] = self._qq_plot(y_test, y_pred)
                charts['regression_metrics'] = self._regression_metrics(y_test, y_pred)
                charts['error_boxplot'] = self._error_boxplot(y_test, y_pred)
                # NEW: Prediction intervals for regression
                try:
                    charts['prediction_intervals'] = self._prediction_intervals(y_test, y_pred)
                except Exception as e:
                    print(f"   ⚠️ Prediction intervals skipped: {e}")
        
        # =====================================================================
        # LEARNING CURVE (requires model and training data)
        # =====================================================================
        if model is not None and X_train is not None and y_test is not None:
            try:
                # Use a subset to avoid long computation
                X_subset = X_train[:min(1000, len(X_train))]
                y_subset = y_test[:min(1000, len(y_test))] if len(y_test) == len(X_train) else y_test[:min(1000, len(X_train))]
                charts['learning_curve'] = self._learning_curve(model, X_subset, y_subset, task_type)
            except Exception as e:
                print(f"   ⚠️ Learning curve skipped: {e}")
        
        print(f"   ✅ Generated {len(charts)} TOP 1% charts")
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
    
    # =========================================================================
    # ADVANCED CHARTS FOR TOP 1% (ADDED v4.0)
    # =========================================================================
    
    def _learning_curve(self, model, X: np.ndarray, y: np.ndarray, task_type: str = 'classification') -> str:
        """Learning curve to detect overfitting/underfitting"""
        from sklearn.model_selection import learning_curve
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        try:
            scoring = 'f1_weighted' if 'classification' in task_type else 'r2'
            
            train_sizes, train_scores, val_scores = learning_curve(
                model, X, y,
                train_sizes=np.linspace(0.1, 1.0, 8),
                cv=3,
                scoring=scoring,
                n_jobs=1,
                random_state=42
            )
            
            train_mean = train_scores.mean(axis=1)
            train_std = train_scores.std(axis=1)
            val_mean = val_scores.mean(axis=1)
            val_std = val_scores.std(axis=1)
            
            ax.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, 
                           alpha=0.2, color=COLORS['blue'])
            ax.fill_between(train_sizes, val_mean - val_std, val_mean + val_std, 
                           alpha=0.2, color=COLORS['green'])
            ax.plot(train_sizes, train_mean, 'o-', color=COLORS['blue'], linewidth=2.5, 
                   markersize=8, label='Training Score')
            ax.plot(train_sizes, val_mean, 'o-', color=COLORS['green'], linewidth=2.5, 
                   markersize=8, label='Validation Score')
            
            # Add gap annotation
            gap = train_mean[-1] - val_mean[-1]
            gap_status = "Low (Good)" if gap < 0.05 else "Medium" if gap < 0.1 else "High (Overfitting)"
            ax.text(0.95, 0.05, f'Train-Val Gap: {gap:.3f}\n({gap_status})', 
                   transform=ax.transAxes, ha='right', va='bottom',
                   fontsize=10, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Learning curve not available\n{str(e)[:50]}', 
                   ha='center', va='center', fontsize=12)
        
        ax.set_xlabel('Training Set Size', fontweight='bold', fontsize=12)
        ax.set_ylabel('Score', fontweight='bold', fontsize=12)
        ax.set_title('📈 Learning Curve (Bias-Variance Analysis)', fontweight='bold', pad=15, fontsize=14)
        ax.legend(loc='lower right', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _calibration_curve(self, y_test: np.ndarray, y_proba: np.ndarray, n_bins: int = 10) -> str:
        """Probability calibration curve for classification"""
        from sklearn.calibration import calibration_curve
        
        fig, ax = plt.subplots(figsize=(8, 8))
        
        try:
            prob_true, prob_pred = calibration_curve(y_test, y_proba, n_bins=n_bins, strategy='uniform')
            
            # Perfect calibration line
            ax.plot([0, 1], [0, 1], 'k--', linewidth=2, label='Perfectly Calibrated')
            ax.plot(prob_pred, prob_true, 'o-', color=COLORS['teal'], 
                   linewidth=2.5, markersize=10, label='Model Calibration')
            
            ax.fill_between(prob_pred, prob_true, prob_pred, alpha=0.2, color=COLORS['teal'])
            
            # Calculate calibration error
            ece = np.mean(np.abs(prob_true - prob_pred))
            ax.text(0.95, 0.05, f'Expected Calibration Error: {ece:.3f}', 
                   transform=ax.transAxes, ha='right', va='bottom',
                   fontsize=10, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Calibration curve not available\n(binary classification only)', 
                   ha='center', va='center', fontsize=12)
            ax.plot([0, 1], [0, 1], 'k--', linewidth=2)
        
        ax.set_xlabel('Mean Predicted Probability', fontweight='bold', fontsize=12)
        ax.set_ylabel('Fraction of Positives', fontweight='bold', fontsize=12)
        ax.set_title('🎯 Probability Calibration Curve', fontweight='bold', pad=15, fontsize=14)
        ax.legend(loc='upper left', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_xlim([-0.02, 1.02])
        ax.set_ylim([-0.02, 1.02])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _lift_gain_curves(self, y_test: np.ndarray, y_proba: np.ndarray) -> str:
        """Lift and Cumulative Gain curves for classification"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        try:
            # Sort by predicted probability (descending)
            sorted_idx = np.argsort(y_proba)[::-1]
            y_sorted = np.array(y_test)[sorted_idx]
            
            # Cumulative gains
            cumulative_positive = np.cumsum(y_sorted)
            total_positive = y_sorted.sum()
            
            if total_positive > 0:
                gains = cumulative_positive / total_positive
            else:
                gains = np.zeros_like(cumulative_positive)
            
            # Percentiles
            percentiles = np.arange(1, len(y_sorted) + 1) / len(y_sorted)
            
            # Lift = Gain / Percentile
            lift = np.where(percentiles > 0, gains / percentiles, 0)
            
            # === GAIN CURVE ===
            axes[0].plot(percentiles, gains, color=COLORS['blue'], linewidth=2.5, label='Model')
            axes[0].plot([0, 1], [0, 1], 'k--', linewidth=2, label='Random')
            axes[0].fill_between(percentiles, gains, percentiles, alpha=0.2, color=COLORS['blue'])
            axes[0].set_xlabel('% of Population', fontweight='bold', fontsize=12)
            axes[0].set_ylabel('% of Positives Captured', fontweight='bold', fontsize=12)
            axes[0].set_title('📈 Cumulative Gains Curve', fontweight='bold', pad=15, fontsize=14)
            axes[0].legend(loc='lower right')
            axes[0].grid(True, alpha=0.3)
            axes[0].spines['top'].set_visible(False)
            axes[0].spines['right'].set_visible(False)
            
            # === LIFT CURVE ===
            axes[1].plot(percentiles, lift, color=COLORS['green'], linewidth=2.5)
            axes[1].axhline(y=1, color='k', linestyle='--', linewidth=2, label='Random (Lift=1)')
            axes[1].fill_between(percentiles, lift, 1, where=(lift > 1), alpha=0.2, color=COLORS['green'])
            axes[1].set_xlabel('% of Population', fontweight='bold', fontsize=12)
            axes[1].set_ylabel('Lift', fontweight='bold', fontsize=12)
            axes[1].set_title('📊 Lift Curve', fontweight='bold', pad=15, fontsize=14)
            axes[1].legend(loc='upper right')
            axes[1].grid(True, alpha=0.3)
            axes[1].spines['top'].set_visible(False)
            axes[1].spines['right'].set_visible(False)
            
        except Exception as e:
            for ax in axes:
                ax.text(0.5, 0.5, f'Lift/Gain not available', ha='center', va='center', fontsize=12)
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _model_radar_comparison(self, leaderboard: List[Dict], is_classification: bool = True) -> str:
        """Radar chart comparing all models across metrics"""
        from math import pi
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
        
        if is_classification:
            metrics = ['accuracy', 'f1', 'precision', 'recall']
        else:
            metrics = ['r2', 'mae', 'rmse']
        
        n_metrics = len(metrics)
        
        # Calculate angles
        angles = [n / float(n_metrics) * 2 * pi for n in range(n_metrics)]
        angles += angles[:1]  # Complete the loop
        
        colors = [COLORS['blue'], COLORS['green'], COLORS['purple'], COLORS['amber'], COLORS['teal']]
        
        for idx, model in enumerate(leaderboard[:5]):
            values = []
            for m in metrics:
                val = model.get('metrics', {}).get(m, 0)
                # Normalize metrics to 0-1 range for comparison
                if m in ['mae', 'rmse']:
                    val = max(0, 1 - val / 100)  # Invert and normalize
                values.append(val)
            
            values += values[:1]  # Complete the loop
            
            ax.plot(angles, values, 'o-', linewidth=2.5, label=model['name'], 
                   color=colors[idx % len(colors)], markersize=8)
            ax.fill(angles, values, alpha=0.15, color=colors[idx % len(colors)])
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([m.upper() for m in metrics], fontsize=11, fontweight='bold')
        ax.set_title('🎯 Model Comparison Radar', fontweight='bold', fontsize=14, y=1.08)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0), fontsize=10)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _confidence_distribution(self, y_proba: np.ndarray) -> str:
        """Distribution of prediction confidences"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Get max probability for each prediction
        if len(y_proba.shape) > 1:
            max_proba = np.max(y_proba, axis=1)
        else:
            max_proba = y_proba
        
        # Histogram
        n, bins, patches = ax.hist(max_proba, bins=30, density=True, alpha=0.7, 
                                   color=COLORS['blue'], edgecolor='white', linewidth=1)
        
        # Color bars by confidence level
        for i, patch in enumerate(patches):
            if bins[i] < 0.5:
                patch.set_facecolor(COLORS['red'])
            elif bins[i] < 0.8:
                patch.set_facecolor(COLORS['orange'])
            else:
                patch.set_facecolor(COLORS['green'])
        
        # Add threshold lines
        ax.axvline(x=0.5, color=COLORS['amber'], linestyle='--', linewidth=2.5, label='50% Threshold')
        ax.axvline(x=0.8, color=COLORS['green'], linestyle='--', linewidth=2.5, label='80% High Confidence')
        
        # Statistics
        mean_conf = np.mean(max_proba)
        high_conf_pct = (max_proba >= 0.8).mean() * 100
        ax.text(0.95, 0.95, f'Mean: {mean_conf:.1%}\nHigh Conf (≥80%): {high_conf_pct:.1f}%', 
               transform=ax.transAxes, ha='right', va='top',
               fontsize=10, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.set_xlabel('Prediction Confidence', fontweight='bold', fontsize=12)
        ax.set_ylabel('Density', fontweight='bold', fontsize=12)
        ax.set_title('🎲 Prediction Confidence Distribution', fontweight='bold', pad=15, fontsize=14)
        ax.legend(loc='upper left')
        ax.set_xlim([0, 1])
        ax.grid(True, alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _prediction_intervals(self, y_test: np.ndarray, y_pred: np.ndarray, confidence: float = 0.95) -> str:
        """Prediction intervals for regression"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Calculate residual std
        residuals = y_test - y_pred
        std = np.std(residuals)
        
        # Calculate z-score for confidence level
        z = stats.norm.ppf((1 + confidence) / 2)
        
        # Sort by predicted value for visualization
        sorted_idx = np.argsort(y_pred)
        y_pred_sorted = y_pred[sorted_idx]
        y_test_sorted = y_test[sorted_idx]
        
        # Calculate bounds
        lower = y_pred_sorted - z * std
        upper = y_pred_sorted + z * std
        
        # Plot
        x_range = np.arange(len(y_pred_sorted))
        
        ax.fill_between(x_range, lower, upper, alpha=0.3, color=COLORS['blue'], 
                       label=f'{confidence:.0%} Prediction Interval')
        ax.plot(x_range, y_pred_sorted, color=COLORS['blue'], linewidth=2, label='Predicted')
        ax.scatter(x_range, y_test_sorted, c=COLORS['green'], alpha=0.6, s=20, label='Actual', zorder=5)
        
        # Calculate coverage
        in_interval = ((y_test_sorted >= lower) & (y_test_sorted <= upper)).mean()
        ax.text(0.95, 0.95, f'Coverage: {in_interval:.1%}\n(Expected: {confidence:.0%})', 
               transform=ax.transAxes, ha='right', va='top',
               fontsize=10, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.set_xlabel('Sample Index (sorted by prediction)', fontweight='bold', fontsize=12)
        ax.set_ylabel('Value', fontweight='bold', fontsize=12)
        ax.set_title(f'📊 {confidence:.0%} Prediction Intervals', fontweight='bold', pad=15, fontsize=14)
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        return fig_to_base64(fig)
    
    def _shap_importance(self, feature_importance: List[Dict]) -> str:
        """SHAP-style feature importance (bar chart with directionality)"""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Get top 15 features
        features = [f['feature'][:25] for f in feature_importance[:15]][::-1]
        values = [f['importance'] for f in feature_importance[:15]][::-1]
        
        # SHAP-style colors (red for positive, blue for negative)
        # Since we only have magnitude, use gradient
        max_val = max(values) if values else 1
        colors = [plt.cm.RdBu_r(0.2 + 0.6 * v / max_val) for v in values]
        
        bars = ax.barh(range(len(features)), values, color=colors, height=0.7,
                      edgecolor='white', linewidth=1)
        
        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height()/2,
                   f'{val:.3f}', va='center', fontsize=9, fontweight='bold')
        
        ax.set_yticks(range(len(features)))
        ax.set_yticklabels(features, fontsize=10)
        ax.set_xlabel('|SHAP Value| (Mean Impact on Prediction)', fontweight='bold', fontsize=12)
        ax.set_title('🔬 SHAP-Style Feature Importance', fontweight='bold', pad=15, fontsize=14)
        ax.grid(axis='x', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Add colorbar legend
        sm = plt.cm.ScalarMappable(cmap='RdBu_r', norm=plt.Normalize(0, max_val))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, shrink=0.5, pad=0.02)
        cbar.set_label('Impact Magnitude', fontsize=10)
        
        plt.tight_layout()
        return fig_to_base64(fig)


# Global instance
chart_generator = MLChartGenerator()
