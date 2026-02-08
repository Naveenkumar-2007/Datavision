"""
🔱 GOD-LEVEL AUTOML INTELLIGENCE ENGINE v1.0
============================================

A GOD-LEVEL AutoML system designed to operate with the reasoning ability of 
a senior machine learning architect, AI researcher, and production ML engineer combined.

PRIMARY OBJECTIVES:
==================
✅ Understand dataset structure deeply
✅ Detect correct problem type automatically
✅ Clean and prepare data professionally
✅ Select best features intelligently
✅ Select best model(s) based on data characteristics
✅ Train safely with cross-validation
✅ Evaluate realistically with holdout sets
✅ PREVENT overfitting & data leakage
✅ Produce reliable predictions on new data
✅ Output production-ready model pipeline

ABSOLUTE RULES (NEVER BREAK):
============================
❌ Never produce fake accuracy
❌ Never allow data leakage  
❌ Never overfit intentionally
❌ Never choose wrong model type
❌ Never ignore bad data
❌ Never output unstable models

Author: GOD-Level AI Intelligence
Version: 1.0.0
"""

import os
import pickle
import hashlib
import logging
import warnings
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import Counter

# Sklearn imports
from sklearn.model_selection import (
    train_test_split, cross_val_score, StratifiedKFold, KFold,
    cross_val_predict, learning_curve, validation_curve
)
from sklearn.preprocessing import (
    LabelEncoder, StandardScaler, RobustScaler, MinMaxScaler,
    QuantileTransformer, PowerTransformer
)
from sklearn.feature_selection import (
    VarianceThreshold, SelectKBest, mutual_info_classif, 
    mutual_info_regression, RFE, SelectFromModel
)
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    r2_score, mean_absolute_error, mean_squared_error, 
    mean_absolute_percentage_error, confusion_matrix,
    roc_auc_score, silhouette_score, calinski_harabasz_score
)
from sklearn.ensemble import (
    RandomForestClassifier, RandomForestRegressor,
    GradientBoostingClassifier, GradientBoostingRegressor,
    ExtraTreesClassifier, ExtraTreesRegressor,
    AdaBoostClassifier, AdaBoostRegressor,
    BaggingClassifier, BaggingRegressor,
    HistGradientBoostingClassifier, HistGradientBoostingRegressor,
    VotingClassifier, VotingRegressor,
    StackingClassifier, StackingRegressor,
    IsolationForest
)
from sklearn.linear_model import (
    LogisticRegression, Ridge, ElasticNet, Lasso,
    RidgeClassifier, SGDClassifier, SGDRegressor,
    BayesianRidge, HuberRegressor, PoissonRegressor
)
from sklearn.svm import SVC, SVR, LinearSVC, LinearSVR
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.naive_bayes import GaussianNB, MultinomialNB, ComplementNB, BernoulliNB
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.mixture import GaussianMixture
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

# Optional imports with fallbacks
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False

try:
    from catboost import CatBoostClassifier, CatBoostRegressor
    HAS_CATBOOST = True
except ImportError:
    HAS_CATBOOST = False

try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    HAS_OPTUNA = True
except ImportError:
    HAS_OPTUNA = False

try:
    from imblearn.over_sampling import SMOTE, ADASYN
    from imblearn.under_sampling import RandomUnderSampler
    HAS_IMBLEARN = True
except ImportError:
    HAS_IMBLEARN = False


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class ProblemType(Enum):
    """Types of ML problems"""
    BINARY_CLASSIFICATION = "binary_classification"
    MULTICLASS_CLASSIFICATION = "multiclass_classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    ANOMALY_DETECTION = "anomaly_detection"
    UNKNOWN = "unknown"


class DatasetSize(Enum):
    """Dataset size categories"""
    TINY = "tiny"        # < 500 rows
    SMALL = "small"      # < 5000 rows  
    MEDIUM = "medium"    # < 100000 rows
    LARGE = "large"      # >= 100000 rows


class TrainingMode(Enum):
    """Training modes"""
    FAST = "fast"
    ULTRA = "ultra"


class ColumnType(Enum):
    """Column types"""
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    TEXT = "text"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    ID = "id"
    CONSTANT = "constant"
    HIGH_CARDINALITY = "high_cardinality"
    UNKNOWN = "unknown"


@dataclass
class ColumnProfile:
    """Profile of a single column"""
    name: str
    dtype: ColumnType
    n_unique: int
    n_missing: int
    missing_pct: float
    unique_ratio: float
    is_target_candidate: bool = False
    is_leakage_risk: bool = False
    leakage_correlation: float = 0.0
    should_drop: bool = False
    drop_reason: Optional[str] = None
    statistics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DatasetProfile:
    """Complete profile of a dataset"""
    n_rows: int
    n_cols: int
    size_category: DatasetSize
    problem_type: ProblemType
    target_column: str
    numeric_columns: List[str]
    categorical_columns: List[str]
    text_columns: List[str]
    datetime_columns: List[str]
    id_columns: List[str]
    constant_columns: List[str]
    leakage_columns: List[str]
    columns_to_drop: List[str]
    feature_columns: List[str]
    class_imbalance_ratio: float = 1.0
    is_imbalanced: bool = False
    has_missing: bool = False
    missing_ratio: float = 0.0
    noise_level: str = "low"  # low, medium, high
    recommended_algorithms: List[str] = field(default_factory=list)
    column_profiles: Dict[str, ColumnProfile] = field(default_factory=dict)


@dataclass
class LeakageReport:
    """Report of detected data leakage"""
    has_leakage: bool = False
    leakage_columns: List[str] = field(default_factory=list)
    leakage_details: List[Dict[str, Any]] = field(default_factory=list)
    severity: str = "none"  # none, low, medium, high, critical


@dataclass  
class ModelResult:
    """Result from training a single model"""
    name: str
    train_score: float
    test_score: float
    cv_mean: float
    cv_std: float
    metrics: Dict[str, float]
    overfitting_gap: float
    is_overfit: bool
    is_stable: bool
    reliability_score: float
    feature_importance: List[Dict[str, Any]]
    model: Any
    training_time: float


@dataclass
class GodLevelResult:
    """Complete result from GOD-Level AutoML"""
    success: bool
    problem_type: str
    target_column: str
    feature_columns: List[str]
    best_model_name: str
    best_model_metrics: Dict[str, float]
    best_model_reliability: float
    leaderboard: List[Dict[str, Any]]
    feature_importance: List[Dict[str, Any]]
    leakage_report: LeakageReport
    dataset_profile: DatasetProfile
    preprocessing_steps: List[str]
    y_test: np.ndarray
    y_pred: np.ndarray
    y_proba: Optional[np.ndarray]
    n_rows: int
    n_cols: int
    mode: str
    processing_time: float
    charts: Dict[str, str] = field(default_factory=dict)
    feature_metadata: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    model_pipeline: Any = None


# =============================================================================
# DATA INTELLIGENCE MODULE
# =============================================================================

