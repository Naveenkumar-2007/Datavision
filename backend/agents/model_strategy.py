"""
🎯 Model Strategy Agent

Dynamically selects algorithms based on dataset characteristics:
- Data size (small vs large)
- Task type (classification vs regression)
- Feature types (numeric vs categorical)
- Class balance
- Dimensionality

No neural networks - traditional ML only.
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import logging

from .base import BaseAgent, AgentResult, AgentStatus, Phase

logger = logging.getLogger(__name__)


@dataclass
class ModelCandidate:
    """A candidate model for training"""
    name: str
    model_class: str
    priority: int  # Higher = try first
    params: Dict[str, Any]
    reason: str


class ModelStrategyAgent(BaseAgent):
    """
    Autonomous Model Strategy Agent
    
    Analyzes data profile → Selects suitable algorithms → Prioritizes candidates
    """
    
    name = "model_strategy"
    description = "Dynamically selects ML algorithms based on data characteristics"
    
    def __init__(self, memory=None):
        super().__init__(memory)
        self.candidates: List[ModelCandidate] = []
        
    def execute(self, **kwargs) -> AgentResult:
        """Main execution: analyze data, select models"""
        
        # Get data characteristics
        X = self.read_state("features_engineered")
        if X is None:
            X = self.read_state("features")
        
        y = self.read_state("target")
        task_type = self.read_state("task_type")
        
        if X is None or y is None:
            return AgentResult(
                status=AgentStatus.FAILED,
                agent_name=self.name,
                phase=self.current_phase,
                errors=["No features found"]
            )
        
        # Analyze data profile
        profile = self._analyze_data_profile(X, y, task_type)
        self.logger.info(f"📊 Data profile: {profile['n_samples']} samples, {profile['n_features']} features")
        
        # Select models based on phase
        if self.is_fast_phase():
            candidates = self._select_fast_models(profile, task_type)
        else:
            candidates = self._select_deep_models(profile, task_type)
        
        self.candidates = candidates
        
        # Store results
        self.write_state("model_candidates", [c.__dict__ for c in candidates], self.name)
        self.write_state("data_profile", profile, self.name)
        
        return AgentResult(
            status=AgentStatus.SUCCESS,
            agent_name=self.name,
            phase=self.current_phase,
            data={
                "n_candidates": len(candidates),
                "models": [c.name for c in candidates]
            },
            metrics={
                "candidates_selected": len(candidates)
            }
        )
    
    # =========================================================================
    # DATA PROFILING
    # =========================================================================
    
    def _analyze_data_profile(self, X: np.ndarray, y: np.ndarray, task_type: str) -> Dict[str, Any]:
        """Analyze data characteristics for model selection"""
        n_samples, n_features = X.shape
        
        profile = {
            "n_samples": n_samples,
            "n_features": n_features,
            "task_type": task_type,
            "is_small": n_samples < 1000,
            "is_large": n_samples > 50000,
            "is_high_dim": n_features > 100,
            "samples_per_feature": n_samples / max(1, n_features)
        }
        
        # Class balance for classification
        if task_type == "classification":
            unique, counts = np.unique(y, return_counts=True)
            profile["n_classes"] = len(unique)
            profile["is_imbalanced"] = max(counts) / min(counts) > 3 if min(counts) > 0 else False
        
        return profile
    
    # =========================================================================
    # FAST PHASE - Limited models
    # =========================================================================
    
    def _select_fast_models(self, profile: Dict, task_type: str) -> List[ModelCandidate]:
        """Select 3-4 fast models for quick evaluation"""
        candidates = []
        
        if task_type == "classification":
            # Always include Random Forest (robust baseline)
            candidates.append(ModelCandidate(
                name="RandomForest",
                model_class="sklearn.ensemble.RandomForestClassifier",
                priority=100,
                params={"n_estimators": 100, "max_depth": 10, "n_jobs": -1, "random_state": 42},
                reason="Robust baseline for classification"
            ))
            
            # XGBoost if available
            candidates.append(ModelCandidate(
                name="XGBoost",
                model_class="xgboost.XGBClassifier",
                priority=95,
                params={"n_estimators": 100, "max_depth": 6, "learning_rate": 0.1, "n_jobs": -1, "random_state": 42},
                reason="High performance gradient boosting"
            ))
            
            # LightGBM for large datasets
            if profile.get("is_large"):
                candidates.append(ModelCandidate(
                    name="LightGBM",
                    model_class="lightgbm.LGBMClassifier",
                    priority=90,
                    params={"n_estimators": 100, "max_depth": 6, "learning_rate": 0.1, "n_jobs": -1, "random_state": 42},
                    reason="Fast for large datasets"
                ))
            else:
                # Logistic Regression for small datasets
                candidates.append(ModelCandidate(
                    name="LogisticRegression",
                    model_class="sklearn.linear_model.LogisticRegression",
                    priority=80,
                    params={"max_iter": 1000, "random_state": 42},
                    reason="Simple baseline"
                ))
        
        else:  # Regression
            candidates.append(ModelCandidate(
                name="RandomForest",
                model_class="sklearn.ensemble.RandomForestRegressor",
                priority=100,
                params={"n_estimators": 100, "max_depth": 10, "n_jobs": -1, "random_state": 42},
                reason="Robust baseline for regression"
            ))
            
            candidates.append(ModelCandidate(
                name="XGBoost",
                model_class="xgboost.XGBRegressor",
                priority=95,
                params={"n_estimators": 100, "max_depth": 6, "learning_rate": 0.1, "n_jobs": -1, "random_state": 42},
                reason="High performance gradient boosting"
            ))
            
            candidates.append(ModelCandidate(
                name="Ridge",
                model_class="sklearn.linear_model.Ridge",
                priority=70,
                params={"alpha": 1.0, "random_state": 42},
                reason="Simple linear baseline"
            ))
        
        self.logger.info(f"   ✅ Fast mode: {len(candidates)} models selected")
        return sorted(candidates, key=lambda x: x.priority, reverse=True)
    
    # =========================================================================
    # DEEP PHASE - Full model suite
    # =========================================================================
    
    def _select_deep_models(self, profile: Dict, task_type: str) -> List[ModelCandidate]:
        """Select comprehensive set of models for thorough evaluation"""
        candidates = self._select_fast_models(profile, task_type)
        
        if task_type == "classification":
            # Add more models
            candidates.extend([
                ModelCandidate(
                    name="ExtraTrees",
                    model_class="sklearn.ensemble.ExtraTreesClassifier",
                    priority=85,
                    params={"n_estimators": 100, "max_depth": 15, "n_jobs": -1, "random_state": 42},
                    reason="Fast alternative to RF"
                ),
                ModelCandidate(
                    name="CatBoost",
                    model_class="catboost.CatBoostClassifier",
                    priority=88,
                    params={"iterations": 100, "depth": 6, "learning_rate": 0.1, "random_state": 42, "verbose": False},
                    reason="Handles categoricals natively"
                ),
                ModelCandidate(
                    name="HistGradientBoosting",
                    model_class="sklearn.ensemble.HistGradientBoostingClassifier",
                    priority=82,
                    params={"max_iter": 100, "max_depth": 6, "random_state": 42},
                    reason="Fast native sklearn boosting"
                ),
            ])
            
            if not profile.get("is_high_dim"):
                candidates.append(ModelCandidate(
                    name="SVC",
                    model_class="sklearn.svm.SVC",
                    priority=60,
                    params={"kernel": "rbf", "probability": True, "random_state": 42},
                    reason="Non-linear classification"
                ))
        
        else:  # Regression
            candidates.extend([
                ModelCandidate(
                    name="ExtraTrees",
                    model_class="sklearn.ensemble.ExtraTreesRegressor",
                    priority=85,
                    params={"n_estimators": 100, "max_depth": 15, "n_jobs": -1, "random_state": 42},
                    reason="Fast alternative to RF"
                ),
                ModelCandidate(
                    name="LightGBM",
                    model_class="lightgbm.LGBMRegressor",
                    priority=90,
                    params={"n_estimators": 100, "max_depth": 6, "learning_rate": 0.1, "n_jobs": -1, "random_state": 42},
                    reason="Fast gradient boosting"
                ),
                ModelCandidate(
                    name="CatBoost",
                    model_class="catboost.CatBoostRegressor",
                    priority=88,
                    params={"iterations": 100, "depth": 6, "learning_rate": 0.1, "random_state": 42, "verbose": False},
                    reason="Handles categoricals natively"
                ),
                ModelCandidate(
                    name="ElasticNet",
                    model_class="sklearn.linear_model.ElasticNet",
                    priority=65,
                    params={"alpha": 1.0, "l1_ratio": 0.5, "random_state": 42},
                    reason="Regularized linear model"
                ),
            ])
        
        self.logger.info(f"   ✅ Deep mode: {len(candidates)} models selected")
        return sorted(candidates, key=lambda x: x.priority, reverse=True)
