"""
🚀 PRODUCTION ML ENGINE v3.0
=============================

ROBUST AutoML Pipeline with:
- Smart column selection (keep useful, drop useless)
- Proper data cleaning
- Correct regression/classification detection
- Best model selection with hyperparameter tuning
- Task-appropriate visualizations
"""

import os
import pickle
import warnings
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.preprocessing import LabelEncoder, StandardScaler, RobustScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_selection import VarianceThreshold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    r2_score, mean_absolute_error, mean_squared_error, confusion_matrix
)

# Models
from sklearn.ensemble import (
    RandomForestClassifier, RandomForestRegressor,
    GradientBoostingClassifier, GradientBoostingRegressor,
    ExtraTreesClassifier, ExtraTreesRegressor,
    HistGradientBoostingClassifier, HistGradientBoostingRegressor
)
from sklearn.linear_model import LogisticRegression, Ridge, ElasticNet, Lasso
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor

# Unsupervised Learning
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    import lightgbm as lgb
    HAS_LGB = True
except ImportError:
    HAS_LGB = False

try:
    from catboost import CatBoostClassifier, CatBoostRegressor
    HAS_CATBOOST = True
except ImportError:
    HAS_CATBOOST = False

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

STORAGE_PATH = "./storage/automl"


@dataclass
class TrainResult:
    """Training result"""
    success: bool
    task_type: str
    target_column: str
    feature_columns: List[str]
    best_model_name: str
    best_model_metrics: Dict[str, float]
    leaderboard: List[Dict]
    feature_importance: List[Dict]
    y_test: np.ndarray
    y_pred: np.ndarray
    y_proba: Optional[np.ndarray]
    feature_metadata: List[Dict]
    n_rows: int
    n_cols: int
    processing_time: float


