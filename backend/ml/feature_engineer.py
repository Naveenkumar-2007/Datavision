"""
🔧 ADVANCED FEATURE ENGINEERING MODULE v1.0
============================================

Automated feature creation for top 1% accuracy:
- Polynomial feature generation
- Feature interaction detection
- Recursive feature elimination (RFECV)
- Target encoding for high-cardinality categoricals
"""

import numpy as np
import pandas as pd
import logging
from typing import List, Dict, Tuple, Any, Optional
from sklearn.preprocessing import PolynomialFeatures
from sklearn.feature_selection import RFECV, SelectKBest, mutual_info_classif, mutual_info_regression
from sklearn.model_selection import cross_val_score

logger = logging.getLogger(__name__)


class AdvancedFeatureEngineer:
    """
    Production-grade feature engineering for top 1% accuracy.
    
    Features:
    - Polynomial feature generation (controlled)
    - Automatic interaction detection
    - Recursive feature elimination
    - Target encoding
    """
    
    def __init__(self):
        self.poly_transformer = None
        self.selected_feature_mask = None
        self.interaction_features = []
        self.target_encodings = {}
        self.feature_names_out = []
    
    def create_polynomial_features(
        self, 
        X: np.ndarray, 
        feature_names: List[str],
        degree: int = 2, 
        top_n: int = 5,
        interaction_only: bool = True
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Create polynomial features from top N most important features.
        
        Args:
            X: Feature matrix
            feature_names: Names of features
            degree: Polynomial degree (2 recommended)
            top_n: Number of top features to use
            interaction_only: If True, only create interactions (no powers)
        
        Returns:
            Tuple of (transformed features, new feature names)
        """
        logger.info(f"🔧 Creating polynomial features (degree={degree}, top_n={top_n})")
        
        # Limit to top N features to avoid explosion
        n_features = min(top_n, X.shape[1])
        X_subset = X[:, :n_features]
        subset_names = feature_names[:n_features]
        
        self.poly_transformer = PolynomialFeatures(
            degree=degree,
            interaction_only=interaction_only,
            include_bias=False
        )
        
        X_poly = self.poly_transformer.fit_transform(X_subset)
        
        # Generate feature names
        poly_names = self.poly_transformer.get_feature_names_out(subset_names)
        
        # Combine with remaining features
        if n_features < X.shape[1]:
            X_combined = np.hstack([X_poly, X[:, n_features:]])
            combined_names = list(poly_names) + feature_names[n_features:]
        else:
            X_combined = X_poly
            combined_names = list(poly_names)
        
        logger.info(f"   ✅ Created {X_poly.shape[1]} polynomial features")
        
        return X_combined, combined_names
    
    def detect_important_interactions(
        self, 
        X: np.ndarray, 
        y: np.ndarray, 
        feature_names: List[str],
        top_k: int = 5,
        is_classification: bool = True
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Automatically detect and create important feature interactions.
        
        Uses mutual information to identify which 2-way interactions
        have the highest predictive power.
        
        Args:
            X: Feature matrix
            y: Target variable
            feature_names: Names of features
            top_k: Number of top interactions to keep
            is_classification: Whether this is a classification task
        
        Returns:
            Tuple of (interaction features, interaction names)
        """
        logger.info(f"🔍 Detecting important feature interactions...")
        
        n_features = X.shape[1]
        interactions = []
        interaction_names = []
        
        # Create all 2-way interactions
        for i in range(min(n_features, 10)):  # Limit to avoid explosion
            for j in range(i + 1, min(n_features, 10)):
                inter = X[:, i] * X[:, j]
                interactions.append(inter)
                name = f"{feature_names[i]}*{feature_names[j]}"
                interaction_names.append(name)
        
        if not interactions:
            return np.array([]).reshape(len(X), 0), []
        
        X_inter = np.column_stack(interactions)
        
        # Score interactions using mutual information
        if is_classification:
            mi_scores = mutual_info_classif(X_inter, y, random_state=42)
        else:
            mi_scores = mutual_info_regression(X_inter, y, random_state=42)
        
        # Select top K interactions
        top_indices = np.argsort(mi_scores)[-top_k:]
        
        selected_interactions = X_inter[:, top_indices]
        selected_names = [interaction_names[i] for i in top_indices]
        
        self.interaction_features = selected_names
        
        logger.info(f"   ✅ Selected {len(selected_names)} best interactions: {selected_names}")
        
        return selected_interactions, selected_names
    
    def recursive_feature_elimination(
        self, 
        X: np.ndarray, 
        y: np.ndarray, 
        estimator,
        feature_names: List[str],
        min_features: int = 3,
        step: int = 1,
        cv: int = 5,
        is_classification: bool = True
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Perform RFECV for optimal feature subset selection.
        
        Uses cross-validation to find the optimal number of features.
        
        Args:
            X: Feature matrix
            y: Target variable
            estimator: Model to use for feature ranking
            feature_names: Names of features
            min_features: Minimum features to keep
            step: Number of features to remove per iteration
            cv: Cross-validation folds
            is_classification: Whether classification task
        
        Returns:
            Tuple of (selected features, selected names)
        """
        logger.info(f"🔄 Running Recursive Feature Elimination (min={min_features})...")
        
        scoring = 'f1_weighted' if is_classification else 'r2'
        
        try:
            rfecv = RFECV(
                estimator=estimator,
                step=step,
                cv=cv,
                scoring=scoring,
                min_features_to_select=min_features,
                n_jobs=1  # Avoid parallelism issues
            )
            
            rfecv.fit(X, y)
            
            self.selected_feature_mask = rfecv.support_
            
            selected_names = [name for name, selected in zip(feature_names, rfecv.support_) if selected]
            X_selected = X[:, rfecv.support_]
            
            logger.info(f"   ✅ Selected {len(selected_names)}/{len(feature_names)} features")
            logger.info(f"   📊 Optimal features: {selected_names[:10]}...")
            
            return X_selected, selected_names
            
        except Exception as e:
            logger.warning(f"   ⚠️ RFECV failed: {e}, returning original features")
            return X, feature_names
    
    def target_encode(
        self, 
        df: pd.DataFrame, 
        categorical_cols: List[str],
        target: pd.Series,
        smoothing: float = 10.0
    ) -> pd.DataFrame:
        """
        Apply target encoding to high-cardinality categorical columns.
        
        Uses smoothed mean encoding to prevent overfitting.
        
        Args:
            df: DataFrame with categorical columns
            categorical_cols: List of columns to encode
            target: Target variable
            smoothing: Smoothing factor (higher = more regularization)
        
        Returns:
            DataFrame with encoded columns
        """
        logger.info(f"🎯 Applying target encoding to {len(categorical_cols)} columns...")
        
        df_encoded = df.copy()
        global_mean = target.mean()
        
        for col in categorical_cols:
            if col not in df.columns:
                continue
                
            # Calculate category statistics
            stats = df.groupby(col)[target.name if hasattr(target, 'name') else 'target'].agg(['mean', 'count'])
            
            # Smoothed encoding: weighted average of category mean and global mean
            # weight = count / (count + smoothing)
            smoothed_mean = (stats['count'] * stats['mean'] + smoothing * global_mean) / (stats['count'] + smoothing)
            
            self.target_encodings[col] = smoothed_mean.to_dict()
            
            # Apply encoding
            df_encoded[f"{col}_encoded"] = df[col].map(smoothed_mean).fillna(global_mean)
            
            logger.info(f"   ✅ Encoded {col}: {len(smoothed_mean)} categories")
        
        return df_encoded
    
    def select_k_best(
        self, 
        X: np.ndarray, 
        y: np.ndarray,
        feature_names: List[str],
        k: int = 10,
        is_classification: bool = True
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Select top K features using mutual information.
        
        Args:
            X: Feature matrix
            y: Target variable
            feature_names: Names of features
            k: Number of features to select
            is_classification: Whether classification task
        
        Returns:
            Tuple of (selected features, selected names)
        """
        logger.info(f"🎯 Selecting top {k} features using mutual information...")
        
        k = min(k, X.shape[1])
        
        score_func = mutual_info_classif if is_classification else mutual_info_regression
        
        selector = SelectKBest(score_func=score_func, k=k)
        X_selected = selector.fit_transform(X, y)
        
        # Get selected feature names
        selected_mask = selector.get_support()
        selected_names = [name for name, sel in zip(feature_names, selected_mask) if sel]
        
        # Log feature scores
        scores = selector.scores_
        top_features = sorted(zip(feature_names, scores), key=lambda x: x[1], reverse=True)[:k]
        
        logger.info(f"   ✅ Top features by MI score:")
        for name, score in top_features[:5]:
            logger.info(f"      {name}: {score:.4f}")
        
        return X_selected, selected_names


def create_feature_engineer() -> AdvancedFeatureEngineer:
    """Factory function to create feature engineer instance"""
    return AdvancedFeatureEngineer()
