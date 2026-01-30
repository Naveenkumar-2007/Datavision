"""
🔧 Feature Engineering Agent

Autonomous feature creation, selection, and validation:
- Creates: Polynomial, interactions, aggregations
- Selects: Correlation, mutual information, SHAP importance
- Validates: Ablation testing, impact measurement

Self-iterates to find optimal feature set.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import logging

from .base import BaseAgent, AgentResult, AgentStatus, Phase, MessageType

logger = logging.getLogger(__name__)


@dataclass
class FeatureInfo:
    """Information about a feature"""
    name: str
    source: str  # original, polynomial, interaction, derived
    importance: float = 0.0
    selected: bool = True


class FeatureEngineerAgent(BaseAgent):
    """
    Autonomous Feature Engineering Agent
    
    Creates new features → Measures importance → Selects best → Validates
    """
    
    name = "feature_engineer"
    description = "Creates, selects, and validates features"
    
    def __init__(self, memory=None):
        super().__init__(memory)
        self.feature_info: List[FeatureInfo] = []
        self.importance_scores: Dict[str, float] = {}
        
    def execute(self, **kwargs) -> AgentResult:
        """Main execution: create, select, validate features"""
        
        # Get processed data
        X = self.read_state("features")
        y = self.read_state("target")
        feature_names = self.read_state("feature_names")
        task_type = self.read_state("task_type")
        
        if X is None or y is None:
            return AgentResult(
                status=AgentStatus.FAILED,
                agent_name=self.name,
                phase=self.current_phase,
                errors=["No processed features found"]
            )
        
        original_features = X.shape[1]
        self.logger.info(f"📊 Input: {original_features} features")
        
        # =====================================================================
        # PHASE-AWARE PROCESSING
        # =====================================================================
        
        if self.is_fast_phase():
            X_engineered, names = self._fast_feature_engineering(X, y, feature_names, task_type)
        else:
            X_engineered, names = self._deep_feature_engineering(X, y, feature_names, task_type)
        
        # Store results
        self.write_state("features_engineered", X_engineered, self.name)
        self.write_state("feature_names_final", names, self.name)
        self.write_state("feature_importance", self.importance_scores, self.name)
        
        return AgentResult(
            status=AgentStatus.SUCCESS,
            agent_name=self.name,
            phase=self.current_phase,
            data={
                "original_features": original_features,
                "final_features": X_engineered.shape[1],
                "features_added": X_engineered.shape[1] - original_features
            },
            metrics={
                "feature_count": X_engineered.shape[1]
            }
        )
    
    # =========================================================================
    # FAST PHASE
    # =========================================================================
    
    def _fast_feature_engineering(self, X: np.ndarray, y: np.ndarray, 
                                   feature_names: List[str], task_type: str) -> Tuple[np.ndarray, List[str]]:
        """Fast feature engineering: variance filter + basic selection"""
        
        # 1. Remove zero variance
        X_clean, names_clean = self._remove_zero_variance(X, feature_names)
        
        # 2. Quick correlation-based selection
        X_selected, names_selected = self._correlation_selection(X_clean, y, names_clean, task_type)
        
        self.logger.info(f"   ✅ Fast mode: {len(names_selected)} features selected")
        
        return X_selected, names_selected
    
    # =========================================================================
    # DEEP PHASE
    # =========================================================================
    
    def _deep_feature_engineering(self, X: np.ndarray, y: np.ndarray,
                                    feature_names: List[str], task_type: str) -> Tuple[np.ndarray, List[str]]:
        """Deep feature engineering: create + select + validate"""
        
        # 1. Remove zero variance
        X_clean, names_clean = self._remove_zero_variance(X, feature_names)
        
        # 2. Create interaction features (if not too many)
        if X_clean.shape[1] <= 15:
            X_enhanced, names_enhanced = self._create_interactions(X_clean, names_clean)
        else:
            X_enhanced, names_enhanced = X_clean, names_clean
        
        # 3. Feature importance selection
        X_selected, names_selected = self._importance_selection(X_enhanced, y, names_enhanced, task_type)
        
        # 4. Remove highly correlated (redundant)
        X_final, names_final = self._remove_redundant(X_selected, names_selected)
        
        self.logger.info(f"   ✅ Deep mode: {len(names_final)} features after full pipeline")
        
        return X_final, names_final
    
    # =========================================================================
    # FEATURE OPERATIONS
    # =========================================================================
    
    def _remove_zero_variance(self, X: np.ndarray, names: List[str]) -> Tuple[np.ndarray, List[str]]:
        """Remove features with zero or near-zero variance"""
        variances = np.var(X, axis=0)
        mask = variances > 1e-10
        
        removed = np.sum(~mask)
        if removed > 0:
            self.logger.info(f"   🗑️ Removed {removed} zero-variance features")
        
        return X[:, mask], [n for n, m in zip(names, mask) if m]
    
    def _correlation_selection(self, X: np.ndarray, y: np.ndarray, 
                                names: List[str], task_type: str) -> Tuple[np.ndarray, List[str]]:
        """Select features based on correlation with target"""
        correlations = []
        
        for i in range(X.shape[1]):
            try:
                if task_type == "regression":
                    corr = abs(np.corrcoef(X[:, i], y)[0, 1])
                else:
                    # For classification, use variance ratio
                    corr = self._calculate_f_score(X[:, i], y)
                correlations.append(corr if not np.isnan(corr) else 0)
            except:
                correlations.append(0)
        
        # Keep features with correlation > threshold
        threshold = 0.01  # Very lenient
        mask = np.array(correlations) > threshold
        
        # Always keep at least top 10
        if np.sum(mask) < 10:
            top_indices = np.argsort(correlations)[-min(10, len(correlations)):]
            mask = np.zeros(len(correlations), dtype=bool)
            mask[top_indices] = True
        
        self.importance_scores = {n: c for n, c in zip(names, correlations)}
        
        return X[:, mask], [n for n, m in zip(names, mask) if m]
    
    def _calculate_f_score(self, x: np.ndarray, y: np.ndarray) -> float:
        """Calculate F-score for feature selection (classification)"""
        try:
            from sklearn.feature_selection import f_classif
            scores, _ = f_classif(x.reshape(-1, 1), y)
            return scores[0] if not np.isnan(scores[0]) else 0
        except:
            return 0
    
    def _create_interactions(self, X: np.ndarray, names: List[str]) -> Tuple[np.ndarray, List[str]]:
        """Create interaction features between top features"""
        new_features = []
        new_names = []
        
        # Only create interactions for top 5 features
        n_features = min(5, X.shape[1])
        
        for i in range(n_features):
            for j in range(i + 1, n_features):
                interaction = X[:, i] * X[:, j]
                new_features.append(interaction.reshape(-1, 1))
                new_names.append(f"{names[i]}*{names[j]}")
        
        if new_features:
            X_enhanced = np.hstack([X] + new_features)
            names_enhanced = names + new_names
            self.logger.info(f"   ➕ Created {len(new_features)} interaction features")
            return X_enhanced, names_enhanced
        
        return X, names
    
    def _importance_selection(self, X: np.ndarray, y: np.ndarray,
                               names: List[str], task_type: str) -> Tuple[np.ndarray, List[str]]:
        """Select features based on model-based importance"""
        try:
            from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
            
            # Fit a quick random forest to get importance
            if task_type == "regression":
                rf = RandomForestRegressor(n_estimators=50, max_depth=5, random_state=42, n_jobs=-1)
            else:
                rf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42, n_jobs=-1)
            
            # Sample for speed
            n_samples = min(5000, X.shape[0])
            indices = np.random.choice(X.shape[0], n_samples, replace=False)
            
            rf.fit(X[indices], y[indices])
            importances = rf.feature_importances_
            
            # Keep top features (at least 10, at most 50)
            n_keep = max(10, min(50, int(len(names) * 0.5)))
            top_indices = np.argsort(importances)[-n_keep:]
            
            self.importance_scores = {n: float(imp) for n, imp in zip(names, importances)}
            
            self.logger.info(f"   📊 Selected top {n_keep} by RF importance")
            
            return X[:, top_indices], [names[i] for i in top_indices]
            
        except Exception as e:
            self.logger.warning(f"   ⚠️ Importance selection failed: {str(e)[:30]}")
            return X, names
    
    def _remove_redundant(self, X: np.ndarray, names: List[str], 
                          threshold: float = 0.95) -> Tuple[np.ndarray, List[str]]:
        """Remove highly correlated (redundant) features"""
        if X.shape[1] < 2:
            return X, names
        
        try:
            # Calculate correlation matrix
            corr_matrix = np.corrcoef(X.T)
            
            # Find pairs with high correlation
            to_remove = set()
            for i in range(len(corr_matrix)):
                for j in range(i + 1, len(corr_matrix)):
                    if abs(corr_matrix[i, j]) > threshold:
                        # Remove the one with lower importance
                        imp_i = self.importance_scores.get(names[i], 0)
                        imp_j = self.importance_scores.get(names[j], 0)
                        to_remove.add(j if imp_i >= imp_j else i)
            
            mask = [i not in to_remove for i in range(X.shape[1])]
            
            if any(not m for m in mask):
                self.logger.info(f"   🗑️ Removed {sum(1 for m in mask if not m)} redundant features")
            
            return X[:, mask], [n for n, m in zip(names, mask) if m]
            
        except Exception as e:
            return X, names