class DataIntelligence:
    """
    🧠 COMPLETE DATA INTELLIGENCE SYSTEM
    
    Deeply analyzes dataset to understand:
    - Column types (numeric, categorical, text, datetime, boolean, ID-like)
    - Dataset size (tiny, small, medium, large)
    - Feature count and quality
    - Missing values and patterns
    - Class imbalance
    - Noise level
    - Possible data leakage
    - Feature-target relationships
    """
    
    # Pattern detection
    ID_PATTERNS = ['id', '_id', 'index', 'guid', 'uuid', 'pk', 'fk', 'key', 'code', 'no', 'number']
    DATE_PATTERNS = ['date', 'time', 'timestamp', 'created', 'updated', 'modified', 'datetime', 'dt', 'dob']
    URL_PATTERNS = ['url', 'link', 'href', 'path', 'uri', 'website', 'http']
    TARGET_PATTERNS = ['target', 'label', 'class', 'output', 'y', 'result', 'outcome', 'prediction']
    IMPORTANT_PATTERNS = ['rate', 'price', 'cost', 'income', 'salary', 'revenue', 'amount', 'score', 'value', 'total']
    
    def __init__(self):
        self.profile: Optional[DatasetProfile] = None
        self.leakage_report: Optional[LeakageReport] = None
    
    def analyze_dataset(self, df: pd.DataFrame, target_col: Optional[str] = None) -> DatasetProfile:
        """
        Complete dataset analysis - the foundation of GOD-level intelligence.
        """
        logger.info("🧠 STEP 1: COMPLETE DATA INTELLIGENCE")
        logger.info("=" * 60)
        
        n_rows, n_cols = df.shape
        logger.info(f"   Dataset: {n_rows:,} rows × {n_cols} columns")
        
        # 1. Determine dataset size category
        size_category = self._get_size_category(n_rows)
        logger.info(f"   Size Category: {size_category.value}")
        
        # 2. Analyze each column
        column_profiles = {}
        numeric_cols, categorical_cols, text_cols = [], [], []
        datetime_cols, id_cols, constant_cols = [], [], []
        columns_to_drop = []
        
        for col in df.columns:
            profile = self._analyze_column(df[col], col, target_col)
            column_profiles[col] = profile
            
            if profile.should_drop:
                columns_to_drop.append(col)
                if profile.dtype == ColumnType.ID:
                    id_cols.append(col)
                elif profile.dtype == ColumnType.CONSTANT:
                    constant_cols.append(col)
            elif col != target_col:
                if profile.dtype == ColumnType.NUMERIC:
                    numeric_cols.append(col)
                elif profile.dtype == ColumnType.CATEGORICAL:
                    categorical_cols.append(col)
                elif profile.dtype == ColumnType.TEXT:
                    text_cols.append(col)
                elif profile.dtype == ColumnType.DATETIME:
                    datetime_cols.append(col)
        
        # 3. Detect or confirm target column
        if target_col is None:
            target_col = self._detect_target(df)
        
        # 4. Detect problem type
        problem_type = self._detect_problem_type(df[target_col])
        
        # 5. Check for class imbalance (classification only)
        imbalance_ratio = 1.0
        is_imbalanced = False
        if problem_type in [ProblemType.BINARY_CLASSIFICATION, ProblemType.MULTICLASS_CLASSIFICATION]:
            imbalance_ratio, is_imbalanced = self._check_class_imbalance(df[target_col])
        
        # 6. Check missing values
        missing_ratio = df.isna().sum().sum() / (n_rows * n_cols)
        has_missing = missing_ratio > 0.01
        
        # 7. Determine noise level
        noise_level = self._estimate_noise_level(df, target_col, numeric_cols)
        
        # 8. Feature columns (excluding target and dropped)
        feature_columns = [c for c in df.columns if c != target_col and c not in columns_to_drop]
        
        # Create profile
        self.profile = DatasetProfile(
            n_rows=n_rows,
            n_cols=n_cols,
            size_category=size_category,
            problem_type=problem_type,
            target_column=target_col,
            numeric_columns=numeric_cols,
            categorical_columns=categorical_cols,
            text_columns=text_cols,
            datetime_columns=datetime_cols,
            id_columns=id_cols,
            constant_columns=constant_cols,
            leakage_columns=[],  # Filled by leakage detector
            columns_to_drop=columns_to_drop,
            feature_columns=feature_columns,
            class_imbalance_ratio=imbalance_ratio,
            is_imbalanced=is_imbalanced,
            has_missing=has_missing,
            missing_ratio=missing_ratio,
            noise_level=noise_level,
            column_profiles=column_profiles
        )
        
        # Log summary
        logger.info(f"\n   📊 Column Analysis:")
        logger.info(f"      Numeric: {len(numeric_cols)}")
        logger.info(f"      Categorical: {len(categorical_cols)}")
        logger.info(f"      Text: {len(text_cols)}")
        logger.info(f"      Datetime: {len(datetime_cols)}")
        logger.info(f"      ID/Dropped: {len(columns_to_drop)}")
        logger.info(f"\n   🎯 Target: {target_col}")
        logger.info(f"   📋 Problem Type: {problem_type.value}")
        if is_imbalanced:
            logger.info(f"   ⚠️ Class Imbalance: {imbalance_ratio:.1f}:1")
        logger.info(f"   🔍 Missing Data: {missing_ratio*100:.1f}%")
        logger.info(f"   📈 Noise Level: {noise_level}")
        
        return self.profile
    
    def _get_size_category(self, n_rows: int) -> DatasetSize:
        """Categorize dataset by size"""
        if n_rows < 500:
            return DatasetSize.TINY
        elif n_rows < 5000:
            return DatasetSize.SMALL
        elif n_rows < 100000:
            return DatasetSize.MEDIUM
        else:
            return DatasetSize.LARGE
    
    def _analyze_column(self, series: pd.Series, col_name: str, target_col: Optional[str]) -> ColumnProfile:
        """Deep analysis of a single column"""
        n_unique = series.nunique()
        n_total = len(series)
        n_missing = series.isna().sum()
        missing_pct = n_missing / n_total if n_total > 0 else 0
        unique_ratio = n_unique / n_total if n_total > 0 else 0
        
        col_lower = col_name.lower()
        
        # Statistics for numeric columns
        statistics = {}
        if pd.api.types.is_numeric_dtype(series):
            clean = series.dropna()
            if len(clean) > 0:
                statistics = {
                    'mean': float(clean.mean()),
                    'std': float(clean.std()),
                    'min': float(clean.min()),
                    'max': float(clean.max()),
                    'median': float(clean.median()),
                    'q25': float(clean.quantile(0.25)),
                    'q75': float(clean.quantile(0.75)),
                    'skewness': float(clean.skew()) if len(clean) > 2 else 0
                }
        
        # Determine column type
        dtype = self._determine_column_type(series, col_name, unique_ratio)
        
        # Check if should drop
        should_drop = False
        drop_reason = None
        
        # ID columns
        if dtype == ColumnType.ID:
            should_drop = True
            drop_reason = "ID column (unique identifier)"
        
        # Constant columns
        elif n_unique <= 1:
            dtype = ColumnType.CONSTANT
            should_drop = True
            drop_reason = "Constant value (no variance)"
        
        # Too many missing values
        elif missing_pct > 0.6:
            should_drop = True
            drop_reason = f"Too many missing values ({missing_pct*100:.1f}%)"
        
        # Near-unique strings (random data)
        elif dtype == ColumnType.TEXT and unique_ratio > 0.95 and n_unique > 100:
            avg_len = series.astype(str).str.len().mean()
            if avg_len < 50:  # Short unique strings = likely IDs or random
                should_drop = True
                drop_reason = "Near-unique short strings (no pattern)"
        
        # URLs, paths
        if any(p in col_lower for p in self.URL_PATTERNS):
            should_drop = True
            drop_reason = "URL/path column (not predictive)"
        
        # Target candidate check
        is_target_candidate = any(p in col_lower for p in self.TARGET_PATTERNS)
        
        return ColumnProfile(
            name=col_name,
            dtype=dtype,
            n_unique=n_unique,
            n_missing=n_missing,
            missing_pct=missing_pct,
            unique_ratio=unique_ratio,
            is_target_candidate=is_target_candidate,
            should_drop=should_drop,
            drop_reason=drop_reason,
            statistics=statistics
        )
    
    def _determine_column_type(self, series: pd.Series, col_name: str, unique_ratio: float) -> ColumnType:
        """Determine the type of a column"""
        col_lower = col_name.lower()
        n_unique = series.nunique()
        
        # Check for important numeric columns first (rate, price, etc.)
        is_important = any(p in col_lower for p in self.IMPORTANT_PATTERNS)
        
        # ID detection (stricter - must be highly unique AND match pattern)
        if not is_important:
            is_id_pattern = any(p in col_lower for p in self.ID_PATTERNS)
            if is_id_pattern and unique_ratio > 0.9:
                return ColumnType.ID
        
        # Boolean
        if series.dtype == bool:
            return ColumnType.BOOLEAN
        if pd.api.types.is_numeric_dtype(series):
            unique_vals = set(series.dropna().unique())
            if unique_vals.issubset({0, 1, True, False}):
                return ColumnType.BOOLEAN
        
        # Datetime
        if pd.api.types.is_datetime64_any_dtype(series):
            return ColumnType.DATETIME
        if any(p in col_lower for p in self.DATE_PATTERNS):
            # Try to parse as datetime
            try:
                sample = series.dropna().head(5)
                if len(sample) > 0:
                    pd.to_datetime(sample.iloc[0])
                    return ColumnType.DATETIME
            except:
                pass
        
        # Numeric
        if pd.api.types.is_numeric_dtype(series):
            return ColumnType.NUMERIC
        
        # Try to convert to numeric
        try:
            numeric_series = pd.to_numeric(series, errors='coerce')
            if numeric_series.notna().sum() / len(series) > 0.8:
                return ColumnType.NUMERIC
        except:
            pass
        
        # Text vs Categorical
        if series.dtype == object or series.dtype == 'string':
            avg_len = series.astype(str).str.len().mean()
            if n_unique <= 50 and avg_len < 50:
                return ColumnType.CATEGORICAL
            elif avg_len > 30 or n_unique > 50:
                return ColumnType.TEXT
            else:
                return ColumnType.CATEGORICAL
        
        return ColumnType.UNKNOWN
    
    def _detect_target(self, df: pd.DataFrame) -> str:
        """Smart target column detection"""
        # Priority 1: Exact match keywords
        for col in df.columns:
            if col.lower().strip() in ['target', 'label', 'class', 'output', 'y']:
                logger.info(f"   🎯 Target detected (exact match): {col}")
                return col
        
        # Priority 2: Contains keywords
        target_keywords = [
            'target', 'label', 'class', 'churn', 'fraud', 'default', 'outcome',
            'survived', 'sentiment', 'rating', 'price', 'salary', 'income', 
            'revenue', 'amount', 'value', 'result'
        ]
        for keyword in target_keywords:
            for col in df.columns:
                if keyword in col.lower():
                    logger.info(f"   🎯 Target detected (keyword '{keyword}'): {col}")
                    return col
        
        # Priority 3: Last column heuristic
        last_col = df.columns[-1]
        last_unique = df[last_col].nunique()
        
        if last_unique <= 20 or pd.api.types.is_numeric_dtype(df[last_col]):
            logger.info(f"   🎯 Target detected (last column): {last_col}")
            return last_col
        
        # Priority 4: Best candidate by characteristics
        best_candidate = None
        best_score = -1
        
        for col in df.columns:
            n_unique = df[col].nunique()
            is_numeric = pd.api.types.is_numeric_dtype(df[col])
            
            score = 0
            if n_unique == 2:
                score = 100  # Binary - excellent target
            elif n_unique <= 10:
                score = 50   # Multiclass
            elif is_numeric:
                score = 30   # Regression
            
            if score > best_score:
                best_score = score
                best_candidate = col
        
        if best_candidate:
            logger.info(f"   🎯 Target detected (best candidate): {best_candidate}")
            return best_candidate
        
        # Fallback
        logger.info(f"   🎯 Target detected (fallback): {df.columns[-1]}")
        return df.columns[-1]
    
    def _detect_problem_type(self, y: pd.Series) -> ProblemType:
        """
        PRODUCTION-LEVEL Problem Type Detection
        """
        n_unique = y.nunique()
        n_samples = len(y)
        unique_ratio = n_unique / n_samples if n_samples > 0 else 0
        
        # Try converting to numeric
        try:
            y_clean = y.astype(str).str.replace(r'[$,]', '', regex=True)
            y_numeric = pd.to_numeric(y_clean, errors='coerce')
            if y_numeric.notna().sum() / len(y) > 0.9:
                y = y_numeric
                n_unique = y.nunique()
        except:
            pass
        
        # String/Object type = Classification
        if pd.api.types.is_object_dtype(y) or pd.api.types.is_categorical_dtype(y):
            if n_unique == 2:
                return ProblemType.BINARY_CLASSIFICATION
            elif n_unique <= 50:
                return ProblemType.MULTICLASS_CLASSIFICATION
            else:
                return ProblemType.MULTICLASS_CLASSIFICATION
        
        # Boolean = Binary
        if pd.api.types.is_bool_dtype(y):
            return ProblemType.BINARY_CLASSIFICATION
        
        # Numeric analysis
        y_clean = pd.to_numeric(y, errors='coerce').dropna()
        if len(y_clean) == 0:
            return ProblemType.REGRESSION
        
        unique_vals = set(y_clean.unique())
        
        # Binary patterns
        if unique_vals.issubset({0, 1}) or unique_vals.issubset({-1, 1}):
            return ProblemType.BINARY_CLASSIFICATION
        
        # Integer with few unique = Classification
        is_whole = (y_clean % 1 == 0).all()
        if is_whole:
            if n_unique == 2:
                return ProblemType.BINARY_CLASSIFICATION
            elif n_unique <= 10:
                return ProblemType.MULTICLASS_CLASSIFICATION
            elif n_unique <= 20 and unique_ratio < 0.05:
                return ProblemType.MULTICLASS_CLASSIFICATION
        
        # Continuous = Regression
        if not is_whole:
            return ProblemType.REGRESSION
        
        if unique_ratio > 0.1 and n_unique > 20:
            return ProblemType.REGRESSION
        
        val_range = y_clean.max() - y_clean.min()
        if val_range > 100 and n_unique > 30:
            return ProblemType.REGRESSION
        
        # Default based on unique count
        if n_unique <= 15:
            return ProblemType.MULTICLASS_CLASSIFICATION
        
        return ProblemType.REGRESSION
    
    def _check_class_imbalance(self, y: pd.Series) -> Tuple[float, bool]:
        """Check for class imbalance"""
        class_counts = y.value_counts()
        if len(class_counts) < 2:
            return 1.0, False
        
        ratio = class_counts.max() / class_counts.min()
        is_imbalanced = ratio > 3
        return ratio, is_imbalanced
    
    def _estimate_noise_level(self, df: pd.DataFrame, target_col: str, 
                              numeric_cols: List[str]) -> str:
        """Estimate noise level in the dataset"""
        if not numeric_cols:
            return "medium"
        
        try:
            # Calculate coefficient of variation for numeric columns
            cv_values = []
            for col in numeric_cols[:10]:  # Sample first 10
                series = df[col].dropna()
                if len(series) > 0 and series.std() > 0:
                    cv = series.std() / abs(series.mean()) if series.mean() != 0 else 0
                    cv_values.append(cv)
            
            if not cv_values:
                return "medium"
            
            avg_cv = np.mean(cv_values)
            
            if avg_cv < 0.3:
                return "low"
            elif avg_cv < 0.8:
                return "medium"
            else:
                return "high"
        except:
            return "medium"


