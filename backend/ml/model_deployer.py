"""
Model Deployer — One-Click ML Model Deployment
================================================
Manages deployment lifecycle: deploy, predict, undeploy, status.
Uses a JSON file registry for deployments and caches loaded engines in memory.
"""

import json
import uuid
import time
import datetime
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from ml.model_persistence import get_model_persistence_manager
from ml.automl_engine import ProductionMLEngine

logger = logging.getLogger(__name__)


class ModelDeployer:
    """Manages one-click deployment of trained ML models"""

    def __init__(self, storage_dir: str = "storage/deployments"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path = self.storage_dir / "registry.json"

        # Load registry
        self.registry = self._load_registry()

        # Cache for loaded engines
        self._engines: Dict[str, ProductionMLEngine] = {}

    # =========================================================================
    # Registry I/O
    # =========================================================================

    def _load_registry(self) -> Dict[str, Any]:
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_registry(self):
        with open(self.registry_path, 'w') as f:
            json.dump(self.registry, f, indent=2)

    # =========================================================================
    # Engine Loading (single source of truth)
    # =========================================================================

    def _load_engine(self, state: Dict[str, Any]) -> ProductionMLEngine:
        """
        Hydrate a ProductionMLEngine from a persisted model state dict.
        This is the ONLY place engine fields are assigned — no duplication.
        """
        engine = ProductionMLEngine()
        engine.model = state.get('model')
        engine.model_name = state.get('model_name', 'Unknown Model')
        engine.task_type = state.get('task_type', 'unknown')
        engine.task_type_simple = (
            'classification' if 'classification' in engine.task_type else 'regression'
        )
        engine.feature_columns = state.get('feature_columns', [])
        engine.target_column = state.get('target_column', '')
        engine.label_encoders = state.get('label_encoders', {})
        engine.scaler = state.get('scaler')
        engine.numeric_cols = state.get('numeric_cols', [])
        engine.categorical_cols = state.get('categorical_cols', [])
        return engine

    def _get_or_load_engine(self, deploy_id: str) -> ProductionMLEngine:
        """Get engine from cache, or load from persistence."""
        if deploy_id in self._engines:
            return self._engines[deploy_id]

        deployment = self.registry.get(deploy_id)
        if not deployment:
            raise ValueError(f"Deployment {deploy_id} not found")

        pm = get_model_persistence_manager()
        state = pm.load_model(deployment["user_id"], version=deployment.get("version"))
        if not state:
            raise ValueError("Underlying model data lost — cannot load engine")

        engine = self._load_engine(state)
        self._engines[deploy_id] = engine
        return engine

    # =========================================================================
    # Deploy / Undeploy
    # =========================================================================

    def deploy_model(self, user_id: str, version: Optional[int] = None) -> Dict[str, Any]:
        """Deploy a user's model and return deployment metadata."""
        pm = get_model_persistence_manager()

        # Verify model exists
        state = pm.load_model(user_id, version=version)
        if not state:
            raise ValueError(
                f"No model found for user {user_id}"
                + (f" (version {version})" if version else "")
            )

        model_name = state.get('model_name', 'Unknown Model')
        task_type = state.get('task_type', 'unknown')

        # Generate deploy ID and API key
        deploy_id = f"deploy_{uuid.uuid4().hex[:8]}"
        api_key = f"dv_{uuid.uuid4().hex}"

        deployment = {
            "deploy_id": deploy_id,
            "user_id": user_id,
            "version": version,
            "model_name": model_name,
            "task_type": task_type,
            "created_at": datetime.datetime.now().isoformat(),
            "status": "active",
            "api_key": api_key,
            "endpoint": f"/api/v1/deploy/predict/{deploy_id}",
            "request_count": 0,
        }

        self.registry[deploy_id] = deployment
        self._save_registry()

        # Pre-load engine into cache
        self._engines[deploy_id] = self._load_engine(state)
        logger.info(f"Deployed model '{model_name}' as {deploy_id} for user {user_id}")

        return deployment

    def undeploy(self, deploy_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Deactivate a deployment. Optionally verify ownership via user_id."""
        if deploy_id not in self.registry:
            raise ValueError(f"Deployment {deploy_id} not found")

        deployment = self.registry[deploy_id]

        if user_id and deployment["user_id"] != user_id:
            raise ValueError("You do not own this deployment")

        deployment["status"] = "inactive"
        deployment["deactivated_at"] = datetime.datetime.now().isoformat()
        self._save_registry()

        # Evict from engine cache
        self._engines.pop(deploy_id, None)
        logger.info(f"Undeployed {deploy_id}")

        return {"deploy_id": deploy_id, "status": "inactive"}

    # =========================================================================
    # Query
    # =========================================================================

    def list_deployments(self, user_id: str) -> List[Dict[str, Any]]:
        return [d for d in self.registry.values() if d["user_id"] == user_id]

    def get_deployment_status(self, deploy_id: str) -> Dict[str, Any]:
        """Return health / metadata for a single deployment."""
        if deploy_id not in self.registry:
            raise ValueError(f"Deployment {deploy_id} not found")

        deployment = self.registry[deploy_id]

        # Check if engine is cached (warm) or needs loading (cold)
        engine_loaded = deploy_id in self._engines

        return {
            "deploy_id": deploy_id,
            "status": deployment.get("status", "unknown"),
            "model_name": deployment.get("model_name"),
            "task_type": deployment.get("task_type"),
            "created_at": deployment.get("created_at"),
            "request_count": deployment.get("request_count", 0),
            "engine_loaded": engine_loaded,
            "endpoint": deployment.get("endpoint"),
        }

    # =========================================================================
    # Inference
    # =========================================================================

    def predict(self, deploy_id: str, data: Dict[str, Any], api_key: str = None) -> Dict[str, Any]:
        """Run inference against a deployed model."""
        if deploy_id not in self.registry:
            raise ValueError(f"Deployment {deploy_id} not found")

        deployment = self.registry[deploy_id]

        if deployment.get("status") != "active":
            raise ValueError(f"Deployment {deploy_id} is not active (status: {deployment.get('status')})")

        # Simple API key auth
        if api_key and deployment["api_key"] != api_key:
            raise ValueError("Invalid API key")

        engine = self._get_or_load_engine(deploy_id)

        start_time = time.time()
        try:
            result = engine.predict(data)
            duration_ms = (time.time() - start_time) * 1000

            # Increment request counter
            deployment["request_count"] = deployment.get("request_count", 0) + 1
            self._save_registry()

            # Log telemetry
            try:
                from ml.model_monitor import ModelMonitor
                ModelMonitor.log_inference(deploy_id, data, duration_ms)
            except Exception as e:
                logger.debug(f"Telemetry logging skipped: {e}")

            return result
        except Exception as e:
            raise ValueError(f"Prediction error: {str(e)}")


# =============================================================================
# Singleton
# =============================================================================

_deployer = None


def get_model_deployer() -> ModelDeployer:
    global _deployer
    if _deployer is None:
        _deployer = ModelDeployer()
    return _deployer
