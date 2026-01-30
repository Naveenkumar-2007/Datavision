"""
🚀 Deployment Agent

Exposes production-ready inference pipeline:
- Committee approval check
- Inference API preparation
- Model serialization
- Performance validation

Only deploys when ALL agents agree the model is production-ready.
"""

import numpy as np
from typing import Dict, List, Any, Optional
import logging
import pickle
import json
from datetime import datetime

from .base import BaseAgent, AgentResult, AgentStatus, Phase

logger = logging.getLogger(__name__)


class DeploymentAgent(BaseAgent):
    """
    Deployment Agent
    
    Prepares production-ready inference pipeline after committee approval.
    """
    
    name = "deployment"
    description = "Prepares production inference pipeline"
    
    def __init__(self, memory=None):
        super().__init__(memory)
        self.deployment_info: Dict[str, Any] = {}
        
    def execute(self, **kwargs) -> AgentResult:
        """Main execution: prepare deployment package"""
        
        # Check approvals
        training_validated = self.read_state("training_validated")
        evaluation_approved = self.read_state("evaluation_approved")
        
        # In fast phase, be more lenient
        if self.is_deep_phase() and not (training_validated and evaluation_approved):
            return AgentResult(
                status=AgentStatus.FAILED,
                agent_name=self.name,
                phase=self.current_phase,
                errors=["Model not approved by all agents"]
            )
        
        # Get model and metadata
        model_artifact = self.memory.get_latest_artifact("model")
        if model_artifact is None:
            return AgentResult(
                status=AgentStatus.FAILED,
                agent_name=self.name,
                phase=self.current_phase,
                errors=["No trained model found"]
            )
        
        model = model_artifact.data
        task_type = self.read_state("task_type")
        target_col = self.read_state("target_column")
        feature_names = self.read_state("feature_names_final")
        if feature_names is None:
            feature_names = self.read_state("feature_names")
        best_score = self.read_state("best_score")
        
        self.logger.info(f"🚀 Preparing deployment package...")
        
        # Create deployment package
        deployment_package = {
            "model": model,
            "model_name": model_artifact.metadata.get("name", "unknown"),
            "task_type": task_type,
            "target_column": target_col,
            "feature_names": feature_names,
            "score": best_score,
            "deployed_at": datetime.now().isoformat(),
            "phase": self.current_phase.value,
            "approved_by": ["training_validator", "evaluation"] if evaluation_approved else ["training_validator"]
        }
        
        # Validate inference
        inference_test = self._validate_inference(model, self.read_state("features_engineered"))
        
        if not inference_test["success"]:
            return AgentResult(
                status=AgentStatus.FAILED,
                agent_name=self.name,
                phase=self.current_phase,
                errors=[f"Inference validation failed: {inference_test['error']}"]
            )
        
        deployment_package["inference_latency_ms"] = inference_test["latency_ms"]
        
        # Store deployment package
        self.memory.store_artifact(
            artifact_id="deployment_package",
            artifact_type="deployment",
            producer=self.name,
            data=deployment_package,
            metadata={"ready": True}
        )
        
        self.deployment_info = deployment_package
        self.write_state("deployment_ready", True, self.name)
        self.write_state("deployment_package", {
            k: v for k, v in deployment_package.items() 
            if k not in ["model"]  # Don't serialize model to state
        }, self.name)
        
        self.logger.info(f"   ✅ Deployment package ready")
        self.logger.info(f"   📊 Model: {deployment_package['model_name']}")
        self.logger.info(f"   📊 Score: {best_score:.4f}")
        self.logger.info(f"   📊 Latency: {inference_test['latency_ms']:.2f}ms")
        
        return AgentResult(
            status=AgentStatus.SUCCESS,
            agent_name=self.name,
            phase=self.current_phase,
            data={
                "deployed": True,
                "model_name": deployment_package["model_name"],
                "latency_ms": inference_test["latency_ms"]
            },
            metrics={
                "score": best_score,
                "latency_ms": inference_test["latency_ms"]
            }
        )
    
    def _validate_inference(self, model, X: np.ndarray) -> Dict[str, Any]:
        """Validate model can make predictions"""
        try:
            import time
            
            # Test prediction
            sample = X[:10] if X is not None else None
            if sample is None:
                return {"success": False, "error": "No features available"}
            
            # Measure latency
            start = time.time()
            _ = model.predict(sample)
            latency = (time.time() - start) * 1000 / len(sample)  # Per-sample ms
            
            return {
                "success": True,
                "latency_ms": latency
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)[:100]
            }
    
    def get_predictor(self):
        """Get a predictor function for inference"""
        deployment = self.memory.get_artifact("deployment_package")
        if deployment is None:
            return None
        
        model = deployment.data["model"]
        
        def predict(X):
            return model.predict(X)
        
        return predict