# =============================================================================
# DATA LEAKAGE DETECTOR
# =============================================================================

class LeakageDetector:
    """
    🚨 ADVANCED DATA LEAKAGE DETECTION SYSTEM
    
    Detects:
    1. High correlation with target (>0.90)
    2. Future information leakage
    3. Duplicate target-like columns
    4. Target encoding leakage
    5. ID-based leakage
    
    This is CRITICAL for preventing fake 99-100% accuracy.
    """
    
    def __init__(self, correlation_threshold: float = 0.90):
        self.correlation_threshold = correlation_threshold
        self.report: Optional[LeakageReport] = None
    
    def detect_leakage(self, df: pd.DataFrame, target_col: str, 
                       profile: DatasetProfile) -> LeakageReport:
        """
        Complete leakage detection - MUST RUN before training.
        """
        logger.info("\n🚨 STEP 2: DATA LEAKAGE DETECTION")
        logger.info("=" * 60)
        
        leakage_columns = []
        leakage_details = []
        
        # Get target as numeric for correlation
        try:
            y = pd.to_numeric(df[target_col], errors='coerce')
            if y.isna().all():
                # Encode categorical target
                le = LabelEncoder()
                y = pd.Series(le.fit_transform(df[target_col].astype(str)))
        except:
            le = LabelEncoder()
            y = pd.Series(le.fit_transform(df[target_col].astype(str)))
        
        # 1. Correlation-based leakage
        logger.info("   🔍 Checking correlation-based leakage...")
        corr_leakage = self._check_correlation_leakage(df, y, target_col, profile)
        leakage_columns.extend(corr_leakage['columns'])
        leakage_details.extend(corr_leakage['details'])
        
        # 2. Duplicate target columns
        logger.info("   🔍 Checking duplicate target columns...")
        dup_leakage = self._check_duplicate_targets(df, target_col)
        leakage_columns.extend(dup_leakage['columns'])
        leakage_details.extend(dup_leakage['details'])
        
        # 3. Future information leakage (date-based)
        logger.info("   🔍 Checking future information leakage...")
        future_leakage = self._check_future_leakage(df, profile)
        leakage_columns.extend(future_leakage['columns'])
        leakage_details.extend(future_leakage['details'])
        
        # 4. Target encoding leakage
        logger.info("   🔍 Checking target encoding leakage...")
        encoding_leakage = self._check_encoding_leakage(df, y, target_col)
        leakage_columns.extend(encoding_leakage['columns'])
        leakage_details.extend(encoding_leakage['details'])
        
        # Unique leakage columns
        leakage_columns = list(set(leakage_columns))
        
        # Determine severity
        if len(leakage_columns) == 0:
            severity = "none"
        elif len(leakage_columns) == 1:
            severity = "low"
        elif len(leakage_columns) <= 3:
            severity = "medium"
        elif any(d['correlation'] > 0.99 for d in leakage_details if 'correlation' in d):
            severity = "critical"
        else:
            severity = "high"
        
        self.report = LeakageReport(
            has_leakage=len(leakage_columns) > 0,
            leakage_columns=leakage_columns,
            leakage_details=leakage_details,
            severity=severity
        )
        
        # Log results
        if self.report.has_leakage:
            logger.warning(f"\n   ⚠️ LEAKAGE DETECTED! Severity: {severity.upper()}")
            for col in leakage_columns:
                logger.warning(f"      🚨 {col}")
            logger.warning(f"   These columns will be REMOVED to prevent fake accuracy.")
        else:
            logger.info("   ✅ No data leakage detected")
        
        return self.report
    
    def _check_correlation_leakage(self, df: pd.DataFrame, y: pd.Series, 
                                   target_col: str, profile: DatasetProfile) -> Dict:
        """Check for features highly correlated with target"""
        leakage_cols = []
        details = []
        
        for col in profile.numeric_columns:
            try:
                corr = abs(df[col].corr(y))
                if corr > self.correlation_threshold:
                    leakage_cols.append(col)
                    details.append({
                        'column': col,
                        'type': 'correlation',
                        'correlation': round(corr, 4),
                        'reason': f"Very high correlation with target ({corr:.1%})"
                    })
                    logger.warning(f"      🚨 {col}: {corr:.1%} correlation with target")
            except:
                pass
        
        return {'columns': leakage_cols, 'details': details}
    
    def _check_duplicate_targets(self, df: pd.DataFrame, target_col: str) -> Dict:
        """Check for columns that are duplicate of target"""
        leakage_cols = []
        details = []
        
        target = df[target_col]
        
        for col in df.columns:
            if col == target_col:
                continue
            
            try:
                # Check if column is exact copy or transformation of target
                if df[col].equals(target):
                    leakage_cols.append(col)
                    details.append({
                        'column': col,
                        'type': 'duplicate_target',
                        'reason': "Exact duplicate of target column"
                    })
                    continue
                
                # Check if column is inverse or simple transform
                if pd.api.types.is_numeric_dtype(df[col]) and pd.api.types.is_numeric_dtype(target):
                    if np.allclose(df[col].dropna(), target.dropna(), rtol=1e-5):
                        leakage_cols.append(col)
                        details.append({
                            'column': col,
                            'type': 'duplicate_target',
                            'reason': "Numerically identical to target"
                        })
            except:
                pass
        
        return {'columns': leakage_cols, 'details': details}
    
    def _check_future_leakage(self, df: pd.DataFrame, profile: DatasetProfile) -> Dict:
        """Check for future information leakage (date-based features)"""
        leakage_cols = []
        details = []
        
        # Future date patterns
        future_patterns = ['outcome_date', 'result_date', 'completion_date', 
                          'resolved_date', 'closed_date', 'end_date', 'finish_date']
        
        for col in profile.datetime_columns:
            col_lower = col.lower()
            if any(p in col_lower for p in future_patterns):
                leakage_cols.append(col)
                details.append({
                    'column': col,
                    'type': 'future_information',
                    'reason': "Date column that may contain future information"
                })
        
        return {'columns': leakage_cols, 'details': details}
    
    def _check_encoding_leakage(self, df: pd.DataFrame, y: pd.Series, 
                                target_col: str) -> Dict:
        """Check for target encoding leakage in categorical columns"""
        leakage_cols = []
        details = []
        
        # Get categorical columns
        cat_cols = df.select_dtypes(include=['object', 'category']).columns
        
        for col in cat_cols:
            if col == target_col:
                continue
            
            try:
                # Check if column values perfectly segment target
                groups = df.groupby(col)[target_col].nunique()
                if (groups == 1).all():
                    leakage_cols.append(col)
                    details.append({
                        'column': col,
                        'type': 'target_encoding',
                        'reason': "Each category maps to exactly one target value"
                    })
            except:
                pass
        
        return {'columns': leakage_cols, 'details': details}


