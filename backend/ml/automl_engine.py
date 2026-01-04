"""
🚀 PRODUCTION ML ENGINE v5.0 - COMPREHENSIVE AI/ML
===================================================

FULL-FEATURED AutoML Pipeline with:
- 15+ ML Algorithms (SVM, Neural Nets, Naive Bayes, AdaBoost, etc.)
- NLP text preprocessing and classification
- Optuna Bayesian hyperparameter optimization
- SMOTE class imbalance handling
- Data leakage detection
- Outlier capping (IQR method)
- Correlation-based feature removal
- Advanced text vectorization (TF-IDF, n-grams)
- 18+ visualization charts
- Stacking ensemble support
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
from sklearn.model_selection import train_test_split, RandomizedSearchCV, cross_val_score, StratifiedKFold, KFold
from sklearn.preprocessing import LabelEncoder, StandardScaler, RobustScaler
from sklearn.ensemble import StackingClassifier, StackingRegressor
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer, HashingVectorizer
from sklearn.feature_selection import VarianceThreshold, SelectKBest, chi2, mutual_info_classif
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    r2_score, mean_absolute_error, mean_squared_error, confusion_matrix
)

# Models - Classification & Regression
from sklearn.ensemble import (
    RandomForestClassifier, RandomForestRegressor,
    GradientBoostingClassifier, GradientBoostingRegressor,
    ExtraTreesClassifier, ExtraTreesRegressor,
    HistGradientBoostingClassifier, HistGradientBoostingRegressor,
    AdaBoostClassifier, AdaBoostRegressor,
    BaggingClassifier, BaggingRegressor
)
from sklearn.linear_model import (
    LogisticRegression, Ridge, ElasticNet, Lasso,
    SGDClassifier, SGDRegressor, PassiveAggressiveClassifier
)
from sklearn.svm import SVC, SVR, LinearSVC
from sklearn.naive_bayes import MultinomialNB, GaussianNB, ComplementNB
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

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

# Optuna for Bayesian hyperparameter optimization
try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    HAS_OPTUNA = True
except ImportError:
    HAS_OPTUNA = False

# SMOTE for class imbalance handling
try:
    from imblearn.over_sampling import SMOTE
    from imblearn.under_sampling import RandomUnderSampler
    HAS_IMBLEARN = True
except ImportError:
    HAS_IMBLEARN = False

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

STORAGE_PATH = "./storage/automl"


@dataclass
class TrainResult:
    """Training result with charts and metrics"""
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
    charts: Optional[Dict[str, str]] = None  # NEW: Base64 encoded charts


class ProductionMLEngine:
    """
    🚀 PRODUCTION ML ENGINE v6.0 - ADAPTIVE INTELLIGENT AUTOML
    ==========================================================
    
    PRODUCTION-LEVEL Features:
    - Adaptive technique selection based on data profile
    - Automatic algorithm selection (not hardcoded)
    - Dynamic preprocessing based on data characteristics
    - NLP pipeline with 10+ text techniques
    - 20+ ML algorithms competing
    - Intelligent model selection based on data size/type
    - Cross-validation with optimal fold selection
    - Early stopping for efficiency
    """
    
    def __init__(self):
        # Model
        self.model = None
        self.model_name = None
        
        # Task info
        self.task_type: str = ""
        self.task_type_simple: str = ""
        self.n_classes: int = 0
        
        # DATA PROFILE - for adaptive technique selection
        self.data_profile = {
            'n_samples': 0,
            'n_features': 0,
            'n_numeric': 0,
            'n_categorical': 0,
            'n_text': 0,
            'is_high_dimensional': False,
            'is_small_data': False,
            'is_large_data': False,
            'is_imbalanced': False,
            'is_nlp_task': False,
            'has_missing': False,
            'missing_ratio': 0.0,
            'recommended_algorithms': [],
            'recommended_techniques': []
        }
        
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
        """Analyze a single column and determine its type and usefulness - ENHANCED"""
        n_unique = series.nunique()
        n_total = len(series)
        n_missing = series.isna().sum()
        missing_pct = n_missing / n_total
        unique_ratio = n_unique / n_total if n_total > 0 else 0
        
        # Determine column type
        col_lower = col_name.lower()
        
        # Check if it's an ID column (expanded patterns)
        id_patterns = ['id', '_id', 'index', 'key', 'code', 'number', 'num', 'no', 'seq', 
                      'uuid', 'guid', 'serial', 'ref', 'pk', 'fk']
        is_id = any(x in col_lower for x in id_patterns) and unique_ratio > 0.85
        
        # Check if it's a date column
        date_patterns = ['date', 'time', 'timestamp', 'created', 'updated', 'modified', 
                        'datetime', 'dt', 'year', 'month', 'day']
        is_date = any(x in col_lower for x in date_patterns)
        
        # Check if it's metadata/url column (useless for prediction)
        # BUT only if the content is short - long text should be kept for NLP
        useless_patterns = ['url', 'link', 'href', 'path', 'file', 'image', 'photo', 'pic',
                           'phone', 'address', 'ip', 'hash', 'password', 'token']
        
        # Check average content length for text columns
        avg_content_len = 0
        if series.dtype == 'object' or series.dtype == 'string':
            avg_content_len = series.astype(str).str.len().mean()
        
        # Only mark as useless if content is short (not real text for NLP)
        is_useless = any(x in col_lower for x in useless_patterns) and avg_content_len < 50
        
        # Special case: "email" in name but long content = likely email body text, keep it
        if 'email' in col_lower and avg_content_len > 30:
            is_useless = False  # This is email content, not email address
        
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
            drop_reason = "Date column (requires special handling)"
        elif is_useless:
            should_drop = True
            drop_reason = "Metadata/URL column (not predictive)"
        elif missing_pct > 0.5:  # Lowered from 0.7 to 0.5
            should_drop = True
            drop_reason = f"Too many missing ({missing_pct:.0%})"
        elif n_unique == 1:
            should_drop = True
            drop_reason = "Constant value"
        elif not is_numeric and unique_ratio > 0.9:  # Lowered from 0.95
            should_drop = True
            drop_reason = "Near-unique per row (no pattern)"
        elif n_unique == n_total and is_numeric:
            # Check if purely sequential (1,2,3,4...)
            try:
                vals = series.dropna().values
                if len(vals) > 10:
                    diffs = np.diff(np.sort(vals))
                    if np.std(diffs) < 0.01:
                        should_drop = True
                        drop_reason = "Sequential numeric (likely index)"
            except:
                pass
        
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
        - Keep text columns for NLP (even if unique - every email IS unique!)
        - Drop IDs, dates, constants, and mostly-missing columns
        """
        numeric_cols = []
        categorical_cols = []
        text_cols = []
        dropped = []
        
        print("📊 Analyzing columns...")
        
        # First pass: detect if this is an NLP dataset
        is_nlp = getattr(self, 'is_nlp_task', False)
        primary_text = getattr(self, 'primary_text_col', None)
        
        for col in df.columns:
            if col == target_col:
                continue
            
            analysis = self._analyze_column(df[col], col)
            
            # SPECIAL CASE: For NLP datasets, ALWAYS keep text columns
            if analysis['dtype'] == 'text' and (is_nlp or col == primary_text):
                text_cols.append(col)
                print(f"   ✅ {col}: NLP text column (kept for text classification)")
                continue
            
            if analysis['should_drop']:
                dropped.append(col)
                print(f"   ❌ {col}: {analysis['drop_reason']}")
            elif analysis['dtype'] == 'numeric' or analysis['dtype'] == 'boolean':
                numeric_cols.append(col)
            elif analysis['dtype'] == 'categorical':
                categorical_cols.append(col)
            elif analysis['dtype'] == 'text':
                # For non-NLP datasets, still keep text if avg length is long enough
                avg_len = df[col].astype(str).str.len().mean()
                if avg_len > 30:  # Long text = valuable content
                    text_cols.append(col)
                    print(f"   ✅ {col}: text column (avg {avg_len:.0f} chars)")
                elif analysis['unique_ratio'] < 0.9:
                    text_cols.append(col)
                else:
                    dropped.append(col)
                    print(f"   ❌ {col}: Short unique text (no pattern)")
        
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
    
    def _cap_outliers(self, data: np.ndarray, method: str = 'iqr') -> np.ndarray:
        """Cap outliers using IQR method to prevent extreme values affecting models"""
        if len(data) < 10:
            return data
        
        try:
            q1 = np.percentile(data, 25)
            q3 = np.percentile(data, 75)
            iqr = q3 - q1
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            capped = np.clip(data, lower_bound, upper_bound)
            n_capped = np.sum((data < lower_bound) | (data > upper_bound))
            
            if n_capped > 0:
                print(f"      🛠️ Capped {n_capped} outliers")
            
            return capped
        except:
            return data
    
    def _remove_highly_correlated(self, df: pd.DataFrame, threshold: float = 0.95) -> List[str]:
        """Remove features with very high correlation (likely duplicates or leakage)"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_cols) < 2:
            return []
        
        try:
            corr_matrix = df[numeric_cols].corr().abs()
            upper_triangle = corr_matrix.where(
                np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
            )
            
            to_drop = [col for col in upper_triangle.columns if any(upper_triangle[col] > threshold)]
            
            if to_drop:
                print(f"   ⚠️ Removing {len(to_drop)} highly correlated features (>{threshold:.0%} correlation)")
                for col in to_drop:
                    print(f"      - {col}")
            
            return to_drop
        except:
            return []
    
    # =========================================================================
    # DATA PROFILING - INTELLIGENT ADAPTIVE SELECTION
    # =========================================================================
    
    def _analyze_data_profile(self, df: pd.DataFrame, target_col: str) -> Dict:
        """
        PRODUCTION-LEVEL: Analyze data and recommend optimal techniques.
        This method profiles the data to intelligently select:
        - Best algorithms for this data size/type
        - Optimal preprocessing techniques
        - Appropriate model complexity
        """
        profile = self.data_profile.copy()
        
        # Basic stats
        profile['n_samples'] = len(df)
        profile['n_features'] = len(df.columns) - 1
        
        # Size categories
        profile['is_small_data'] = len(df) < 1000
        profile['is_medium_data'] = 1000 <= len(df) < 50000
        profile['is_large_data'] = len(df) >= 50000
        
        # Dimensionality
        profile['is_high_dimensional'] = profile['n_features'] > 100
        profile['is_low_dimensional'] = profile['n_features'] < 10
        
        # Missing data
        missing_ratio = df.isna().sum().sum() / (len(df) * len(df.columns))
        profile['has_missing'] = missing_ratio > 0.01
        profile['missing_ratio'] = missing_ratio
        
        # Class imbalance for classification
        if target_col in df.columns:
            y = df[target_col]
            if y.dtype == 'object' or y.nunique() < 20:
                class_counts = y.value_counts()
                if len(class_counts) > 1:
                    imbalance_ratio = class_counts.max() / class_counts.min()
                    profile['is_imbalanced'] = imbalance_ratio > 3
                    profile['imbalance_ratio'] = imbalance_ratio
        
        # Count column types
        for col in df.columns:
            if col == target_col:
                continue
            if pd.api.types.is_numeric_dtype(df[col]):
                profile['n_numeric'] += 1
            elif df[col].dtype == 'object' or df[col].dtype == 'string':
                avg_len = df[col].astype(str).str.len().mean()
                if avg_len > 50:
                    profile['n_text'] += 1
                else:
                    profile['n_categorical'] += 1
        
        profile['is_nlp_task'] = profile['n_text'] > 0 and profile['n_text'] >= profile['n_numeric']
        
        # INTELLIGENT ALGORITHM RECOMMENDATIONS
        recommended = []
        techniques = []
        
        print("📊 DATA PROFILE ANALYSIS:")
        print(f"   Samples: {profile['n_samples']:,} | Features: {profile['n_features']}")
        print(f"   Numeric: {profile['n_numeric']} | Categorical: {profile['n_categorical']} | Text: {profile['n_text']}")
        
        # === ALGORITHM SELECTION RULES ===
        
        # Small data: prefer simpler models, avoid deep learning
        if profile['is_small_data']:
            recommended.extend(['LogisticRegression', 'RandomForest', 'SVM', 'KNN', 'DecisionTree'])
            techniques.append('cross_validation_10_fold')
            print("   📈 Small data → Simple models + more CV folds")
        
        # Medium data: balanced approach
        elif profile['is_medium_data']:
            recommended.extend(['RandomForest', 'XGBoost', 'LightGBM', 'HistGradientBoosting', 'MLP'])
            techniques.append('cross_validation_5_fold')
            print("   📈 Medium data → Ensemble + gradient boosting")
        
        # Large data: gradient boosting shines, can use neural nets
        else:
            recommended.extend(['LightGBM', 'XGBoost', 'CatBoost', 'HistGradientBoosting', 'MLP'])
            techniques.append('cross_validation_3_fold')
            techniques.append('early_stopping')
            print("   📈 Large data → Fast gradient boosting + early stopping")
        
        # High dimensional: regularization important
        if profile['is_high_dimensional']:
            recommended.extend(['SGDClassifier', 'LogisticRegression', 'LinearSVC'])
            techniques.append('feature_selection')
            techniques.append('regularization')
            print("   📈 High dimensional → Linear models + regularization")
        
        # NLP/Text data: specific algorithms
        if profile['is_nlp_task']:
            recommended = ['MultinomialNB', 'ComplementNB', 'LogisticRegression', 'LinearSVC', 
                          'SGDClassifier', 'PassiveAggressive', 'MLP']
            techniques.extend(['tfidf', 'ngrams', 'sentiment_features', 'text_stats'])
            print("   📈 NLP task → Text-optimized classifiers")
        
        # Imbalanced data: specific handling
        if profile.get('is_imbalanced', False):
            techniques.append('smote')
            techniques.append('class_weights')
            print(f"   ⚠️ Imbalanced (ratio: {profile.get('imbalance_ratio', 0):.1f}:1) → SMOTE + class weights")
        
        # Add ensemble techniques for accuracy
        techniques.append('stacking_ensemble')
        techniques.append('voting_ensemble')
        
        profile['recommended_algorithms'] = list(set(recommended))
        profile['recommended_techniques'] = list(set(techniques))
        
        print(f"   🎯 Recommended: {', '.join(profile['recommended_algorithms'][:5])}")
        
        self.data_profile = profile
        return profile
    
    def _get_adaptive_models(self) -> Dict[str, Tuple[Any, Dict]]:
        """
        PRODUCTION-LEVEL: Return models adapted to data profile.
        Instead of hardcoded model list, this selects optimal algorithms
        based on data characteristics analyzed by _analyze_data_profile.
        """
        profile = self.data_profile
        recommended = profile.get('recommended_algorithms', [])
        
        # All available models
        all_classification_models = {
            'LogisticRegression': (
                LogisticRegression(max_iter=1000, random_state=42, n_jobs=-1),
                {'C': [0.1, 1, 10], 'penalty': ['l1', 'l2'], 'solver': ['saga']}
            ),
            'SGDClassifier': (
                SGDClassifier(random_state=42, max_iter=1000, early_stopping=True),
                {'alpha': [0.0001, 0.001, 0.01], 'penalty': ['l1', 'l2', 'elasticnet']}
            ),
            'DecisionTree': (
                DecisionTreeClassifier(random_state=42),
                {'max_depth': [5, 10, 20, None], 'min_samples_split': [2, 5, 10]}
            ),
            'RandomForest': (
                RandomForestClassifier(n_jobs=-1, random_state=42),
                {'n_estimators': [100, 200], 'max_depth': [10, 20, None]}
            ),
            'ExtraTrees': (
                ExtraTreesClassifier(n_jobs=-1, random_state=42),
                {'n_estimators': [100, 200], 'max_depth': [10, 20, None]}
            ),
            'HistGradientBoosting': (
                HistGradientBoostingClassifier(random_state=42, early_stopping=True),
                {'max_iter': [100, 200], 'max_depth': [5, 10], 'learning_rate': [0.05, 0.1]}
            ),
            'AdaBoost': (
                AdaBoostClassifier(random_state=42),
                {'n_estimators': [50, 100, 200], 'learning_rate': [0.1, 0.5, 1.0]}
            ),
            'SVM': (
                SVC(random_state=42, probability=True),
                {'C': [0.1, 1, 10], 'kernel': ['rbf', 'linear']}
            ),
            'LinearSVC': (
                LinearSVC(random_state=42, max_iter=2000, dual=False),
                {'C': [0.1, 1, 10]}
            ),
            'GaussianNB': (
                GaussianNB(),
                {'var_smoothing': [1e-9, 1e-8, 1e-7]}
            ),
            'MultinomialNB': (
                MultinomialNB(),
                {'alpha': [0.01, 0.1, 0.5, 1.0]}
            ),
            'ComplementNB': (
                ComplementNB(),
                {'alpha': [0.01, 0.1, 0.5, 1.0]}
            ),
            'MLP': (
                MLPClassifier(random_state=42, max_iter=500, early_stopping=True),
                {'hidden_layer_sizes': [(100,), (100, 50)], 'alpha': [0.0001, 0.001]}
            ),
            'KNN': (
                KNeighborsClassifier(n_jobs=-1),
                {'n_neighbors': [3, 5, 7], 'weights': ['uniform', 'distance']}
            ),
            'PassiveAggressive': (
                PassiveAggressiveClassifier(random_state=42, max_iter=1000),
                {'C': [0.01, 0.1, 1.0]}
            ),
        }
        
        all_regression_models = {
            'Ridge': (Ridge(random_state=42), {'alpha': [0.01, 0.1, 1, 10, 100]}),
            'Lasso': (Lasso(random_state=42, max_iter=2000), {'alpha': [0.01, 0.1, 1, 10]}),
            'ElasticNet': (ElasticNet(random_state=42, max_iter=2000), 
                          {'alpha': [0.01, 0.1, 1], 'l1_ratio': [0.2, 0.5, 0.8]}),
            'SGDRegressor': (SGDRegressor(random_state=42, max_iter=1000, early_stopping=True),
                            {'alpha': [0.0001, 0.001, 0.01]}),
            'DecisionTree': (DecisionTreeRegressor(random_state=42),
                            {'max_depth': [5, 10, 20, None], 'min_samples_split': [2, 5, 10]}),
            'RandomForest': (RandomForestRegressor(n_jobs=-1, random_state=42),
                            {'n_estimators': [100, 200], 'max_depth': [10, 20, None]}),
            'ExtraTrees': (ExtraTreesRegressor(n_jobs=-1, random_state=42),
                          {'n_estimators': [100, 200], 'max_depth': [10, 20, None]}),
            'HistGradientBoosting': (HistGradientBoostingRegressor(random_state=42, early_stopping=True),
                                    {'max_iter': [100, 200], 'max_depth': [5, 10]}),
            'AdaBoost': (AdaBoostRegressor(random_state=42),
                        {'n_estimators': [50, 100, 200], 'learning_rate': [0.1, 0.5, 1.0]}),
            'SVR': (SVR(), {'C': [0.1, 1, 10], 'kernel': ['rbf', 'linear']}),
            'MLP': (MLPRegressor(random_state=42, max_iter=500, early_stopping=True),
                   {'hidden_layer_sizes': [(100,), (100, 50)], 'alpha': [0.0001, 0.001]}),
            'KNN': (KNeighborsRegressor(n_jobs=-1), 
                   {'n_neighbors': [3, 5, 7], 'weights': ['uniform', 'distance']}),
        }
        
        # Add gradient boosting libraries if available
        if HAS_XGB:
            all_classification_models['XGBoost'] = (
                xgb.XGBClassifier(n_jobs=-1, random_state=42, verbosity=0, eval_metric='logloss'),
                {'n_estimators': [100, 200], 'max_depth': [5, 10], 'learning_rate': [0.05, 0.1]}
            )
            all_regression_models['XGBoost'] = (
                xgb.XGBRegressor(n_jobs=-1, random_state=42, verbosity=0),
                {'n_estimators': [100, 200], 'max_depth': [5, 10], 'learning_rate': [0.05, 0.1]}
            )
        
        if HAS_LGB:
            all_classification_models['LightGBM'] = (
                lgb.LGBMClassifier(n_jobs=-1, random_state=42, verbose=-1),
                {'n_estimators': [100, 200], 'max_depth': [5, 10], 'learning_rate': [0.05, 0.1]}
            )
            all_regression_models['LightGBM'] = (
                lgb.LGBMRegressor(n_jobs=-1, random_state=42, verbose=-1),
                {'n_estimators': [100, 200], 'max_depth': [5, 10], 'learning_rate': [0.05, 0.1]}
            )
        
        if HAS_CATBOOST:
            all_classification_models['CatBoost'] = (
                CatBoostClassifier(random_state=42, verbose=0, thread_count=-1),
                {'iterations': [100, 200], 'depth': [6, 8], 'learning_rate': [0.05, 0.1]}
            )
            all_regression_models['CatBoost'] = (
                CatBoostRegressor(random_state=42, verbose=0, thread_count=-1),
                {'iterations': [100, 200], 'depth': [6, 8], 'learning_rate': [0.05, 0.1]}
            )
        
        # Select models based on task type
        all_models = all_classification_models if self.task_type_simple == 'classification' else all_regression_models
        
        # Filter to recommended models, but ensure we have at least 5
        if recommended:
            selected = {k: v for k, v in all_models.items() 
                       if any(r.lower() in k.lower() for r in recommended)}
            # Add core models if we filtered too aggressively
            if len(selected) < 5:
                for key in ['RandomForest', 'HistGradientBoosting', 'LogisticRegression', 'Ridge']:
                    if key in all_models and key not in selected:
                        selected[key] = all_models[key]
            return selected
        
        return all_models
    
    # =========================================================================
    # NLP PROCESSING PIPELINE - COMPREHENSIVE
    # =========================================================================
    
    def _is_nlp_dataset(self, df: pd.DataFrame, target_col: str) -> Tuple[bool, str]:
        """Detect if this is primarily an NLP/text classification dataset"""
        text_cols = []
        for col in df.columns:
            if col == target_col:
                continue
            series = df[col].dropna()
            if series.dtype == object or series.dtype == 'string':
                avg_len = series.astype(str).str.len().mean()
                avg_words = series.astype(str).str.split().str.len().mean()
                if avg_len > 50 or avg_words > 5:  # Likely text column
                    text_cols.append(col)
        
        # If main feature is text, this is an NLP dataset
        non_target_cols = [c for c in df.columns if c != target_col]
        if len(text_cols) > 0 and len(text_cols) >= len(non_target_cols) * 0.5:
            return True, text_cols[0] if text_cols else None
        return False, None
    
    def _clean_text_nlp(self, text: str) -> str:
        """Advanced NLP text cleaning for better predictions"""
        import re
        
        if not isinstance(text, str) or not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\.\S+', ' ', text)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', ' ', text)
        
        # Remove mentions and hashtags
        text = re.sub(r'[@#]\w+', ' ', text)
        
        # Remove numbers (keep words with numbers like "3d", "2nd")
        text = re.sub(r'\b\d+\b', ' ', text)
        
        # Remove special characters but keep apostrophes for contractions
        text = re.sub(r"[^a-z\s']", ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove very short tokens (less than 2 chars)
        tokens = text.split()
        tokens = [t for t in tokens if len(t) > 1]
        
        return ' '.join(tokens)
    
    def _apply_stemming(self, text: str) -> str:
        """Apply Porter stemming for NLP"""
        try:
            from nltk.stem import PorterStemmer
            stemmer = PorterStemmer()
            tokens = text.split()
            return ' '.join([stemmer.stem(t) for t in tokens])
        except:
            return text
    
    def _apply_lemmatization(self, text: str) -> str:
        """Apply WordNet lemmatization for NLP"""
        try:
            from nltk.stem import WordNetLemmatizer
            lemmatizer = WordNetLemmatizer()
            tokens = text.split()
            return ' '.join([lemmatizer.lemmatize(t) for t in tokens])
        except:
            return text
    
    def _get_text_statistics(self, text: str) -> Dict[str, float]:
        """Extract statistical features from text"""
        if not text:
            return {'char_count': 0, 'word_count': 0, 'avg_word_len': 0, 
                   'sentence_count': 0, 'uppercase_ratio': 0, 'digit_ratio': 0}
        
        words = text.split()
        sentences = text.count('.') + text.count('!') + text.count('?') + 1
        
        return {
            'char_count': len(text),
            'word_count': len(words),
            'avg_word_len': sum(len(w) for w in words) / max(len(words), 1),
            'sentence_count': sentences,
            'uppercase_ratio': sum(1 for c in text if c.isupper()) / max(len(text), 1),
            'digit_ratio': sum(1 for c in text if c.isdigit()) / max(len(text), 1)
        }
    
    def _get_sentiment_features(self, text: str) -> Dict[str, float]:
        """Extract basic sentiment features without external dependencies"""
        # Positive and negative word lists (basic)
        positive_words = {'good', 'great', 'excellent', 'best', 'amazing', 'love', 'wonderful', 
                         'fantastic', 'awesome', 'perfect', 'happy', 'positive', 'beautiful',
                         'nice', 'brilliant', 'superb', 'outstanding', 'recommend', 'enjoy',
                         'pleased', 'satisfied', 'delighted', 'impressive', 'helpful'}
        negative_words = {'bad', 'worst', 'terrible', 'awful', 'horrible', 'hate', 'poor',
                         'disappointing', 'useless', 'waste', 'negative', 'ugly', 'boring',
                         'broken', 'problem', 'issue', 'fail', 'failed', 'wrong', 'angry',
                         'frustrated', 'annoyed', 'disappointed', 'complaint', 'refund'}
        
        words = set(text.lower().split())
        pos_count = len(words & positive_words)
        neg_count = len(words & negative_words)
        total = pos_count + neg_count
        
        return {
            'positive_score': pos_count / max(len(words), 1),
            'negative_score': neg_count / max(len(words), 1),
            'sentiment_ratio': (pos_count - neg_count) / max(total, 1) if total > 0 else 0,
            'polarity': 1 if pos_count > neg_count else (-1 if neg_count > pos_count else 0)
        }
    
    def _extract_nlp_features(self, text_series: pd.Series, col_name: str) -> np.ndarray:
        """Extract comprehensive NLP features from text column"""
        print(f"   🔤 NLP Processing: {col_name}")
        
        # Clean text
        clean_texts = text_series.fillna('').astype(str).apply(self._clean_text_nlp)
        print(f"      ✅ Text cleaned")
        
        # 1. TF-IDF vectorization (main features)
        try:
            tfidf = TfidfVectorizer(
                max_features=200,
                stop_words='english',
                ngram_range=(1, 3),
                min_df=2,
                max_df=0.9,
                lowercase=True,
                strip_accents='unicode',
                sublinear_tf=True  # Use sublinear TF for better NLP
            )
            tfidf_features = tfidf.fit_transform(clean_texts).toarray()
            self.text_vectorizers[col_name] = tfidf
            print(f"      ✅ TF-IDF: {tfidf_features.shape[1]} features")
        except:
            tfidf_features = np.zeros((len(text_series), 1))
        
        # 2. Text statistics features
        stats_list = clean_texts.apply(self._get_text_statistics).tolist()
        stats_features = np.array([[s['char_count'], s['word_count'], s['avg_word_len'], 
                                   s['sentence_count'], s['uppercase_ratio'], s['digit_ratio']] 
                                  for s in stats_list])
        print(f"      ✅ Text stats: 6 features")
        
        # 3. Sentiment features
        sentiment_list = clean_texts.apply(self._get_sentiment_features).tolist()
        sentiment_features = np.array([[s['positive_score'], s['negative_score'], 
                                       s['sentiment_ratio'], s['polarity']] 
                                      for s in sentiment_list])
        print(f"      ✅ Sentiment: 4 features")
        
        # Combine all features
        all_features = np.hstack([tfidf_features, stats_features, sentiment_features])
        print(f"      ✅ Total NLP features: {all_features.shape[1]}")
        
        return all_features
    
    def _get_nlp_models(self) -> Dict[str, Tuple[Any, Dict]]:
        """Get models optimized for NLP/text classification"""
        models = {
            # Naive Bayes - excellent for text
            'MultinomialNB': (
                MultinomialNB(),
                {'alpha': [0.01, 0.1, 0.5, 1.0]}
            ),
            'ComplementNB': (
                ComplementNB(),
                {'alpha': [0.01, 0.1, 0.5, 1.0]}
            ),
            
            # Linear models - fast for high-dimensional text
            'LogisticRegression': (
                LogisticRegression(max_iter=1000, random_state=42),
                {'C': [0.1, 1, 10], 'penalty': ['l1', 'l2'], 'solver': ['saga']}
            ),
            'SGDClassifier': (
                SGDClassifier(random_state=42, max_iter=1000, early_stopping=True),
                {'alpha': [0.0001, 0.001, 0.01], 'penalty': ['l1', 'l2', 'elasticnet']}
            ),
            'LinearSVC': (
                LinearSVC(random_state=42, max_iter=2000),
                {'C': [0.1, 1, 10]}
            ),
            'PassiveAggressive': (
                PassiveAggressiveClassifier(random_state=42, max_iter=1000),
                {'C': [0.01, 0.1, 1.0]}
            ),
            
            # Tree-based (for shorter texts)
            'RandomForest': (
                RandomForestClassifier(n_jobs=-1, random_state=42),
                {'n_estimators': [100, 200], 'max_depth': [10, 20]}
            ),
            
            # Neural Network
            'MLPClassifier': (
                MLPClassifier(random_state=42, max_iter=500, early_stopping=True),
                {'hidden_layer_sizes': [(100,), (100, 50)], 'alpha': [0.0001, 0.001]}
            ),
        }
        
        if HAS_XGB:
            models['XGBoost'] = (
                xgb.XGBClassifier(n_jobs=-1, random_state=42, verbosity=0),
                {'n_estimators': [100], 'max_depth': [5, 10]}
            )
        
        if HAS_LGB:
            models['LightGBM'] = (
                lgb.LGBMClassifier(n_jobs=-1, random_state=42, verbose=-1),
                {'n_estimators': [100], 'max_depth': [5, 10]}
            )
        
        return models
    
    def _detect_target_leakage(self, X: pd.DataFrame, y: pd.Series, threshold: float = 0.95) -> List[str]:
        """Detect features that perfectly predict target (data leakage)"""
        leaky_features = []
        numeric_cols = X.select_dtypes(include=[np.number]).columns
        
        try:
            for col in numeric_cols:
                corr = abs(X[col].corr(y))
                if corr > threshold:
                    leaky_features.append(col)
                    print(f"   🚨 LEAKAGE detected: '{col}' has {corr:.1%} correlation with target!")
            
            # SAFEGUARD: If ALL numeric features are considered leakage, don't drop them!
            # This happens in small datasets where features ARE the predictors
            if len(leaky_features) > 0 and len(leaky_features) == len(numeric_cols):
                print(f"   ⚠️ WARNING: All numeric features are highly correlated (>95%). ")
                print(f"      Keeping them to avoid empty dataset (might be small dataset or strong predictors).")
                return []
                
        except:
            pass
        
        return leaky_features
    
    def _preprocess_training(self, df: pd.DataFrame, target_col: str) -> Tuple[np.ndarray, np.ndarray]:
        """Preprocess data for training - ENHANCED for messy real-world data and NLP"""
        
        print("🧹 ADVANCED DATA CLEANING...")
        
        X = df.drop(columns=[target_col]).copy()
        y = df[target_col].copy()
        
        self.target_column = target_col
        
        # Detect task type
        task_info = self._detect_task_type(y)
        self.task_type = task_info[0]
        self.n_classes = task_info[1]
        self.task_type_simple = 'classification' if 'classification' in self.task_type else 'regression'
        
        print(f"   Task: {self.task_type} ({'n_classes=' + str(self.n_classes) if self.n_classes else 'continuous'})")
        
        # DETECT NLP DATASET
        self.is_nlp_task, self.primary_text_col = self._is_nlp_dataset(df, target_col)
        if self.is_nlp_task:
            print(f"   📝 DETECTED: NLP/Text Classification Dataset")
            print(f"   📝 Primary text column: {self.primary_text_col}")
        
        # STEP 1: Detect data leakage (features that perfectly predict target)
        y_numeric = pd.to_numeric(y, errors='coerce')
        if not y_numeric.isna().all():
            leaky_cols = self._detect_target_leakage(X, y_numeric, threshold=0.95)
            if leaky_cols:
                X = X.drop(columns=leaky_cols)
                print(f"   🚨 Removed {len(leaky_cols)} leaky features")
        
        # STEP 2: Remove highly correlated features (>95% correlation)
        correlated_cols = self._remove_highly_correlated(X, threshold=0.95)
        if correlated_cols:
            X = X.drop(columns=correlated_cols)
        
        # STEP 3: Select columns (drops IDs, dates, constants, etc.)
        self.numeric_cols, self.categorical_cols, self.text_cols, self.dropped_cols = \
            self._select_columns(df.drop(columns=leaky_cols + correlated_cols if 'leaky_cols' in dir() else [], errors='ignore'), target_col)
        
        # Remove any dropped leaky/correlated columns from our selected columns
        self.numeric_cols = [c for c in self.numeric_cols if c in X.columns]
        self.categorical_cols = [c for c in self.categorical_cols if c in X.columns]
        self.text_cols = [c for c in self.text_cols if c in X.columns]
        
        self.feature_columns = self.numeric_cols + self.categorical_cols + self.text_cols
        
        if len(self.feature_columns) == 0:
            raise ValueError("No valid features found after column selection and cleaning")
        
        # Process features
        processed_parts = []
        self.feature_metadata = []
        
        # 1. NUMERIC FEATURES
        if self.numeric_cols:
            numeric_data = []
            for col in self.numeric_cols:
                cleaned, fill_val = self._clean_numeric(X[col])
                # Cap outliers using IQR method for robust predictions
                cleaned = self._cap_outliers(cleaned)
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
        
        # 3. TEXT FEATURES (Comprehensive NLP Processing)
        for col in self.text_cols.copy():
            series = X[col].fillna('').astype(str)
            
            try:
                # Use comprehensive NLP extraction for NLP datasets or primary text column
                if getattr(self, 'is_nlp_task', False) or col == getattr(self, 'primary_text_col', None):
                    # FULL NLP PIPELINE - sentiment, stats, TF-IDF with 200 features
                    nlp_features = self._extract_nlp_features(series, col)
                    
                    # Handle negative values for Naive Bayes (make all non-negative)
                    nlp_features = np.abs(nlp_features)
                    
                    processed_parts.append(nlp_features)
                    self.feature_metadata.append({
                        'name': col,
                        'type': 'nlp_text',
                        'n_features': nlp_features.shape[1],
                        'has_sentiment': True
                    })
                else:
                    # Standard text processing for non-primary text columns
                    clean_texts = series.apply(self._clean_text_nlp)
                    
                    vectorizer = TfidfVectorizer(
                        max_features=100,
                        stop_words='english',
                        ngram_range=(1, 3),
                        min_df=2,
                        max_df=0.9,
                        lowercase=True,
                        strip_accents='unicode'
                    )
                    vectors = vectorizer.fit_transform(clean_texts).toarray()
                    
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
                print(f"   ⚠️ Skipping {col}: {str(e)[:50]}")
                if col in self.text_cols:
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
        """Get ALL available ML models with hyperparameter grids - COMPREHENSIVE"""
        
        if self.task_type_simple == 'classification':
            models = {
                # === LINEAR MODELS ===
                'LogisticRegression': (
                    LogisticRegression(max_iter=1000, n_jobs=-1, random_state=42),
                    {'C': [0.01, 0.1, 1, 10], 'penalty': ['l1', 'l2'], 'solver': ['saga']}
                ),
                'SGDClassifier': (
                    SGDClassifier(random_state=42, max_iter=1000),
                    {'alpha': [0.0001, 0.001, 0.01], 'penalty': ['l1', 'l2', 'elasticnet']}
                ),
                
                # === TREE-BASED MODELS ===
                'DecisionTree': (
                    DecisionTreeClassifier(random_state=42),
                    {'max_depth': [5, 10, 20, None], 'min_samples_split': [2, 5, 10]}
                ),
                'RandomForest': (
                    RandomForestClassifier(n_jobs=-1, random_state=42),
                    {'n_estimators': [100, 200], 'max_depth': [10, 20, None], 'min_samples_split': [2, 5]}
                ),
                'ExtraTrees': (
                    ExtraTreesClassifier(n_jobs=-1, random_state=42),
                    {'n_estimators': [100, 200], 'max_depth': [10, 20, None]}
                ),
                'HistGradientBoosting': (
                    HistGradientBoostingClassifier(random_state=42),
                    {'max_iter': [100, 200], 'max_depth': [5, 10], 'learning_rate': [0.05, 0.1]}
                ),
                'AdaBoost': (
                    AdaBoostClassifier(random_state=42),
                    {'n_estimators': [50, 100, 200], 'learning_rate': [0.01, 0.1, 1.0]}
                ),
                
                # === SVM MODELS ===
                'SVM': (
                    SVC(random_state=42, probability=True),
                    {'C': [0.1, 1, 10], 'kernel': ['rbf', 'linear']}
                ),
                
                # === NAIVE BAYES (great for NLP/text) ===
                'GaussianNB': (
                    GaussianNB(),
                    {'var_smoothing': [1e-9, 1e-8, 1e-7]}
                ),
                
                # === NEURAL NETWORK ===
                'MLPClassifier': (
                    MLPClassifier(random_state=42, max_iter=500, early_stopping=True),
                    {'hidden_layer_sizes': [(50,), (100,), (100, 50)], 'alpha': [0.0001, 0.001]}
                ),
                
                # === KNN ===
                'KNN': (
                    KNeighborsClassifier(n_jobs=-1),
                    {'n_neighbors': [3, 5, 7, 11], 'weights': ['uniform', 'distance']}
                ),
            }
            
            # Gradient Boosting libraries
            if HAS_XGB:
                models['XGBoost'] = (
                    xgb.XGBClassifier(n_jobs=-1, random_state=42, verbosity=0, eval_metric='logloss'),
                    {'n_estimators': [100, 200], 'max_depth': [5, 10], 'learning_rate': [0.05, 0.1]}
                )
            if HAS_LGB:
                models['LightGBM'] = (
                    lgb.LGBMClassifier(n_jobs=-1, random_state=42, verbose=-1),
                    {'n_estimators': [100, 200], 'max_depth': [5, 10], 'learning_rate': [0.05, 0.1]}
                )
            if HAS_CATBOOST:
                models['CatBoost'] = (
                    CatBoostClassifier(random_state=42, verbose=0, thread_count=-1),
                    {'iterations': [100, 200], 'depth': [6, 8], 'learning_rate': [0.05, 0.1]}
                )
                
        else:  # REGRESSION
            models = {
                # === LINEAR MODELS ===
                'Ridge': (
                    Ridge(random_state=42),
                    {'alpha': [0.01, 0.1, 1, 10, 100]}
                ),
                'ElasticNet': (
                    ElasticNet(random_state=42, max_iter=2000),
                    {'alpha': [0.01, 0.1, 1], 'l1_ratio': [0.2, 0.5, 0.8]}
                ),
                'Lasso': (
                    Lasso(random_state=42, max_iter=2000),
                    {'alpha': [0.01, 0.1, 1, 10]}
                ),
                'SGDRegressor': (
                    SGDRegressor(random_state=42, max_iter=1000),
                    {'alpha': [0.0001, 0.001, 0.01], 'penalty': ['l1', 'l2', 'elasticnet']}
                ),
                
                # === TREE-BASED MODELS ===
                'DecisionTree': (
                    DecisionTreeRegressor(random_state=42),
                    {'max_depth': [5, 10, 20, None], 'min_samples_split': [2, 5, 10]}
                ),
                'RandomForest': (
                    RandomForestRegressor(n_jobs=-1, random_state=42),
                    {'n_estimators': [100, 200], 'max_depth': [10, 20, None], 'min_samples_split': [2, 5]}
                ),
                'ExtraTrees': (
                    ExtraTreesRegressor(n_jobs=-1, random_state=42),
                    {'n_estimators': [100, 200], 'max_depth': [10, 20, None]}
                ),
                'HistGradientBoosting': (
                    HistGradientBoostingRegressor(random_state=42),
                    {'max_iter': [100, 200], 'max_depth': [5, 10], 'learning_rate': [0.05, 0.1]}
                ),
                'AdaBoost': (
                    AdaBoostRegressor(random_state=42),
                    {'n_estimators': [50, 100, 200], 'learning_rate': [0.01, 0.1, 1.0]}
                ),
                
                # === SVM ===
                'SVR': (
                    SVR(),
                    {'C': [0.1, 1, 10], 'kernel': ['rbf', 'linear']}
                ),
                
                # === NEURAL NETWORK ===
                'MLPRegressor': (
                    MLPRegressor(random_state=42, max_iter=500, early_stopping=True),
                    {'hidden_layer_sizes': [(50,), (100,), (100, 50)], 'alpha': [0.0001, 0.001]}
                ),
                
                # === KNN ===
                'KNN': (
                    KNeighborsRegressor(n_jobs=-1),
                    {'n_neighbors': [3, 5, 7, 11], 'weights': ['uniform', 'distance']}
                ),
            }
            
            # Gradient Boosting libraries
            if HAS_XGB:
                models['XGBoost'] = (
                    xgb.XGBRegressor(n_jobs=-1, random_state=42, verbosity=0),
                    {'n_estimators': [100, 200], 'max_depth': [5, 10], 'learning_rate': [0.05, 0.1]}
                )
            if HAS_LGB:
                models['LightGBM'] = (
                    lgb.LGBMRegressor(n_jobs=-1, random_state=42, verbose=-1),
                    {'n_estimators': [100, 200], 'max_depth': [5, 10], 'learning_rate': [0.05, 0.1]}
                )
            if HAS_CATBOOST:
                models['CatBoost'] = (
                    CatBoostRegressor(random_state=42, verbose=0, thread_count=-1),
                    {'iterations': [100, 200], 'depth': [6, 8], 'learning_rate': [0.05, 0.1]}
                )
        
        return models
        
        return models
    
    # =========================================================================
    # ADVANCED METHODS FOR TOP 1% ACCURACY
    # =========================================================================
    
    def _handle_class_imbalance(self, X_train: np.ndarray, y_train: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Handle class imbalance using SMOTE if available"""
        if not HAS_IMBLEARN or self.task_type_simple != 'classification':
            return X_train, y_train
        
        try:
            class_counts = np.bincount(y_train.astype(int))
            if len(class_counts) < 2:
                return X_train, y_train
            
            imbalance_ratio = max(class_counts) / max(min(class_counts), 1)
            
            if imbalance_ratio > 3:
                print(f"   ⚠️ Class imbalance detected (ratio={imbalance_ratio:.1f}:1), applying SMOTE...")
                smote = SMOTE(random_state=42, k_neighbors=min(5, min(class_counts) - 1))
                X_resampled, y_resampled = smote.fit_resample(X_train, y_train)
                print(f"   ✅ Resampled: {len(X_train)} → {len(X_resampled)} samples")
                return X_resampled, y_resampled
        except Exception as e:
            print(f"   ⚠️ SMOTE failed: {e}")
        
        return X_train, y_train
    
    def _optimize_with_optuna(
        self, 
        model_name: str, 
        X_train: np.ndarray, 
        y_train: np.ndarray, 
        n_trials: int = 30
    ) -> Tuple[Any, Dict]:
        """Bayesian hyperparameter optimization with Optuna"""
        if not HAS_OPTUNA:
            return None, {}
        
        scoring = 'f1_weighted' if self.task_type_simple == 'classification' else 'r2'
        cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42) if self.task_type_simple == 'classification' else KFold(n_splits=3, shuffle=True, random_state=42)
        
        def objective(trial):
            if model_name == 'XGBoost' and HAS_XGB:
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 100, 500),
                    'max_depth': trial.suggest_int('max_depth', 3, 15),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                    'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                    'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                    'reg_alpha': trial.suggest_float('reg_alpha', 1e-8, 10.0, log=True),
                    'reg_lambda': trial.suggest_float('reg_lambda', 1e-8, 10.0, log=True),
                }
                if self.task_type_simple == 'classification':
                    model = xgb.XGBClassifier(**params, n_jobs=-1, random_state=42, verbosity=0, eval_metric='logloss')
                else:
                    model = xgb.XGBRegressor(**params, n_jobs=-1, random_state=42, verbosity=0)
            
            elif model_name == 'LightGBM' and HAS_LGB:
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 100, 500),
                    'max_depth': trial.suggest_int('max_depth', 3, 15),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                    'num_leaves': trial.suggest_int('num_leaves', 20, 150),
                    'min_child_samples': trial.suggest_int('min_child_samples', 5, 100),
                }
                if self.task_type_simple == 'classification':
                    model = lgb.LGBMClassifier(**params, n_jobs=-1, random_state=42, verbose=-1)
                else:
                    model = lgb.LGBMRegressor(**params, n_jobs=-1, random_state=42, verbose=-1)
            
            elif model_name == 'RandomForest':
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 100, 400),
                    'max_depth': trial.suggest_int('max_depth', 5, 30),
                    'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
                    'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
                }
                if self.task_type_simple == 'classification':
                    model = RandomForestClassifier(**params, n_jobs=-1, random_state=42)
                else:
                    model = RandomForestRegressor(**params, n_jobs=-1, random_state=42)
            else:
                return 0.0
            
            try:
                scores = cross_val_score(model, X_train, y_train, cv=cv, scoring=scoring, n_jobs=1)
                return scores.mean()
            except:
                return 0.0
        
        try:
            study = optuna.create_study(direction='maximize')
            study.optimize(objective, n_trials=n_trials, show_progress_bar=False, n_jobs=1)
            
            print(f"   🎯 Optuna best score: {study.best_value:.4f}")
            return study.best_params, study.best_value
        except Exception as e:
            print(f"   ⚠️ Optuna failed: {e}")
            return None, {}
    
    def _build_stacking_ensemble(
        self, 
        trained_models: Dict[str, Any], 
        X_train: np.ndarray, 
        y_train: np.ndarray
    ) -> Any:
        """Build stacking ensemble from trained models"""
        if len(trained_models) < 2:
            return None
        
        try:
            # Select top 3 models for stacking
            estimators = [(name, model) for name, model in list(trained_models.items())[:3]]
            
            print(f"   🏗️ Building stacking ensemble with {len(estimators)} models...")
            
            if self.task_type_simple == 'classification':
                meta_learner = LogisticRegression(max_iter=1000, random_state=42)
                stacker = StackingClassifier(
                    estimators=estimators,
                    final_estimator=meta_learner,
                    cv=3,
                    passthrough=False,
                    n_jobs=1
                )
            else:
                meta_learner = Ridge(random_state=42)
                stacker = StackingRegressor(
                    estimators=estimators,
                    final_estimator=meta_learner,
                    cv=3,
                    passthrough=False,
                    n_jobs=1
                )
            
            stacker.fit(X_train, y_train)
            print(f"   ✅ Stacking ensemble trained successfully")
            return stacker
        except Exception as e:
            print(f"   ⚠️ Stacking failed: {e}")
            return None
    
    # =========================================================================
    # TRAINING
    # =========================================================================
    
    async def train(self, df: pd.DataFrame, target_col: Optional[str] = None, user_id: str = "default") -> TrainResult:
        """PRODUCTION-LEVEL Main training pipeline with adaptive technique selection"""
        self.errors = []
        start = datetime.now()
        
        print("=" * 60)
        print("🚀 PRODUCTION ML ENGINE v6.0 - ADAPTIVE INTELLIGENT AUTOML")
        print("=" * 60)
        print(f"📊 Data: {len(df)} rows, {len(df.columns)} columns")
        
        # Detect target
        if not target_col:
            target_col = self._detect_target(df)
        else:
            print(f"🎯 Target (user specified): {target_col}")
        
        # ADAPTIVE: Analyze data profile BEFORE preprocessing to recommend techniques
        self._analyze_data_profile(df, target_col)
        
        # Preprocess
        X, y = self._preprocess_training(df, target_col)
        
        # Split (stratified for classification)
        stratify = y if self.task_type_simple == 'classification' and self.n_classes < 100 else None
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=stratify
        )
        print(f"   Train: {len(X_train)}, Test: {len(X_test)}")
        
        # Store for learning curves and chart generation
        self._X_train = X_train
        self._X_test = X_test
        
        # Apply SMOTE if recommended by data profile
        if 'smote' in self.data_profile.get('recommended_techniques', []):
            X_train_balanced, y_train_balanced = self._handle_class_imbalance(X_train, y_train)
        else:
            X_train_balanced, y_train_balanced = X_train, y_train
        
        # ADAPTIVE: Get models based on data profile (not hardcoded)
        models = self._get_adaptive_models()
        results = []
        
        best_score = -np.inf
        best_model = None
        best_name = None
        best_pred = None
        best_proba = None
        
        scoring = 'f1_weighted' if self.task_type_simple == 'classification' else 'r2'
        
        # ADAPTIVE: CV folds based on data profile
        profile = self.data_profile
        if profile.get('is_small_data'):
            cv_folds = 10
            n_iter = 10
        elif profile.get('is_large_data'):
            cv_folds = 3
            n_iter = 5
        else:
            cv_folds = 5
            n_iter = 8
        
        print(f"🤖 Training {len(models)} ADAPTIVE models ({cv_folds}-fold CV)...")  
        
        # Track trained models for stacking
        trained_models = {}
        
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
                    search.fit(X_train_balanced, y_train_balanced)
                    best_est = search.best_estimator_
                    best_params = search.best_params_
                except Exception as search_err:
                    print(f"   ⚠️ Search failed ({str(search_err)[:50]}), falling back to simple fit...")
                    model.fit(X_train_balanced, y_train_balanced)
                    best_est = model
                    best_params = "default"
                
                # Store trained model for stacking
                trained_models[name] = best_est
                
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
        
        # Generate all charts using the enhanced chart generator
        try:
            from ml.chart_generator import chart_generator
            charts = chart_generator.generate_all_charts(
                task_type=self.task_type,
                y_test=y_test,
                y_pred=best_pred,
                y_proba=best_proba[:, 1] if best_proba is not None and self.task_type_simple == 'classification' and len(best_proba.shape) > 1 and best_proba.shape[1] == 2 else best_proba,
                feature_importance=results[0].get('importance', []) if results else [],
                leaderboard=results,
                model=self.model,
                X_train=X_train
            )
        except Exception as chart_err:
            print(f"⚠️ Chart generation error: {chart_err}")
            charts = {}
        
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
            processing_time=processing_time,
            charts=charts
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
        """Get all ML charts for the trained model using enhanced chart generator"""
        try:
            from ml.chart_generator import chart_generator
            
            y_test = getattr(self, '_y_test', None)
            y_pred = getattr(self, '_y_pred', None)
            y_proba = getattr(self, '_y_proba', None)
            X_train = getattr(self, '_X_train', None)
            
            if y_test is None or y_pred is None:
                return {'error': 'No model trained yet'}
            
            # Get feature importance
            importance = self._get_importance(self.model) if self.model else []
            
            # Generate all charts using the enhanced generator
            charts = chart_generator.generate_all_charts(
                task_type=self.task_type,
                y_test=y_test,
                y_pred=y_pred,
                y_proba=y_proba,
                feature_importance=importance,
                leaderboard=[],  # Not stored, but can be added if needed
                model=self.model,
                X_train=X_train
            )
            
            logger.info(f"✅ Generated {len(charts)} ML charts")
            return charts
            
        except Exception as e:
            logger.error(f"Chart generation error: {e}")
            return {'error': str(e)}


# Global instance
automl_engine = ProductionMLEngine()
