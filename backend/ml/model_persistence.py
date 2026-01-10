"""
🗄️ MODEL PERSISTENCE MANAGER - Per-User AutoML Model Storage
==============================================================

Provides persistent storage for trained ML models with:
- Per-user model isolation
- Model versioning
- Metadata tracking (training date, metrics, features)
- Model listing and management
- Auto-save after training
- Auto-load for predictions
"""

import os
import pickle
import json
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Base storage path
MODELS_STORAGE_PATH = Path("./storage/models")


class ModelMetadata:
    """Metadata for a saved model"""
    def __init__(
        self,
        model_id: str,
        user_id: str,
        model_name: str,
        task_type: str,
        target_column: str,
        feature_columns: List[str],
        metrics: Dict[str, float],
        training_date: str,
        dataset_info: Dict[str, Any],
        version: int = 1,
        is_active: bool = True
    ):
        self.model_id = model_id
        self.user_id = user_id
        self.model_name = model_name
        self.task_type = task_type
        self.target_column = target_column
        self.feature_columns = feature_columns
        self.metrics = metrics
        self.training_date = training_date
        self.dataset_info = dataset_info
        self.version = version
        self.is_active = is_active
    
    def to_dict(self) -> Dict:
        return {
            "model_id": self.model_id,
            "user_id": self.user_id,
            "model_name": self.model_name,
            "task_type": self.task_type,
            "target_column": self.target_column,
            "feature_columns": self.feature_columns,
            "metrics": self.metrics,
            "training_date": self.training_date,
            "dataset_info": self.dataset_info,
            "version": self.version,
            "is_active": self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ModelMetadata':
        return cls(**data)


class ModelPersistenceManager:
    """
    🗄️ Manages persistent storage of ML models per user.
    
    Directory Structure:
    ./storage/models/
    └── {user_id}/
        ├── active_model.pkl      # Currently active model
        ├── active_metadata.json  # Metadata for active model
        └── history/
            ├── model_v1.pkl
            ├── model_v1_metadata.json
            ├── model_v2.pkl
            └── model_v2_metadata.json
    """
    
    def __init__(self, base_path: Path = MODELS_STORAGE_PATH):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Model Persistence Manager initialized at: {self.base_path}")
    
    def _get_user_dir(self, user_id: str) -> Path:
        """Get user-specific model directory"""
        user_dir = self.base_path / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    
    def _get_history_dir(self, user_id: str) -> Path:
        """Get user's model history directory"""
        history_dir = self._get_user_dir(user_id) / "history"
        history_dir.mkdir(parents=True, exist_ok=True)
        return history_dir
    
    def save_model(
        self,
        user_id: str,
        engine_state: Dict[str, Any],
        model_name: str,
        task_type: str,
        target_column: str,
        feature_columns: List[str],
        metrics: Dict[str, float],
        dataset_info: Dict[str, Any]
    ) -> ModelMetadata:
        """
        Save a trained model for a user.
        
        Args:
            user_id: User identifier
            engine_state: Complete state of the ML engine (model, encoders, scalers, etc.)
            model_name: Name of the best model
            task_type: classification/regression
            target_column: Target column name
            feature_columns: List of feature column names
            metrics: Model performance metrics
            dataset_info: Info about the training dataset
        
        Returns:
            ModelMetadata object
        """
        try:
            user_dir = self._get_user_dir(user_id)
            history_dir = self._get_history_dir(user_id)
            
            # Get next version number
            version = self._get_next_version(user_id)
            
            # Generate model ID
            model_id = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_v{version}"
            
            # Create metadata
            metadata = ModelMetadata(
                model_id=model_id,
                user_id=user_id,
                model_name=model_name,
                task_type=task_type,
                target_column=target_column,
                feature_columns=feature_columns,
                metrics=metrics,
                training_date=datetime.now().isoformat(),
                dataset_info=dataset_info,
                version=version,
                is_active=True
            )
            
            # Archive current active model if exists
            active_model_path = user_dir / "active_model.pkl"
            if active_model_path.exists():
                old_version = version - 1
                if old_version > 0:
                    shutil.copy(
                        active_model_path,
                        history_dir / f"model_v{old_version}.pkl"
                    )
                    old_meta_path = user_dir / "active_metadata.json"
                    if old_meta_path.exists():
                        shutil.copy(
                            old_meta_path,
                            history_dir / f"model_v{old_version}_metadata.json"
                        )
            
            # Save new model as active
            with open(active_model_path, 'wb') as f:
                pickle.dump(engine_state, f)
            
            # Save metadata
            with open(user_dir / "active_metadata.json", 'w') as f:
                json.dump(metadata.to_dict(), f, indent=2, default=str)
            
            logger.info(f"✅ Model saved for user {user_id}: {model_name} (v{version})")
            logger.info(f"   📊 Metrics: {metrics}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"❌ Failed to save model for {user_id}: {e}")
            raise
    
    def load_model(self, user_id: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Load a saved model for a user.
        
        Args:
            user_id: User identifier
            version: Specific version to load (None = active model)
        
        Returns:
            Engine state dict or None if not found
        """
        try:
            user_dir = self._get_user_dir(user_id)
            
            if version is None:
                # Load active model
                model_path = user_dir / "active_model.pkl"
            else:
                # Load specific version from history
                model_path = self._get_history_dir(user_id) / f"model_v{version}.pkl"
            
            if not model_path.exists():
                logger.warning(f"⚠️ No model found for user {user_id}")
                return None
            
            with open(model_path, 'rb') as f:
                engine_state = pickle.load(f)
            
            logger.info(f"✅ Loaded model for user {user_id}")
            return engine_state
            
        except Exception as e:
            logger.error(f"❌ Failed to load model for {user_id}: {e}")
            return None
    
    def get_metadata(self, user_id: str, version: Optional[int] = None) -> Optional[ModelMetadata]:
        """Get metadata for a user's model"""
        try:
            user_dir = self._get_user_dir(user_id)
            
            if version is None:
                meta_path = user_dir / "active_metadata.json"
            else:
                meta_path = self._get_history_dir(user_id) / f"model_v{version}_metadata.json"
            
            if not meta_path.exists():
                return None
            
            with open(meta_path, 'r') as f:
                data = json.load(f)
            
            return ModelMetadata.from_dict(data)
            
        except Exception as e:
            logger.error(f"❌ Failed to load metadata for {user_id}: {e}")
            return None
    
    def list_models(self, user_id: str) -> List[ModelMetadata]:
        """List all models for a user (active + history)"""
        models = []
        
        try:
            # Get active model
            active_meta = self.get_metadata(user_id)
            if active_meta:
                models.append(active_meta)
            
            # Get historical models
            history_dir = self._get_history_dir(user_id)
            for meta_file in sorted(history_dir.glob("model_v*_metadata.json")):
                with open(meta_file, 'r') as f:
                    data = json.load(f)
                    data['is_active'] = False
                    models.append(ModelMetadata.from_dict(data))
            
            # Sort by version (newest first)
            models.sort(key=lambda m: m.version, reverse=True)
            
        except Exception as e:
            logger.error(f"❌ Failed to list models for {user_id}: {e}")
        
        return models
    
    def delete_model(self, user_id: str, version: Optional[int] = None) -> bool:
        """Delete a specific model version or all models for a user"""
        try:
            if version is None:
                # Delete all models for user
                user_dir = self._get_user_dir(user_id)
                if user_dir.exists():
                    shutil.rmtree(user_dir)
                    logger.info(f"🗑️ Deleted all models for user {user_id}")
                    return True
            else:
                # Delete specific version
                history_dir = self._get_history_dir(user_id)
                model_path = history_dir / f"model_v{version}.pkl"
                meta_path = history_dir / f"model_v{version}_metadata.json"
                
                deleted = False
                if model_path.exists():
                    model_path.unlink()
                    deleted = True
                if meta_path.exists():
                    meta_path.unlink()
                    deleted = True
                
                if deleted:
                    logger.info(f"🗑️ Deleted model v{version} for user {user_id}")
                return deleted
                
        except Exception as e:
            logger.error(f"❌ Failed to delete model: {e}")
            return False
    
    def rollback_to_version(self, user_id: str, version: int) -> bool:
        """Rollback to a previous model version"""
        try:
            user_dir = self._get_user_dir(user_id)
            history_dir = self._get_history_dir(user_id)
            
            # Check if version exists
            old_model = history_dir / f"model_v{version}.pkl"
            old_meta = history_dir / f"model_v{version}_metadata.json"
            
            if not old_model.exists():
                logger.warning(f"⚠️ Version {version} not found for user {user_id}")
                return False
            
            # Copy historical version to active
            shutil.copy(old_model, user_dir / "active_model.pkl")
            if old_meta.exists():
                shutil.copy(old_meta, user_dir / "active_metadata.json")
            
            logger.info(f"✅ Rolled back to v{version} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to rollback: {e}")
            return False
    
    def _get_next_version(self, user_id: str) -> int:
        """Get the next version number for a user"""
        metadata = self.get_metadata(user_id)
        if metadata:
            return metadata.version + 1
        return 1
    
    def has_model(self, user_id: str) -> bool:
        """Check if user has a trained model"""
        user_dir = self._get_user_dir(user_id)
        return (user_dir / "active_model.pkl").exists()
    
    def get_all_users_with_models(self) -> List[str]:
        """Get list of all user IDs that have trained models"""
        users = []
        if self.base_path.exists():
            for user_dir in self.base_path.iterdir():
                if user_dir.is_dir() and (user_dir / "active_model.pkl").exists():
                    users.append(user_dir.name)
        return users


# Global instance
model_persistence = ModelPersistenceManager()