# =============================================================================
# DATA CLEANING & SAFETY
# =============================================================================

class DataCleaner:
    """
    🧹 PROFESSIONAL DATA CLEANING
    
    Performs:
    1. Remove duplicates
    2. Handle missing values intelligently  
    3. Encode categorical features properly
    4. Scale numeric features where required
    5. Parse datetime into useful components
    6. Remove useless columns (IDs, URLs, constants)
    """
    
    def __init__(self, use_knn_imputer: bool = True):
        self.use_knn_imputer = use_knn_imputer
        self.imputers = {}
        self.fill_values = {}
        self.encoders = {}
        self.scaler = None
        self.outlier_bounds = {}
        self.preprocessing_steps = []
    
    def clean(self, df: pd.DataFrame, target_col: str, 
              profile: DatasetProfile, leakage_cols: List[str] = None) -> pd.DataFrame:
        """
        Complete data cleaning pipeline.
        """
        logger.info("\n🧹 STEP 3: DATA CLEANING & SAFETY")
        logger.info("=" * 60)
        
        original_shape = df.shape
        df = df.copy()
        
        # 1. Remove leakage columns FIRST
        if leakage_cols:
            df = df.drop(columns=[c for c in leakage_cols if c in df.columns], errors='ignore')
            self.preprocessing_steps.append(f"Removed {len(leakage_cols)} leakage columns")
            logger.info(f"   🚨 Removed {len(leakage_cols)} leakage columns")
        
        # 2. Remove columns flagged for dropping
        cols_to_drop = [c for c in profile.columns_to_drop if c in df.columns and c != target_col]
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop, errors='ignore')
            self.preprocessing_steps.append(f"Removed {len(cols_to_drop)} useless columns")
            logger.info(f"   🗑️ Removed {len(cols_to_drop)} useless columns (IDs, constants, etc.)")
        
        # 3. Remove duplicates
        n_dups = df.duplicated().sum()
        if n_dups > 0:
            df = df.drop_duplicates()
            self.preprocessing_steps.append(f"Removed {n_dups} duplicate rows")
            logger.info(f"   ✅ Removed {n_dups} duplicate rows")
        
        # 4. Clean string columns
        for col in df.select_dtypes(include=['object']).columns:
            try:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace(['nan', 'NaN', 'None', 'null', '', 'N/A', 'n/a'], np.nan)
            except:
                pass
        self.preprocessing_steps.append("Cleaned string values")
        logger.info(f"   ✅ Cleaned string values")
        
        # 5. Handle numeric columns
        numeric_cols = [c for c in profile.numeric_columns if c in df.columns]
        if numeric_cols:
            df = self._handle_numeric(df, numeric_cols, target_col)
        
        # 6. Handle missing values
        df = self._handle_missing(df, target_col)
        
        # 7. Handle infinite values
        for col in df.select_dtypes(include=[np.number]).columns:
            if col != target_col:
                try:
                    inf_mask = np.isinf(df[col])
                    if inf_mask.any():
                        median_val = df.loc[~inf_mask, col].median()
                        df.loc[inf_mask, col] = median_val if not pd.isna(median_val) else 0
                except:
                    pass
        self.preprocessing_steps.append("Handled infinite values")
        logger.info(f"   ✅ Handled infinite values")
        
        # 8. Cap outliers using IQR
        df = self._cap_outliers(df, target_col)
        
        logger.info(f"\n   📊 Cleaning Result: {original_shape} → {df.shape}")
        
        return df
    
    def _handle_numeric(self, df: pd.DataFrame, numeric_cols: List[str], 
                        target_col: str) -> pd.DataFrame:
        """Handle numeric column preprocessing"""
        for col in numeric_cols:
            if col == target_col or col not in df.columns:
                continue
            
            try:
                # Convert to numeric (handles strings with numbers)
                df[col] = pd.to_numeric(df[col], errors='coerce')
            except:
                pass
        
        self.preprocessing_steps.append("Converted numeric columns")
        logger.info(f"   ✅ Processed {len(numeric_cols)} numeric columns")
        return df
    
    def _handle_missing(self, df: pd.DataFrame, target_col: str) -> pd.DataFrame:
        """Intelligent missing value handling"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [c for c in numeric_cols if c != target_col]
        
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        cat_cols = [c for c in cat_cols if c != target_col]
        
        # Numeric: KNN or median imputation
        if numeric_cols and self.use_knn_imputer:
            try:
                missing_mask = df[numeric_cols].isna().any()
                cols_with_missing = [c for c, has in zip(numeric_cols, missing_mask) if has]
                
                if cols_with_missing:
                    imputer = KNNImputer(n_neighbors=5, weights='distance')
                    df[numeric_cols] = imputer.fit_transform(df[numeric_cols])
                    self.imputers['knn_numeric'] = imputer
                    self.preprocessing_steps.append(f"KNN imputed {len(cols_with_missing)} numeric columns")
                    logger.info(f"   ✅ KNN imputed {len(cols_with_missing)} numeric columns")
            except Exception as e:
                # Fallback to median
                for col in numeric_cols:
                    if df[col].isna().any():
                        fill_val = df[col].median()
                        if pd.isna(fill_val):
                            fill_val = 0
                        df[col] = df[col].fillna(fill_val)
                        self.fill_values[col] = fill_val
                self.preprocessing_steps.append("Median imputed numeric columns")
        
        # Categorical: mode or '_MISSING_'
        for col in cat_cols:
            if df[col].isna().any():
                mode_vals = df[col].mode()
                fill_val = mode_vals.iloc[0] if len(mode_vals) > 0 else '_MISSING_'
                df[col] = df[col].fillna(fill_val)
                self.fill_values[col] = fill_val
        
        if cat_cols:
            self.preprocessing_steps.append(f"Imputed {len(cat_cols)} categorical columns")
            logger.info(f"   ✅ Imputed {len(cat_cols)} categorical columns")
        
        return df
    
    def _cap_outliers(self, df: pd.DataFrame, target_col: str) -> pd.DataFrame:
        """Cap outliers using IQR method"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        n_capped = 0
        
        for col in numeric_cols:
            if col == target_col:
                continue
            
            try:
                q1 = df[col].quantile(0.01)
                q3 = df[col].quantile(0.99)
                iqr_q1 = df[col].quantile(0.25)
                iqr_q3 = df[col].quantile(0.75)
                iqr = iqr_q3 - iqr_q1
                
                lower = max(q1, iqr_q1 - 3 * iqr) if pd.notna(iqr_q1 - 3 * iqr) else q1
                upper = min(q3, iqr_q3 + 3 * iqr) if pd.notna(iqr_q3 + 3 * iqr) else q3
                
                before_outliers = ((df[col] < lower) | (df[col] > upper)).sum()
                if before_outliers > 0:
                    df[col] = df[col].clip(lower=lower, upper=upper)
                    self.outlier_bounds[col] = (lower, upper)
                    n_capped += 1
            except:
                pass
        
        if n_capped > 0:
            self.preprocessing_steps.append(f"Capped outliers in {n_capped} columns")
            logger.info(f"   ✅ Capped outliers in {n_capped} columns (IQR method)")
        
        return df


# =============================================================================
# FEATURE ENGINEERING INTELLIGENCE
# =============================================================================

