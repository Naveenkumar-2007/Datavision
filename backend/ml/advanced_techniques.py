"""
🚀 ADVANCED ML TECHNIQUES v1.0
==============================

Extra techniques to enhance AutoML for both Fast and Ultra modes.

Includes:
1. Advanced Feature Engineering (binning, cyclic, rare category handling)
2. Advanced Preprocessing (quantile transform, target encoding)
3. Feature Selection (mutual information, RFE, boruta-style)
4. Data Augmentation (SMOTE variants, noise injection)
5. Model Calibration (isotonic, sigmoid)

Author: AI Business Analyst Team
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from sklearn.preprocessing import (
    QuantileTransformer, PowerTransformer, 
    KBinsDiscretizer, PolynomialFeatures
)
from sklearn.feature_selection import (
    SelectKBest, mutual_info_classif, mutual_info_regression,
    RFE, SelectFromModel, VarianceThreshold
)
from sklearn.calibration import CalibratedClassifierCV
from sklearn.base import BaseEstimator, TransformerMixin
import warnings
warnings.filterwarnings('ignore')


# =============================================================================
# ADVANCED PREPROCESSING TECHNIQUES
# =============================================================================

class AdvancedPreprocessor:
    """
    Advanced preprocessing techniques beyond basic scaling.
    
    Techniques:
    1. Quantile Transform - Makes features gaussian-like
    2. Power Transform (Yeo-Johnson) - Handles skewed data
    3. Winsorization - Robust outlier handling
    4. Feature Clipping - Bound extreme values
    """
    
    def __init__(self, mode: str = 'fast'):
        self.mode = mode
        self.transformers = {}
        self.fitted = False
    
    def fit_transform_quantile(self, X: np.ndarray, feature_names: List[str] = None) -> np.ndarray:
        """
        Apply Quantile Transform to make features more gaussian-like.
        Great for algorithms that assume normal distributions (LDA, QDA, GaussianNB).
        """
        try:
            qt = QuantileTransformer(
                n_quantiles=min(1000, len(X)),
                output_distribution='normal',
                random_state=42
            )
            X_transformed = qt.fit_transform(X)
            self.transformers['quantile'] = qt
            return np.nan_to_num(X_transformed, nan=0.0)
        except Exception as e:
            print(f"   ⚠️ Quantile transform failed: {str(e)[:50]}")
            return X
    
    def fit_transform_power(self, X: np.ndarray) -> np.ndarray:
        """
        Apply Yeo-Johnson Power Transform for skewed features.
        Works with both positive and negative values.
        """
        try:
            pt = PowerTransformer(method='yeo-johnson', standardize=True)
            X_transformed = pt.fit_transform(X)
            self.transformers['power'] = pt
            return np.nan_to_num(X_transformed, nan=0.0)
        except Exception as e:
            print(f"   ⚠️ Power transform failed: {str(e)[:50]}")
            return X
    
    def winsorize(self, X: np.ndarray, lower: float = 0.01, upper: float = 0.99) -> np.ndarray:
        """
        Winsorization - cap extreme values at percentiles.
        More robust than simple clipping.
        """
        X_clipped = X.copy()
        for col in range(X.shape[1]):
            lower_bound = np.percentile(X[:, col], lower * 100)
            upper_bound = np.percentile(X[:, col], upper * 100)
            X_clipped[:, col] = np.clip(X[:, col], lower_bound, upper_bound)
        return X_clipped


# =============================================================================
# ADVANCED FEATURE ENGINEERING
# =============================================================================

class AdvancedFeatureEngineer:
    """
    Advanced feature engineering techniques.
    
    Techniques:
    1. Binning - Discretize continuous features
    2. Cyclic Encoding - For time-based features (hour, day, month)
    3. Rare Category Grouping - Handle high cardinality categoricals
    4. Interaction Features - Polynomial and cross features
    5. Statistical Aggregations - Rolling stats, ratios
    """
    
    def __init__(self, mode: str = 'fast'):
        self.mode = mode
        self.encoders = {}
        self.rare_mappings = {}
    
    def create_bins(self, X: np.ndarray, n_bins: int = 10, strategy: str = 'quantile') -> Tuple[np.ndarray, object]:
        """
        Discretize continuous features into bins.
        Useful for tree-based models and reducing noise.
        
        Args:
            X: Feature array
            n_bins: Number of bins
            strategy: 'quantile', 'uniform', or 'kmeans'
        """
        try:
            discretizer = KBinsDiscretizer(
                n_bins=n_bins, 
                encode='ordinal', 
                strategy=strategy,
                subsample=None  # Use all data
            )
            X_binned = discretizer.fit_transform(X)
            return X_binned, discretizer
        except Exception as e:
            print(f"   ⚠️ Binning failed: {str(e)[:50]}")
            return X, None
    
    def cyclic_encode(self, values: np.ndarray, period: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Cyclic encoding for periodic features (hour, day of week, month).
        Converts to sin/cos to preserve cyclical nature.
        
        Args:
            values: Array of values (e.g., hour 0-23)
            period: Period of the cycle (e.g., 24 for hours)
        """
        sin_values = np.sin(2 * np.pi * values / period)
        cos_values = np.cos(2 * np.pi * values / period)
        return sin_values, cos_values
    
    def encode_datetime_cyclic(self, df: pd.DataFrame, datetime_col: str) -> pd.DataFrame:
        """
        Extract cyclic time features from datetime column.
        Returns: DataFrame with sin/cos encoded time features
        """
        try:
            dt = pd.to_datetime(df[datetime_col])
            
            features = pd.DataFrame()
            
            # Hour (period=24)
            hour_sin, hour_cos = self.cyclic_encode(dt.dt.hour.values, 24)
            features[f'{datetime_col}_hour_sin'] = hour_sin
            features[f'{datetime_col}_hour_cos'] = hour_cos
            
            # Day of week (period=7)
            dow_sin, dow_cos = self.cyclic_encode(dt.dt.dayofweek.values, 7)
            features[f'{datetime_col}_dow_sin'] = dow_sin
            features[f'{datetime_col}_dow_cos'] = dow_cos
            
            # Day of month (period=31)
            dom_sin, dom_cos = self.cyclic_encode(dt.dt.day.values, 31)
            features[f'{datetime_col}_dom_sin'] = dom_sin
            features[f'{datetime_col}_dom_cos'] = dom_cos
            
            # Month (period=12)
            month_sin, month_cos = self.cyclic_encode(dt.dt.month.values, 12)
            features[f'{datetime_col}_month_sin'] = month_sin
            features[f'{datetime_col}_month_cos'] = month_cos
            
            # Year (as continuous)
            features[f'{datetime_col}_year'] = dt.dt.year.values
            
            # Is weekend
            features[f'{datetime_col}_is_weekend'] = (dt.dt.dayofweek >= 5).astype(int)
            
            return features
            
        except Exception as e:
            print(f"   ⚠️ Cyclic datetime encoding failed: {str(e)[:50]}")
            return pd.DataFrame()
    
    def group_rare_categories(self, series: pd.Series, threshold: float = 0.01) -> Tuple[pd.Series, Dict]:
        """
        Group rare categories into '_OTHER_' to reduce cardinality.
        
        Args:
            series: Categorical series
            threshold: Minimum frequency to keep category (default 1%)
        """
        value_counts = series.value_counts(normalize=True)
        rare_categories = value_counts[value_counts < threshold].index.tolist()
        
        mapping = {cat: '_OTHER_' for cat in rare_categories}
        
        if mapping:
            series_grouped = series.replace(mapping)
            self.rare_mappings[series.name] = mapping
            return series_grouped, mapping
        
        return series, {}
    
    def create_interaction_features(
        self, 
        X: np.ndarray, 
        feature_names: List[str],
        degree: int = 2,
        interaction_only: bool = True,
        max_features: int = 50
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Create polynomial interaction features.
        
        Args:
            X: Feature array
            feature_names: List of feature names
            degree: Polynomial degree (2 = pairs, 3 = triples)
            interaction_only: If True, only interaction terms (no x^2)
            max_features: Maximum number of interaction features
        """
        try:
            # Limit input features to avoid explosion
            n_input = min(X.shape[1], 10)
            X_subset = X[:, :n_input]
            names_subset = feature_names[:n_input]
            
            poly = PolynomialFeatures(
                degree=degree,
                interaction_only=interaction_only,
                include_bias=False
            )
            
            X_poly = poly.fit_transform(X_subset)
            
            # Get feature names
            poly_names = poly.get_feature_names_out(names_subset)
            
            # Remove original features (we already have them)
            new_features_mask = ~np.isin(poly_names, names_subset)
            X_interactions = X_poly[:, new_features_mask]
            interaction_names = poly_names[new_features_mask].tolist()
            
            # Limit to max_features most correlated with variance
            if X_interactions.shape[1] > max_features:
                # Select by variance
                variances = np.var(X_interactions, axis=0)
                top_indices = np.argsort(variances)[-max_features:]
                X_interactions = X_interactions[:, top_indices]
                interaction_names = [interaction_names[i] for i in top_indices]
            
            return X_interactions, interaction_names
            
        except Exception as e:
            print(f"   ⚠️ Interaction features failed: {str(e)[:50]}")
            return np.array([]).reshape(len(X), 0), []
    
    def create_statistical_features(
        self, 
        X: np.ndarray, 
        feature_names: List[str]
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Create statistical aggregation features.
        
        Features:
        - Row-wise mean, std, min, max, range
        - Skewness, kurtosis (if enough columns)
        """
        features = []
        names = []
        
        if X.shape[1] >= 3:
            # Row-wise statistics
            features.append(np.mean(X, axis=1).reshape(-1, 1))
            names.append('_row_mean')
            
            features.append(np.std(X, axis=1).reshape(-1, 1))
            names.append('_row_std')
            
            features.append(np.min(X, axis=1).reshape(-1, 1))
            names.append('_row_min')
            
            features.append(np.max(X, axis=1).reshape(-1, 1))
            names.append('_row_max')
            
            features.append((np.max(X, axis=1) - np.min(X, axis=1)).reshape(-1, 1))
            names.append('_row_range')
            
            # Median
            features.append(np.median(X, axis=1).reshape(-1, 1))
            names.append('_row_median')
            
        if X.shape[1] >= 5:
            # Skewness (requires scipy)
            try:
                from scipy.stats import skew, kurtosis
                features.append(skew(X, axis=1).reshape(-1, 1))
                names.append('_row_skew')
                
                features.append(kurtosis(X, axis=1).reshape(-1, 1))
                names.append('_row_kurtosis')
            except:
                pass
        
        if features:
            return np.hstack(features), names
        return np.array([]).reshape(len(X), 0), []


# =============================================================================
# FEATURE SELECTION TECHNIQUES
# =============================================================================

class AdvancedFeatureSelector:
    """
    Advanced feature selection techniques.
    
    Techniques:
    1. Mutual Information - Non-linear correlation
    2. Recursive Feature Elimination (RFE)
    3. Model-based Selection (L1, Tree importance)
    4. Variance Threshold
    5. Correlation Filter
    """
    
    def __init__(self, task_type: str = 'classification', mode: str = 'fast'):
        self.task_type = task_type
        self.mode = mode
        self.selected_features = None
        self.selector = None
    
    def select_by_mutual_info(
        self, 
        X: np.ndarray, 
        y: np.ndarray, 
        k: int = 50,
        feature_names: List[str] = None
    ) -> Tuple[np.ndarray, List[int], Dict[str, float]]:
        """
        Select top k features by mutual information.
        Works for both classification and regression.
        """
        try:
            if self.task_type == 'classification':
                mi_func = mutual_info_classif
            else:
                mi_func = mutual_info_regression
            
            selector = SelectKBest(score_func=mi_func, k=min(k, X.shape[1]))
            X_selected = selector.fit_transform(X, y)
            
            selected_indices = selector.get_support(indices=True).tolist()
            self.selected_features = selected_indices
            self.selector = selector
            
            # Get scores
            scores = selector.scores_
            if feature_names:
                feature_scores = {feature_names[i]: scores[i] for i in selected_indices}
            else:
                feature_scores = {f'feature_{i}': scores[i] for i in selected_indices}
            
            return X_selected, selected_indices, feature_scores
            
        except Exception as e:
            print(f"   ⚠️ Mutual info selection failed: {str(e)[:50]}")
            return X, list(range(X.shape[1])), {}
    
    def select_by_variance(
        self, 
        X: np.ndarray, 
        threshold: float = 0.01
    ) -> Tuple[np.ndarray, List[int]]:
        """
        Remove features with low variance (near-constant).
        """
        try:
            selector = VarianceThreshold(threshold=threshold)
            X_selected = selector.fit_transform(X)
            selected_indices = selector.get_support(indices=True).tolist()
            return X_selected, selected_indices
        except Exception as e:
            print(f"   ⚠️ Variance selection failed: {str(e)[:50]}")
            return X, list(range(X.shape[1]))
    
    def remove_correlated_features(
        self, 
        X: np.ndarray, 
        threshold: float = 0.95,
        feature_names: List[str] = None
    ) -> Tuple[np.ndarray, List[int]]:
        """
        Remove highly correlated features (keeping one from each pair).
        Reduces redundancy and multicollinearity.
        """
        try:
            # Compute correlation matrix
            corr_matrix = np.corrcoef(X.T)
            
            # Handle NaN correlations
            corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
            
            # Find highly correlated pairs
            to_remove = set()
            n_features = X.shape[1]
            
            for i in range(n_features):
                if i in to_remove:
                    continue
                for j in range(i + 1, n_features):
                    if j in to_remove:
                        continue
                    if abs(corr_matrix[i, j]) > threshold:
                        # Remove the one with lower variance
                        if np.var(X[:, i]) < np.var(X[:, j]):
                            to_remove.add(i)
                        else:
                            to_remove.add(j)
            
            selected_indices = [i for i in range(n_features) if i not in to_remove]
            X_selected = X[:, selected_indices]
            
            if to_remove:
                print(f"   ✅ Removed {len(to_remove)} highly correlated features")
            
            return X_selected, selected_indices
            
        except Exception as e:
            print(f"   ⚠️ Correlation filter failed: {str(e)[:50]}")
            return X, list(range(X.shape[1]))
    
    def select_by_model(
        self, 
        X: np.ndarray, 
        y: np.ndarray,
        max_features: int = 50
    ) -> Tuple[np.ndarray, List[int]]:
        """
        Select features using model importance (tree-based or L1).
        """
        try:
            from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
            
            if self.task_type == 'classification':
                model = RandomForestClassifier(
                    n_estimators=100, 
                    max_depth=10, 
                    random_state=42, 
                    n_jobs=-1
                )
            else:
                model = RandomForestRegressor(
                    n_estimators=100, 
                    max_depth=10, 
                    random_state=42, 
                    n_jobs=-1
                )
            
            selector = SelectFromModel(
                model, 
                max_features=max_features, 
                threshold=-np.inf  # Use max_features as limit
            )
            
            X_selected = selector.fit_transform(X, y)
            selected_indices = selector.get_support(indices=True).tolist()
            
            return X_selected, selected_indices
            
        except Exception as e:
            print(f"   ⚠️ Model-based selection failed: {str(e)[:50]}")
            return X, list(range(X.shape[1]))


# =============================================================================
# DATA AUGMENTATION TECHNIQUES
# =============================================================================

class DataAugmentor:
    """
    Data augmentation techniques for small datasets and imbalanced classes.
    
    Techniques:
    1. SMOTE variants (SMOTE, ADASYN, BorderlineSMOTE)
    2. Random oversampling with noise
    3. Synthetic data generation
    """
    
    def __init__(self, task_type: str = 'classification', mode: str = 'fast'):
        self.task_type = task_type
        self.mode = mode
    
    def augment_with_smote(
        self, 
        X: np.ndarray, 
        y: np.ndarray,
        strategy: str = 'auto'
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        SMOTE oversampling with automatic parameter tuning.
        """
        try:
            from imblearn.over_sampling import SMOTE, ADASYN, BorderlineSMOTE
            
            unique, counts = np.unique(y, return_counts=True)
            min_count = min(counts)
            
            # Choose k_neighbors based on minority class size
            k_neighbors = min(5, min_count - 1)
            
            if k_neighbors < 1:
                print("   ⚠️ Too few minority samples for SMOTE")
                return X, y
            
            # Choose SMOTE variant based on mode
            if self.mode == 'ultra' and min_count >= 10:
                # Try BorderlineSMOTE for better quality
                try:
                    sampler = BorderlineSMOTE(
                        k_neighbors=k_neighbors,
                        sampling_strategy=strategy,
                        random_state=42
                    )
                except:
                    sampler = SMOTE(
                        k_neighbors=k_neighbors,
                        sampling_strategy=strategy,
                        random_state=42
                    )
            else:
                sampler = SMOTE(
                    k_neighbors=k_neighbors,
                    sampling_strategy=strategy,
                    random_state=42
                )
            
            X_resampled, y_resampled = sampler.fit_resample(X, y)
            print(f"   ✅ SMOTE: {len(X)} → {len(X_resampled)} samples")
            
            return X_resampled, y_resampled
            
        except ImportError:
            print("   ⚠️ imblearn not installed")
            return X, y
        except Exception as e:
            print(f"   ⚠️ SMOTE failed: {str(e)[:50]}")
            return X, y
    
    def augment_with_noise(
        self, 
        X: np.ndarray, 
        y: np.ndarray,
        noise_factor: float = 0.1,
        n_augmented: int = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Augment by adding Gaussian noise to existing samples.
        Simple but effective for small datasets.
        """
        if n_augmented is None:
            n_augmented = len(X) // 2
        
        # Randomly select samples to augment
        indices = np.random.choice(len(X), n_augmented, replace=True)
        
        # Add noise
        noise = np.random.normal(0, noise_factor, (n_augmented, X.shape[1]))
        std_per_feature = np.std(X, axis=0) + 1e-8
        scaled_noise = noise * std_per_feature
        
        X_augmented = X[indices] + scaled_noise
        y_augmented = y[indices]
        
        # Combine
        X_combined = np.vstack([X, X_augmented])
        y_combined = np.concatenate([y, y_augmented])
        
        print(f"   ✅ Noise augmentation: {len(X)} → {len(X_combined)} samples")
        
        return X_combined, y_combined


# =============================================================================
# MODEL CALIBRATION
# =============================================================================

class ModelCalibrator:
    """
    Probability calibration for better confidence estimates.
    
    Techniques:
    1. Isotonic Regression - Non-parametric, flexible
    2. Sigmoid/Platt Scaling - Parametric, smooth
    """
    
    def __init__(self, method: str = 'isotonic'):
        self.method = method
        self.calibrated_model = None
    
    def calibrate(
        self, 
        model, 
        X_cal: np.ndarray, 
        y_cal: np.ndarray,
        cv: int = 5
    ):
        """
        Calibrate a trained model's probability estimates.
        """
        try:
            self.calibrated_model = CalibratedClassifierCV(
                model,
                method=self.method,
                cv=cv
            )
            self.calibrated_model.fit(X_cal, y_cal)
            print(f"   ✅ Model calibrated with {self.method} method")
            return self.calibrated_model
        except Exception as e:
            print(f"   ⚠️ Calibration failed: {str(e)[:50]}")
            return model


# =============================================================================
# ENHANCED ENSEMBLE TECHNIQUES
# =============================================================================

class EnhancedEnsembleBuilder:
    """
    Advanced ensemble techniques beyond basic voting/stacking.
    
    Techniques:
    1. Weighted Voting (by validation score)
    2. Blending (meta-learner on holdout)
    3. Multi-layer Stacking
    """
    
    def __init__(self, task_type: str = 'classification'):
        self.task_type = task_type
        self.weights = None
        self.ensemble_model = None
    
    def build_weighted_ensemble(
        self, 
        models: List[Tuple[str, Any]], 
        X_val: np.ndarray, 
        y_val: np.ndarray
    ) -> Tuple[Any, Dict[str, float]]:
        """
        Build ensemble with weights based on validation performance.
        """
        from sklearn.ensemble import VotingClassifier, VotingRegressor
        from sklearn.metrics import f1_score, r2_score
        
        # Calculate weights based on validation score
        weights = []
        weight_dict = {}
        
        for name, model in models:
            try:
                y_pred = model.predict(X_val)
                if self.task_type == 'classification':
                    score = f1_score(y_val, y_pred, average='macro', zero_division=0)
                else:
                    score = max(0, r2_score(y_val, y_pred))
                
                # Use exponential weighting for better separation
                weight = np.exp(score * 2)
                weights.append(weight)
                weight_dict[name] = weight
            except:
                weights.append(1.0)
                weight_dict[name] = 1.0
        
        # Normalize weights
        total = sum(weights)
        weights = [w / total for w in weights]
        
        # Update weight dict with normalized
        for i, (name, _) in enumerate(models):
            weight_dict[name] = weights[i]
        
        self.weights = weight_dict
        
        # Build weighted ensemble
        try:
            if self.task_type == 'classification':
                # Check which models support predict_proba
                soft_voting = all(hasattr(m, 'predict_proba') for _, m in models)
                voting = 'soft' if soft_voting else 'hard'
                
                ensemble = VotingClassifier(
                    estimators=models,
                    voting=voting,
                    weights=weights,
                    n_jobs=1
                )
            else:
                ensemble = VotingRegressor(
                    estimators=models,
                    weights=weights,
                    n_jobs=1
                )
            
            self.ensemble_model = ensemble
            return ensemble, weight_dict
            
        except Exception as e:
            print(f"   ⚠️ Weighted ensemble failed: {str(e)[:50]}")
            return None, weight_dict
    
    def blend_predictions(
        self, 
        models: List[Tuple[str, Any]], 
        X_train: np.ndarray, 
        y_train: np.ndarray,
        X_val: np.ndarray, 
        y_val: np.ndarray
    ) -> Any:
        """
        Blending - train meta-learner on holdout predictions.
        More robust than stacking for small datasets.
        """
        from sklearn.linear_model import LogisticRegression, Ridge
        
        # Get predictions on validation set
        val_predictions = []
        for name, model in models:
            try:
                if self.task_type == 'classification' and hasattr(model, 'predict_proba'):
                    pred = model.predict_proba(X_val)
                else:
                    pred = model.predict(X_val).reshape(-1, 1)
                val_predictions.append(pred)
            except:
                continue
        
        if not val_predictions:
            return None
        
        # Stack predictions
        X_blend = np.hstack(val_predictions)
        
        # Train meta-learner
        if self.task_type == 'classification':
            meta_learner = LogisticRegression(max_iter=1000, random_state=42)
        else:
            meta_learner = Ridge(random_state=42)
        
        meta_learner.fit(X_blend, y_val)
        
        # Create blending ensemble
        class BlendingEnsemble:
            def __init__(self, base_models, meta_learner, task_type):
                self.base_models = base_models
                self.meta_learner = meta_learner
                self.task_type = task_type
            
            def predict(self, X):
                predictions = []
                for name, model in self.base_models:
                    try:
                        if self.task_type == 'classification' and hasattr(model, 'predict_proba'):
                            pred = model.predict_proba(X)
                        else:
                            pred = model.predict(X).reshape(-1, 1)
                        predictions.append(pred)
                    except:
                        continue
                
                if not predictions:
                    return np.zeros(len(X))
                
                X_blend = np.hstack(predictions)
                return self.meta_learner.predict(X_blend)
            
            def predict_proba(self, X):
                if self.task_type != 'classification':
                    raise ValueError("predict_proba only for classification")
                
                predictions = []
                for name, model in self.base_models:
                    try:
                        if hasattr(model, 'predict_proba'):
                            pred = model.predict_proba(X)
                        else:
                            pred = model.predict(X).reshape(-1, 1)
                        predictions.append(pred)
                    except:
                        continue
                
                if not predictions:
                    return np.zeros((len(X), 2))
                
                X_blend = np.hstack(predictions)
                return self.meta_learner.predict_proba(X_blend)
        
        return BlendingEnsemble(models, meta_learner, self.task_type)


# =============================================================================
# UTILITY: APPLY ALL ADVANCED TECHNIQUES
# =============================================================================

def apply_advanced_techniques(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    feature_names: List[str],
    task_type: str = 'classification',
    mode: str = 'fast'
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, List[str]]:
    """
    Apply all advanced techniques based on mode.
    
    Fast Mode:
    - Variance filter
    - Remove correlated features
    
    Ultra Mode:
    - All Fast mode techniques
    - Mutual information selection
    - Interaction features
    - Statistical features
    - SMOTE (if imbalanced)
    """
    print("\n🔬 APPLYING ADVANCED TECHNIQUES")
    print("=" * 50)
    
    is_ultra = mode == 'ultra'
    new_feature_names = list(feature_names)
    
    # === FEATURE SELECTION ===
    selector = AdvancedFeatureSelector(task_type=task_type, mode=mode)
    
    # 1. Remove low variance features
    X_train, var_indices = selector.select_by_variance(X_train, threshold=0.01)
    X_test = X_test[:, var_indices]
    new_feature_names = [new_feature_names[i] for i in var_indices]
    print(f"   ✅ Variance filter: {len(feature_names)} → {X_train.shape[1]} features")
    
    # 2. Remove highly correlated features
    X_train, corr_indices = selector.remove_correlated_features(X_train, threshold=0.95)
    X_test = X_test[:, corr_indices]
    new_feature_names = [new_feature_names[i] for i in corr_indices]
    
    if is_ultra:
        # 3. Mutual information selection (top 100 features)
        if X_train.shape[1] > 100:
            X_train, mi_indices, mi_scores = selector.select_by_mutual_info(
                X_train, y_train, k=100, feature_names=new_feature_names
            )
            X_test = X_test[:, mi_indices]
            new_feature_names = [new_feature_names[i] for i in mi_indices]
            print(f"   ✅ Mutual info selection: {len(mi_indices)} features")
        
        # 4. Add interaction features
        engineer = AdvancedFeatureEngineer(mode=mode)
        X_interact, interact_names = engineer.create_interaction_features(
            X_train, new_feature_names, degree=2, max_features=30
        )
        if X_interact.shape[1] > 0:
            X_interact_test, _ = engineer.create_interaction_features(
                X_test, new_feature_names, degree=2, max_features=30
            )
            X_train = np.hstack([X_train, X_interact])
            X_test = np.hstack([X_test, X_interact_test])
            new_feature_names.extend(interact_names)
            print(f"   ✅ Added {len(interact_names)} interaction features")
        
        # 5. Add statistical features
        X_stats, stat_names = engineer.create_statistical_features(X_train, new_feature_names)
        if X_stats.shape[1] > 0:
            X_stats_test, _ = engineer.create_statistical_features(X_test, new_feature_names)
            X_train = np.hstack([X_train, X_stats])
            X_test = np.hstack([X_test, X_stats_test])
            new_feature_names.extend(stat_names)
            print(f"   ✅ Added {len(stat_names)} statistical features")
    
    print(f"   📊 Final feature count: {X_train.shape[1]}")
    
    return X_train, y_train, X_test, y_test, new_feature_names
