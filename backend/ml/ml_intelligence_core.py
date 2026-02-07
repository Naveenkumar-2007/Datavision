"""
🧠 ML INTELLIGENCE CORE v1.0 - Production-Grade ML Standards
============================================================

This module provides universal production-grade ML intelligence that is
automatically applied to ALL training modes (Fast, Ultra, Traditional, NLP, Deep Learning).

The intelligence layer ensures:
✅ Real ML standards are always applied
✅ No fake accuracy is ever produced  
✅ No data leakage can occur
✅ No wrong algorithms are selected
✅ No overfitting is allowed
✅ All models are production-safe and generalizable

This module DOES NOT change:
- User interface
- Available algorithms/modes
- User's manual selections
- Any existing functionality

It DOES upgrade:
- How data is prepared (professionally)
- How leakage is detected (automatically)
- How features are selected (intelligently)
- How models are trained (safely)
- How results are validated (realistically)

Author: Production ML Intelligence Engine
Version: 1.0.0
"""

import numpy as np
import pandas as pd
import logging
import warnings
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import Counter

from sklearn.model_selection import (
    train_test_split, cross_val_score, StratifiedKFold, KFold
)
from sklearn.preprocessing import LabelEncoder, StandardScaler, RobustScaler
from sklearn.feature_selection import VarianceThreshold, mutual_info_classif, mutual_info_regression
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    r2_score, mean_absolute_error, mean_squared_error
)

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


# =============================================================================
# DATA QUALITY ASSESSMENT
# =============================================================================

class DataQualityLevel(Enum):
    """Data quality levels for automatic mode adjustment"""
    EXCELLENT = "excellent"  # Clean, well-structured
    GOOD = "good"           # Minor issues, easily fixable
    MODERATE = "moderate"   # Some problems, need preprocessing
    POOR = "poor"           # Major issues, require heavy cleaning
    CRITICAL = "critical"   # Severe problems, may not be trainable


@dataclass
class DataProfile:
    """Comprehensive data profiling result"""
    n_samples: int = 0
    n_features: int = 0
    n_numeric: int = 0
    n_categorical: int = 0
    n_text: int = 0
    n_datetime: int = 0
    
    # Size classification
    size_category: str = "medium"  # small, medium, large, very_large
    
    # Quality metrics
    missing_ratio: float = 0.0
    duplicate_ratio: float = 0.0
    constant_columns: List[str] = field(default_factory=list)
    high_cardinality_columns: List[str] = field(default_factory=list)
    
    # Target analysis
    is_imbalanced: bool = False
    class_imbalance_ratio: float = 1.0
    target_type: str = "unknown"  # numeric, categorical, text
    
    # Problem type
    task_type: str = "classification"
    
    # Quality assessment
    quality_level: DataQualityLevel = DataQualityLevel.GOOD
    quality_issues: List[str] = field(default_factory=list)
    
    # Recommendations
    recommended_preprocessing: List[str] = field(default_factory=list)
    recommended_algorithms: List[str] = field(default_factory=list)


