"""
📊 SHAP EXPLAINABILITY ENGINE
=============================

Provides model explanations using SHAP (SHapley Additive exPlanations):
- Global feature importance (summary plot)
- Local explanations (waterfall for single predictions)
- Force plots for decision paths

Uses TreeExplainer for tree-based models, KernelExplainer as fallback.
"""

import numpy as np
import pandas as pd
import base64
import io
import logging
from typing import Dict, List, Any, Optional, Tuple

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

# Check if SHAP is available
try:
    import shap
    HAS_SHAP = True
    logger.info("✅ SHAP library available for explainability")
except ImportError:
    HAS_SHAP = False
    logger.warning("⚠️ SHAP not installed. Run: pip install shap")


def _fig_to_base64(fig) -> str:
    """Convert matplotlib figure to base64 string"""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{img_base64}"


class SHAPExplainer:
    """
    🔍 SHAP-based model explainer.
    
    Creates explanations for:
    - Why did the model make this prediction?
    - Which features are most important globally?
    - How does each feature push the prediction?
    """
    
    def __init__(self, model, X_background: np.ndarray, feature_names: List[str] = None):
        """
        Initialize explainer with model and background data.
        
        Args:
            model: Trained sklearn model
            X_background: Background dataset for SHAP (subset of training data)
            feature_names: Optional list of feature names
        """
        self.model = model
        self.feature_names = feature_names or [f"Feature {i}" for i in range(X_background.shape[1])]
        self.explainer = None
        self.explainer_type = None
        
        if not HAS_SHAP:
            logger.warning("SHAP not available")
            return
        
        # Sample background data for efficiency (max 100 samples)
        if len(X_background) > 100:
            indices = np.random.choice(len(X_background), 100, replace=False)
            X_background = X_background[indices]
        
        self.X_background = X_background
        
        # Choose appropriate explainer
        model_name = type(model).__name__
        tree_models = ['RandomForest', 'GradientBoosting', 'XGB', 'LGBM', 
                       'CatBoost', 'ExtraTrees', 'DecisionTree', 'HistGradient']
        
        try:
            if any(name in model_name for name in tree_models):
                # TreeExplainer is fast and exact for tree models
                self.explainer = shap.TreeExplainer(model)
                self.explainer_type = "TreeExplainer"
                logger.info(f"✅ Using TreeExplainer for {model_name}")
            else:
                # KernelExplainer works for any model but is slower
                if hasattr(model, 'predict_proba'):
                    self.explainer = shap.KernelExplainer(model.predict_proba, X_background)
                else:
                    self.explainer = shap.KernelExplainer(model.predict, X_background)
                self.explainer_type = "KernelExplainer"
                logger.info(f"✅ Using KernelExplainer for {model_name}")
        except Exception as e:
            logger.warning(f"⚠️ Could not create SHAP explainer: {e}")
            self.explainer = None
    
    def explain_prediction(self, X_single: np.ndarray) -> Dict[str, Any]:
        """
        Explain a single prediction.
        
        Args:
            X_single: Single sample to explain (1D or 2D array)
            
        Returns:
            Dictionary with SHAP values, base value, and explanation chart
        """
        if not HAS_SHAP or self.explainer is None:
            return {"error": "SHAP not available"}
        
        try:
            # Ensure 2D
            if X_single.ndim == 1:
                X_single = X_single.reshape(1, -1)
            
            # Calculate SHAP values
            shap_values = self.explainer.shap_values(X_single)
            
            # Handle multi-class (use positive class for binary)
            if isinstance(shap_values, list):
                # Classification with multiple classes
                shap_values = shap_values[1] if len(shap_values) == 2 else shap_values[0]
            
            shap_values = shap_values.flatten()
            
            # Get base value
            if hasattr(self.explainer, 'expected_value'):
                base_value = self.explainer.expected_value
                if isinstance(base_value, np.ndarray):
                    base_value = base_value[1] if len(base_value) == 2 else base_value[0]
            else:
                base_value = 0
            
            # Create feature contributions dict
            contributions = []
            for i, (name, value, shap_val) in enumerate(zip(
                self.feature_names, X_single.flatten(), shap_values
            )):
                contributions.append({
                    "feature": name,
                    "value": float(value),
                    "shap_value": float(shap_val),
                    "direction": "positive" if shap_val > 0 else "negative"
                })
            
            # Sort by absolute SHAP value
            contributions.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
            
            # Generate waterfall chart
            waterfall_chart = self._generate_waterfall_chart(
                shap_values, X_single.flatten(), base_value
            )
            
            return {
                "success": True,
                "base_value": float(base_value),
                "prediction_contribution": float(sum(shap_values)),
                "contributions": contributions[:50],  # Top 50 features (increased from 15)
                "waterfall_chart": waterfall_chart
            }
            
        except Exception as e:
            logger.error(f"SHAP explanation error: {e}")
            return {"error": str(e)}
    
    def get_global_importance(self, X_sample: np.ndarray = None) -> Dict[str, Any]:
        """
        Get global feature importance using SHAP.
        
        Args:
            X_sample: Sample of data to calculate importance (uses background if None)
            
        Returns:
            Dictionary with importance values and summary chart
        """
        if not HAS_SHAP or self.explainer is None:
            return {"error": "SHAP not available"}
        
        try:
            X_sample = X_sample if X_sample is not None else self.X_background
            
            # Limit samples for speed
            if len(X_sample) > 200:
                indices = np.random.choice(len(X_sample), 200, replace=False)
                X_sample = X_sample[indices]
            
            # Calculate SHAP values
            shap_values = self.explainer.shap_values(X_sample)
            
            # Handle multi-class
            if isinstance(shap_values, list):
                shap_values = shap_values[1] if len(shap_values) == 2 else shap_values[0]
            
            # Calculate mean absolute SHAP values for importance
            importance = np.abs(shap_values).mean(axis=0)
            
            # Create importance dict
            feature_importance = []
            for name, imp in zip(self.feature_names, importance):
                feature_importance.append({
                    "feature": name,
                    "importance": float(imp)
                })
            
            # Sort by importance
            feature_importance.sort(key=lambda x: x["importance"], reverse=True)
            
            # Generate summary plot
            summary_chart = self._generate_summary_chart(shap_values, X_sample)
            beeswarm_chart = self._generate_beeswarm_chart(shap_values, X_sample)
            
            return {
                "success": True,
                "feature_importance": feature_importance[:20],
                "summary_chart": summary_chart,
                "beeswarm_chart": beeswarm_chart
            }
            
        except Exception as e:
            logger.error(f"Global importance error: {e}")
            return {"error": str(e)}
    
    def _generate_waterfall_chart(self, shap_values: np.ndarray, 
                                   feature_values: np.ndarray, 
                                   base_value: float) -> Optional[str]:
        """Generate SHAP waterfall chart for single prediction"""
        try:
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Sort by absolute value
            indices = np.argsort(np.abs(shap_values))[::-1][:12]  # Top 12
            
            sorted_shap = shap_values[indices]
            sorted_names = [f"{self.feature_names[i][:20]} = {feature_values[i]:.2g}" 
                           for i in indices]
            
            # Calculate cumulative values
            cumsum = np.cumsum(sorted_shap)
            
            # Colors: green for positive, red for negative
            colors = ['#10B981' if v > 0 else '#EF4444' for v in sorted_shap]
            
            # Create waterfall
            y_pos = np.arange(len(sorted_shap))
            bars = ax.barh(y_pos, sorted_shap, color=colors, edgecolor='white', height=0.7)
            
            # Add base value annotation
            final_value = base_value + sum(shap_values)
            ax.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
            
            ax.set_yticks(y_pos)
            ax.set_yticklabels(sorted_names, fontsize=9)
            ax.set_xlabel('SHAP Value (impact on prediction)', fontsize=11)
            ax.set_title(f'🔍 Prediction Explanation\nBase: {base_value:.3f} → Final: {final_value:.3f}', 
                        fontsize=12, pad=10)
            
            # Add value labels
            for bar, val in zip(bars, sorted_shap):
                width = bar.get_width()
                ax.text(width + 0.01, bar.get_y() + bar.get_height()/2,
                       f'{val:+.3f}', va='center', fontsize=8,
                       color='#10B981' if val > 0 else '#EF4444')
            
            ax.invert_yaxis()
            plt.tight_layout()
            
            return _fig_to_base64(fig)
            
        except Exception as e:
            logger.warning(f"Waterfall chart error: {e}")
            return None
    
    def _generate_summary_chart(self, shap_values: np.ndarray, X: np.ndarray) -> Optional[str]:
        """Generate SHAP summary bar chart"""
        try:
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Mean absolute SHAP values
            importance = np.abs(shap_values).mean(axis=0)
            indices = np.argsort(importance)[::-1][:15]  # Top 15
            
            sorted_importance = importance[indices]
            sorted_names = [self.feature_names[i][:25] for i in indices]
            
            # Gradient colors
            colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(sorted_importance)))[::-1]
            
            y_pos = np.arange(len(sorted_importance))
            bars = ax.barh(y_pos, sorted_importance, color=colors, edgecolor='white', height=0.7)
            
            ax.set_yticks(y_pos)
            ax.set_yticklabels(sorted_names, fontsize=10)
            ax.set_xlabel('Mean |SHAP Value|', fontsize=11)
            ax.set_title('📊 Global Feature Importance (SHAP)', fontsize=13, pad=10)
            
            # Add value labels
            for bar, val in zip(bars, sorted_importance):
                ax.text(bar.get_width() + 0.002, bar.get_y() + bar.get_height()/2,
                       f'{val:.3f}', va='center', fontsize=9)
            
            ax.invert_yaxis()
            plt.tight_layout()
            
            return _fig_to_base64(fig)
            
        except Exception as e:
            logger.warning(f"Summary chart error: {e}")
            return None
    
    def _generate_beeswarm_chart(self, shap_values: np.ndarray, X: np.ndarray) -> Optional[str]:
        """Generate SHAP beeswarm plot showing feature value distributions"""
        try:
            if not HAS_SHAP:
                return None
                
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Use shap's built-in summary plot
            shap.summary_plot(shap_values, X, 
                             feature_names=self.feature_names,
                             max_display=15,
                             show=False,
                             plot_size=None)
            
            plt.title('🐝 SHAP Beeswarm (Feature Impact Distribution)', fontsize=12, pad=10)
            plt.tight_layout()
            
            # Get current figure
            fig = plt.gcf()
            return _fig_to_base64(fig)
            
        except Exception as e:
            logger.warning(f"Beeswarm chart error: {e}")
            return None


def explain_model(model, X_train: np.ndarray, X_explain: np.ndarray, 
                  feature_names: List[str] = None) -> Dict[str, Any]:
    """
    Convenience function to explain a model.
    
    Args:
        model: Trained model
        X_train: Training data (for background)
        X_explain: Data to explain (single sample or multiple)
        feature_names: Optional feature names
        
    Returns:
        Dictionary with explanations and charts
    """
    explainer = SHAPExplainer(model, X_train, feature_names)
    
    result = {}
    
    # Global importance
    global_exp = explainer.get_global_importance()
    if global_exp.get("success"):
        result["global"] = global_exp
    
    # Single prediction explanation
    if X_explain is not None:
        local_exp = explainer.explain_prediction(X_explain)
        if local_exp.get("success"):
            result["local"] = local_exp
    
    return result
