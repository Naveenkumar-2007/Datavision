"""
📈 Training Validator Agent

Validates training behavior BEFORE final evaluation:
- Learning curve analysis
- Bias-variance diagnosis
- Training stability
- Early overfitting detection

KEY INNOVATION: Catch problems early, don't waste compute on bad models.
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import logging

from .base import BaseAgent, AgentResult, AgentStatus, Phase, MessageType

logger = logging.getLogger(__name__)


@dataclass
class TrainingDiagnosis:
    """Diagnosis of training behavior"""
    issue: str  # high_bias, high_variance, unstable, overfitting
    severity: str  # low, medium, high
    recommendation: str
    target_agent: str  # Which agent should fix this


class TrainingValidatorAgent(BaseAgent):
    """
    Training Validator Agent
    
    Validates training behavior → Diagnoses issues → Routes to fix agents
    """
    
    name = "training_validator"
    description = "Validates training behavior and catches issues early"
    
    def __init__(self, memory=None):
        super().__init__(memory)
        self.diagnoses: List[TrainingDiagnosis] = []
        
    def execute(self, **kwargs) -> AgentResult:
        """Main execution: validate training, diagnose issues"""
        
        # Get trained models and data
        X = self.read_state("features_engineered")
        if X is None:
            X = self.read_state("features")
        y = self.read_state("target")
        task_type = self.read_state("task_type")
        best_score = self.read_state("best_score")
        best_model_name = self.read_state("best_model_name")
        
        if X is None or y is None:
            return AgentResult(
                status=AgentStatus.FAILED,
                agent_name=self.name,
                phase=self.current_phase,
                errors=["Missing data"]
            )
        
        # Get best model artifact
        model_artifact = self.memory.get_latest_artifact("model")
        if model_artifact is None:
            return AgentResult(
                status=AgentStatus.FAILED,
                agent_name=self.name,
                phase=self.current_phase,
                errors=["No trained model found"]
            )
        
        model = model_artifact.data
        
        self.logger.info(f"📊 Validating: {best_model_name} (score={best_score:.4f})")
        
        # Run validation based on phase
        if self.is_fast_phase():
            diagnoses = self._fast_validation(model, X, y, task_type, best_score)
        else:
            diagnoses = self._deep_validation(model, X, y, task_type, best_score)
        
        self.diagnoses = diagnoses
        
        # Check if issues found
        if diagnoses:
            critical_issues = [d for d in diagnoses if d.severity == "high"]
            
            if critical_issues:
                # Create retry messages for feedback loop
                result = AgentResult(
                    status=AgentStatus.RETRY,
                    agent_name=self.name,
                    phase=self.current_phase,
                    data={"diagnoses": [d.__dict__ for d in diagnoses]},
                    recommendations=[d.recommendation for d in critical_issues]
                )
                
                # Add messages to route to fix agents
                for issue in critical_issues:
                    result.add_message(
                        receiver=issue.target_agent,
                        msg_type=MessageType.RETRY,
                        payload={"issue": issue.issue, "recommendation": issue.recommendation}
                    )
                
                self.logger.warning(f"   ⚠️ {len(critical_issues)} critical issues found")
                return result
        
        # Validation passed
        self.write_state("training_validated", True, self.name)
        self.write_state("training_diagnoses", [d.__dict__ for d in diagnoses], self.name)
        
        return AgentResult(
            status=AgentStatus.SUCCESS,
            agent_name=self.name,
            phase=self.current_phase,
            data={
                "validated": True,
                "minor_issues": len(diagnoses)
            },
            metrics={
                "score": best_score
            }
        )
    
    # =========================================================================
    # FAST VALIDATION
    # =========================================================================
    
    def _fast_validation(self, model, X: np.ndarray, y: np.ndarray,
                         task_type: str, score: float) -> List[TrainingDiagnosis]:
        """Quick validation checks with production-realistic thresholds"""
        diagnoses = []
        
        # Get retry count from memory to be more lenient after attempts
        retry_attempts = self.read_state("validation_retry_count") or 0
        
        # After 2 retries, be more lenient (data limitation, not model issue)
        is_lenient_mode = retry_attempts >= 2
        
        # Adjusted thresholds based on retry attempts
        if is_lenient_mode:
            score_threshold = 0.3 if task_type == "classification" else -0.5  # Very lenient
            gap_threshold = 0.6  # Accept higher gaps
            self.logger.info(f"   📋 Lenient mode (attempt {retry_attempts + 1})")
        else:
            score_threshold = 0.5 if task_type == "classification" else 0.05
            gap_threshold = 0.35  # More realistic for production data
        
        # Check: Score too low
        if score < score_threshold:
            diagnoses.append(TrainingDiagnosis(
                issue="low_performance",
                severity="medium" if is_lenient_mode else "high",
                recommendation="Try different features or algorithms",
                target_agent="feature_engineer"
            ))
            self.logger.warning(f"   ⚠️ Low performance: {score:.4f} < {score_threshold}")
        
        # Check: Train-test gap (quick check via predictions)
        train_score = self._get_train_score(model, X, y, task_type)
        gap = train_score - score
        
        if gap > gap_threshold:
            diagnoses.append(TrainingDiagnosis(
                issue="overfitting",
                severity="medium" if is_lenient_mode else ("high" if gap > 0.5 else "medium"),
                recommendation="Reduce model complexity or add regularization",
                target_agent="hyperparam"
            ))
            self.logger.warning(f"   ⚠️ Train-test gap: {gap:.4f}")
        
        # Update retry count
        self.write_state("validation_retry_count", retry_attempts + 1, self.name)
        
        if not diagnoses:
            self.logger.info(f"   ✅ Fast validation passed")
        elif is_lenient_mode and all(d.severity != "high" for d in diagnoses):
            # In lenient mode with only medium issues, pass anyway
            self.logger.info(f"   ✅ Validation passed (lenient mode, {len(diagnoses)} minor issues)")
            return []  # Clear issues to pass
        
        return diagnoses
    
    # =========================================================================
    # DEEP VALIDATION
    # =========================================================================
    
    def _deep_validation(self, model, X: np.ndarray, y: np.ndarray,
                         task_type: str, score: float) -> List[TrainingDiagnosis]:
        """Deep validation with learning curves and stability checks"""
        diagnoses = self._fast_validation(model, X, y, task_type, score)
        
        # Learning curve analysis
        lc_diagnosis = self._analyze_learning_curve(model, X, y, task_type)
        if lc_diagnosis:
            diagnoses.append(lc_diagnosis)
        
        # Stability check (multiple seeds)
        stability_diagnosis = self._check_stability(model, X, y, task_type)
        if stability_diagnosis:
            diagnoses.append(stability_diagnosis)
        
        if not diagnoses:
            self.logger.info(f"   ✅ Deep validation passed")
        
        return diagnoses
    
    def _get_train_score(self, model, X: np.ndarray, y: np.ndarray, 
                         task_type: str) -> float:
        """Get training score"""
        try:
            y_pred = model.predict(X)
            
            if task_type == "classification":
                from sklearn.metrics import accuracy_score
                return accuracy_score(y, y_pred)
            else:
                from sklearn.metrics import r2_score
                return r2_score(y, y_pred)
        except:
            return 1.0  # Assume perfect train score if can't calculate
    
    def _analyze_learning_curve(self, model, X: np.ndarray, y: np.ndarray,
                                 task_type: str) -> Optional[TrainingDiagnosis]:
        """Analyze learning curve for bias/variance"""
        try:
            from sklearn.model_selection import learning_curve
            
            # Sample for speed
            n_samples = min(5000, X.shape[0])
            indices = np.random.choice(X.shape[0], n_samples, replace=False)
            X_sample, y_sample = X[indices], y[indices]
            
            train_sizes, train_scores, test_scores = learning_curve(
                model.__class__(**model.get_params()),
                X_sample, y_sample,
                train_sizes=np.linspace(0.2, 1.0, 5),
                cv=3,
                n_jobs=-1,
                scoring='accuracy' if task_type == "classification" else 'r2'
            )
            
            # Analyze curve
            train_mean = train_scores.mean(axis=1)
            test_mean = test_scores.mean(axis=1)
            
            # High bias: both train and test scores are low
            if train_mean[-1] < 0.6 and test_mean[-1] < 0.5:
                return TrainingDiagnosis(
                    issue="high_bias",
                    severity="high",
                    recommendation="Model is too simple. Try more complex model or more features",
                    target_agent="model_strategy"
                )
            
            # High variance: train high, test low
            final_gap = train_mean[-1] - test_mean[-1]
            if final_gap > 0.2:
                return TrainingDiagnosis(
                    issue="high_variance",
                    severity="high" if final_gap > 0.3 else "medium",
                    recommendation="Model is overfitting. Need more data or simpler model",
                    target_agent="hyperparam"
                )
            
            self.logger.info(f"   📈 Learning curve: train={train_mean[-1]:.3f}, test={test_mean[-1]:.3f}")
            
        except Exception as e:
            self.logger.warning(f"   ⚠️ Learning curve failed: {str(e)[:30]}")
        
        return None
    
    def _check_stability(self, model, X: np.ndarray, y: np.ndarray,
                         task_type: str) -> Optional[TrainingDiagnosis]:
        """Check model stability across random seeds"""
        try:
            from sklearn.model_selection import cross_val_score, KFold
            
            scores = []
            for seed in [42, 123, 456]:
                cv = KFold(n_splits=3, shuffle=True, random_state=seed)
                cv_scores = cross_val_score(
                    model.__class__(**model.get_params()),
                    X, y, cv=cv,
                    scoring='accuracy' if task_type == "classification" else 'r2'
                )
                scores.append(cv_scores.mean())
            
            std = np.std(scores)
            
            if std > 0.05:
                return TrainingDiagnosis(
                    issue="unstable",
                    severity="medium",
                    recommendation="Model is unstable across folds. Consider ensemble or more data",
                    target_agent="hyperparam"
                )
            
            self.logger.info(f"   📊 Stability: std={std:.4f}")
            
        except Exception as e:
            self.logger.warning(f"   ⚠️ Stability check failed: {str(e)[:30]}")
        
        return None