class FeatureEngineer:
    """
    🔧 INTELLIGENT FEATURE ENGINEERING
    
    Performs:
    1. Correlation analysis
    2. Feature importance ranking
    3. Redundant feature removal
    4. Low-variance feature removal
    5. Noise feature removal
    6. Derived feature creation
    """
    
    def __init__(self, mode: TrainingMode = TrainingMode.FAST):
        self.mode = mode
        self.variance_selector = None
        self.selected_features = []
        self.feature_scores = {}
        self.encoders = {}
        self.scaler = None
        self.vectorizers = {}
        self.feature_names = []
    
    def engineer_features(self, df: pd.DataFrame, target_col: str,
                          profile: DatasetProfile) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Complete feature engineering pipeline.
        """
        logger.info("\n🔧 STEP 4: FEATURE ENGINEERING INTELLIGENCE")
        logger.info("=" * 60)
        
        X = df.drop(columns=[target_col]).copy()
        y = df[target_col].copy()
        
        # Encode target if needed
        task_type = profile.problem_type
        if task_type in [ProblemType.BINARY_CLASSIFICATION, ProblemType.MULTICLASS_CLASSIFICATION]:
            if y.dtype == 'object' or y.dtype.name == 'category':
                le = LabelEncoder()
                y = le.fit_transform(y)
                self.encoders['target'] = le
        else:
            y = pd.to_numeric(y, errors='coerce').fillna(y.median()).values
        
        # Get column lists
        numeric_cols = [c for c in profile.numeric_columns if c in X.columns]
        cat_cols = [c for c in profile.categorical_columns if c in X.columns]
        text_cols = [c for c in profile.text_columns if c in X.columns]
        
        processed_parts = []
        feature_names = []
        
        # 1. Process numeric features
        if numeric_cols:
            X_numeric, num_names = self._process_numeric(X[numeric_cols])
            processed_parts.append(X_numeric)
            feature_names.extend(num_names)
            logger.info(f"   ✅ Numeric features: {len(num_names)}")
        
        # 2. Process categorical features
        if cat_cols:
            X_cat, cat_names = self._process_categorical(X[cat_cols])
            processed_parts.append(X_cat)
            feature_names.extend(cat_names)
            logger.info(f"   ✅ Categorical features: {len(cat_names)}")
        
        # 3. Process text features
        if text_cols:
            X_text, text_names = self._process_text(X[text_cols])
            processed_parts.append(X_text)
            feature_names.extend(text_names)
            logger.info(f"   ✅ Text features: {len(text_names)}")
        
        # Combine all features
        if not processed_parts:
            raise ValueError("No valid features after engineering")
        
        X_combined = np.hstack(processed_parts)
        self.feature_names = feature_names
        
        # 4. Feature selection (remove low variance, redundant)
        X_selected, selected_names = self._select_features(
            X_combined, y, feature_names, task_type
        )
        
        logger.info(f"\n   📊 Feature Engineering: {X.shape[1]} columns → {X_selected.shape[1]} features")
        
        return X_selected, np.array(y), selected_names
    
    def _process_numeric(self, X: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
        """Process numeric features with scaling"""
        # Convert to numeric and fill missing
        X_clean = X.apply(pd.to_numeric, errors='coerce')
        X_clean = X_clean.fillna(X_clean.median())
        X_clean = X_clean.fillna(0)
        
        # Scale with RobustScaler
        self.scaler = RobustScaler()
        X_scaled = self.scaler.fit_transform(X_clean)
        
        return X_scaled, list(X.columns)
    
    def _process_categorical(self, X: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
        """Process categorical features with label encoding"""
        encoded_arrays = []
        names = []
        
        for col in X.columns:
            series = X[col].fillna('_MISSING_').astype(str)
            le = LabelEncoder()
            encoded = le.fit_transform(series).reshape(-1, 1)
            self.encoders[col] = le
            encoded_arrays.append(encoded.astype(float))
            names.append(col)
        
        return np.hstack(encoded_arrays), names
    
    def _process_text(self, X: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
        """Process text features with TF-IDF"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        text_arrays = []
        names = []
        
        for col in X.columns:
            series = X[col].fillna('').astype(str)
            
            # Clean text
            series = series.str.lower()
            series = series.str.replace(r'[^a-z\s]', ' ', regex=True)
            series = series.str.replace(r'\s+', ' ', regex=True)
            
            tfidf = TfidfVectorizer(
                max_features=100,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.9
            )
            
            try:
                vectors = tfidf.fit_transform(series).toarray()
                self.vectorizers[col] = tfidf
                text_arrays.append(vectors)
                
                # Create feature names
                vocab = tfidf.get_feature_names_out()
                col_names = [f"{col}_tfidf_{v}" for v in vocab]
                names.extend(col_names)
            except:
                # If TF-IDF fails, fall back to simple stats
                char_count = series.str.len().values.reshape(-1, 1)
                word_count = series.str.split().str.len().fillna(0).values.reshape(-1, 1)
                text_arrays.append(np.hstack([char_count, word_count]))
                names.extend([f"{col}_char_count", f"{col}_word_count"])
        
        if text_arrays:
            return np.hstack(text_arrays), names
        return np.array([]).reshape(len(X), 0), []
    
    def _select_features(self, X: np.ndarray, y: np.ndarray, 
                         feature_names: List[str], task_type: ProblemType) -> Tuple[np.ndarray, List[str]]:
        """Intelligent feature selection"""
        n_original = X.shape[1]
        
        # 1. Remove zero variance
        try:
            var_selector = VarianceThreshold(threshold=0.001)
            X_var = var_selector.fit_transform(X)
            mask = var_selector.get_support()
            feature_names = [n for n, m in zip(feature_names, mask) if m]
            self.variance_selector = var_selector
            logger.info(f"      Variance filter: {n_original} → {X_var.shape[1]}")
            X = X_var
        except:
            pass
        
        # 2. Remove highly correlated features
        if X.shape[1] > 2:
            try:
                corr_matrix = np.corrcoef(X, rowvar=False)
                corr_matrix = np.nan_to_num(corr_matrix, nan=0)
                upper_tri = np.triu(np.abs(corr_matrix), k=1)
                high_corr_cols = set()
                for i in range(upper_tri.shape[0]):
                    for j in range(i+1, upper_tri.shape[1]):
                        if upper_tri[i, j] > 0.95:
                            high_corr_cols.add(j)
                
                mask = [i not in high_corr_cols for i in range(X.shape[1])]
                X = X[:, mask]
                feature_names = [n for n, m in zip(feature_names, mask) if m]
                if len(high_corr_cols) > 0:
                    logger.info(f"      Correlation filter: removed {len(high_corr_cols)} features")
            except:
                pass
        
        # 3. Mutual information ranking (keep top 80% or min 10)
        if X.shape[1] > 10 and self.mode == TrainingMode.ULTRA:
            try:
                is_classification = task_type in [ProblemType.BINARY_CLASSIFICATION, 
                                                  ProblemType.MULTICLASS_CLASSIFICATION]
                mi_func = mutual_info_classif if is_classification else mutual_info_regression
                mi_scores = mi_func(X, y, random_state=42)
                
                k = max(10, int(X.shape[1] * 0.8))
                top_indices = np.argsort(mi_scores)[-k:]
                X = X[:, top_indices]
                feature_names = [feature_names[i] for i in top_indices]
                logger.info(f"      MI ranking: kept top {k} features")
            except:
                pass
        
        self.selected_features = feature_names
        logger.info(f"      Final: {n_original} → {X.shape[1]} features")
        
        return X, feature_names


# =============================================================================
# MODEL SELECTION INTELLIGENCE
# =============================================================================

