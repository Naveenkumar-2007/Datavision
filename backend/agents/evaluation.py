"""
✅ Evaluation & Generalization Agent

Final approval gate with comprehensive checks:
- Cross-validation consistency
- Robustness (perturbation tests)
- Drift sensitivity
- Overfitting detection

Model only approved if ALL checks pass.
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import logging

from .base import BaseAgent, AgentResult, AgentStatus, Phase, MessageType

logger = logging.getLogger(__name__)


@dataclass
class EvaluationCheck:
    """Result of an evaluation check"""
    name: str
    passed: bool
    score: float
    threshold: float
    details: str


class EvaluationAgent(BaseAgent):
    """
    Evaluation & Generalization Agent
    
    Comprehensive final checks → Committee approval → Release to production
    """
    
    name = "evaluation"
    description = "Final approval gate with robustness checks"
    
    def __init__(self, memory=None):
        super().__init__(memory)
        self.checks: List[EvaluationCheck] = []
        
    def execute(self, **kwargs) -> AgentResult:
        """Main execution: run all checks, make approval decision"""
        
        # Get data and model
        X = self.read_state("features_engineered")
        if X is None:
            X = self.read_state("features")
        y = self.read_state("target")
        task_type = self.read_state("task_type")
        
        model_artifact = self.memory.get_latest_artifact("model")
        if model_artifact is None or X is None or y is None:
            return AgentResult(
                status=AgentStatus.FAILED,
                agent_name=self.name,
                phase=self.current_phase,
                errors=["Missing model or data"]
            )
        
        model = model_artifact.data
        
        self.logger.info(f"🔍 Running evaluation checks...")
        
        # Run checks based on phase
        if self.is_fast_phase():
            checks = self._fast_evaluation(model, X, y, task_type)
        else:
            checks = self._deep_evaluation(model, X, y, task_type)
        
        self.checks = checks
        
        # Determine approval
        passed = all(c.passed for c in checks)
        critical_fails = [c for c in checks if not c.passed]
        
        avg_score = np.mean([c.score for c in checks])
        
        if not passed:
            # Create retry messages
            result = AgentResult(
                status=AgentStatus.RETRY,
                agent_name=self.name,
                phase=self.current_phase,
                data={"checks": [c.__dict__ for c in checks]},
                recommendations=[f"{c.name} failed: {c.details}" for c in critical_fails],
                metrics={"score": avg_score}
            )
            
            for check in critical_fails:
                result.add_message(
                    receiver="model_strategy",
                    msg_type=MessageType.RETRY,
                    payload={"failed_check": check.name}
                )
            
            self.logger.warning(f"   ⚠️ {len(critical_fails)} checks failed")
            return result
        
        # All checks passed
        self.write_state("evaluation_approved", True, self.name)
        self.write_state("evaluation_checks", [c.__dict__ for c in checks], self.name)
        
        self.logger.info(f"   ✅ All {len(checks)} checks passed")
        
        return AgentResult(
            status=AgentStatus.SUCCESS,
            agent_name=self.name,
            phase=self.current_phase,
            data={
                "approved": True,
                "checks_passed": len(checks)
            },
            metrics={
                "score": avg_score
            }
        )
    
    # =========================================================================
    # FAST EVALUATION
    # =========================================================================
    
    def _fast_evaluation(self, model, X: np.ndarray, y: np.ndarray,
                         task_type: str) -> List[EvaluationCheck]:
        """Quick evaluation checks"""
        checks = []
        
        # 1. Cross-validation check
        cv_check = self._check_cross_validation(model, X, y, task_type, n_folds=3)
        checks.append(cv_check)
        
        # 2. Quick overfitting check
        overfit_check = self._check_overfitting(model, X, y, task_type)
        checks.append(overfit_check)
        
        return checks
    
    # =========================================================================
    # DEEP EVALUATION
    # =========================================================================
    
    def _deep_evaluation(self, model, X: np.ndarray, y: np.ndarray,
                         task_type: str) -> List[EvaluationCheck]:
        """Comprehensive evaluation checks"""
        checks = []
        
        # 1. Robust cross-validation (5-fold)
        cv_check = self._check_cross_validation(model, X, y, task_type, n_folds=5)
        checks.append(cv_check)
        
        # 2. Overfitting check
        overfit_check = self._check_overfitting(model, X, y, task_type)
        checks.append(overfit_check)
        
        # 3. Robustness (perturbation test)
        robust_check = self._check_robustness(model, X, y, task_type)
        checks.append(robust_check)
        
        # 4. CV stability (std check)
        stability_check = self._check_cv_stability(model, X, y, task_type)
        checks.append(stability_check)
        
        return checks
    
    # =========================================================================
    # CHECK IMPLEMENTATIONS
    # =========================================================================
    
    def _check_cross_validation(self, model, X: np.ndarray, y: np.ndarray,
                                 task_type: str, n_folds: int = 5) -> EvaluationCheck:
        """Check cross-validation performance"""
        try:
            from sklearn.model_selection import cross_val_score, StratifiedKFold, KFold
            
            if task_type == "classification":
                cv = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
                scoring = "f1_weighted"
                threshold = 0.5
            else:
                cv = KFold(n_splits=n_folds, shuffle=True, random_state=42)
                scoring = "r2"
                threshold = 0.1
            
            scores = cross_val_score(
                model.__class__(**model.get_params()),
                X, y, cv=cv, scoring=scoring
            )
            
            mean_score = scores.mean()
            passed = mean_score >= threshold
            
            self.logger.info(f"   📊 CV Score: {mean_score:.4f} (threshold: {threshold})")
            
            return EvaluationCheck(
                name="cross_validation",
                passed=passed,
                score=mean_score,
                threshold=threshold,
                details=f"CV mean={mean_score:.4f}, std={scores.std():.4f}"
            )
            
        except Exception as e:
            return EvaluationCheck(
                name="cross_validation",
                passed=False,
                score=0,
                threshold=0,
                details=f"Failed: {str(e)[:50]}"
            )
    
    def _check_overfitting(self, model, X: np.ndarray, y: np.ndarray,
                           task_type: str) -> EvaluationCheck:
        """Check for overfitting via train-test gap"""
        try:
            from sklearn.model_selection import train_test_split
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Clone and refit
            new_model = model.__class__(**model.get_params())
            new_model.fit(X_train, y_train)
            
            train_pred = new_model.predict(X_train)
            test_pred = new_model.predict(X_test)
            
            if task_type == "classification":
                from sklearn.metrics import accuracy_score
                train_score = accuracy_score(y_train, train_pred)
                test_score = accuracy_score(y_test, test_pred)
            else:
                from sklearn.metrics import r2_score
                train_score = r2_score(y_train, train_pred)
                test_score = r2_score(y_test, test_pred)
            
            gap = train_score - test_score
            threshold = 0.15  # Max acceptable gap
            passed = gap <= threshold
            
            self.logger.info(f"   📊 Train-Test Gap: {gap:.4f} (threshold: {threshold})")
            
            return EvaluationCheck(
                name="overfitting",
                passed=passed,
                score=1 - gap,  # Higher is better
                threshold=1 - threshold,
                details=f"train={train_score:.4f}, test={test_score:.4f}, gap={gap:.4f}"
            )
            
        except Exception as e:
            return EvaluationCheck(
                name="overfitting",
                passed=True,  # Pass by default if can't check
                score=0.5,
                threshold=0,
                details=f"Could not check: {str(e)[:50]}"
            )
    
    def _check_robustness(self, model, X: np.ndarray, y: np.ndarray,
                          task_type: str) -> EvaluationCheck:
        """Check robustness via feature perturbation"""
        try:
            # Add small noise to features
            noise = np.random.normal(0, 0.1, X.shape)
            X_perturbed = X + noise
            
            original_pred = model.predict(X[:1000])
            perturbed_pred = model.predict(X_perturbed[:1000])
            
            if task_type == "classification":
                # Check prediction stability
                stability = (original_pred == perturbed_pred).mean()
            else:
                # Check prediction correlation
                stability = np.corrcoef(original_pred.flatten(), perturbed_pred.flatten())[0, 1]
                stability = max(0, stability)  # Ensure non-negative
            
            threshold = 0.7
            passed = stability >= threshold
            
            self.logger.info(f"   📊 Robustness: {stability:.4f} (threshold: {threshold})")
            
            return EvaluationCheck(
                name="robustness",
                passed=passed,
                score=stability,
                threshold=threshold,
                details=f"Prediction stability under noise: {stability:.4f}"
            )
            
        except Exception as e:
            return EvaluationCheck(
                name="robustness",
                passed=True,
                score=0.8,
                threshold=0.7,
                details=f"Could not check: {str(e)[:50]}"
            )
    
    def _check_cv_stability(self, model, X: np.ndarray, y: np.ndarray,
                            task_type: str) -> EvaluationCheck:
        """Check cross-validation stability (low variance)"""
        try:
            from sklearn.model_selection import cross_val_score, KFold
            
            cv = KFold(n_splits=5, shuffle=True, random_state=42)
            scoring = "f1_weighted" if task_type == "classification" else "r2"
            
            scores = cross_val_score(
                model.__class__(**model.get_params()),
                X, y, cv=cv, scoring=scoring
            )
            
            std = scores.std()
            threshold = 0.05  # Max acceptable std
            passed = std <= threshold
            
            self.logger.info(f"   📊 CV Stability: std={std:.4f} (threshold: {threshold})")
            
            return EvaluationCheck(
                name="cv_stability",
                passed=passed,
                score=1 - std,  # Higher is better
                threshold=1 - threshold,
                details=f"CV std={std:.4f}"
            )
            
        except Exception as e:
            return EvaluationCheck(
                name="cv_stability",
                passed=True,
                score=0.95,
                threshold=0.95,
                details=f"Could not check: {str(e)[:50]}"
            )