class ProductionMLEngine:
    """
    Production-Ready ML Engine v3.0
    
    Features:
    - Smart column detection and selection
    - Robust data cleaning
    - Automatic task detection
    - Hyperparameter tuning
    - Feature importance analysis
    """
    
    def __init__(self):
        # Model
        self.model = None
        self.model_name = None
        
        # Task info
        self.task_type: str = ""  # 'binary_classification', 'multiclass_classification', 'regression'
        self.task_type_simple: str = ""  # 'classification' or 'regression'
        self.n_classes: int = 0
        
        # Columns
        self.target_column: str = ""
        self.feature_columns: List[str] = []
        self.numeric_cols: List[str] = []
        self.categorical_cols: List[str] = []
        self.text_cols: List[str] = []
        self.dropped_cols: List[str] = []
        
        # Preprocessing
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.target_encoder: Optional[LabelEncoder] = None
        self.text_vectorizers: Dict[str, TfidfVectorizer] = {}
        self.scaler: Optional[RobustScaler] = None
        self.numeric_fill_values: Dict[str, float] = {}
        self.feature_metadata: List[Dict] = []
    
    # =========================================================================
    # COLUMN ANALYSIS & SELECTION
    # =========================================================================
    
    def _analyze_column(self, series: pd.Series, col_name: str) -> Dict:
        """Analyze a single column and determine its type and usefulness"""
        n_unique = series.nunique()
        n_total = len(series)
        n_missing = series.isna().sum()
        missing_pct = n_missing / n_total
        unique_ratio = n_unique / n_total if n_total > 0 else 0
        
        # Determine column type
        col_lower = col_name.lower()
        
        # Check if it's an ID column
        is_id = any(x in col_lower for x in ['id', '_id', 'index', 'key', 'code']) and unique_ratio > 0.9
        
        # Check if it's a date column
        is_date = any(x in col_lower for x in ['date', 'time', 'timestamp', 'created', 'updated'])
        
        # Check if numeric
        is_numeric = pd.api.types.is_numeric_dtype(series)
        
        # Check if boolean
        is_bool = series.dtype == bool or (is_numeric and n_unique == 2 and set(series.dropna().unique()).issubset({0, 1}))
        
        # Determine usefulness
        should_drop = False
        drop_reason = None
        
        if is_id:
            should_drop = True
            drop_reason = "ID column (unique identifier)"
        elif is_date:
            should_drop = True
            drop_reason = "Date column (not processed)"
        elif missing_pct > 0.7:
            should_drop = True
            drop_reason = f"Too many missing ({missing_pct:.0%})"
        elif n_unique == 1:
            should_drop = True
            drop_reason = "Constant value"
        elif not is_numeric and unique_ratio > 0.95:
            should_drop = True
            drop_reason = "Unique per row (no pattern)"
        
        # Determine final type
        if is_numeric:
            if is_bool:
                dtype = 'boolean'
            else:
                dtype = 'numeric'
        elif n_unique <= 50:
            dtype = 'categorical'
        else:
            dtype = 'text'
        
        return {
            'name': col_name,
            'dtype': dtype,
            'n_unique': n_unique,
            'n_missing': n_missing,
            'missing_pct': missing_pct,
            'unique_ratio': unique_ratio,
            'should_drop': should_drop,
            'drop_reason': drop_reason
        }
    
    def _select_columns(self, df: pd.DataFrame, target_col: str) -> Tuple[List[str], List[str], List[str], List[str]]:
        """
        Smart column selection:
        - Keep useful numeric columns
        - Keep categorical with reasonable cardinality
        - Keep text columns that might have predictive value
        - Drop IDs, dates, constants, and mostly-missing columns
        """
        numeric_cols = []
        categorical_cols = []
        text_cols = []
        dropped = []
        
        print("📊 Analyzing columns...")
        
        for col in df.columns:
            if col == target_col:
                continue
            
            analysis = self._analyze_column(df[col], col)
            
            if analysis['should_drop']:
                dropped.append(col)
                print(f"   ❌ {col}: {analysis['drop_reason']}")
            elif analysis['dtype'] == 'numeric' or analysis['dtype'] == 'boolean':
                numeric_cols.append(col)
            elif analysis['dtype'] == 'categorical':
                categorical_cols.append(col)
            elif analysis['dtype'] == 'text':
                # Only keep text if not too unique
                if analysis['unique_ratio'] < 0.8:
                    text_cols.append(col)
                else:
                    dropped.append(col)
                    print(f"   ❌ {col}: Text too unique ({analysis['unique_ratio']:.0%})")
        
        print(f"   ✅ Keeping: {len(numeric_cols)} numeric, {len(categorical_cols)} categorical, {len(text_cols)} text")
        print(f"   ❌ Dropped: {len(dropped)} columns")
        
        return numeric_cols, categorical_cols, text_cols, dropped
    
    # =========================================================================
    # TARGET DETECTION
    # =========================================================================
    
    def _detect_target(self, df: pd.DataFrame) -> str:
        """Smart target detection with priority keywords"""
        
        # Priority 1: Exact match keywords
        exact_keywords = ['target', 'label', 'class', 'output', 'y']
        for col in df.columns:
            if col.lower().strip() in exact_keywords:
                print(f"🎯 Target (exact match): {col}")
                return col
        
        # Priority 2: Contains keywords (sorted by priority)
        contains_keywords = [
            'target', 'label', 'class', 'churn', 'fraud', 'default', 'outcome',
            'survived', 'sentiment', 'rating', 'score',
            'price', 'salary', 'income', 'revenue', 'amount', 'value', 'total'
        ]
        
        for keyword in contains_keywords:
            for col in df.columns:
                if keyword in col.lower():
                    print(f"🎯 Target (contains '{keyword}'): {col}")
                    return col
        
        # Priority 3: Heuristic - prefer last column if it's a good target
        last_col = df.columns[-1]
        last_unique = df[last_col].nunique()
        
        if last_unique <= 20 or pd.api.types.is_numeric_dtype(df[last_col]):
            print(f"🎯 Target (last column): {last_col}")
            return last_col
        
        # Priority 4: Find best candidate
        candidates = []
        for col in df.columns:
            n_unique = df[col].nunique()
            is_numeric = pd.api.types.is_numeric_dtype(df[col])
            score = 0
            
            if n_unique == 2:
                score = 100  # Binary - great target
            elif n_unique <= 10:
                score = 50  # Multiclass
            elif is_numeric:
                score = 30  # Regression
            
            if score > 0:
                candidates.append((col, score))
        
        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            print(f"🎯 Target (best candidate): {candidates[0][0]}")
            return candidates[0][0]
        
        print(f"🎯 Target (fallback): {df.columns[-1]}")
        return df.columns[-1]
    
    def _detect_task_type(self, y: pd.Series) -> Tuple[str, int]:
        """
        PRODUCTION-LEVEL Task Type Detection
        
        Uses multiple heuristics:
        1. Data type (string = classification)
        2. Unique value count
        3. Unique ratio (unique/total)
        4. Value characteristics (decimals, range)
        """
        n_unique = y.nunique()
        n_samples = len(y)
        unique_ratio = n_unique / n_samples if n_samples > 0 else 0
        
        print(f"   🔍 Analyzing target: {n_unique} unique values, ratio={unique_ratio:.2%}")
        
        # ====== RULE 1: String/Object type = Classification ======
        if pd.api.types.is_object_dtype(y) or pd.api.types.is_categorical_dtype(y):
            if n_unique == 2:
                print(f"   ✅ Binary Classification (string, 2 classes)")
                return 'binary_classification', 2
            elif n_unique <= 50:
                print(f"   ✅ Multiclass Classification (string, {n_unique} classes)")
                return 'multiclass_classification', n_unique
            else:
                # Too many classes for effective classification
                print(f"   ⚠️ High-cardinality string ({n_unique} unique) - treating as multiclass")
                return 'multiclass_classification', n_unique
        
        # ====== RULE 2: Boolean = Binary Classification ======
        if pd.api.types.is_bool_dtype(y):
            print(f"   ✅ Binary Classification (boolean)")
            return 'binary_classification', 2
        
        # ====== RULE 3: Numeric Analysis ======
        y_clean = pd.to_numeric(y, errors='coerce').dropna()
        
        if len(y_clean) == 0:
            print(f"   ⚠️ No valid numeric values - defaulting to regression")
            return 'regression', 0
        
        # Check for binary (0/1 or similar)
        unique_vals = set(y_clean.unique())
        if unique_vals.issubset({0, 1}) or unique_vals.issubset({-1, 1}):
            print(f"   ✅ Binary Classification (0/1 or -1/1)")
            return 'binary_classification', 2
        
        # Check if values are whole numbers
        is_whole_numbers = (y_clean % 1 == 0).all()
        
        # Integer with few unique values = Classification
        if is_whole_numbers:
            if n_unique == 2:
                print(f"   ✅ Binary Classification (2 integer classes)")
                return 'binary_classification', 2
            elif n_unique <= 10:
                print(f"   ✅ Multiclass Classification ({n_unique} integer classes)")
                return 'multiclass_classification', n_unique
            elif n_unique <= 20 and unique_ratio < 0.05:
                # Low unique ratio suggests classification
                print(f"   ✅ Multiclass Classification ({n_unique} classes, low ratio)")
                return 'multiclass_classification', n_unique
        
        # ====== RULE 4: Continuous values = Regression ======
        # Check for decimal places
        has_decimals = not is_whole_numbers
        
        # Check value range (large range suggests regression)
        val_range = y_clean.max() - y_clean.min()
        
        if has_decimals:
            print(f"   ✅ Regression (continuous decimals, range={val_range:.2f})")
            return 'regression', 0
        
        if unique_ratio > 0.1 and n_unique > 20:
            print(f"   ✅ Regression (high unique ratio={unique_ratio:.1%}, {n_unique} values)")
            return 'regression', 0
        
        if val_range > 100 and n_unique > 30:
            print(f"   ✅ Regression (large range={val_range:.0f})")
            return 'regression', 0
        
        # Default based on unique count
        if n_unique <= 15:
            print(f"   ✅ Multiclass Classification ({n_unique} classes, default)")
            return 'multiclass_classification', n_unique
        
        print(f"   ✅ Regression (default, {n_unique} unique values)")
        return 'regression', 0
    
    # =========================================================================
    # DATA CLEANING & PREPROCESSING
    # =========================================================================
    
    def _clean_numeric(self, series: pd.Series) -> Tuple[np.ndarray, float]:
        """Clean numeric column: handle missing, outliers"""
        # Convert to numeric, coerce errors
        numeric = pd.to_numeric(series, errors='coerce')
        
        # Calculate fill value (median is robust to outliers)
        fill_val = numeric.median()
        if pd.isna(fill_val):
            fill_val = 0.0
        
        # Fill missing
        cleaned = numeric.fillna(fill_val).values.astype(float)
        
        # Handle inf
        cleaned = np.nan_to_num(cleaned, nan=fill_val, posinf=fill_val, neginf=fill_val)
        
        return cleaned, fill_val
    
    def _preprocess_training(self, df: pd.DataFrame, target_col: str) -> Tuple[np.ndarray, np.ndarray]:
        """Preprocess data for training"""
        
        X = df.drop(columns=[target_col]).copy()
        y = df[target_col].copy()
        
        self.target_column = target_col
        
        # Detect task type
        task_info = self._detect_task_type(y)
        self.task_type = task_info[0]
        self.n_classes = task_info[1]
        self.task_type_simple = 'classification' if 'classification' in self.task_type else 'regression'
        
        print(f"   Task: {self.task_type} ({'n_classes=' + str(self.n_classes) if self.n_classes else 'continuous'})")
        
        # Select columns
        self.numeric_cols, self.categorical_cols, self.text_cols, self.dropped_cols = \
            self._select_columns(df, target_col)
        
        self.feature_columns = self.numeric_cols + self.categorical_cols + self.text_cols
        
        if len(self.feature_columns) == 0:
            raise ValueError("No valid features found after column selection")
        
        # Process features
        processed_parts = []
        self.feature_metadata = []
        
        # 1. NUMERIC FEATURES
        if self.numeric_cols:
            numeric_data = []
            for col in self.numeric_cols:
                cleaned, fill_val = self._clean_numeric(X[col])
                self.numeric_fill_values[col] = fill_val
                numeric_data.append(cleaned)
                
                # Calculate percentiles for better display
                try:
                    p25 = float(np.nanpercentile(cleaned, 25))
                    p75 = float(np.nanpercentile(cleaned, 75))
                except:
                    p25 = p75 = fill_val
                
                self.feature_metadata.append({
                    'name': col,
                    'type': 'numeric',
                    'min': float(np.nanmin(cleaned)) if not np.isnan(np.nanmin(cleaned)) else 0,
                    'max': float(np.nanmax(cleaned)) if not np.isnan(np.nanmax(cleaned)) else 100,
                    'mean': float(np.nanmean(cleaned)) if not np.isnan(np.nanmean(cleaned)) else 50,
                    'default': float(fill_val),
                    'p25': p25,
                    'p75': p75,
                    'placeholder': f"{fill_val:.2f} (typical: {p25:.1f} - {p75:.1f})"
                })
            
            numeric_array = np.column_stack(numeric_data)
            
            # Scale with RobustScaler (handles outliers better)
            self.scaler = RobustScaler()
            numeric_scaled = self.scaler.fit_transform(numeric_array)
            processed_parts.append(numeric_scaled)
        
        # 2. CATEGORICAL FEATURES
        for col in self.categorical_cols:
            series = X[col].fillna('_MISSING_').astype(str).str.strip()
            encoder = LabelEncoder()
            encoded = encoder.fit_transform(series).reshape(-1, 1)
            self.label_encoders[col] = encoder
            processed_parts.append(encoded.astype(float))
            
            # Get most common value as default
            mode = series.mode()[0] if len(series.mode()) > 0 else encoder.classes_[0]
            
            self.feature_metadata.append({
                'name': col,
                'type': 'categorical',
                'options': encoder.classes_.tolist()[:50],
                'default': mode,
                'n_categories': len(encoder.classes_)
            })
        
        # 3. TEXT FEATURES
        for col in self.text_cols.copy():
            series = X[col].fillna('').astype(str)
            
            try:
                vectorizer = TfidfVectorizer(
                    max_features=50,
                    stop_words='english',
                    ngram_range=(1, 2),
                    min_df=1,
                    max_df=0.95
                )
                vectors = vectorizer.fit_transform(series).toarray()
                
                if vectors.shape[1] > 0:
                    self.text_vectorizers[col] = vectorizer
                    processed_parts.append(vectors)
                    self.feature_metadata.append({
                        'name': col,
                        'type': 'text',
                        'vocab_size': len(vectorizer.vocabulary_)
                    })
                    print(f"   ✅ {col}: {len(vectorizer.vocabulary_)} text features")
                else:
                    self.text_cols.remove(col)
            except Exception as e:
                print(f"   ⚠️ Skipping {col}: {str(e)[:40]}")
                self.text_cols.remove(col)
        
        # Combine
        if processed_parts:
            X_processed = np.hstack(processed_parts)
        else:
            raise ValueError("No valid features after preprocessing")
        
        # Clean final array
        X_processed = np.nan_to_num(X_processed, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Process target
        if self.task_type_simple == 'classification':
            self.target_encoder = LabelEncoder()
            y_processed = self.target_encoder.fit_transform(y.fillna('_MISSING_').astype(str).str.strip())
        else:
            y_processed = pd.to_numeric(y, errors='coerce').fillna(0).values.astype(float)
            y_processed = np.nan_to_num(y_processed, nan=0.0)
        
        print(f"   Final shape: {X_processed.shape}")
        
        return X_processed, y_processed
    
    def _preprocess_single(self, data: Dict[str, Any]) -> np.ndarray:
        """Preprocess single input for prediction"""
        parts = []
        
        # Numeric
        if self.numeric_cols:
            numeric_vals = []
            for col in self.numeric_cols:
                val = data.get(col, self.numeric_fill_values.get(col, 0))
                try:
                    numeric_vals.append(float(val) if val is not None else self.numeric_fill_values.get(col, 0))
                except:
                    numeric_vals.append(self.numeric_fill_values.get(col, 0))
            
            numeric_array = np.array([numeric_vals])
            if self.scaler:
                parts.append(self.scaler.transform(numeric_array))
            else:
                parts.append(numeric_array)
        
        # Categorical
        for col in self.categorical_cols:
            encoder = self.label_encoders.get(col)
            if encoder:
                val = str(data.get(col, '_MISSING_')).strip()
                encoded = encoder.transform([val])[0] if val in encoder.classes_ else 0
                parts.append(np.array([[float(encoded)]]))
        
        # Text
        for col in self.text_cols:
            vectorizer = self.text_vectorizers.get(col)
            if vectorizer:
                text = str(data.get(col, ''))
                parts.append(vectorizer.transform([text]).toarray())
        
        return np.hstack(parts) if parts else np.array([[0]])
    
    # =========================================================================
    # MODELS
    # =========================================================================
    
    def _get_models(self) -> Dict[str, Tuple[Any, Dict]]:
        """Get models with hyperparameter grids based on task"""
        
        if self.task_type_simple == 'classification':
            models = {
                'LogisticRegression': (
                    LogisticRegression(max_iter=500, n_jobs=-1, random_state=42),
                    {'C': [0.1, 1, 10]}
                ),
                'RandomForest': (
                    RandomForestClassifier(n_jobs=-1, random_state=42),
                    {'n_estimators': [100, 200], 'max_depth': [10, 20, None]}
                ),
                'HistGradientBoosting': (
                    HistGradientBoostingClassifier(random_state=42),
                    {'max_iter': [100, 200], 'max_depth': [5, 10]}
                ),
            }
            if HAS_XGB:
                models['XGBoost'] = (
                    xgb.XGBClassifier(n_jobs=-1, random_state=42, verbosity=0, eval_metric='logloss'),
                    {'n_estimators': [100, 200], 'max_depth': [5, 10]}
                )
            if HAS_LGB:
                models['LightGBM'] = (
                    lgb.LGBMClassifier(n_jobs=-1, random_state=42, verbose=-1),
                    {'n_estimators': [100, 200], 'max_depth': [5, 10]}
                )
        else:
            models = {
                'Ridge': (
                    Ridge(random_state=42),
                    {'alpha': [0.1, 1, 10]}
                ),
                'RandomForest': (
                    RandomForestRegressor(n_jobs=-1, random_state=42),
                    {'n_estimators': [100, 200], 'max_depth': [10, 20, None]}
                ),
                'HistGradientBoosting': (
                    HistGradientBoostingRegressor(random_state=42),
                    {'max_iter': [100, 200], 'max_depth': [5, 10]}
                ),
            }
            if HAS_XGB:
                models['XGBoost'] = (
                    xgb.XGBRegressor(n_jobs=-1, random_state=42, verbosity=0),
                    {'n_estimators': [100, 200], 'max_depth': [5, 10]}
                )
            if HAS_LGB:
                models['LightGBM'] = (
                    lgb.LGBMRegressor(n_jobs=-1, random_state=42, verbose=-1),
                    {'n_estimators': [100, 200], 'max_depth': [5, 10]}
                )
        
        return models
    
    # =========================================================================
    # TRAINING
    # =========================================================================
    
    async def train(self, df: pd.DataFrame, target_col: Optional[str] = None, user_id: str = "default") -> TrainResult:
        """Main training pipeline"""
        self.errors = []  # Initialize error list
        start = datetime.now()
        
        print("=" * 60)
        print("🚀 PRODUCTION ML ENGINE v3.0")
        print("=" * 60)
        print(f"📊 Data: {len(df)} rows, {len(df.columns)} columns")
        
        # Detect target
        if not target_col:
            target_col = self._detect_target(df)
        else:
            print(f"🎯 Target (user specified): {target_col}")
        
        # Preprocess
        X, y = self._preprocess_training(df, target_col)
        
        # Split
        stratify = y if self.task_type_simple == 'classification' and self.n_classes < 100 else None
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=stratify
        )
        print(f"   Train: {len(X_train)}, Test: {len(X_test)}")
        
        # Get models
        models = self._get_models()
        results = []
        
        best_score = -np.inf
        best_model = None
        best_name = None
        best_pred = None
        best_proba = None
        
        scoring = 'f1_weighted' if self.task_type_simple == 'classification' else 'r2'
        
        # Reduce CV for complex problems
        n_iter = 5 if self.n_classes > 20 or len(X) > 50000 else 8
        cv_folds = 2 if self.n_classes > 20 or len(X) > 50000 else 3
        
        print(f"🤖 Training {len(models)} models (tuning: {n_iter} iter, {cv_folds}-fold CV)...")
        
        for idx, (name, (model, params)) in enumerate(models.items(), 1):
            try:
                t0 = datetime.now()
                print(f"   [{idx}/{len(models)}] {name}...", end=" ", flush=True)
                
                # Fallback mechanism: Try GridSearch/RandomSearch first, then simple fit
                try:
                    search = RandomizedSearchCV(
                        model, params, n_iter=min(n_iter, np.prod([len(v) for v in params.values()])),
                        cv=cv_folds, scoring=scoring, n_jobs=1, random_state=42, error_score='raise'
                    )
                    search.fit(X_train, y_train)
                    best_est = search.best_estimator_
                    best_params = search.best_params_
                except Exception as search_err:
                    print(f"   ⚠️ Search failed ({str(search_err)[:50]}), falling back to simple fit...")
                    model.fit(X_train, y_train)
                    best_est = model
                    best_params = "default"
                
                # Predict
                y_pred = best_est.predict(X_test)
                
                y_proba = None
                if hasattr(best_est, 'predict_proba'):
                    try:
                        y_proba = best_est.predict_proba(X_test)
                    except:
                        pass
                
                # Metrics
                if self.task_type_simple == 'classification':
                    score = f1_score(y_test, y_pred, average='weighted', zero_division=0)
                    acc = accuracy_score(y_test, y_pred)
                    metrics = {'f1': round(score, 4), 'accuracy': round(acc, 4)}
                else:
                    score = r2_score(y_test, y_pred)
                    mae = mean_absolute_error(y_test, y_pred)
                    metrics = {'r2': round(score, 4), 'mae': round(mae, 4)}
                
                elapsed = (datetime.now() - t0).total_seconds()
                
                results.append({
                    'name': name,
                    'metrics': metrics,
                    'training_time': round(elapsed, 2),
                    'importance': self._get_importance(best_est),
                    'best_params': best_params
                })
                
                metric_name = 'f1' if self.task_type_simple == 'classification' else 'r2'
                print(f"{metric_name}={score:.3f} ({elapsed:.1f}s)")
                
                if score > best_score:
                    best_score = score
                    best_model = best_est
                    best_name = name
                    best_pred = y_pred
                    best_proba = y_proba
                    
            except Exception as e:
                import traceback
                traceback.print_exc()
                error_msg = f"{name}: {str(e)[:100]}"
                print(f"ERROR - {error_msg}")
                self.errors.append(error_msg)  # Store error for reporting
        
        self.model = best_model
        self.model_name = best_name
        
        if self.model is None:
            error_summary = "; ".join(self.errors[-3:]) if hasattr(self, 'errors') else "Unknown error"
            raise ValueError(f"All models failed to train. Errors: {error_summary}")

        print(f"🏆 Best: {best_name} (score={best_score:.3f})")
        
        # Retrain on full data
        try:
            print(f"🔄 Retraining {best_name} on full data...")
            self.model.fit(X, y)
        except Exception as e:
            print(f"⚠️ Retraining failed, keeping split model: {e}")
            # Keep the already trained best_model from split
            pass
        print(f"   ✅ Retrained on {len(X)} samples")
        
        # Sort results
        metric_key = 'f1' if self.task_type_simple == 'classification' else 'r2'
        results.sort(key=lambda x: x['metrics'].get(metric_key, 0), reverse=True)
        
        # CRITICAL: Store training metrics on self BEFORE saving
        # These are needed for get_model_metrics() to return real values
        self._y_test = y_test
        self._y_pred = best_pred
        self._y_proba = best_proba
        self.metrics = results[0]['metrics'] if results else {}
        
        # Calculate and store confusion matrix for classification
        if self.task_type_simple == 'classification':
            try:
                # Use global imports instead of local re-import to avoid UnboundLocalError
                self.confusion_matrix = confusion_matrix(y_test, best_pred)
                # Also store full metrics
                self.metrics['accuracy'] = float(accuracy_score(y_test, best_pred))
                self.metrics['f1'] = float(f1_score(y_test, best_pred, average='weighted', zero_division=0))
                self.metrics['precision'] = float(precision_score(y_test, best_pred, average='weighted', zero_division=0))
                self.metrics['recall'] = float(recall_score(y_test, best_pred, average='weighted', zero_division=0))
                print(f"📊 Stored metrics: Accuracy={self.metrics['accuracy']:.1%}, F1={self.metrics['f1']:.1%}")
            except Exception as cm_err:
                print(f"⚠️ Confusion matrix error: {cm_err}")
                self.confusion_matrix = None
        else:
            # Regression metrics
            try:
                # Use global imports to avoid UnboundLocalError
                self.metrics['r2'] = float(r2_score(y_test, best_pred))
                self.metrics['mae'] = float(mean_absolute_error(y_test, best_pred))
                self.metrics['rmse'] = float(np.sqrt(mean_squared_error(y_test, best_pred)))
                print(f"📊 Stored metrics: R²={self.metrics['r2']:.3f}, MAE={self.metrics['mae']:.2f}")
            except Exception as reg_err:
                print(f"⚠️ Regression metrics error: {reg_err}")
        
        # Save (now includes metrics, y_test, y_pred, confusion_matrix)
        self._save(user_id)
        
        # Verify
        self._verify(df.head(5), target_col)
        
        processing_time = (datetime.now() - start).total_seconds()
        
        print("=" * 60)
        print(f"✅ Complete in {processing_time:.1f}s")
        print("=" * 60)
        
        return TrainResult(
            success=True,
            task_type=self.task_type,
            target_column=target_col,
            feature_columns=self.feature_columns,
            best_model_name=best_name,
            best_model_metrics=results[0]['metrics'] if results else {},
            leaderboard=results,
            feature_importance=results[0].get('importance', []) if results else [],
            y_test=y_test,
            y_pred=best_pred,
            y_proba=best_proba[:, 1] if best_proba is not None and self.task_type_simple == 'classification' and len(best_proba.shape) > 1 and best_proba.shape[1] == 2 else None,
            feature_metadata=self.feature_metadata,
            n_rows=len(df),
            n_cols=len(df.columns),
            processing_time=processing_time
        )
    
    def _get_importance(self, model) -> List[Dict]:
        """Get feature importance"""
        if hasattr(model, 'feature_importances_'):
            values = model.feature_importances_
        elif hasattr(model, 'coef_'):
            values = np.abs(model.coef_).flatten()
        else:
            return []
        
        # Build feature names
        names = []
        for col in self.numeric_cols:
            names.append(col)
        for col in self.categorical_cols:
            names.append(col)
        for col in self.text_cols:
            vec = self.text_vectorizers.get(col)
            if vec:
                for w in list(vec.vocabulary_.keys())[:5]:
                    names.append(f"{col}:{w}")
        
        if len(values) != len(names):
            names = [f"Feature_{i}" for i in range(len(values))]
        
        if values.sum() > 0:
            values = values / values.sum()
        
        importance = []
        for rank, (n, v) in enumerate(sorted(zip(names, values), key=lambda x: x[1], reverse=True), 1):
            if rank > 15:
                break
            importance.append({'feature': n, 'importance': round(float(v), 4), 'rank': rank})
        
        return importance
    
    def _verify(self, df: pd.DataFrame, target_col: str):
        """Verify predictions"""
        print("\n📋 Verification:")
        for i in range(min(5, len(df))):
            row = df.iloc[i]
            actual = row[target_col]
            
            data = {col: row[col] for col in self.feature_columns if col in row.index}
            
            try:
                pred = self.predict(data)
                p = pred['prediction']
                
                if self.task_type_simple == 'regression':
                    try:
                        err = abs(float(p) - float(actual)) / abs(float(actual)) * 100 if float(actual) != 0 else 0
                        print(f"   Row {i}: Actual={actual:.2f}, Pred={float(p):.2f}, Error={err:.1f}%")
                    except:
                        print(f"   Row {i}: Actual={actual}, Pred={p}")
                else:
                    match = "✅" if str(p) == str(actual) else "❌"
                    print(f"   Row {i}: Actual={actual}, Pred={p} {match}")
            except Exception as e:
                print(f"   Row {i}: ERROR - {e}")
    
    def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction"""
        if self.model is None:
            raise ValueError("No model trained")
        
        X = self._preprocess_single(data)
        pred = self.model.predict(X)[0]
        
        if self.target_encoder:
            try:
                pred = self.target_encoder.inverse_transform([int(pred)])[0]
            except:
                pass
        
        prob = None
        conf = None
        if hasattr(self.model, 'predict_proba'):
            try:
                proba = self.model.predict_proba(X)[0]
                prob = [float(p) for p in proba]
                conf = float(max(proba))
            except:
                pass
        
        return {'prediction': str(pred), 'probability': prob, 'confidence': conf, 'model': self.model_name}
    
    def _save(self, user_id: str):
        """Save model and preprocessors"""
        save_dir = os.path.join(STORAGE_PATH, user_id)
        os.makedirs(save_dir, exist_ok=True)
        
        data = {
            'model': self.model,
            'model_name': self.model_name,
            'task_type': self.task_type,
            'task_type_simple': self.task_type_simple,
            'n_classes': self.n_classes,
            'target_column': self.target_column,
            'feature_columns': self.feature_columns,
            'numeric_cols': self.numeric_cols,
            'categorical_cols': self.categorical_cols,
            'text_cols': self.text_cols,
            'label_encoders': self.label_encoders,
            'target_encoder': self.target_encoder,
            'text_vectorizers': self.text_vectorizers,
            'scaler': self.scaler,
            'numeric_fill_values': self.numeric_fill_values,
            'feature_metadata': self.feature_metadata,
            'metrics': getattr(self, 'metrics', {}),
            'confusion_matrix': getattr(self, 'confusion_matrix', None),
            'y_test': getattr(self, '_y_test', None),
            'y_pred': getattr(self, '_y_pred', None),
        }
        
        with open(os.path.join(save_dir, "model.pkl"), 'wb') as f:
            pickle.dump(data, f)
        
        print(f"💾 Saved to {save_dir}")
    
    def load(self, user_id: str) -> bool:
        """Load model"""
        # Ensure storage directory exists
        save_dir = os.path.join(STORAGE_PATH, user_id)
        os.makedirs(save_dir, exist_ok=True)
        
        path = os.path.join(save_dir, "model.pkl")
        
        if not os.path.exists(path):
            return False
        
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
            
            self.model = data['model']
            self.model_name = data['model_name']
            self.task_type = data.get('task_type', '')
            self.task_type_simple = data.get('task_type_simple', '')
            self.n_classes = data.get('n_classes', 0)
            self.target_column = data.get('target_column', '')
            self.feature_columns = data.get('feature_columns', [])
            self.numeric_cols = data.get('numeric_cols', [])
            self.categorical_cols = data.get('categorical_cols', [])
            self.text_cols = data.get('text_cols', [])
            self.label_encoders = data.get('label_encoders', {})
            self.target_encoder = data.get('target_encoder')
            self.text_vectorizers = data.get('text_vectorizers', {})
            self.scaler = data.get('scaler')
            self.numeric_fill_values = data.get('numeric_fill_values', {})
            self.feature_metadata = data.get('feature_metadata', [])
            self.metrics = data.get('metrics', {})
            self.confusion_matrix = data.get('confusion_matrix')
            self._y_test = data.get('y_test')
            self._y_pred = data.get('y_pred')
            
            print(f"📂 Loaded from {path}")
            return True
        except Exception as e:
            print(f"⚠️ Load error: {e}")
            return False
    
    def get_model_metrics(self) -> Dict[str, Any]:
        """Get model performance metrics"""
        metrics = getattr(self, 'metrics', {})
        
        result = {
            'model_name': self.model_name,
            'task_type': self.task_type,
            'target': self.target_column,
            'n_features': len(self.feature_columns),
            'metrics': metrics,
        }
        
        # Add confusion matrix for classification
        if self.task_type_simple == 'classification':
            cm = getattr(self, 'confusion_matrix', None)
            if cm is not None:
                result['confusion_matrix'] = cm.tolist() if hasattr(cm, 'tolist') else cm
            
            # Calculate from stored predictions
            y_test = getattr(self, '_y_test', None)
            y_pred = getattr(self, '_y_pred', None)
            
            if y_test is not None and y_pred is not None:
                try:
                    from sklearn.metrics import confusion_matrix, accuracy_score, f1_score, precision_score, recall_score
                    
                    cm = confusion_matrix(y_test, y_pred)
                    result['confusion_matrix'] = cm.tolist()
                    result['metrics']['accuracy'] = float(accuracy_score(y_test, y_pred))
                    result['metrics']['f1'] = float(f1_score(y_test, y_pred, average='weighted'))
                    result['metrics']['precision'] = float(precision_score(y_test, y_pred, average='weighted', zero_division=0))
                    result['metrics']['recall'] = float(recall_score(y_test, y_pred, average='weighted', zero_division=0))
                except Exception as e:
                    print(f"Metrics calc error: {e}")
        
        return result
    
    def get_feature_metadata(self) -> List[Dict]:
        return self.feature_metadata
    
    # =========================================================================
    # UNSUPERVISED LEARNING - CLUSTERING
    # =========================================================================
    
    def run_clustering(
        self, 
        df: pd.DataFrame, 
        n_clusters: int = None,
        algorithm: str = 'kmeans'
    ) -> Dict[str, Any]:
        """
        Run unsupervised clustering on the data.
        
        Args:
            df: DataFrame with numeric features
            n_clusters: Number of clusters (auto-detected if None)
            algorithm: 'kmeans', 'dbscan', or 'hierarchical'
        
        Returns:
            Dict with cluster labels, metrics, and visualization data
        """
        logger.info(f"🔮 Running {algorithm} clustering...")
        
        result = {
            'success': False,
            'algorithm': algorithm,
            'n_clusters': 0,
            'labels': [],
            'metrics': {},
            'pca_2d': None,
            'charts': {}
        }
        
        try:
            # Prepare numeric data
            numeric_df = df.select_dtypes(include=[np.number]).dropna()
            
            if numeric_df.empty or len(numeric_df) < 10:
                result['error'] = "Not enough numeric data for clustering"
                return result
            
            # Scale the data
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(numeric_df)
            
            # Auto-detect optimal clusters if not specified
            if n_clusters is None and algorithm != 'dbscan':
                n_clusters = self._find_optimal_clusters(X_scaled)
            
            # Run clustering
            if algorithm == 'kmeans':
                model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                labels = model.fit_predict(X_scaled)
            elif algorithm == 'dbscan':
                model = DBSCAN(eps=0.5, min_samples=5)
                labels = model.fit_predict(X_scaled)
                n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            elif algorithm == 'hierarchical':
                model = AgglomerativeClustering(n_clusters=n_clusters)
                labels = model.fit_predict(X_scaled)
            else:
                result['error'] = f"Unknown algorithm: {algorithm}"
                return result
            
            # Calculate metrics
            if len(set(labels)) > 1 and -1 not in labels:
                silhouette = silhouette_score(X_scaled, labels)
            else:
                silhouette = 0.0
            
            # PCA for visualization
            pca = PCA(n_components=2)
            X_2d = pca.fit_transform(X_scaled)
            
            # Store results
            result['success'] = True
            result['n_clusters'] = n_clusters
            result['labels'] = labels.tolist()
            result['metrics'] = {
                'silhouette_score': float(silhouette),
                'n_samples': len(labels),
                'pca_variance_explained': float(sum(pca.explained_variance_ratio_))
            }
            result['pca_2d'] = X_2d.tolist()
            
            # Generate cluster scatter chart (base64 image)
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import io
            import base64
            
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Color palette
            colors = ['#2563eb', '#16a34a', '#dc2626', '#ea580c', '#9333ea', 
                      '#0891b2', '#db2777', '#d97706', '#0d9488', '#4f46e5']
            
            unique_labels = sorted(set(labels))
            for i, label in enumerate(unique_labels):
                mask = labels == label
                color = colors[i % len(colors)] if label >= 0 else '#6b7280'
                label_name = f'Cluster {label}' if label >= 0 else 'Noise'
                ax.scatter(X_2d[mask, 0], X_2d[mask, 1], 
                          c=color, label=label_name, alpha=0.7, s=50,
                          edgecolors='white', linewidth=0.5)
            
            ax.set_xlabel('PCA Component 1', fontweight='bold', fontsize=12)
            ax.set_ylabel('PCA Component 2', fontweight='bold', fontsize=12)
            ax.set_title(f'🔮 {algorithm.title()} Clustering (Silhouette: {silhouette:.3f})', 
                        fontweight='bold', pad=15, fontsize=14)
            ax.legend(loc='best', fontsize=10)
            ax.grid(alpha=0.3)
            ax.set_facecolor('#ffffff')
            fig.set_facecolor('#f8f9fa')
            
            # Convert to base64
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                       facecolor='#f8f9fa', edgecolor='none')
            buf.seek(0)
            cluster_chart = f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"
            plt.close(fig)
            
            result['charts']['cluster_scatter'] = cluster_chart
            
            # Add cluster distribution
            unique, counts = np.unique(labels, return_counts=True)
            result['cluster_distribution'] = {
                f"Cluster {k}" if k >= 0 else "Noise": int(v) 
                for k, v in zip(unique, counts)
            }
            
            logger.info(f"✅ Clustering complete: {n_clusters} clusters, silhouette={silhouette:.3f}")
            
        except Exception as e:
            logger.error(f"Clustering error: {e}")
            result['error'] = str(e)
        
        return result
    
    def _find_optimal_clusters(self, X: np.ndarray, max_k: int = 10) -> int:
        """Find optimal number of clusters using elbow method + silhouette"""
        logger.info("🔍 Finding optimal number of clusters...")
        
        max_k = min(max_k, len(X) - 1)
        k_range = range(2, max_k + 1)
        
        inertias = []
        silhouettes = []
        
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X)
            inertias.append(kmeans.inertia_)
            silhouettes.append(silhouette_score(X, labels))
        
        # Best k by silhouette score
        best_k = list(k_range)[np.argmax(silhouettes)]
        logger.info(f"   Optimal K = {best_k} (silhouette = {max(silhouettes):.3f})")
        
        return best_k
    
    def get_all_ml_charts(self) -> Dict[str, Any]:
        """Get all ML charts for the trained model"""
        charts = {}
        
        try:
            from ml.ml_chart_generator import MLChartGenerator
            
            y_test = getattr(self, '_y_test', None)
            y_pred = getattr(self, '_y_pred', None)
            y_proba = getattr(self, '_y_pred_proba', None)
            
            if y_test is None or y_pred is None:
                return {'error': 'No model trained yet'}
            
            is_classification = 'classification' in self.task_type
            
            if is_classification:
                # Classification charts
                charts['confusion_matrix'] = MLChartGenerator.confusion_matrix_chart(y_test, y_pred)
                
                if y_proba is not None:
                    charts['roc_curve'] = MLChartGenerator.roc_curve_chart(y_test, y_proba)
                    charts['precision_recall'] = MLChartGenerator.precision_recall_chart(y_test, y_proba)
            else:
                # Regression charts
                charts['actual_vs_predicted'] = MLChartGenerator.actual_vs_predicted_chart(
                    y_test, y_pred, f"{self.target_column} Predictions"
                )
                charts['residuals'] = MLChartGenerator.residuals_chart(y_test, y_pred)
            
            # Feature importance
            if self.feature_columns:
                importance = self._get_importance(self.model) or []
                features = [f['feature'] for f in importance]
                values = [f['importance'] for f in importance]
                if features:
                    charts['feature_importance'] = MLChartGenerator.feature_importance_chart(
                        features, values, f"Feature Importance for {self.target_column}"
                    )
            
            logger.info(f"✅ Generated {len(charts)} ML charts")
            
        except Exception as e:
            logger.error(f"Chart generation error: {e}")
            charts['error'] = str(e)
        
        return charts


# Global instance
automl_engine = ProductionMLEngine()