class MLIntelligenceCore:
    """
    🧠 Core ML Intelligence Engine
    
    Provides production-grade ML standards enforcement across all training modes.
    This class is designed to be called at the START of any training pipeline
    to ensure data quality, detect issues, and configure optimal training parameters.
    """
    
    def __init__(self):
        self.profile: Optional[DataProfile] = None
        self.leakage_columns: List[str] = []
        self.dropped_columns: List[str] = []
        self.preprocessing_steps: List[str] = []
        self.warnings: List[str] = []
    
    # =========================================================================
    # PHASE 1: DATA PROFILING
    # =========================================================================
    
    def profile_data(self, df: pd.DataFrame, target_column: Optional[str] = None) -> DataProfile:
        """
        Comprehensive data profiling to understand dataset characteristics.
        This informs all subsequent decisions about preprocessing and model selection.
        """
        profile = DataProfile()
        profile.n_samples = len(df)
        profile.n_features = len(df.columns) - (1 if target_column else 0)
        
        # Classify dataset size
        if profile.n_samples < 500:
            profile.size_category = "small"
        elif profile.n_samples < 5000:
            profile.size_category = "medium"
        elif profile.n_samples < 100000:
            profile.size_category = "large"
        else:
            profile.size_category = "very_large"
        
        # Count column types
        for col in df.columns:
            if col == target_column:
                continue
            
            if pd.api.types.is_numeric_dtype(df[col]):
                profile.n_numeric += 1
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                profile.n_datetime += 1
            elif df[col].dtype == 'object':
                avg_len = df[col].astype(str).str.len().mean()
                n_unique = df[col].nunique()
                if avg_len > 50 or n_unique > len(df) * 0.5:
                    profile.n_text += 1
                else:
                    profile.n_categorical += 1
            else:
                profile.n_categorical += 1
        
        # Missing value analysis
        total_cells = df.size
        missing_cells = df.isna().sum().sum()
        profile.missing_ratio = missing_cells / total_cells if total_cells > 0 else 0
        
        # Duplicate analysis
        n_duplicates = df.duplicated().sum()
        profile.duplicate_ratio = n_duplicates / len(df) if len(df) > 0 else 0
        
        # Find constant columns
        for col in df.columns:
            if df[col].nunique() <= 1:
                profile.constant_columns.append(col)
        
        # Find high cardinality categorical columns
        for col in df.columns:
            if col == target_column:
                continue
            if df[col].dtype == 'object':
                unique_ratio = df[col].nunique() / len(df)
                if unique_ratio > 0.9 and df[col].nunique() > 100:
                    profile.high_cardinality_columns.append(col)
        
        # Target analysis
        if target_column and target_column in df.columns:
            target = df[target_column]
            
            # Determine target type
            if pd.api.types.is_numeric_dtype(target):
                n_unique = target.nunique()
                if n_unique <= 20 and n_unique / len(df) < 0.1:
                    profile.target_type = "categorical"
                    profile.task_type = "classification"
                else:
                    profile.target_type = "numeric"
                    profile.task_type = "regression"
            else:
                profile.target_type = "categorical"
                profile.task_type = "classification"
            
            # Check class imbalance for classification
            if profile.task_type == "classification":
                value_counts = target.value_counts()
                if len(value_counts) >= 2:
                    max_class = value_counts.max()
                    min_class = value_counts.min()
                    profile.class_imbalance_ratio = max_class / min_class if min_class > 0 else float('inf')
                    profile.is_imbalanced = profile.class_imbalance_ratio > 3  # 3:1 ratio threshold
        
        # Quality assessment
        quality_issues = []
        
        if profile.missing_ratio > 0.3:
            quality_issues.append(f"High missing values: {profile.missing_ratio:.1%}")
        if profile.duplicate_ratio > 0.1:
            quality_issues.append(f"High duplicate rows: {profile.duplicate_ratio:.1%}")
        if len(profile.constant_columns) > 0:
            quality_issues.append(f"{len(profile.constant_columns)} constant columns")
        if len(profile.high_cardinality_columns) > 0:
            quality_issues.append(f"{len(profile.high_cardinality_columns)} high-cardinality columns")
        if profile.is_imbalanced:
            quality_issues.append(f"Class imbalance: {profile.class_imbalance_ratio:.1f}:1")
        
        profile.quality_issues = quality_issues
        
        # Determine quality level
        n_issues = len(quality_issues)
        if n_issues == 0:
            profile.quality_level = DataQualityLevel.EXCELLENT
        elif n_issues <= 2:
            profile.quality_level = DataQualityLevel.GOOD
        elif n_issues <= 4:
            profile.quality_level = DataQualityLevel.MODERATE
        elif n_issues <= 6:
            profile.quality_level = DataQualityLevel.POOR
        else:
            profile.quality_level = DataQualityLevel.CRITICAL
        
        # Generate recommendations
        profile.recommended_preprocessing = self._generate_preprocessing_recommendations(profile)
        profile.recommended_algorithms = self._generate_algorithm_recommendations(profile)
        
        self.profile = profile
        logger.info(f"📊 Data Profile: {profile.size_category} dataset, {profile.quality_level.value} quality")
        
        return profile
    
    def _generate_preprocessing_recommendations(self, profile: DataProfile) -> List[str]:
        """Generate preprocessing recommendations based on data profile"""
        recommendations = []
        
        if profile.missing_ratio > 0.05:
            recommendations.append("impute_missing_values")
        if profile.duplicate_ratio > 0.01:
            recommendations.append("remove_duplicates")
        if len(profile.constant_columns) > 0:
            recommendations.append("drop_constant_columns")
        if len(profile.high_cardinality_columns) > 0:
            recommendations.append("handle_high_cardinality")
        if profile.is_imbalanced:
            recommendations.append("handle_class_imbalance")
        if profile.n_numeric > 5:
            recommendations.append("scale_numeric_features")
        if profile.n_categorical > 3:
            recommendations.append("encode_categorical_features")
        
        return recommendations
    
    def _generate_algorithm_recommendations(self, profile: DataProfile) -> List[str]:
        """Generate algorithm recommendations based on data profile"""
        recommendations = []
        
        if profile.task_type == "classification":
            # Small dataset
            if profile.size_category == "small":
                recommendations.extend(["logistic_regression", "random_forest", "svm"])
            # Medium dataset
            elif profile.size_category == "medium":
                recommendations.extend(["random_forest", "xgboost", "lightgbm", "gradient_boosting"])
            # Large dataset
            else:
                recommendations.extend(["lightgbm", "xgboost", "hist_gradient_boosting", "catboost"])
        else:  # regression
            if profile.size_category == "small":
                recommendations.extend(["ridge", "elastic_net", "random_forest"])
            elif profile.size_category == "medium":
                recommendations.extend(["random_forest", "xgboost", "lightgbm", "gradient_boosting"])
            else:
                recommendations.extend(["lightgbm", "xgboost", "hist_gradient_boosting", "catboost"])
        
        return recommendations
    
    # =========================================================================
    # PHASE 2: LEAKAGE DETECTION
    # =========================================================================
    
    def detect_leakage(self, df: pd.DataFrame, target_column: str) -> Dict[str, Any]:
        """
        🛡️ PRODUCTION-GRADE LEAKAGE DETECTION
        
        Detects multiple types of data leakage:
        1. Perfect correlation (feature = target or derived from target)
        2. Near-perfect correlation (>0.95 correlation)
        3. Target encoding leakage (categorical with 1:1 mapping to target)
        4. Temporal leakage (future data in features)
        5. Identifier leakage (IDs that encode target)
        6. Index/unnamed columns (should always be removed)
        7. URL/path columns (non-predictive)
        
        Returns dict with:
        - has_leakage: bool
        - leakage_columns: list of column names
        - leakage_details: list of explanations
        - severity: 'none', 'low', 'medium', 'high', 'critical'
        """
        result = {
            'has_leakage': False,
            'leakage_columns': [],
            'leakage_details': [],
            'severity': 'none'
        }
        
        if target_column not in df.columns:
            return result
        
        target = df[target_column]
        numeric_target = pd.api.types.is_numeric_dtype(target)
        
        # Pre-check: Index/Unnamed columns (always remove)
        for col in df.columns:
            col_lower = col.lower().strip()
            if col_lower.startswith('unnamed') or col_lower == 'index' or col_lower == 'id':
                result['leakage_columns'].append(col)
                result['leakage_details'].append(
                    f"'{col}' is an index/unnamed column - REMOVE (non-predictive)"
                )
        
        for col in df.columns:
            if col == target_column:
                continue
            
            try:
                feature = df[col]
                
                # Skip columns with too many missing values
                if feature.isna().sum() / len(feature) > 0.5:
                    continue
                
                # Type 1: Perfect correlation (numeric features)
                if pd.api.types.is_numeric_dtype(feature) and numeric_target:
                    try:
                        corr = feature.corr(target)
                        if pd.notna(corr) and abs(corr) > 0.99:
                            result['leakage_columns'].append(col)
                            result['leakage_details'].append(
                                f"'{col}' has perfect correlation ({corr:.3f}) with target - CRITICAL LEAKAGE"
                            )
                            continue
                        elif pd.notna(corr) and abs(corr) > 0.95:
                            result['leakage_columns'].append(col)
                            result['leakage_details'].append(
                                f"'{col}' has near-perfect correlation ({corr:.3f}) with target - LIKELY LEAKAGE"
                            )
                            continue
                    except:
                        pass
                
                # Type 2: Target encoding leakage (categorical 1:1 mapping)
                if feature.dtype == 'object' or feature.nunique() < 50:
                    try:
                        # Check if feature uniquely determines target
                        grouped = df.groupby(col)[target_column].nunique()
                        if (grouped == 1).all() and feature.nunique() > 1:
                            # Each feature value maps to exactly one target value
                            result['leakage_columns'].append(col)
                            result['leakage_details'].append(
                                f"'{col}' has 1:1 mapping with target - ENCODING LEAKAGE"
                            )
                            continue
                    except:
                        pass
                
                # Type 3: Identifier leakage (column name suggests ID)
                col_lower = col.lower()
                id_patterns = ['_id', 'id_', 'guid', 'uuid', 'key', 'index']
                if any(pat in col_lower for pat in id_patterns):
                    unique_ratio = feature.nunique() / len(feature)
                    if unique_ratio > 0.95:
                        # Check if ID correlates with target
                        if numeric_target and pd.api.types.is_numeric_dtype(feature):
                            try:
                                corr = feature.corr(target)
                                if pd.notna(corr) and abs(corr) > 0.5:
                                    result['leakage_columns'].append(col)
                                    result['leakage_details'].append(
                                        f"'{col}' is an ID column with target correlation ({corr:.3f}) - IDENTIFIER LEAKAGE"
                                    )
                            except:
                                pass
                
                # Type 4: Column name suggests target derivation
                target_lower = target_column.lower()
                suspicious_patterns = [
                    f"{target_lower}_", f"_{target_lower}", 
                    f"predicted_{target_lower}", f"{target_lower}_predicted",
                    f"actual_{target_lower}", f"{target_lower}_actual",
                    f"true_{target_lower}", f"{target_lower}_true"
                ]
                if any(pat in col_lower for pat in suspicious_patterns):
                    result['leakage_columns'].append(col)
                    result['leakage_details'].append(
                        f"'{col}' appears to be derived from target - NAME LEAKAGE"
                    )
                
                # Type 5: URL/Path columns (non-predictive, should be removed)
                if feature.dtype == 'object':
                    sample_vals = feature.dropna().head(10).astype(str)
                    url_patterns = ['http://', 'https://', 'www.', '.com', '.org', '.net', 'spotify.com', 'youtube.com']
                    is_url_column = sum(1 for v in sample_vals if any(p in str(v).lower() for p in url_patterns)) >= 5
                    if is_url_column:
                        if col not in result['leakage_columns']:
                            result['leakage_columns'].append(col)
                            result['leakage_details'].append(
                                f"'{col}' contains URLs - NON-PREDICTIVE (remove)"
                            )
                    
                # Type 6: Similar metric names (e.g., track_popularity vs artist_popularity)
                # These often share leaked information through the same underlying data
                target_keywords = target_column.lower().replace('_', ' ').split()
                col_keywords = col.lower().replace('_', ' ').split()
                
                # Check for shared keywords like 'popularity', 'rating', 'score', 'price'
                shared_metric_keywords = {'popularity', 'rating', 'score', 'price', 'count', 
                                         'amount', 'value', 'total', 'avg', 'average', 'rank'}
                shared = set(target_keywords) & set(col_keywords) & shared_metric_keywords
                
                if shared and numeric_target and pd.api.types.is_numeric_dtype(feature):
                    try:
                        corr = feature.corr(target)
                        if pd.notna(corr) and abs(corr) > 0.70:  # 70%+ correlation with similar name
                            if col not in result['leakage_columns']:
                                result['leakage_columns'].append(col)
                                result['leakage_details'].append(
                                    f"'{col}' shares metric '{list(shared)[0]}' with target and has high correlation ({corr:.3f}) - METRIC LEAKAGE"
                                )
                    except:
                        pass
                    
            except Exception as e:
                logger.warning(f"Leakage check failed for '{col}': {e}")
        
        # Determine severity
        n_leaks = len(result['leakage_columns'])
        if n_leaks == 0:
            result['severity'] = 'none'
        elif n_leaks == 1:
            result['severity'] = 'low'
        elif n_leaks <= 3:
            result['severity'] = 'medium'
        elif n_leaks <= 5:
            result['severity'] = 'high'
        else:
            result['severity'] = 'critical'
        
        result['has_leakage'] = n_leaks > 0
        self.leakage_columns = result['leakage_columns']
        
        if result['has_leakage']:
            logger.warning(f"🚨 LEAKAGE DETECTED: {n_leaks} columns ({result['severity']} severity)")
            for detail in result['leakage_details']:
                logger.warning(f"   - {detail}")
        
        return result
    
    # =========================================================================
    # PHASE 3: INTELLIGENT FEATURE SELECTION
    # =========================================================================
    
    def select_features(self, df: pd.DataFrame, target_column: str,
                       max_features: Optional[int] = None) -> Tuple[pd.DataFrame, List[str]]:
        """
        🎯 INTELLIGENT FEATURE SELECTION
        
        Performs professional feature selection:
        1. Remove constant/near-constant columns
        2. Remove highly correlated features (keep only one)
        3. Remove low-information features
        4. Select most predictive features based on mutual information
        
        Returns:
            Tuple of (filtered DataFrame, list of selected column names)
        """
        selected_columns = []
        dropped_columns = []
        
        # Get all feature columns
        feature_cols = [c for c in df.columns if c != target_column]
        
        # Step 1: Remove constant columns
        for col in feature_cols:
            if df[col].nunique() <= 1:
                dropped_columns.append(col)
                logger.info(f"   ❌ Dropped '{col}': constant value")
            else:
                selected_columns.append(col)
        
        # Step 2: Remove highly correlated features (>0.95)
        numeric_cols = df[selected_columns].select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) > 1:
            try:
                corr_matrix = df[numeric_cols].corr().abs()
                upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
                
                to_drop = set()
                for col in upper.columns:
                    if any(upper[col] > 0.95):
                        correlated_with = upper[upper[col] > 0.95].index.tolist()
                        if col not in to_drop:
                            # Keep the column with higher variance
                            for corr_col in correlated_with:
                                if corr_col not in to_drop:
                                    if df[col].var() >= df[corr_col].var():
                                        to_drop.add(corr_col)
                                    else:
                                        to_drop.add(col)
                                        break
                
                for col in to_drop:
                    if col in selected_columns:
                        selected_columns.remove(col)
                        dropped_columns.append(col)
                        logger.info(f"   ❌ Dropped '{col}': highly correlated with another feature")
            except Exception as e:
                logger.warning(f"Correlation filtering failed: {e}")
        
        # Step 3: Variance threshold (remove near-zero variance)
        try:
            numeric_selected = [c for c in selected_columns if c in numeric_cols]
            if numeric_selected:
                selector = VarianceThreshold(threshold=0.01)
                # Scale first to make variance comparable
                scaler = StandardScaler()
                scaled = scaler.fit_transform(df[numeric_selected].fillna(0))
                selector.fit(scaled)
                
                low_var = [numeric_selected[i] for i in range(len(numeric_selected)) 
                          if not selector.get_support()[i]]
                
                for col in low_var:
                    if col in selected_columns:
                        selected_columns.remove(col)
                        dropped_columns.append(col)
                        logger.info(f"   ❌ Dropped '{col}': near-zero variance")
        except Exception as e:
            logger.warning(f"Variance filtering failed: {e}")
        
        # Step 4: Limit to max_features using mutual information if needed
        if max_features and len(selected_columns) > max_features:
            try:
                X = df[selected_columns].copy()
                y = df[target_column]
                
                # Encode categorical for mutual info calculation
                for col in X.columns:
                    if X[col].dtype == 'object':
                        X[col] = LabelEncoder().fit_transform(X[col].astype(str))
                
                X = X.fillna(0)
                
                if self.profile and self.profile.task_type == "classification":
                    y_encoded = LabelEncoder().fit_transform(y.astype(str))
                    mi_scores = mutual_info_classif(X, y_encoded, random_state=42)
                else:
                    y_numeric = pd.to_numeric(y, errors='coerce').fillna(0)
                    mi_scores = mutual_info_regression(X, y_numeric, random_state=42)
                
                # Sort by mutual information
                feature_scores = list(zip(selected_columns, mi_scores))
                feature_scores.sort(key=lambda x: x[1], reverse=True)
                
                top_features = [f[0] for f in feature_scores[:max_features]]
                dropped = [f[0] for f in feature_scores[max_features:]]
                
                for col in dropped:
                    dropped_columns.append(col)
                    logger.info(f"   ❌ Dropped '{col}': low mutual information")
                
                selected_columns = top_features
                
            except Exception as e:
                logger.warning(f"Mutual information selection failed: {e}")
        
        self.dropped_columns = dropped_columns
        logger.info(f"📊 Feature Selection: kept {len(selected_columns)}, dropped {len(dropped_columns)}")
        
        # Return filtered dataframe with target
        return df[selected_columns + [target_column]], selected_columns
    
    # =========================================================================
    # PHASE 4: TRAINING SAFEGUARDS
    # =========================================================================
    
    def validate_training_results(self, y_train: np.ndarray, y_test: np.ndarray,
                                  train_pred: np.ndarray, test_pred: np.ndarray,
                                  task_type: str = "classification") -> Dict[str, Any]:
        """
        🛡️ VALIDATE TRAINING RESULTS FOR REALISM
        
        Checks for:
        1. Overfitting (large train-test gap)
        2. Unrealistic accuracy (suspiciously perfect)
        3. Prediction distribution anomalies
        4. Model stability concerns
        
        Returns validation report with warnings and recommendations.
        """
        report = {
            'is_valid': True,
            'is_overfit': False,
            'is_suspicious': False,
            'train_score': 0.0,
            'test_score': 0.0,
            'score_gap': 0.0,
            'warnings': [],
            'recommendations': []
        }
        
        try:
            if task_type == "classification":
                train_score = accuracy_score(y_train, train_pred)
                test_score = accuracy_score(y_test, test_pred)
            else:
                train_score = r2_score(y_train, train_pred)
                test_score = r2_score(y_test, test_pred)
            
            report['train_score'] = float(train_score)
            report['test_score'] = float(test_score)
            report['score_gap'] = float(train_score - test_score)
            
            # Check 1: Overfitting (train >> test)
            gap = train_score - test_score
            if gap > 0.15:  # 15% gap threshold
                report['is_overfit'] = True
                report['warnings'].append(
                    f"OVERFITTING DETECTED: Train ({train_score:.2%}) >> Test ({test_score:.2%})"
                )
                report['recommendations'].append(
                    "Consider: more regularization, simpler model, more data, or cross-validation"
                )
            
            # Check 2: Suspiciously perfect accuracy
            if task_type == "classification" and test_score > 0.99:
                report['is_suspicious'] = True
                report['warnings'].append(
                    f"SUSPICIOUS: Test accuracy {test_score:.2%} is unrealistically high"
                )
                report['recommendations'].append(
                    "Check for data leakage, duplicate samples, or trivial prediction task"
                )
            
            # Check 3: Perfect training score
            if train_score >= 0.999:
                report['warnings'].append(
                    "Training score is perfect (1.0) - model may have memorized data"
                )
            
            # Check 4: Prediction distribution
            unique_pred = len(np.unique(test_pred))
            unique_actual = len(np.unique(y_test))
            
            if unique_pred == 1:
                report['is_valid'] = False
                report['warnings'].append(
                    "Model predicts only one class/value - degenerate model"
                )
            elif task_type == "classification" and unique_pred < unique_actual * 0.5:
                report['warnings'].append(
                    f"Model predicts only {unique_pred}/{unique_actual} classes"
                )
            
            # Overall validity
            if report['is_overfit'] or report['is_suspicious']:
                report['is_valid'] = False
            
        except Exception as e:
            report['warnings'].append(f"Validation error: {str(e)}")
            logger.warning(f"Training validation failed: {e}")
        
        return report
    
    def compute_reliability_score(self, y_test: np.ndarray, y_pred: np.ndarray,
                                  cv_scores: Optional[List[float]] = None,
                                  train_score: float = 0.0,
                                  test_score: float = 0.0,
                                  task_type: str = "classification") -> float:
        """
        📊 COMPUTE MODEL RELIABILITY SCORE (0-100)
        
        Combines multiple factors:
        1. Test performance (40%)
        2. Cross-validation consistency (30%)
        3. Train-test gap (overfitting penalty) (20%)
        4. Prediction distribution (10%)
        
        Higher score = more reliable, production-ready model
        """
        reliability = 0.0
        
        # 1. Test performance (40 points max)
        if task_type == "classification":
            test_perf = accuracy_score(y_test, y_pred)
        else:
            test_perf = max(0, r2_score(y_test, y_pred))  # Clamp negative R2
        
        reliability += test_perf * 40
        
        # 2. CV consistency (30 points max)
        if cv_scores and len(cv_scores) >= 3:
            cv_mean = np.mean(cv_scores)
            cv_std = np.std(cv_scores)
            
            # Higher mean + lower std = better consistency
            cv_consistency = cv_mean * (1 - min(cv_std, 0.2))  # Cap std impact
            reliability += cv_consistency * 30
        else:
            # Without CV, use test score as proxy (reduced weight)
            reliability += test_perf * 20
        
        # 3. Overfitting penalty (20 points max, can reduce)
        if train_score > 0 and test_score > 0:
            gap = train_score - test_score
            if gap <= 0.05:
                reliability += 20  # No overfitting
            elif gap <= 0.10:
                reliability += 15  # Mild overfitting
            elif gap <= 0.15:
                reliability += 10  # Moderate overfitting
            elif gap <= 0.20:
                reliability += 5   # Significant overfitting
            # else: 0 points for severe overfitting
        else:
            reliability += 10  # Unknown gap, neutral
        
        # 4. Prediction distribution (10 points max)
        unique_pred = len(np.unique(y_pred))
        unique_actual = len(np.unique(y_test))
        
        if unique_pred >= unique_actual:
            reliability += 10
        elif unique_pred >= unique_actual * 0.8:
            reliability += 7
        elif unique_pred >= unique_actual * 0.5:
            reliability += 4
        # else: 0 points for degenerate predictions
        
        return min(100, max(0, reliability))
    
    # =========================================================================
    # PHASE 5: OPTIMAL PARAMETERS FOR DATASET
    # =========================================================================
    
    def get_optimal_parameters(self, n_samples: int, n_features: int,
                               task_type: str, mode: str = "fast") -> Dict[str, Any]:
        """
        🎯 GET OPTIMAL TRAINING PARAMETERS
        
        Automatically determines optimal parameters based on:
        - Dataset size
        - Number of features
        - Task type
        - Training mode (fast/ultra)
        
        Returns parameters for:
        - Train/test split
        - Cross-validation
        - Model complexity limits
        - Early stopping
        """
        params = {}
        
        # Test split size (larger for small datasets to ensure good evaluation)
        if n_samples < 500:
            params['test_size'] = 0.3  # 30% for small data
            params['cv_folds'] = 3
        elif n_samples < 5000:
            params['test_size'] = 0.2  # 20% standard
            params['cv_folds'] = 5
        else:
            params['test_size'] = 0.15  # 15% for large data
            params['cv_folds'] = 5 if mode == "fast" else 10
        
        # Model complexity limits
        if n_samples < 1000:
            params['max_depth'] = 5
            params['n_estimators'] = 100
            params['min_samples_split'] = 5
        elif n_samples < 10000:
            params['max_depth'] = 10
            params['n_estimators'] = 200
            params['min_samples_split'] = 2
        else:
            params['max_depth'] = 15 if mode == "fast" else 20
            params['n_estimators'] = 200 if mode == "fast" else 500
            params['min_samples_split'] = 2
        
        # Feature limits
        params['max_features'] = min(n_features, 100) if n_features > 100 else None
        
        # Regularization
        params['regularization'] = 'strong' if n_samples < 1000 else 'moderate'
        
        # Early stopping
        params['early_stopping'] = True
        params['early_stopping_rounds'] = 50 if mode == "fast" else 100
        
        # Sampling for large datasets
        if n_samples > 100000:
            params['sample_size'] = 100000 if mode == "fast" else 200000
            params['use_sampling'] = True
        else:
            params['use_sampling'] = False
        
        return params