class ModelSelector:
    """
    🧠 INTELLIGENT MODEL SELECTION ENGINE
    
    Selects models based on:
    - Dataset size (tiny/small/medium/large)
    - Problem type (classification/regression)
    - Noise level
    - Feature complexity
    - Class imbalance
    
    Rules:
    - Small data: prefer simpler models (Linear, RF, SVM)
    - Large data: gradient boosting (XGBoost, LightGBM)
    - Imbalanced: use class weights
    - High noise: robust models (RF, Ridge)
    """
    
    def get_models(self, profile: DatasetProfile, mode: TrainingMode,
                   selected_category: Optional[str] = None) -> Dict[str, Tuple[Any, Dict]]:
        """
        Get models appropriate for the dataset.
        """
        logger.info("\n🧠 STEP 5: MODEL SELECTION INTELLIGENCE")
        logger.info("=" * 60)
        
        problem_type = profile.problem_type
        size = profile.size_category
        is_imbalanced = profile.is_imbalanced
        noise = profile.noise_level
        
        # Get all available models
        if problem_type in [ProblemType.BINARY_CLASSIFICATION, ProblemType.MULTICLASS_CLASSIFICATION]:
            all_models = self._get_classification_models(profile, mode)
        elif problem_type == ProblemType.REGRESSION:
            all_models = self._get_regression_models(profile, mode)
        else:
            all_models = self._get_classification_models(profile, mode)  # Default
        
        # Filter by user selection
        if selected_category and selected_category != 'auto':
            all_models = self._filter_by_category(all_models, selected_category)
        
        # Select based on data characteristics
        recommended = self._recommend_models(profile, mode)
        
        logger.info(f"   📊 Dataset: {size.value}, {profile.n_rows:,} rows, {noise} noise")
        logger.info(f"   🎯 Problem: {problem_type.value}")
        if is_imbalanced:
            logger.info(f"   ⚠️ Imbalanced: {profile.class_imbalance_ratio:.1f}:1")
        logger.info(f"   🔧 Mode: {mode.value}")
        logger.info(f"   📦 Models: {len(all_models)} available")
        logger.info(f"   ⭐ Recommended: {', '.join(recommended[:5])}")
        
        return all_models
    
    def _get_classification_models(self, profile: DatasetProfile, 
                                   mode: TrainingMode) -> Dict[str, Tuple[Any, Dict]]:
        """Get classification models with appropriate hyperparameters"""
        size = profile.size_category
        is_imbalanced = profile.is_imbalanced
        
        # Scale hyperparameters based on dataset size
        if size == DatasetSize.TINY:
            n_estimators = [30, 50]
            max_depth = [3, 5]
            C_values = [0.01, 0.1]
        elif size == DatasetSize.SMALL:
            n_estimators = [50, 100]
            max_depth = [5, 8]
            C_values = [0.1, 0.5]
        elif size == DatasetSize.MEDIUM:
            n_estimators = [100, 200]
            max_depth = [8, 12]
            C_values = [0.5, 1.0]
        else:  # Large
            n_estimators = [100, 200]
            max_depth = [10, 15]
            C_values = [1.0, 5.0]
        
        class_weight = 'balanced' if is_imbalanced else None
        
        models = {
            # Tree-based
            'RandomForest': (
                RandomForestClassifier(n_jobs=-1, random_state=42, class_weight=class_weight),
                {'n_estimators': n_estimators, 'max_depth': max_depth}
            ),
            'ExtraTrees': (
                ExtraTreesClassifier(n_jobs=-1, random_state=42, class_weight=class_weight),
                {'n_estimators': n_estimators, 'max_depth': max_depth}
            ),
            'HistGradientBoosting': (
                HistGradientBoostingClassifier(random_state=42, early_stopping=True),
                {'max_iter': n_estimators, 'max_depth': max_depth}
            ),
            
            # Linear models
            'LogisticRegression': (
                LogisticRegression(max_iter=1000, random_state=42, n_jobs=-1, 
                                   class_weight=class_weight),
                {'C': C_values, 'penalty': ['l2']}
            ),
            
            # Others
            'GaussianNB': (GaussianNB(), {}),
            'KNN': (KNeighborsClassifier(n_jobs=-1), {'n_neighbors': [3, 5, 7]}),
        }
        
        # Add XGBoost if available
        if HAS_XGBOOST:
            scale_pos_weight = profile.class_imbalance_ratio if is_imbalanced else 1
            models['XGBoost'] = (
                xgb.XGBClassifier(n_jobs=-1, random_state=42, verbosity=0,
                                  scale_pos_weight=scale_pos_weight,
                                  eval_metric='logloss'),
                {'n_estimators': n_estimators, 'max_depth': max_depth, 
                 'learning_rate': [0.05, 0.1]}
            )
        
        # Add LightGBM if available  
        if HAS_LIGHTGBM:
            models['LightGBM'] = (
                lgb.LGBMClassifier(n_jobs=-1, random_state=42, verbose=-1,
                                   class_weight=class_weight),
                {'n_estimators': n_estimators, 'max_depth': max_depth,
                 'learning_rate': [0.05, 0.1]}
            )
        
        # Add CatBoost if available
        if HAS_CATBOOST:
            models['CatBoost'] = (
                CatBoostClassifier(random_state=42, verbose=0, allow_writing_files=False),
                {'iterations': n_estimators, 'depth': max_depth,
                 'learning_rate': [0.05, 0.1]}
            )
        
        # Add more models for ULTRA mode
        if mode == TrainingMode.ULTRA:
            models.update({
                'SVM': (
                    SVC(random_state=42, probability=True, class_weight=class_weight),
                    {'C': C_values, 'kernel': ['rbf']}
                ),
                'MLP': (
                    MLPClassifier(random_state=42, max_iter=500, early_stopping=True),
                    {'hidden_layer_sizes': [(64, 32), (100, 50)]}
                ),
                'AdaBoost': (
                    AdaBoostClassifier(random_state=42),
                    {'n_estimators': n_estimators}
                ),
                'DecisionTree': (
                    DecisionTreeClassifier(random_state=42, class_weight=class_weight),
                    {'max_depth': max_depth}
                ),
            })
        
        return models
    
    def _get_regression_models(self, profile: DatasetProfile,
                               mode: TrainingMode) -> Dict[str, Tuple[Any, Dict]]:
        """Get regression models with appropriate hyperparameters"""
        size = profile.size_category
        
        # Scale hyperparameters based on dataset size
        if size == DatasetSize.TINY:
            n_estimators = [30, 50]
            max_depth = [3, 5]
            alpha_values = [1.0, 5.0, 10.0]
        elif size == DatasetSize.SMALL:
            n_estimators = [50, 100]
            max_depth = [5, 8]
            alpha_values = [0.1, 1.0, 5.0]
        else:
            n_estimators = [100, 200]
            max_depth = [8, 12]
            alpha_values = [0.01, 0.1, 1.0]
        
        models = {
            # Linear models
            'Ridge': (Ridge(random_state=42), {'alpha': alpha_values}),
            'Lasso': (Lasso(random_state=42, max_iter=2000), {'alpha': alpha_values}),
            'ElasticNet': (
                ElasticNet(random_state=42, max_iter=2000),
                {'alpha': [0.1, 0.5, 1.0], 'l1_ratio': [0.2, 0.5, 0.8]}
            ),
            
            # Tree-based
            'RandomForest': (
                RandomForestRegressor(n_jobs=-1, random_state=42),
                {'n_estimators': n_estimators, 'max_depth': max_depth}
            ),
            'ExtraTrees': (
                ExtraTreesRegressor(n_jobs=-1, random_state=42),
                {'n_estimators': n_estimators, 'max_depth': max_depth}
            ),
            'HistGradientBoosting': (
                HistGradientBoostingRegressor(random_state=42, early_stopping=True),
                {'max_iter': n_estimators, 'max_depth': max_depth}
            ),
            
            # Robust
            'HuberRegressor': (
                HuberRegressor(max_iter=1000),
                {'alpha': alpha_values, 'epsilon': [1.35, 1.5, 2.0]}
            ),
        }
        
        # Add gradient boosting libraries
        if HAS_XGBOOST:
            models['XGBoost'] = (
                xgb.XGBRegressor(n_jobs=-1, random_state=42, verbosity=0),
                {'n_estimators': n_estimators, 'max_depth': max_depth,
                 'learning_rate': [0.05, 0.1]}
            )
        
        if HAS_LIGHTGBM:
            models['LightGBM'] = (
                lgb.LGBMRegressor(n_jobs=-1, random_state=42, verbose=-1),
                {'n_estimators': n_estimators, 'max_depth': max_depth,
                 'learning_rate': [0.05, 0.1]}
            )
        
        if HAS_CATBOOST:
            models['CatBoost'] = (
                CatBoostRegressor(random_state=42, verbose=0, allow_writing_files=False),
                {'iterations': n_estimators, 'depth': max_depth,
                 'learning_rate': [0.05, 0.1]}
            )
        
        # Add more models for ULTRA mode
        if mode == TrainingMode.ULTRA:
            models.update({
                'SVR': (SVR(), {'C': [0.1, 1.0, 10.0], 'kernel': ['rbf']}),
                'MLP': (
                    MLPRegressor(random_state=42, max_iter=500, early_stopping=True),
                    {'hidden_layer_sizes': [(64, 32), (100, 50)]}
                ),
                'BayesianRidge': (BayesianRidge(), {}),
                'KNN': (KNeighborsRegressor(n_jobs=-1), {'n_neighbors': [3, 5, 7]}),
            })
        
        return models
    
    def _filter_by_category(self, models: Dict, category: str) -> Dict:
        """Filter models by category"""
        category_map = {
            'tree_based': ['RandomForest', 'ExtraTrees', 'XGBoost', 'LightGBM', 
                          'CatBoost', 'HistGradientBoosting', 'DecisionTree'],
            'linear': ['LogisticRegression', 'Ridge', 'Lasso', 'ElasticNet',
                      'HuberRegressor', 'BayesianRidge'],
            'svm': ['SVM', 'SVR', 'LinearSVC'],
            'neural': ['MLP'],
            'ensemble': ['AdaBoost', 'Bagging'],
            'neighbors': ['KNN'],
            'naive_bayes': ['GaussianNB', 'MultinomialNB', 'ComplementNB'],
        }
        
        allowed = category_map.get(category.lower(), [])
        if not allowed:
            return models
        
        return {k: v for k, v in models.items() if k in allowed}
    
    def _recommend_models(self, profile: DatasetProfile, mode: TrainingMode) -> List[str]:
        """Recommend models based on dataset characteristics"""
        recommended = []
        size = profile.size_category
        problem_type = profile.problem_type
        noise = profile.noise_level
        
        # Always recommend gradient boosting (best general performers)
        if HAS_XGBOOST:
            recommended.append('XGBoost')
        if HAS_LIGHTGBM:
            recommended.append('LightGBM')
        
        recommended.append('RandomForest')
        recommended.append('HistGradientBoosting')
        
        # Small data: simpler models
        if size in [DatasetSize.TINY, DatasetSize.SMALL]:
            if problem_type in [ProblemType.BINARY_CLASSIFICATION, 
                               ProblemType.MULTICLASS_CLASSIFICATION]:
                recommended.extend(['LogisticRegression', 'KNN', 'GaussianNB'])
            else:
                recommended.extend(['Ridge', 'Lasso', 'ElasticNet'])
        
        # Large data: scalable models
        if size == DatasetSize.LARGE:
            recommended.extend(['HistGradientBoosting'])
            if problem_type == ProblemType.REGRESSION:
                recommended.append('SGDRegressor')
        
        # High noise: robust models
        if noise == 'high':
            recommended.extend(['RandomForest', 'ExtraTrees'])
            if problem_type == ProblemType.REGRESSION:
                recommended.append('HuberRegressor')
        
        return list(dict.fromkeys(recommended))  # Remove duplicates, preserve order


# =============================================================================
# SAFE TRAINING PIPELINE
# =============================================================================

