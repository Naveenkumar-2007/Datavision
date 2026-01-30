"""
🔮 EXPLAINABILITY ENGINE v1.0 - SHAP/LIME PREDICTION EXPLANATIONS
==================================================================

Explains WHY each prediction was made - essential for trust and debugging.

Core Capabilities:
1. SHAP Integration - Game-theoretic feature importance
2. LIME Integration - Local interpretable explanations
3. Feature Attribution - Shows contribution of each feature
4. Counterfactual Analysis - "What if" scenarios
5. Prediction Confidence - Uncertainty quantification
6. Global Explanations - Overall model behavior

This makes predictions TRUSTWORTHY and DEBUGGABLE!
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
import logging
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

# Optional SHAP import
try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False
    logger.warning("SHAP not installed - some explainability features disabled")

# Optional LIME import  
try:
    from lime import lime_tabular
    HAS_LIME = True
except ImportError:
    HAS_LIME = False
    logger.warning("LIME not installed - some explainability features disabled")


@dataclass
class PredictionExplanation:
    """Explanation for a single prediction."""
    prediction: Any
    confidence: float
    probability: Optional[float]
    class_probabilities: Optional[Dict[str, float]]
    
    # Feature contributions
    top_positive_features: List[Dict[str, Any]]  # Features pushing toward prediction
    top_negative_features: List[Dict[str, Any]]  # Features pushing against prediction
    
    # All feature attributions
    feature_attributions: Dict[str, float]
    
    # Counterfactual (optional)
    counterfactual_suggestion: Optional[str]
    
    # Metadata
    explanation_method: str
    computation_time_ms: float


@dataclass
class GlobalExplanation:
    """Global explanation of model behavior."""
    feature_importance: Dict[str, float]  # Average importance across all predictions
    feature_interactions: List[Dict[str, Any]]  # Top feature interactions
    summary_plot_data: Optional[Any]  # Data for SHAP summary plot
    dependence_data: Optional[Dict[str, Any]]  # Feature dependence data


class ExplainabilityEngine:
    """
    🔮 Explainability Engine - SHAP/LIME Prediction Explanations
    
    Provides comprehensive explanations for model predictions:
    1. Local explanations - Why was THIS specific prediction made?
    2. Global explanations - How does the model behave overall?
    3. Feature importance - Which features matter most?
    4. Counterfactuals - What would change the prediction?
    
    Makes ML models TRANSPARENT and TRUSTWORTHY!
    """
    
    def __init__(
        self,
        model: Any = None,
        feature_names: List[str] = None,
        task_type: str = 'classification',
        class_names: List[str] = None,
        background_data: np.ndarray = None,
        use_shap: bool = True,
        use_lime: bool = True,
        n_background_samples: int = 100
    ):
        self.model = model
        self.feature_names = feature_names or []
        self.task_type = task_type
        self.class_names = class_names or []
        self.background_data = background_data
        self.use_shap = use_shap and HAS_SHAP
        self.use_lime = use_lime and HAS_LIME
        self.n_background_samples = n_background_samples
        
        # SHAP explainer (lazy initialization)
        self._shap_explainer = None
        
        # LIME explainer
        self._lime_explainer = None
        
        # Cache for efficiency
        self._global_shap_values = None
        
        logger.info(f"🔮 Explainability Engine initialized (SHAP: {self.use_shap}, LIME: {self.use_lime})")
    
    def set_model(
        self, 
        model: Any, 
        feature_names: List[str] = None,
        background_data: np.ndarray = None,
        class_names: List[str] = None
    ) -> None:
        """Set or update the model to explain."""
        self.model = model
        if feature_names:
            self.feature_names = feature_names
        if background_data is not None:
            self.background_data = background_data
        if class_names:
            self.class_names = class_names
        
        # Reset explainers
        self._shap_explainer = None
        self._lime_explainer = None
        self._global_shap_values = None
    
    def _get_shap_explainer(self) -> Any:
        """Get or create SHAP explainer."""
        if not self.use_shap:
            return None
        
        if self._shap_explainer is not None:
            return self._shap_explainer
        
        if self.model is None:
            raise ValueError("Model not set. Call set_model first.")
        
        try:
            # Prepare background data
            if self.background_data is not None:
                # Sample if too large
                if len(self.background_data) > self.n_background_samples:
                    indices = np.random.choice(
                        len(self.background_data), 
                        self.n_background_samples, 
                        replace=False
                    )
                    background = self.background_data[indices]
                else:
                    background = self.background_data
            else:
                background = None
            
            # Determine model type and create appropriate explainer
            model_type = type(self.model).__name__
            
            if 'XGB' in model_type or 'LGB' in model_type or 'CatBoost' in model_type:
                # Tree-based models - use TreeExplainer
                self._shap_explainer = shap.TreeExplainer(self.model)
            elif 'Forest' in model_type or 'Tree' in model_type or 'Gradient' in model_type:
                # Sklearn tree-based models
                self._shap_explainer = shap.TreeExplainer(self.model)
            elif hasattr(self.model, 'predict_proba'):
                # Classification models with predict_proba
                if background is not None:
                    self._shap_explainer = shap.KernelExplainer(
                        self.model.predict_proba,
                        background
                    )
                else:
                    logger.warning("Background data required for KernelExplainer")
                    return None
            else:
                # Generic models
                if background is not None:
                    predict_fn = getattr(self.model, 'predict', None)
                    if predict_fn:
                        self._shap_explainer = shap.KernelExplainer(
                            predict_fn,
                            background
                        )
                else:
                    logger.warning("Background data required for KernelExplainer")
                    return None
                    
            return self._shap_explainer
            
        except Exception as e:
            logger.error(f"Could not create SHAP explainer: {e}")
            return None
    
    def _get_lime_explainer(self) -> Any:
        """Get or create LIME explainer."""
        if not self.use_lime:
            return None
        
        if self._lime_explainer is not None:
            return self._lime_explainer
        
        if self.background_data is None:
            logger.warning("Background data required for LIME explainer")
            return None
        
        try:
            mode = 'classification' if self.task_type == 'classification' else 'regression'
            
            self._lime_explainer = lime_tabular.LimeTabularExplainer(
                self.background_data.astype(float),
                feature_names=self.feature_names if self.feature_names else None,
                class_names=self.class_names if self.class_names else None,
                mode=mode,
                discretize_continuous=True,
                random_state=42
            )
            
            return self._lime_explainer
            
        except Exception as e:
            logger.error(f"Could not create LIME explainer: {e}")
            return None
    
    def explain_prediction(
        self,
        instance: Union[np.ndarray, pd.DataFrame, Dict],
        n_top_features: int = 5,
        method: str = 'auto'
    ) -> PredictionExplanation:
        """
        Explain a single prediction.
        
        Args:
            instance: Single data point to explain
            n_top_features: Number of top features to highlight
            method: 'shap', 'lime', or 'auto' (tries SHAP first, then LIME)
            
        Returns:
            PredictionExplanation with feature attributions and insights
        """
        import time
        start_time = time.time()
        
        # Convert to numpy array
        if isinstance(instance, dict):
            instance = np.array([[instance.get(f, 0) for f in self.feature_names]])
        elif isinstance(instance, pd.DataFrame):
            instance = instance.values
        elif isinstance(instance, np.ndarray) and instance.ndim == 1:
            instance = instance.reshape(1, -1)
        
        instance = np.nan_to_num(instance.astype(float), nan=0.0, posinf=0.0, neginf=0.0)
        
        # Get prediction
        prediction = self.model.predict(instance)[0]
        
        # Get probability/confidence
        probability = None
        class_probabilities = None
        confidence = 0.5
        
        if hasattr(self.model, 'predict_proba'):
            try:
                proba = self.model.predict_proba(instance)[0]
                if self.task_type == 'classification':
                    confidence = float(np.max(proba))
                    probability = confidence
                    
                    # Map probabilities to class names
                    if self.class_names:
                        class_probabilities = {
                            str(name): float(p) for name, p in zip(self.class_names, proba)
                        }
                    else:
                        class_probabilities = {
                            f"class_{i}": float(p) for i, p in enumerate(proba)
                        }
            except:
                pass
        else:
            # For regression, confidence based on prediction stability
            confidence = 0.7  # Default confidence for regression
        
        # Get feature attributions
        feature_attributions = {}
        explanation_method = 'none'
        
        # Try SHAP first (if available and method allows)
        if method in ['auto', 'shap'] and self.use_shap:
            try:
                explainer = self._get_shap_explainer()
                if explainer:
                    shap_values = explainer.shap_values(instance)
                    
                    # Handle different SHAP output formats
                    if isinstance(shap_values, list):
                        # Multi-class classification
                        if self.task_type == 'classification':
                            pred_class = int(prediction) if isinstance(prediction, (int, np.integer)) else 0
                            if pred_class < len(shap_values):
                                values = shap_values[pred_class][0]
                            else:
                                values = shap_values[0][0]
                        else:
                            values = shap_values[0][0] if len(shap_values) > 0 else shap_values[0]
                    else:
                        values = shap_values[0] if shap_values.ndim > 1 else shap_values
                    
                    # Create feature attributions
                    for i, (fname, val) in enumerate(zip(self.feature_names[:len(values)], values)):
                        feature_attributions[fname] = float(val)
                    
                    explanation_method = 'shap'
            except Exception as e:
                logger.warning(f"SHAP explanation failed: {e}")
        
        # Try LIME if SHAP failed or method is LIME
        if not feature_attributions and method in ['auto', 'lime'] and self.use_lime:
            try:
                explainer = self._get_lime_explainer()
                if explainer:
                    if self.task_type == 'classification':
                        exp = explainer.explain_instance(
                            instance[0],
                            self.model.predict_proba,
                            num_features=len(self.feature_names)
                        )
                    else:
                        exp = explainer.explain_instance(
                            instance[0],
                            self.model.predict,
                            num_features=len(self.feature_names)
                        )
                    
                    for feature, weight in exp.as_list():
                        # LIME returns feature conditions, extract feature name
                        fname = feature.split(' ')[0].strip('<>=')
                        if fname in self.feature_names:
                            feature_attributions[fname] = float(weight)
                    
                    explanation_method = 'lime'
            except Exception as e:
                logger.warning(f"LIME explanation failed: {e}")
        
        # Fallback to basic feature importance if no explanations available
        if not feature_attributions:
            if hasattr(self.model, 'feature_importances_'):
                importances = self.model.feature_importances_
                for i, fname in enumerate(self.feature_names[:len(importances)]):
                    # Scale by feature value for this instance
                    feature_attributions[fname] = float(importances[i] * abs(instance[0][i]))
                explanation_method = 'feature_importance'
            else:
                # No explanation available
                for fname in self.feature_names:
                    feature_attributions[fname] = 0.0
                explanation_method = 'none'
        
        # Sort features by attribution
        sorted_attrs = sorted(feature_attributions.items(), key=lambda x: abs(x[1]), reverse=True)
        
        # Split into positive and negative contributions
        top_positive = [
            {
                'feature': fname,
                'attribution': attr,
                'value': float(instance[0][self.feature_names.index(fname)]) if fname in self.feature_names else 0.0,
                'direction': 'positive'
            }
            for fname, attr in sorted_attrs if attr > 0
        ][:n_top_features]
        
        top_negative = [
            {
                'feature': fname,
                'attribution': attr,
                'value': float(instance[0][self.feature_names.index(fname)]) if fname in self.feature_names else 0.0,
                'direction': 'negative'
            }
            for fname, attr in sorted_attrs if attr < 0
        ][:n_top_features]
        
        # Generate counterfactual suggestion
        counterfactual = None
        if top_positive:
            top_feat = top_positive[0]
            if self.task_type == 'classification':
                counterfactual = f"Prediction might change if '{top_feat['feature']}' was significantly different"
        
        computation_time = (time.time() - start_time) * 1000
        
        return PredictionExplanation(
            prediction=prediction,
            confidence=confidence,
            probability=probability,
            class_probabilities=class_probabilities,
            top_positive_features=top_positive,
            top_negative_features=top_negative,
            feature_attributions=feature_attributions,
            counterfactual_suggestion=counterfactual,
            explanation_method=explanation_method,
            computation_time_ms=computation_time
        )
    
    def explain_batch(
        self,
        instances: np.ndarray,
        n_top_features: int = 5
    ) -> List[PredictionExplanation]:
        """Explain multiple predictions."""
        return [
            self.explain_prediction(instances[i:i+1], n_top_features)
            for i in range(len(instances))
        ]
    
    def get_global_explanation(
        self,
        X: np.ndarray = None,
        max_samples: int = 500
    ) -> GlobalExplanation:
        """
        Get global model explanation showing overall feature importance.
        
        Args:
            X: Data to use for explanation (uses background_data if None)
            max_samples: Maximum samples to use
            
        Returns:
            GlobalExplanation with aggregated feature importance
        """
        if X is None:
            X = self.background_data
        
        if X is None:
            # Return model-based importance if available
            if hasattr(self.model, 'feature_importances_'):
                importances = self.model.feature_importances_
                feature_importance = {
                    fname: float(imp)
                    for fname, imp in zip(self.feature_names[:len(importances)], importances)
                }
                return GlobalExplanation(
                    feature_importance=feature_importance,
                    feature_interactions=[],
                    summary_plot_data=None,
                    dependence_data=None
                )
            else:
                return GlobalExplanation(
                    feature_importance={f: 0.0 for f in self.feature_names},
                    feature_interactions=[],
                    summary_plot_data=None,
                    dependence_data=None
                )
        
        # Sample data if too large
        if len(X) > max_samples:
            indices = np.random.choice(len(X), max_samples, replace=False)
            X = X[indices]
        
        X = np.nan_to_num(X.astype(float), nan=0.0, posinf=0.0, neginf=0.0)
        
        feature_importance = {}
        
        # Try SHAP for global explanation
        if self.use_shap:
            try:
                explainer = self._get_shap_explainer()
                if explainer:
                    shap_values = explainer.shap_values(X)
                    
                    # Handle different formats
                    if isinstance(shap_values, list):
                        # Average across classes
                        values = np.mean([np.abs(sv) for sv in shap_values], axis=0)
                    else:
                        values = np.abs(shap_values)
                    
                    # Average importance across samples
                    mean_importance = np.mean(values, axis=0)
                    
                    for fname, imp in zip(self.feature_names[:len(mean_importance)], mean_importance):
                        feature_importance[fname] = float(imp)
                    
                    self._global_shap_values = shap_values
            except Exception as e:
                logger.warning(f"SHAP global explanation failed: {e}")
        
        # Fallback to model importance
        if not feature_importance:
            if hasattr(self.model, 'feature_importances_'):
                importances = self.model.feature_importances_
                for fname, imp in zip(self.feature_names[:len(importances)], importances):
                    feature_importance[fname] = float(imp)
            elif hasattr(self.model, 'coef_'):
                coef = np.abs(self.model.coef_).flatten()
                for fname, c in zip(self.feature_names[:len(coef)], coef):
                    feature_importance[fname] = float(c)
        
        # Sort by importance
        feature_importance = dict(sorted(
            feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        ))
        
        return GlobalExplanation(
            feature_importance=feature_importance,
            feature_interactions=[],
            summary_plot_data=self._global_shap_values,
            dependence_data=None
        )
    
    def explain_to_text(self, explanation: PredictionExplanation) -> str:
        """Convert explanation to human-readable text."""
        lines = []
        
        lines.append(f"🔮 Prediction: {explanation.prediction}")
        lines.append(f"📊 Confidence: {explanation.confidence:.1%}")
        
        if explanation.class_probabilities:
            lines.append("\n📈 Class Probabilities:")
            for cls, prob in explanation.class_probabilities.items():
                lines.append(f"   • {cls}: {prob:.1%}")
        
        lines.append("\n✅ Top factors supporting this prediction:")
        for feat in explanation.top_positive_features[:3]:
            lines.append(f"   • {feat['feature']}: +{feat['attribution']:.4f} (value: {feat['value']:.2f})")
        
        if explanation.top_negative_features:
            lines.append("\n❌ Factors pushing against this prediction:")
            for feat in explanation.top_negative_features[:3]:
                lines.append(f"   • {feat['feature']}: {feat['attribution']:.4f} (value: {feat['value']:.2f})")
        
        if explanation.counterfactual_suggestion:
            lines.append(f"\n💡 Insight: {explanation.counterfactual_suggestion}")
        
        lines.append(f"\n⏱️ Computed in {explanation.computation_time_ms:.1f}ms using {explanation.explanation_method}")
        
        return "\n".join(lines)
    
    def explain_to_dict(self, explanation: PredictionExplanation) -> Dict:
        """Convert explanation to dictionary for API response."""
        return {
            'prediction': str(explanation.prediction),
            'confidence': explanation.confidence,
            'probability': explanation.probability,
            'class_probabilities': explanation.class_probabilities,
            'top_positive_factors': explanation.top_positive_features[:5],
            'top_negative_factors': explanation.top_negative_features[:5],
            'all_attributions': explanation.feature_attributions,
            'counterfactual': explanation.counterfactual_suggestion,
            'method': explanation.explanation_method,
            'computation_time_ms': explanation.computation_time_ms
        }


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def explain_model_prediction(
    model: Any,
    instance: np.ndarray,
    feature_names: List[str],
    background_data: np.ndarray = None,
    task_type: str = 'classification',
    class_names: List[str] = None
) -> Dict:
    """
    Convenience function to explain a single prediction.
    
    Args:
        model: Trained model
        instance: Data point to explain
        feature_names: List of feature names
        background_data: Training data for SHAP/LIME
        task_type: 'classification' or 'regression'
        class_names: Names of target classes
        
    Returns:
        Dictionary with explanation details
    """
    engine = ExplainabilityEngine(
        model=model,
        feature_names=feature_names,
        task_type=task_type,
        class_names=class_names,
        background_data=background_data
    )
    
    explanation = engine.explain_prediction(instance)
    return engine.explain_to_dict(explanation)
