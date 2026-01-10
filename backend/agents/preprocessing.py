"""
⚙️ Preprocessing Agent

Autonomously selects encoding, scaling, and transformation techniques:
- Encoding: OneHot, Label, Target, Ordinal
- Scaling: Standard, Robust, MinMax, Power
- Transformations: Log, Box-Cox, Yeo-Johnson

Selection is based on data distribution and model compatibility.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import logging

from .base import BaseAgent, AgentResult, AgentStatus, Phase

logger = logging.getLogger(__name__)


@dataclass
class PreprocessingDecision:
    """A preprocessing decision made by the agent"""
    column: str
    technique: str
    reason: str
    params: Dict[str, Any]


class PreprocessingAgent(BaseAgent):
    """
    Autonomous Preprocessing Agent
    
    Analyzes data characteristics → Selects best techniques → Applies transformations
    """
    
    name = "preprocessing"
    description = "Auto-selects encoding, scaling, and transformations"
    
    def __init__(self, memory=None):
        super().__init__(memory)
        self.decisions: List[PreprocessingDecision] = []
        self.transformers: Dict[str, Any] = {}
        
    def execute(self, **kwargs) -> AgentResult:
        """Main execution: analyze, decide, transform"""
        
        # Get cleaned dataset
        df = self.read_state("dataset_cleaned")
        if df is None:
            df = self.read_state("dataset")
        
        target_col = self.read_state("target_column")
        
        if df is None:
            return AgentResult(
                status=AgentStatus.FAILED,
                agent_name=self.name,
                phase=self.current_phase,
                errors=["No dataset found"]
            )
        
        df = df.copy()
        
        # Separate target
        if target_col in df.columns:
            y = df[target_col].copy()
            X = df.drop(columns=[target_col])
        else:
            return AgentResult(
                status=AgentStatus.FAILED,
                agent_name=self.name,
                phase=self.current_phase,
                errors=[f"Target column '{target_col}' not found"]
            )
        
        self.logger.info(f"📊 Preprocessing {X.shape[1]} features")
        
        # =====================================================================
        # PHASE-AWARE PROCESSING
        # =====================================================================
        
        if self.is_fast_phase():
            X_processed, feature_names = self._fast_preprocess(X, y)
        else:
            X_processed, feature_names = self._deep_preprocess(X, y)
        
        # Process target
        y_processed, task_type = self._process_target(y)
        
        # Store results
        self.write_state("features", X_processed, self.name)
        self.write_state("target", y_processed, self.name)
        self.write_state("feature_names", feature_names, self.name)
        self.write_state("task_type", task_type, self.name)
        self.write_state("preprocessing_decisions", [d.__dict__ for d in self.decisions], self.name)
        
        return AgentResult(
            status=AgentStatus.SUCCESS,
            agent_name=self.name,
            phase=self.current_phase,
            data={
                "n_features": len(feature_names),
                "task_type": task_type,
                "decisions": len(self.decisions)
            },
            metrics={
                "feature_count": len(feature_names)
            }
        )
    
    # =========================================================================
    # FAST PHASE
    # =========================================================================
    
    def _fast_preprocess(self, X: pd.DataFrame, y: pd.Series) -> Tuple[np.ndarray, List[str]]:
        """Fast preprocessing with sensible defaults"""
        feature_parts = []
        feature_names = []
        
        for col in X.columns:
            try:
                if pd.api.types.is_numeric_dtype(X[col]):
                    # Numeric: just scale
                    data, name = self._scale_numeric(X[col], col)
                    feature_parts.append(data)
                    feature_names.append(name)
                else:
                    # Categorical: encode
                    data, names = self._encode_categorical(X[col], col)
                    feature_parts.append(data)
                    feature_names.extend(names)
            except Exception as e:
                self.logger.warning(f"   ⚠️ Skipped {col}: {str(e)[:30]}")
        
        if not feature_parts:
            return np.zeros((len(X), 1)), ["_empty_"]
        
        X_processed = np.hstack(feature_parts)
        self.logger.info(f"   ✅ Generated {X_processed.shape[1]} features (fast mode)")
        
        return X_processed, feature_names
    
    # =========================================================================
    # DEEP PHASE
    # =========================================================================
    
    def _deep_preprocess(self, X: pd.DataFrame, y: pd.Series) -> Tuple[np.ndarray, List[str]]:
        """Deep preprocessing with distribution-aware selection"""
        feature_parts = []
        feature_names = []
        
        for col in X.columns:
            try:
                if pd.api.types.is_numeric_dtype(X[col]):
                    # Analyze distribution
                    skewness = X[col].skew()
                    
                    if abs(skewness) > 2:
                        # Highly skewed: use log transform
                        data, name = self._transform_skewed(X[col], col)
                    else:
                        # Normal: use robust scaling
                        data, name = self._scale_numeric(X[col], col, method='robust')
                    
                    feature_parts.append(data)
                    feature_names.append(name)
                    
                    # Add polynomial features for important numerics
                    if len(X.columns) <= 10:
                        sq_data = data ** 2
                        feature_parts.append(sq_data)
                        feature_names.append(f"{col}^2")
                    
                else:
                    # Categorical: smart encoding
                    nunique = X[col].nunique()
                    
                    if nunique <= 5:
                        data, names = self._encode_categorical(X[col], col, method='onehot')
                    elif nunique <= 50:
                        data, names = self._encode_target(X[col], col, y)
                    else:
                        data, names = self._encode_categorical(X[col], col, method='label')
                    
                    feature_parts.append(data)
                    feature_names.extend(names)
                    
            except Exception as e:
                self.logger.warning(f"   ⚠️ Skipped {col}: {str(e)[:30]}")
        
        if not feature_parts:
            return np.zeros((len(X), 1)), ["_empty_"]
        
        X_processed = np.hstack(feature_parts)
        self.logger.info(f"   ✅ Generated {X_processed.shape[1]} features (deep mode)")
        
        return X_processed, feature_names
    
    # =========================================================================
    # TRANSFORMATION METHODS
    # =========================================================================
    
    def _scale_numeric(self, series: pd.Series, col: str, method: str = 'robust') -> Tuple[np.ndarray, str]:
        """Scale numeric column"""
        from sklearn.preprocessing import RobustScaler, StandardScaler
        
        data = series.fillna(series.median()).values.reshape(-1, 1)
        
        if method == 'robust':
            scaler = RobustScaler()
        else:
            scaler = StandardScaler()
        
        scaled = scaler.fit_transform(data)
        self.transformers[f"{col}_scaler"] = scaler
        
        self.decisions.append(PreprocessingDecision(col, f"{method}_scaling", "Numeric column", {}))
        
        return scaled, col
    
    def _transform_skewed(self, series: pd.Series, col: str) -> Tuple[np.ndarray, str]:
        """Transform skewed numeric column"""
        data = series.fillna(0).values
        
        # Use log1p for non-negative, else standard scaling
        if data.min() >= 0:
            transformed = np.log1p(data).reshape(-1, 1)
            self.decisions.append(PreprocessingDecision(col, "log1p", f"Skewed (skew={series.skew():.1f})", {}))
        else:
            from sklearn.preprocessing import RobustScaler
            scaler = RobustScaler()
            transformed = scaler.fit_transform(data.reshape(-1, 1))
            self.transformers[f"{col}_scaler"] = scaler
            self.decisions.append(PreprocessingDecision(col, "robust_scaling", "Skewed but has negatives", {}))
        
        return transformed, col
    
    def _encode_categorical(self, series: pd.Series, col: str, method: str = 'auto') -> Tuple[np.ndarray, List[str]]:
        """Encode categorical column"""
        series = series.fillna("_MISSING_").astype(str)
        nunique = series.nunique()
        
        if method == 'onehot' or (method == 'auto' and nunique <= 10):
            # One-hot encoding
            dummies = pd.get_dummies(series, prefix=col, drop_first=True)
            self.decisions.append(PreprocessingDecision(col, "onehot", f"{nunique} categories", {}))
            return dummies.values.astype(float), dummies.columns.tolist()
        else:
            # Label encoding
            from sklearn.preprocessing import LabelEncoder
            le = LabelEncoder()
            encoded = le.fit_transform(series).reshape(-1, 1).astype(float)
            self.transformers[f"{col}_encoder"] = le
            self.decisions.append(PreprocessingDecision(col, "label", f"{nunique} categories", {}))
            return encoded, [f"{col}_encoded"]
    
    def _encode_target(self, series: pd.Series, col: str, y: pd.Series) -> Tuple[np.ndarray, List[str]]:
        """Target encoding for categorical column"""
        series = series.fillna("_MISSING_").astype(str)
        
        try:
            y_numeric = pd.to_numeric(y, errors='coerce')
            if y_numeric.notna().sum() < len(y) * 0.5:
                # Target is not numeric, fall back to label encoding
                return self._encode_categorical(series, col, method='label')
            
            global_mean = y_numeric.mean()
            target_means = {}
            
            for cat in series.unique():
                mask = series == cat
                if mask.sum() >= 5:
                    target_means[cat] = y_numeric[mask].mean()
                else:
                    target_means[cat] = global_mean
            
            encoded = series.map(target_means).fillna(global_mean).values.reshape(-1, 1)
            self.transformers[f"{col}_target_enc"] = target_means
            self.decisions.append(PreprocessingDecision(col, "target_encoding", f"{series.nunique()} categories", {}))
            
            return encoded.astype(float), [f"{col}_target_enc"]
            
        except Exception as e:
            return self._encode_categorical(series, col, method='label')
    
    def _process_target(self, y: pd.Series) -> Tuple[np.ndarray, str]:
        """Process target variable and detect task type"""
        y_clean = y.dropna()
        
        # Try to convert to numeric
        y_numeric = pd.to_numeric(y_clean, errors='coerce')
        numeric_ratio = y_numeric.notna().sum() / len(y_clean)
        
        if numeric_ratio > 0.9:
            # Numeric target
            nunique = y_numeric.nunique()
            is_decimal = (y_numeric % 1 != 0).any()
            
            if is_decimal or nunique > 20:
                task_type = "regression"
                y_processed = y_numeric.fillna(y_numeric.median()).values
            else:
                task_type = "classification"
                from sklearn.preprocessing import LabelEncoder
                le = LabelEncoder()
                y_processed = le.fit_transform(y_clean.astype(str))
                self.transformers["target_encoder"] = le
        else:
            # Categorical target
            task_type = "classification"
            from sklearn.preprocessing import LabelEncoder
            le = LabelEncoder()
            y_processed = le.fit_transform(y_clean.astype(str))
            self.transformers["target_encoder"] = le
        
        self.logger.info(f"   📋 Task type: {task_type}")
        
        return y_processed, task_type