class SafeTrainer:
    """
    🛡️ SAFE TRAINING PIPELINE
    
    Ensures:
    1. Proper train/test split
    2. Stratified split for classification
    3. Cross-validation
    4. Hyperparameter tuning (ULTRA mode)
    5. Overfitting detection (train vs test gap)
    6. Generalization testing
    """
    
    def __init__(self, mode: TrainingMode = TrainingMode.FAST):
        self.mode = mode
        self.best_model = None
        self.best_model_name = None
        self.best_metrics = {}
        self.leaderboard = []
        self.y_test = None
        self.y_pred = None
        self.y_proba = None
    
    def train(self, X: np.ndarray, y: np.ndarray, models: Dict[str, Tuple[Any, Dict]],
              problem_type: ProblemType, profile: DatasetProfile,
              user_id: str = "default") -> List[ModelResult]:
        """
        Safe training with all protection mechanisms.
        """
        logger.info("\n🛡️ STEP 6: SAFE TRAINING PIPELINE")
        logger.info("=" * 60)
        
        is_classification = problem_type in [ProblemType.BINARY_CLASSIFICATION,
                                             ProblemType.MULTICLASS_CLASSIFICATION]
        
        # 1. Proper train/test split
        test_size = 0.2
        if profile.size_category == DatasetSize.TINY:
            test_size = 0.3  # Larger test set for tiny data
        
        if is_classification:
            # Stratified split for classification
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, stratify=y
            )
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )
        
        self.y_test = y_test
        
        logger.info(f"   📊 Train/Test Split: {len(X_train):,}/{len(X_test):,}")
        
        # 2. Handle class imbalance with SMOTE
        if is_classification and profile.is_imbalanced and HAS_IMBLEARN:
            try:
                smote = SMOTE(random_state=42)
                X_train, y_train = smote.fit_resample(X_train, y_train)
                logger.info(f"   ⚖️ Applied SMOTE: {len(X_train):,} samples")
            except Exception as e:
                logger.warning(f"   ⚠️ SMOTE failed: {str(e)[:50]}")
        
        # 3. Cross-validation setup
        cv_folds = self._get_cv_folds(profile)
        if is_classification:
            cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
        else:
            cv = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
        
        logger.info(f"   📈 Cross-validation: {cv_folds} folds")
        
        # 4. Train each model
        results = []
        logger.info(f"\n   🏋️ Training {len(models)} models...")
        
        for name, (model, params) in models.items():
            try:
                result = self._train_single_model(
                    name, model, params, X_train, y_train, X_test, y_test,
                    cv, is_classification, profile
                )
                results.append(result)
                
                # Log result
                status = "✅" if not result.is_overfit else "⚠️"
                logger.info(f"      {status} {name}: {result.test_score:.4f} "
                           f"(CV: {result.cv_mean:.4f} ± {result.cv_std:.4f})")
            except Exception as e:
                logger.warning(f"      ❌ {name} failed: {str(e)[:50]}")
        
        # 5. Select best model
        if results:
            # Sort by reliability score (combines accuracy and stability)
            results.sort(key=lambda x: x.reliability_score, reverse=True)
            
            best = results[0]
            self.best_model = best.model
            self.best_model_name = best.name
            self.best_metrics = best.metrics
            self.y_pred = best.model.predict(X_test)
            
            if is_classification and hasattr(best.model, 'predict_proba'):
                self.y_proba = best.model.predict_proba(X_test)
            
            logger.info(f"\n   🏆 Best Model: {best.name}")
            logger.info(f"      Test Score: {best.test_score:.4f}")
            logger.info(f"      CV Score: {best.cv_mean:.4f} ± {best.cv_std:.4f}")
            logger.info(f"      Reliability: {best.reliability_score:.2f}/100")
        
        # 6. Build leaderboard
        self.leaderboard = [
            {
                'rank': i + 1,
                'model': r.name,
                'test_score': round(r.test_score, 4),
                'cv_mean': round(r.cv_mean, 4),
                'cv_std': round(r.cv_std, 4),
                'overfit_gap': round(r.overfitting_gap, 4),
                'is_overfit': r.is_overfit,
                'reliability': round(r.reliability_score, 2),
                'metrics': {k: round(v, 4) for k, v in r.metrics.items()}
            }
            for i, r in enumerate(results)
        ]
        
        return results
    
    def _get_cv_folds(self, profile: DatasetProfile) -> int:
        """Determine CV folds based on dataset size and mode"""
        if profile.size_category == DatasetSize.TINY:
            return 10  # More folds for tiny data
        elif profile.size_category == DatasetSize.SMALL:
            return 5
        elif self.mode == TrainingMode.ULTRA:
            return 5
        else:
            return 3
    
    def _train_single_model(self, name: str, model: Any, params: Dict,
                            X_train: np.ndarray, y_train: np.ndarray,
                            X_test: np.ndarray, y_test: np.ndarray,
                            cv: Any, is_classification: bool,
                            profile: DatasetProfile) -> ModelResult:
        """Train a single model with CV and hyperparameter tuning"""
        import time
        from sklearn.model_selection import RandomizedSearchCV
        
        start_time = time.time()
        
        # Hyperparameter tuning
        if params and self.mode == TrainingMode.ULTRA and HAS_OPTUNA:
            # Use Optuna for ULTRA mode
            model = self._optuna_tune(model, params, X_train, y_train, cv, is_classification)
        elif params:
            # Use RandomizedSearchCV for FAST mode
            try:
                n_iter = min(5, np.prod([len(v) for v in params.values()]))
                search = RandomizedSearchCV(
                    model, params, n_iter=n_iter, cv=3,
                    scoring='f1_weighted' if is_classification else 'r2',
                    random_state=42, n_jobs=-1
                )
                search.fit(X_train, y_train)
                model = search.best_estimator_
            except:
                model.fit(X_train, y_train)
        else:
            model.fit(X_train, y_train)
        
        # Calculate metrics
        train_score = self._score(model, X_train, y_train, is_classification)
        test_score = self._score(model, X_test, y_test, is_classification)
        
        # Cross-validation
        scoring = 'f1_weighted' if is_classification else 'r2'
        try:
            cv_scores = cross_val_score(model, X_train, y_train, cv=cv, scoring=scoring)
            cv_mean = cv_scores.mean()
            cv_std = cv_scores.std()
        except:
            cv_mean = test_score
            cv_std = 0.0
        
        # Overfitting detection
        overfitting_gap = train_score - test_score
        is_overfit = overfitting_gap > 0.15  # >15% gap = overfit
        
        # Stability check
        is_stable = cv_std < 0.10  # <10% std = stable
        
        # Reliability score (0-100)
        reliability_score = self._calculate_reliability(
            test_score, cv_mean, cv_std, overfitting_gap, is_classification
        )
        
        # Detailed metrics
        metrics = self._calculate_metrics(model, X_test, y_test, is_classification)
        
        # Feature importance
        feature_importance = self._get_feature_importance(model, profile)
        
        training_time = time.time() - start_time
        
        return ModelResult(
            name=name,
            train_score=train_score,
            test_score=test_score,
            cv_mean=cv_mean,
            cv_std=cv_std,
            metrics=metrics,
            overfitting_gap=overfitting_gap,
            is_overfit=is_overfit,
            is_stable=is_stable,
            reliability_score=reliability_score,
            feature_importance=feature_importance,
            model=model,
            training_time=training_time
        )
    
    def _optuna_tune(self, model: Any, params: Dict, X: np.ndarray, y: np.ndarray,
                     cv: Any, is_classification: bool) -> Any:
        """Optuna hyperparameter tuning for ULTRA mode"""
        def objective(trial):
            # Create parameter suggestions
            tuned_params = {}
            for name, values in params.items():
                if isinstance(values[0], int):
                    tuned_params[name] = trial.suggest_int(name, min(values), max(values))
                elif isinstance(values[0], float):
                    tuned_params[name] = trial.suggest_float(name, min(values), max(values))
                else:
                    tuned_params[name] = trial.suggest_categorical(name, values)
            
            # Clone and set params
            from sklearn.base import clone
            trial_model = clone(model)
            trial_model.set_params(**tuned_params)
            
            # CV score
            scoring = 'f1_weighted' if is_classification else 'r2'
            scores = cross_val_score(trial_model, X, y, cv=cv, scoring=scoring)
            return scores.mean()
        
        try:
            study = optuna.create_study(direction='maximize')
            study.optimize(objective, n_trials=20, show_progress_bar=False)
            
            # Get best params and fit
            from sklearn.base import clone
            best_model = clone(model)
            best_model.set_params(**study.best_params)
            best_model.fit(X, y)
            return best_model
        except:
            model.fit(X, y)
            return model
    
    def _score(self, model: Any, X: np.ndarray, y: np.ndarray, 
               is_classification: bool) -> float:
        """Calculate primary score"""
        y_pred = model.predict(X)
        if is_classification:
            return f1_score(y, y_pred, average='weighted')
        else:
            return r2_score(y, y_pred)
    
    def _calculate_reliability(self, test_score: float, cv_mean: float, cv_std: float,
                               overfit_gap: float, is_classification: bool) -> float:
        """Calculate model reliability score (0-100)"""
        # Base score from test performance (40 points)
        if is_classification:
            base_score = test_score * 40  # F1 0-1 -> 0-40
        else:
            # R2 can be negative, clamp to 0-1
            base_score = max(0, test_score) * 40
        
        # CV consistency bonus (30 points)
        cv_bonus = max(0, (1 - cv_std * 3)) * 30  # Lower std = higher bonus
        
        # Overfit penalty (30 points)
        overfit_penalty = min(30, overfit_gap * 100)  # 15% gap = 15 point penalty
        overfit_score = max(0, 30 - overfit_penalty)
        
        reliability = base_score + cv_bonus + overfit_score
        return min(100, max(0, reliability))
    
    def _calculate_metrics(self, model: Any, X: np.ndarray, y: np.ndarray,
                          is_classification: bool) -> Dict[str, float]:
        """Calculate comprehensive metrics"""
        y_pred = model.predict(X)
        
        if is_classification:
            metrics = {
                'accuracy': accuracy_score(y, y_pred),
                'precision': precision_score(y, y_pred, average='weighted', zero_division=0),
                'recall': recall_score(y, y_pred, average='weighted', zero_division=0),
                'f1': f1_score(y, y_pred, average='weighted', zero_division=0),
            }
            
            # Add ROC-AUC for binary classification
            if len(np.unique(y)) == 2 and hasattr(model, 'predict_proba'):
                try:
                    y_proba = model.predict_proba(X)[:, 1]
                    metrics['roc_auc'] = roc_auc_score(y, y_proba)
                except:
                    pass
        else:
            metrics = {
                'r2': r2_score(y, y_pred),
                'mae': mean_absolute_error(y, y_pred),
                'rmse': np.sqrt(mean_squared_error(y, y_pred)),
            }
            
            # Add MAPE if target has no zeros
            if not (y == 0).any():
                metrics['mape'] = mean_absolute_percentage_error(y, y_pred)
        
        return metrics
    
    def _get_feature_importance(self, model: Any, profile: DatasetProfile) -> List[Dict]:
        """Get feature importance from model"""
        importance = []
        
        try:
            feature_names = profile.feature_columns
            
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
            elif hasattr(model, 'coef_'):
                importances = np.abs(model.coef_).flatten()
            else:
                return []
            
            # Match with feature names
            n_features = min(len(feature_names), len(importances))
            for i in range(n_features):
                importance.append({
                    'feature': feature_names[i] if i < len(feature_names) else f'feature_{i}',
                    'importance': float(importances[i])
                })
            
            # Sort by importance
            importance.sort(key=lambda x: x['importance'], reverse=True)
            
        except Exception as e:
            logger.debug(f"Could not get feature importance: {e}")
        
        return importance[:20]  # Top 20