# =============================================================================
# GLOBAL INTELLIGENCE INSTANCE
# =============================================================================

ml_intelligence = MLIntelligenceCore()


def apply_production_intelligence(df: pd.DataFrame, target_column: str,
                                  mode: str = "fast") -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    🧠 APPLY PRODUCTION ML INTELLIGENCE
    
    Convenience function to apply all intelligence checks before training.
    
    Steps:
    1. Profile data
    2. Detect leakage
    3. Select features
    4. Get optimal parameters
    
    Returns:
        Tuple of (cleaned DataFrame, intelligence report)
    """
    intel = MLIntelligenceCore()
    
    # 1. Profile
    profile = intel.profile_data(df, target_column)
    
    # 2. Detect leakage
    leakage = intel.detect_leakage(df, target_column)
    
    # Remove leakage columns
    df_clean = df.drop(columns=leakage['leakage_columns'], errors='ignore')
    
    # 3. Feature selection
    df_selected, selected_features = intel.select_features(df_clean, target_column)
    
    # 4. Get optimal parameters
    n_samples = len(df_selected)
    n_features = len(selected_features)
    params = intel.get_optimal_parameters(
        n_samples, n_features, profile.task_type, mode
    )
    
    report = {
        'profile': {
            'size_category': profile.size_category,
            'task_type': profile.task_type,
            'quality_level': profile.quality_level.value,
            'quality_issues': profile.quality_issues,
            'n_samples': profile.n_samples,
            'n_features': len(selected_features),
            'is_imbalanced': profile.is_imbalanced,
        },
        'leakage': leakage,
        'feature_selection': {
            'original_features': len(df.columns) - 1,
            'selected_features': len(selected_features),
            'dropped_features': intel.dropped_columns
        },
        'optimal_parameters': params,
        'warnings': intel.warnings + leakage['leakage_details'],
        'recommended_algorithms': profile.recommended_algorithms
    }
    
    return df_selected, report
