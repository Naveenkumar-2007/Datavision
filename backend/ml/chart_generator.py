"""
📊 DYNAMIC CHART GENERATOR - Task-Specific ML Visualizations
=============================================================

Generates different charts based on task type:
- Classification: Confusion Matrix, ROC, Class Distribution
- Regression: Residuals, Actual vs Predicted, Error Distribution
- Both: Model Comparison, Feature Importance

NO HARDCODED DATA. All charts from real y_test, y_pred.
"""

import io
import base64
from typing import Dict, List, Optional, Any
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import confusion_matrix, roc_curve, auc, precision_recall_curve


class DynamicChartGenerator:
    """Generates ML charts based on task type and real data"""
    
    def __init__(self):
        # Dark theme matching DataVision
        self.colors = {
            'bg': '#0F172A',
            'card': '#1E293B',
            'text': '#F8FAFC',
            'muted': '#94A3B8',
            'teal': '#2DD4BF',
            'blue': '#3B82F6',
            'purple': '#8B5CF6',
            'amber': '#F59E0B',
            'red': '#EF4444',
            'green': '#10B981',
        }
        
        # Color palette for models
        self.palette = ['#2DD4BF', '#3B82F6', '#8B5CF6', '#F59E0B', '#EF4444', 
                       '#10B981', '#EC4899', '#6366F1', '#14B8A6', '#F97316']
    
    def _setup_style(self, fig, ax):
        """Apply dark theme to figure"""
        fig.patch.set_facecolor(self.colors['bg'])
        ax.set_facecolor(self.colors['card'])
        ax.tick_params(colors=self.colors['text'])
        ax.xaxis.label.set_color(self.colors['text'])
        ax.yaxis.label.set_color(self.colors['text'])
        ax.title.set_color(self.colors['text'])
        for spine in ax.spines.values():
            spine.set_color(self.colors['muted'])
    
    def _to_base64(self, fig) -> str:
        """Convert figure to base64 string"""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=120, bbox_inches='tight', 
                   facecolor=self.colors['bg'], edgecolor='none')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode()
        plt.close(fig)
        return f"data:image/png;base64,{img_str}"
    
    def generate_all_charts(
        self,
        task_type: str,
        y_test: np.ndarray,
        y_pred: np.ndarray,
        y_proba: Optional[np.ndarray],
        feature_importance: List[Dict],
        leaderboard: List[Dict]
    ) -> Dict[str, str]:
        """Generate all charts based on task type"""
        charts = {}
        
        if y_test is None or y_pred is None:
            print("⚠️ No predictions available for charts")
            return charts
        
        try:
            # 1. Model Comparison (always)
            if leaderboard:
                charts['model_comparison'] = self.generate_model_comparison(leaderboard, task_type)
            
            # 2. Feature Importance (always)
            if feature_importance:
                charts['feature_importance'] = self.generate_feature_importance(feature_importance)
            
            # 3. Task-specific charts
            if task_type in ['binary', 'multiclass', 'classification']:
                charts['confusion_matrix'] = self.generate_confusion_matrix(y_test, y_pred)
                charts['class_distribution'] = self.generate_class_distribution(y_test, y_pred)
                
                if task_type == 'binary' and y_proba is not None:
                    charts['roc_curve'] = self.generate_roc_curve(y_test, y_proba)
                    charts['precision_recall'] = self.generate_pr_curve(y_test, y_proba)
            else:
                # Regression
                charts['actual_vs_predicted'] = self.generate_actual_vs_predicted(y_test, y_pred)
                charts['residual_plot'] = self.generate_residuals(y_test, y_pred)
                charts['error_distribution'] = self.generate_error_distribution(y_test, y_pred)
            
            print(f"📊 Generated {len(charts)} charts for {task_type}")
            
        except Exception as e:
            print(f"⚠️ Chart generation error: {e}")
        
        return charts
    
    # =========================================================================
    # COMMON CHARTS
    # =========================================================================
    
    def generate_model_comparison(self, leaderboard: List[Dict], task_type: str) -> str:
        """Bar chart comparing model performance"""
        fig, ax = plt.subplots(figsize=(10, 6))
        self._setup_style(fig, ax)
        
        models = [m['name'] for m in leaderboard[:10]]
        
        # Get primary metric
        if task_type in ['binary', 'multiclass', 'classification']:
            metric_key = 'f1'
            metric_label = 'F1 Score'
        else:
            metric_key = 'r2'
            metric_label = 'R² Score'
        
        scores = [m['metrics'].get(metric_key, 0) for m in leaderboard[:10]]
        
        colors = [self.colors['teal'] if i == 0 else self.colors['blue'] 
                 for i in range(len(models))]
        
        bars = ax.barh(models[::-1], scores[::-1], color=colors[::-1], edgecolor='none')
        
        # Add value labels
        for bar, score in zip(bars, scores[::-1]):
            ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                   f'{score:.3f}', va='center', color=self.colors['text'], fontsize=10)
        
        ax.set_xlabel(metric_label, fontsize=12)
        ax.set_title('Model Performance Comparison', fontsize=14, fontweight='bold')
        ax.set_xlim(0, max(scores) * 1.15 if scores else 1)
        
        plt.tight_layout()
        return self._to_base64(fig)
    
    def generate_feature_importance(self, importance: List[Dict]) -> str:
        """Bar chart of feature importance"""
        fig, ax = plt.subplots(figsize=(10, 6))
        self._setup_style(fig, ax)
        
        features = [f['feature'] for f in importance[:10]]
        values = [f['importance'] for f in importance[:10]]
        
        colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(features)))
        
        bars = ax.barh(features[::-1], values[::-1], color=colors[::-1], edgecolor='none')
        
        # Add value labels
        for bar, val in zip(bars, values[::-1]):
            ax.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height()/2,
                   f'{val:.3f}', va='center', color=self.colors['text'], fontsize=10)
        
        ax.set_xlabel('Importance', fontsize=12)
        ax.set_title('Feature Importance (Top 10)', fontsize=14, fontweight='bold')
        ax.set_xlim(0, max(values) * 1.2 if values else 1)
        
        plt.tight_layout()
        return self._to_base64(fig)
    
    # =========================================================================
    # CLASSIFICATION CHARTS
    # =========================================================================
    
    def generate_confusion_matrix(self, y_test: np.ndarray, y_pred: np.ndarray) -> str:
        """Confusion matrix heatmap"""
        fig, ax = plt.subplots(figsize=(8, 6))
        self._setup_style(fig, ax)
        
        cm = confusion_matrix(y_test, y_pred)
        
        # Normalize for coloring
        cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        cm_normalized = np.nan_to_num(cm_normalized)
        
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                   cbar_kws={'label': 'Count'}, linewidths=0.5,
                   annot_kws={'size': 14, 'weight': 'bold'})
        
        ax.set_xlabel('Predicted', fontsize=12)
        ax.set_ylabel('Actual', fontsize=12)
        ax.set_title('Confusion Matrix', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        return self._to_base64(fig)
    
    def generate_class_distribution(self, y_test: np.ndarray, y_pred: np.ndarray) -> str:
        """Compare actual vs predicted class distribution"""
        fig, ax = plt.subplots(figsize=(10, 6))
        self._setup_style(fig, ax)
        
        # Get unique classes
        classes = np.unique(np.concatenate([y_test, y_pred]))
        
        # Count occurrences
        actual_counts = [np.sum(y_test == c) for c in classes]
        pred_counts = [np.sum(y_pred == c) for c in classes]
        
        x = np.arange(len(classes))
        width = 0.35
        
        ax.bar(x - width/2, actual_counts, width, label='Actual', color=self.colors['teal'])
        ax.bar(x + width/2, pred_counts, width, label='Predicted', color=self.colors['blue'])
        
        ax.set_xlabel('Class', fontsize=12)
        ax.set_ylabel('Count', fontsize=12)
        ax.set_title('Class Distribution: Actual vs Predicted', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels([str(c) for c in classes])
        ax.legend(facecolor=self.colors['card'], edgecolor=self.colors['muted'],
                 labelcolor=self.colors['text'])
        
        plt.tight_layout()
        return self._to_base64(fig)
    
    def generate_roc_curve(self, y_test: np.ndarray, y_proba: np.ndarray) -> str:
        """ROC curve for binary classification"""
        fig, ax = plt.subplots(figsize=(8, 6))
        self._setup_style(fig, ax)
        
        try:
            fpr, tpr, _ = roc_curve(y_test, y_proba)
            roc_auc = auc(fpr, tpr)
            
            ax.plot(fpr, tpr, color=self.colors['teal'], lw=2,
                   label=f'ROC Curve (AUC = {roc_auc:.3f})')
            ax.plot([0, 1], [0, 1], color=self.colors['muted'], lw=1, linestyle='--',
                   label='Random Classifier')
            
            ax.set_xlabel('False Positive Rate', fontsize=12)
            ax.set_ylabel('True Positive Rate', fontsize=12)
            ax.set_title('ROC Curve', fontsize=14, fontweight='bold')
            ax.legend(loc='lower right', facecolor=self.colors['card'],
                     edgecolor=self.colors['muted'], labelcolor=self.colors['text'])
            ax.set_xlim([0, 1])
            ax.set_ylim([0, 1.05])
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Could not generate ROC curve', 
                   ha='center', va='center', color=self.colors['text'])
        
        plt.tight_layout()
        return self._to_base64(fig)
    
    def generate_pr_curve(self, y_test: np.ndarray, y_proba: np.ndarray) -> str:
        """Precision-Recall curve"""
        fig, ax = plt.subplots(figsize=(8, 6))
        self._setup_style(fig, ax)
        
        try:
            precision, recall, _ = precision_recall_curve(y_test, y_proba)
            
            ax.plot(recall, precision, color=self.colors['purple'], lw=2)
            ax.fill_between(recall, precision, alpha=0.2, color=self.colors['purple'])
            
            ax.set_xlabel('Recall', fontsize=12)
            ax.set_ylabel('Precision', fontsize=12)
            ax.set_title('Precision-Recall Curve', fontsize=14, fontweight='bold')
            ax.set_xlim([0, 1])
            ax.set_ylim([0, 1.05])
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Could not generate PR curve',
                   ha='center', va='center', color=self.colors['text'])
        
        plt.tight_layout()
        return self._to_base64(fig)
    
    # =========================================================================
    # REGRESSION CHARTS
    # =========================================================================
    
    def generate_actual_vs_predicted(self, y_test: np.ndarray, y_pred: np.ndarray) -> str:
        """Scatter plot of actual vs predicted values"""
        fig, ax = plt.subplots(figsize=(8, 6))
        self._setup_style(fig, ax)
        
        ax.scatter(y_test, y_pred, alpha=0.5, color=self.colors['teal'], edgecolor='none')
        
        # Perfect prediction line
        min_val = min(y_test.min(), y_pred.min())
        max_val = max(y_test.max(), y_pred.max())
        ax.plot([min_val, max_val], [min_val, max_val], 
               color=self.colors['red'], linestyle='--', lw=2, label='Perfect Prediction')
        
        ax.set_xlabel('Actual Values', fontsize=12)
        ax.set_ylabel('Predicted Values', fontsize=12)
        ax.set_title('Actual vs Predicted', fontsize=14, fontweight='bold')
        ax.legend(facecolor=self.colors['card'], edgecolor=self.colors['muted'],
                 labelcolor=self.colors['text'])
        
        plt.tight_layout()
        return self._to_base64(fig)
    
    def generate_residuals(self, y_test: np.ndarray, y_pred: np.ndarray) -> str:
        """Residual plot"""
        fig, ax = plt.subplots(figsize=(8, 6))
        self._setup_style(fig, ax)
        
        residuals = y_test - y_pred
        
        ax.scatter(y_pred, residuals, alpha=0.5, color=self.colors['blue'], edgecolor='none')
        ax.axhline(y=0, color=self.colors['red'], linestyle='--', lw=2)
        
        ax.set_xlabel('Predicted Values', fontsize=12)
        ax.set_ylabel('Residuals', fontsize=12)
        ax.set_title('Residual Plot', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        return self._to_base64(fig)
    
    def generate_error_distribution(self, y_test: np.ndarray, y_pred: np.ndarray) -> str:
        """Histogram of prediction errors"""
        fig, ax = plt.subplots(figsize=(8, 6))
        self._setup_style(fig, ax)
        
        errors = y_test - y_pred
        
        ax.hist(errors, bins=30, color=self.colors['purple'], edgecolor='none', alpha=0.7)
        ax.axvline(x=0, color=self.colors['red'], linestyle='--', lw=2)
        ax.axvline(x=np.mean(errors), color=self.colors['amber'], linestyle='-', lw=2,
                  label=f'Mean: {np.mean(errors):.2f}')
        
        ax.set_xlabel('Prediction Error', fontsize=12)
        ax.set_ylabel('Frequency', fontsize=12)
        ax.set_title('Error Distribution', fontsize=14, fontweight='bold')
        ax.legend(facecolor=self.colors['card'], edgecolor=self.colors['muted'],
                 labelcolor=self.colors['text'])
        
        plt.tight_layout()
        return self._to_base64(fig)


# Global instance
chart_generator = DynamicChartGenerator()