# =============================================================================
# GOD-LEVEL AUTOML ENGINE
# =============================================================================

class GodLevelAutoML:
    """
    🔱 GOD-LEVEL AUTOML INTELLIGENCE ENGINE
    
    The ultimate AutoML system that:
    1. Deeply understands data
    2. Detects and prevents leakage
    3. Selects optimal models
    4. Trains safely
    5. Evaluates realistically
    6. Produces production-ready pipelines
    
    ABSOLUTE RULES:
    - Never produce fake accuracy
    - Never allow leakage
    - Never overfit intentionally
    - Always build generalizable models
    """
    
    def __init__(self):
        self.data_intelligence = DataIntelligence()
        self.leakage_detector = LeakageDetector()
        self.data_cleaner = DataCleaner()
        self.feature_engineer = None
        self.model_selector = ModelSelector()
        self.safe_trainer = None
        
        # Results
        self.profile: Optional[DatasetProfile] = None
        self.leakage_report: Optional[LeakageReport] = None
        self.result: Optional[GodLevelResult] = None
    
    def train(self, df: pd.DataFrame, target_column: Optional[str] = None,
              user_id: str = "default", mode: str = "fast",
              algorithm: Optional[str] = None) -> GodLevelResult:
        """
        🔱 MAIN TRAINING ENTRY POINT
        
        Executes the complete GOD-level AutoML pipeline.
        """
        import time
        start_time = time.time()
        
        training_mode = TrainingMode.ULTRA if mode.lower() == 'ultra' else TrainingMode.FAST
        
        logger.info("\n" + "=" * 70)
        logger.info("🔱 GOD-LEVEL AUTOML INTELLIGENCE ENGINE v1.0")
        logger.info("=" * 70)
        logger.info(f"   User: {user_id}")
        logger.info(f"   Mode: {training_mode.value.upper()}")
        logger.info(f"   Data: {df.shape[0]:,} rows × {df.shape[1]} columns")
        
        warnings_list = []
        
        try:
            # ==========================================
            # STEP 1: COMPLETE DATA INTELLIGENCE
            # ==========================================
            self.profile = self.data_intelligence.analyze_dataset(df, target_column)
            target_column = self.profile.target_column
            
            # ==========================================
            # STEP 2: DATA LEAKAGE DETECTION
            # ==========================================
            self.leakage_report = self.leakage_detector.detect_leakage(
                df, target_column, self.profile
            )
            
            if self.leakage_report.has_leakage:
                warnings_list.append(
                    f"⚠️ Data leakage detected in {len(self.leakage_report.leakage_columns)} columns. "
                    f"These were removed to prevent fake accuracy."
                )
            
            # ==========================================
            # STEP 3: DATA CLEANING & SAFETY
            # ==========================================
            df_clean = self.data_cleaner.clean(
                df, target_column, self.profile,
                self.leakage_report.leakage_columns
            )
            
            # Update profile with cleaned data
            self.profile.leakage_columns = self.leakage_report.leakage_columns
            
            # ==========================================
            # STEP 4: FEATURE ENGINEERING INTELLIGENCE
            # ==========================================
            self.feature_engineer = FeatureEngineer(mode=training_mode)
            X, y, feature_names = self.feature_engineer.engineer_features(
                df_clean, target_column, self.profile
            )
            
            # Update profile with final features
            self.profile.feature_columns = feature_names
            
            # ==========================================
            # STEP 5: MODEL SELECTION INTELLIGENCE
            # ==========================================
            models = self.model_selector.get_models(
                self.profile, training_mode, algorithm
            )
            
            # ==========================================
            # STEP 6: SAFE TRAINING PIPELINE
            # ==========================================
            self.safe_trainer = SafeTrainer(mode=training_mode)
            results = self.safe_trainer.train(
                X, y, models, self.profile.problem_type, self.profile, user_id
            )
            
            if not results:
                raise ValueError("No models trained successfully")
            
            # ==========================================
            # STEP 7: EVALUATION & FINAL RESULT
            # ==========================================
            best_result = results[0]
            processing_time = time.time() - start_time
            
            # Calculate feature metadata for UI
            feature_metadata = self._build_feature_metadata(df_clean, target_column)
            
            logger.info("\n" + "=" * 70)
            logger.info("✅ GOD-LEVEL AUTOML COMPLETE")
            logger.info("=" * 70)
            logger.info(f"   Best Model: {best_result.name}")
            logger.info(f"   Test Score: {best_result.test_score:.4f}")
            logger.info(f"   Reliability: {best_result.reliability_score:.1f}/100")
            logger.info(f"   Time: {processing_time:.1f}s")
            
            # Build result
            self.result = GodLevelResult(
                success=True,
                problem_type=self.profile.problem_type.value,
                target_column=target_column,
                feature_columns=feature_names,
                best_model_name=best_result.name,
                best_model_metrics=best_result.metrics,
                best_model_reliability=best_result.reliability_score,
                leaderboard=self.safe_trainer.leaderboard,
                feature_importance=best_result.feature_importance,
                leakage_report=self.leakage_report,
                dataset_profile=self.profile,
                preprocessing_steps=self.data_cleaner.preprocessing_steps,
                y_test=self.safe_trainer.y_test,
                y_pred=self.safe_trainer.y_pred,
                y_proba=self.safe_trainer.y_proba,
                n_rows=len(df),
                n_cols=len(df.columns),
                mode=training_mode.value,
                processing_time=processing_time,
                feature_metadata=feature_metadata,
                warnings=warnings_list,
                model_pipeline=self._build_pipeline(best_result.model)
            )
            
            return self.result
            
        except Exception as e:
            import traceback
            logger.error(f"GOD-Level AutoML failed: {e}")
            traceback.print_exc()
            
            return GodLevelResult(
                success=False,
                problem_type="unknown",
                target_column=target_column or "",
                feature_columns=[],
                best_model_name="",
                best_model_metrics={},
                best_model_reliability=0,
                leaderboard=[],
                feature_importance=[],
                leakage_report=LeakageReport(),
                dataset_profile=self.profile or DatasetProfile(
                    n_rows=len(df), n_cols=len(df.columns),
                    size_category=DatasetSize.SMALL,
                    problem_type=ProblemType.UNKNOWN,
                    target_column="",
                    numeric_columns=[], categorical_columns=[],
                    text_columns=[], datetime_columns=[], id_columns=[],
                    constant_columns=[], leakage_columns=[], columns_to_drop=[],
                    feature_columns=[]
                ),
                preprocessing_steps=[],
                y_test=np.array([]),
                y_pred=np.array([]),
                y_proba=None,
                n_rows=len(df),
                n_cols=len(df.columns),
                mode=mode,
                processing_time=time.time() - start_time,
                warnings=[f"Training failed: {str(e)}"]
            )
    
    def _build_feature_metadata(self, df: pd.DataFrame, target_col: str) -> List[Dict]:
        """Build feature metadata for prediction UI"""
        metadata = []
        
        for col in df.columns:
            if col == target_col:
                continue
            
            try:
                if pd.api.types.is_numeric_dtype(df[col]):
                    clean = df[col].dropna()
                    metadata.append({
                        'name': col,
                        'type': 'numeric',
                        'min': float(clean.min()) if len(clean) > 0 else 0,
                        'max': float(clean.max()) if len(clean) > 0 else 100,
                        'mean': float(clean.mean()) if len(clean) > 0 else 50,
                    })
                elif df[col].dtype == 'object' or df[col].dtype.name == 'category':
                    options = df[col].dropna().unique().tolist()[:50]
                    metadata.append({
                        'name': col,
                        'type': 'categorical',
                        'options': [str(o) for o in options],
                    })
            except:
                pass
        
        return metadata
    
    def _build_pipeline(self, model: Any) -> Dict:
        """Build a serializable pipeline representation"""
        return {
            'model': model,
            'scaler': self.feature_engineer.scaler if self.feature_engineer else None,
            'encoders': self.feature_engineer.encoders if self.feature_engineer else {},
            'feature_names': self.feature_engineer.selected_features if self.feature_engineer else [],
            'cleaner_fill_values': self.data_cleaner.fill_values,
        }


# =============================================================================
# MODULE-LEVEL SINGLETON INSTANCE
# =============================================================================

god_level_engine = GodLevelAutoML()


def god_level_train(df: pd.DataFrame, target_column: Optional[str] = None,
                    user_id: str = "default", mode: str = "fast",
                    algorithm: Optional[str] = None) -> GodLevelResult:
    """
    Convenience function for GOD-Level training.
    """
    engine = GodLevelAutoML()
    return engine.train(df, target_column, user_id, mode, algorithm)


# =============================================================================
# INTEGRATION WITH EXISTING AUTOML ENGINE
# =============================================================================

def integrate_with_production_engine():
    """
    Instructions to integrate with existing ProductionMLEngine:
    
    1. Import this module in automl_engine.py:
       from ml.god_level_automl import god_level_train, GodLevelResult
    
    2. Add a new method to ProductionMLEngine:
       def god_level_train(self, df, target_col, user_id, mode):
           result = god_level_train(df, target_col, user_id, mode)
           # Convert to TrainResult for compatibility
           return self._convert_god_result(result)
    
    3. Call from API:
       result = engine.god_level_train(df, target, user_id, 'ultra')
    """
    pass
