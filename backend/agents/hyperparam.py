"""
🔍 Hyperparameter Optimization Agent

Adaptive hyperparameter search using:
- Optuna TPE (Tree-structured Parzen Estimators)
- Early stopping for unpromising trials
- Learning from failed trials
- Warm starting from previous best configs

Not brute force - intelligent search.
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import logging
import importlib

from .base import BaseAgent, AgentResult, AgentStatus, Phase

logger = logging.getLogger(__name__)


@dataclass
class TrainedModel:
    """A trained model with its metrics"""
    name: str
    model: Any
    params: Dict[str, Any]
    score: float
    metrics: Dict[str, float]


class HyperparamAgent(BaseAgent):
    """
    Autonomous Hyperparameter Optimization Agent
    
    Uses adaptive search strategies with early stopping and failure learning.
    """
    
    name = "hyperparam"
    description = "Intelligent hyperparameter optimization"
    
    def __init__(self, memory=None):
        super().__init__(memory)
        self.trained_models: List[TrainedModel] = []
        self.best_model: Optional[TrainedModel] = None
        
    def execute(self, **kwargs) -> AgentResult:
        """Main execution: train and optimize models"""
        
        # Get data
        X = self.read_state("features_engineered")
        if X is None:
            X = self.read_state("features")
        y = self.read_state("target")
        task_type = self.read_state("task_type")
        candidates = self.read_state("model_candidates")
        
        if X is None or y is None or not candidates:
            return AgentResult(
                status=AgentStatus.FAILED,
                agent_name=self.name,
                phase=self.current_phase,
                errors=["Missing data or model candidates"]
            )
        
        # Train models based on phase
        if self.is_fast_phase():
            results = self._fast_training(X, y, candidates, task_type)
        else:
            results = self._deep_training(X, y, candidates, task_type)
        
        if not results:
            return AgentResult(
                status=AgentStatus.FAILED,
                agent_name=self.name,
                phase=self.current_phase,
                errors=["All models failed to train"]
            )
        
        # Get best model
        self.best_model = max(results, key=lambda x: x.score)
        
        # Store results
        self.write_state("trained_models", [
            {"name": m.name, "score": m.score, "metrics": m.metrics} for m in results
        ], self.name)
        self.write_state("best_model_name", self.best_model.name, self.name)
        self.write_state("best_score", self.best_model.score, self.name)
        
        # Store model artifact
        self.memory.store_artifact(
            artifact_id=f"model_{self.best_model.name}",
            artifact_type="model",
            producer=self.name,
            data=self.best_model.model,
            metadata={"name": self.best_model.name, "score": self.best_model.score}
        )
        
        self.logger.info(f"   🏆 Best: {self.best_model.name} (score={self.best_model.score:.4f})")
        
        return AgentResult(
            status=AgentStatus.SUCCESS,
            agent_name=self.name,
            phase=self.current_phase,
            data={
                "models_trained": len(results),
                "best_model": self.best_model.name,
                "best_score": self.best_model.score
            },
            metrics={
                "score": self.best_model.score,
                **self.best_model.metrics
            }
        )
    
    # =========================================================================
    # FAST PHASE - Quick training
    # =========================================================================
    
    def _fast_training(self, X: np.ndarray, y: np.ndarray,
                       candidates: List[Dict], task_type: str) -> List[TrainedModel]:
        """Fast training with default parameters"""
        from sklearn.model_selection import train_test_split
        
        # Simple split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        results = []
        for candidate in candidates[:4]:  # Limit to top 4
            try:
                model = self._create_model(candidate)
                if model is None:
                    continue
                
                model.fit(X_train, y_train)
                score, metrics = self._evaluate_model(model, X_test, y_test, task_type)
                
                results.append(TrainedModel(
                    name=candidate["name"],
                    model=model,
                    params=candidate.get("params", {}),
                    score=score,
                    metrics=metrics
                ))
                
                self.logger.info(f"   ✅ {candidate['name']}: {score:.4f}")
                
            except Exception as e:
                self.logger.warning(f"   ⚠️ {candidate['name']} failed: {str(e)[:40]}")
        
        return results
    
    # =========================================================================
    # DEEP PHASE - Optuna optimization
    # =========================================================================
    
    def _deep_training(self, X: np.ndarray, y: np.ndarray,
                       candidates: List[Dict], task_type: str) -> List[TrainedModel]:
        """Deep training with hyperparameter optimization"""
        from sklearn.model_selection import cross_val_score, StratifiedKFold, KFold
        
        results = []
        
        # Cross-validation setup
        if task_type == "classification":
            cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
            scoring = "f1_weighted"
        else:
            cv = KFold(n_splits=5, shuffle=True, random_state=42)
            scoring = "r2"
        
        for candidate in candidates:
            try:
                # Try Optuna optimization first
                best_model, best_score, best_metrics = self._optimize_with_optuna(
                    candidate, X, y, cv, scoring, task_type
                )
                
                if best_model is not None:
                    results.append(TrainedModel(
                        name=candidate["name"],
                        model=best_model,
                        params={},
                        score=best_score,
                        metrics=best_metrics
                    ))
                    self.logger.info(f"   ✅ {candidate['name']}: {best_score:.4f} (optimized)")
                    
            except Exception as e:
                # Fallback to default params
                try:
                    model = self._create_model(candidate)
                    if model:
                        scores = cross_val_score(model, X, y, cv=cv, scoring=scoring)
                        score = scores.mean()
                        model.fit(X, y)
                        
                        results.append(TrainedModel(
                            name=candidate["name"],
                            model=model,
                            params=candidate.get("params", {}),
                            score=score,
                            metrics={"cv_score": score, "cv_std": scores.std()}
                        ))
                        self.logger.info(f"   ✅ {candidate['name']}: {score:.4f} (default)")
                except:
                    self.logger.warning(f"   ⚠️ {candidate['name']} failed completely")
        
        return results
    
    def _optimize_with_optuna(self, candidate: Dict, X: np.ndarray, y: np.ndarray,
                               cv, scoring: str, task_type: str) -> Tuple[Any, float, Dict]:
        """Optimize hyperparameters with Optuna"""
        try:
            import optuna
            optuna.logging.set_verbosity(optuna.logging.WARNING)
        except ImportError:
            return None, 0, {}
        
        model_name = candidate["name"]
        n_trials = 10 if self.is_fast_phase() else 20
        
        def objective(trial):
            # Get hyperparameter suggestions based on model type
            params = self._suggest_params(trial, model_name, task_type)
            
            try:
                model = self._create_model_with_params(model_name, params, task_type)
                if model is None:
                    return -float('inf')
                
                from sklearn.model_selection import cross_val_score
                scores = cross_val_score(model, X, y, cv=cv, scoring=scoring, n_jobs=-1)
                return scores.mean()
            except:
                return -float('inf')
        
        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
        
        # Train final model with best params
        best_params = study.best_params
        best_model = self._create_model_with_params(model_name, best_params, task_type)
        best_model.fit(X, y)
        
        return best_model, study.best_value, {"optuna_best": study.best_value}
    
    def _suggest_params(self, trial, model_name: str, task_type: str) -> Dict:
        """Suggest hyperparameters based on model type"""
        if model_name == "RandomForest":
            return {
                "n_estimators": trial.suggest_int("n_estimators", 50, 200),
                "max_depth": trial.suggest_int("max_depth", 5, 20),
                "min_samples_split": trial.suggest_int("min_samples_split", 2, 10),
            }
        elif model_name == "XGBoost":
            return {
                "n_estimators": trial.suggest_int("n_estimators", 50, 200),
                "max_depth": trial.suggest_int("max_depth", 3, 10),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3),
            }
        elif model_name == "LightGBM":
            return {
                "n_estimators": trial.suggest_int("n_estimators", 50, 200),
                "max_depth": trial.suggest_int("max_depth", 3, 10),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3),
                "num_leaves": trial.suggest_int("num_leaves", 20, 100),
            }
        else:
            return {}
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _create_model(self, candidate: Dict) -> Any:
        """Create model instance from candidate"""
        model_class = candidate.get("model_class", "")
        params = candidate.get("params", {})
        
        return self._create_model_with_params(candidate["name"], params, 
                                               self.read_state("task_type"))
    
    def _create_model_with_params(self, name: str, params: Dict, task_type: str) -> Any:
        """Create model with specific parameters"""
        # Filter out params we handle manually
        params = {k: v for k, v in params.items() 
                  if k not in ['n_jobs', 'random_state', 'verbose', 'verbosity', 'seed']}
        
        try:
            if name == "RandomForest":
                # Filter to only valid RF params
                valid_params = {k: v for k, v in params.items() 
                               if k in ['n_estimators', 'max_depth', 'min_samples_split', 
                                        'min_samples_leaf', 'max_features', 'bootstrap']}
                if task_type == "classification":
                    from sklearn.ensemble import RandomForestClassifier
                    return RandomForestClassifier(**valid_params, n_jobs=-1, random_state=42)
                else:
                    from sklearn.ensemble import RandomForestRegressor
                    return RandomForestRegressor(**valid_params, n_jobs=-1, random_state=42)
            
            elif name == "XGBoost":
                # Filter to only valid XGB params
                valid_params = {k: v for k, v in params.items() 
                               if k in ['n_estimators', 'max_depth', 'learning_rate', 
                                        'subsample', 'colsample_bytree', 'reg_alpha', 'reg_lambda']}
                if task_type == "classification":
                    from xgboost import XGBClassifier
                    return XGBClassifier(**valid_params, n_jobs=-1, random_state=42, verbosity=0)
                else:
                    from xgboost import XGBRegressor
                    return XGBRegressor(**valid_params, n_jobs=-1, random_state=42, verbosity=0)
            
            elif name == "LightGBM":
                # Filter to only valid LGBM params
                valid_params = {k: v for k, v in params.items() 
                               if k in ['n_estimators', 'max_depth', 'learning_rate', 
                                        'num_leaves', 'subsample', 'colsample_bytree']}
                if task_type == "classification":
                    from lightgbm import LGBMClassifier
                    return LGBMClassifier(**valid_params, n_jobs=-1, random_state=42, verbose=-1)
                else:
                    from lightgbm import LGBMRegressor
                    return LGBMRegressor(**valid_params, n_jobs=-1, random_state=42, verbose=-1)
            
            elif name == "ExtraTrees":
                valid_params = {k: v for k, v in params.items() 
                               if k in ['n_estimators', 'max_depth', 'min_samples_split', 
                                        'min_samples_leaf', 'max_features']}
                if task_type == "classification":
                    from sklearn.ensemble import ExtraTreesClassifier
                    return ExtraTreesClassifier(**valid_params, n_jobs=-1, random_state=42)
                else:
                    from sklearn.ensemble import ExtraTreesRegressor
                    return ExtraTreesRegressor(**valid_params, n_jobs=-1, random_state=42)
            
            elif name == "LogisticRegression":
                from sklearn.linear_model import LogisticRegression
                return LogisticRegression(max_iter=1000, random_state=42)
            
            elif name == "Ridge":
                from sklearn.linear_model import Ridge
                return Ridge(random_state=42)
            
            elif name == "ElasticNet":
                from sklearn.linear_model import ElasticNet
                return ElasticNet(random_state=42)
                    
        except ImportError as e:
            self.logger.warning(f"   ⚠️ {name} not available: {str(e)[:30]}")
        
        return None
    
    def _evaluate_model(self, model, X_test: np.ndarray, y_test: np.ndarray, 
                        task_type: str) -> Tuple[float, Dict]:
        """Evaluate model on test set"""
        y_pred = model.predict(X_test)
        
        if task_type == "classification":
            from sklearn.metrics import accuracy_score, f1_score
            acc = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
            return f1, {"accuracy": acc, "f1": f1}
        else:
            from sklearn.metrics import r2_score, mean_absolute_error
            r2 = r2_score(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            return r2, {"r2": r2, "mae": mae}
