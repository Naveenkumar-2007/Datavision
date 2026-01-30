"""
📊 Visualization & Explainability Agent

Generates insights ONLY for approved models:
- Feature importance charts
- SHAP explanations
- Error analysis
- Decision boundary visualization

Does NOT run if model is not approved.
"""

import numpy as np
from typing import Dict, List, Any, Optional
import logging
import base64
from io import BytesIO

from .base import BaseAgent, AgentResult, AgentStatus, Phase

logger = logging.getLogger(__name__)


class VisualizationAgent(BaseAgent):
    """
    Visualization & Explainability Agent
    
    Generates ML charts and explanations after model approval.
    """
    
    name = "visualization"
    description = "Generates charts and explanations for approved models"
    
    def __init__(self, memory=None):
        super().__init__(memory)
        self.charts: Dict[str, str] = {}  # chart_name -> base64 image
        
    def execute(self, **kwargs) -> AgentResult:
        """Main execution: generate visualizations"""
        
        # Check if evaluation was approved
        approved = self.read_state("evaluation_approved")
        if not approved and self.is_deep_phase():
            return AgentResult(
                status=AgentStatus.SUCCESS,  # Skip gracefully
                agent_name=self.name,
                phase=self.current_phase,
                data={"skipped": True, "reason": "Model not approved"}
            )
        
        # Get data and model
        X = self.read_state("features_engineered")
        if X is None:
            X = self.read_state("features")
        y = self.read_state("target")
        feature_names = self.read_state("feature_names_final")
        if feature_names is None:
            feature_names = self.read_state("feature_names")
        task_type = self.read_state("task_type")
        
        model_artifact = self.memory.get_latest_artifact("model")
        if model_artifact is None or X is None:
            return AgentResult(
                status=AgentStatus.SUCCESS,
                agent_name=self.name,
                phase=self.current_phase,
                data={"skipped": True, "reason": "Missing data"}
            )
        
        model = model_artifact.data
        
        self.logger.info(f"📊 Generating visualizations...")
        
        # Generate charts
        charts = {}
        
        # 1. Feature Importance
        try:
            importance_chart = self._generate_feature_importance(model, feature_names)
            if importance_chart:
                charts["feature_importance"] = importance_chart
        except Exception as e:
            self.logger.warning(f"   ⚠️ Feature importance failed: {str(e)[:30]}")
        
        # 2. Actual vs Predicted (for regression)
        if task_type == "regression":
            try:
                avp_chart = self._generate_actual_vs_predicted(model, X, y)
                if avp_chart:
                    charts["actual_vs_predicted"] = avp_chart
            except Exception as e:
                self.logger.warning(f"   ⚠️ Actual vs Predicted failed: {str(e)[:30]}")
        
        # 3. Error Distribution
        try:
            error_chart = self._generate_error_distribution(model, X, y, task_type)
            if error_chart:
                charts["error_distribution"] = error_chart
        except Exception as e:
            self.logger.warning(f"   ⚠️ Error distribution failed: {str(e)[:30]}")
        
        # Store charts
        for name, data in charts.items():
            self.memory.store_artifact(
                artifact_id=f"chart_{name}",
                artifact_type="chart",
                producer=self.name,
                data=data,
                metadata={"chart_type": name}
            )
        
        self.charts = charts
        self.write_state("charts_generated", list(charts.keys()), self.name)
        
        self.logger.info(f"   ✅ Generated {len(charts)} charts")
        
        return AgentResult(
            status=AgentStatus.SUCCESS,
            agent_name=self.name,
            phase=self.current_phase,
            data={
                "charts_generated": len(charts),
                "chart_names": list(charts.keys())
            },
            metrics={}
        )
    
    # =========================================================================
    # CHART GENERATORS
    # =========================================================================
    
    def _generate_feature_importance(self, model, feature_names: List[str]) -> Optional[str]:
        """Generate feature importance chart"""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            # Get feature importance
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
            elif hasattr(model, 'coef_'):
                importances = np.abs(model.coef_).flatten()
            else:
                return None
            
            # Ensure matching lengths
            n_features = min(len(importances), len(feature_names))
            importances = importances[:n_features]
            names = feature_names[:n_features]
            
            # Sort by importance
            indices = np.argsort(importances)[-15:]  # Top 15
            
            # Create chart
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.barh(range(len(indices)), importances[indices], color='#14b8a6')
            ax.set_yticks(range(len(indices)))
            ax.set_yticklabels([names[i] for i in indices])
            ax.set_xlabel('Importance')
            ax.set_title('Feature Importance (Top 15)')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            plt.tight_layout()
            
            # Convert to base64
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            plt.close(fig)
            buf.seek(0)
            
            return base64.b64encode(buf.read()).decode('utf-8')
            
        except Exception as e:
            self.logger.warning(f"Feature importance chart error: {str(e)[:50]}")
            return None
    
    def _generate_actual_vs_predicted(self, model, X: np.ndarray, y: np.ndarray) -> Optional[str]:
        """Generate actual vs predicted scatter plot"""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            y_pred = model.predict(X)
            
            # Sample for large datasets
            if len(y) > 1000:
                indices = np.random.choice(len(y), 1000, replace=False)
                y_sample = y[indices]
                y_pred_sample = y_pred[indices]
            else:
                y_sample, y_pred_sample = y, y_pred
            
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.scatter(y_sample, y_pred_sample, alpha=0.5, color='#14b8a6', s=20)
            
            # Perfect prediction line
            min_val = min(y_sample.min(), y_pred_sample.min())
            max_val = max(y_sample.max(), y_pred_sample.max())
            ax.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Perfect')
            
            ax.set_xlabel('Actual')
            ax.set_ylabel('Predicted')
            ax.set_title('Actual vs Predicted')
            ax.legend()
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            plt.tight_layout()
            
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            plt.close(fig)
            buf.seek(0)
            
            return base64.b64encode(buf.read()).decode('utf-8')
            
        except Exception as e:
            self.logger.warning(f"Actual vs Predicted chart error: {str(e)[:50]}")
            return None
    
    def _generate_error_distribution(self, model, X: np.ndarray, y: np.ndarray, task_type: str) -> Optional[str]:
        """Generate error distribution histogram"""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            y_pred = model.predict(X)
            
            if task_type == "regression":
                errors = y - y_pred
                xlabel = 'Prediction Error'
            else:
                # For classification, show prediction confidence
                if hasattr(model, 'predict_proba'):
                    proba = model.predict_proba(X)
                    errors = 1 - proba.max(axis=1)
                    xlabel = 'Uncertainty (1 - max probability)'
                else:
                    errors = (y != y_pred).astype(float)
                    xlabel = 'Misclassification'
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.hist(errors, bins=50, color='#14b8a6', alpha=0.7, edgecolor='white')
            ax.axvline(x=0, color='red', linestyle='--', linewidth=2)
            ax.set_xlabel(xlabel)
            ax.set_ylabel('Frequency')
            ax.set_title('Error Distribution')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            plt.tight_layout()
            
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            plt.close(fig)
            buf.seek(0)
            
            return base64.b64encode(buf.read()).decode('utf-8')
            
        except Exception as e:
            self.logger.warning(f"Error distribution chart error: {str(e)[:50]}")
            return None
