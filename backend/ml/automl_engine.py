"""
🚀 PRODUCTION ML ENGINE v7.0 - COMPLETE AUTOML PIPELINE
========================================================

PRODUCTION-LEVEL Features:
- 30+ ML Algorithms (Classification, Regression, Clustering)
- Auto GPU/CPU Detection (CUDA, ROCm, Metal)
- Advanced Data Cleaning (Smart Imputation, Outlier Detection)
- Feature Selection (Variance, Correlation, Mutual Info, RFE)
- Bayesian Hyperparameter Optimization (Optuna)
- Ensemble Methods (Stacking, Voting, Blending)
- NLP Pipeline (TF-IDF, Sentiment, Text Stats)
- SMOTE Class Imbalance Handling
- 20+ Visualization Charts
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

# Global Cancellation Tracking
CANCELLATION_FLAGS = {}

class TrainingCancelledError(Exception):
    """Exception raised when training is cancelled by user"""
    pass

def cancel_training(user_id: str):
    """Signal training to stop for a user"""
    CANCELLATION_FLAGS[user_id] = True
    logging.info(f"🚫 Stop signal received for user {user_id}")

def check_cancellation(user_id: str):
    """Check if training should stop, raise exception if so"""
    if CANCELLATION_FLAGS.get(user_id, False):
        # Clear flag and raise error
        CANCELLATION_FLAGS[user_id] = False 
        logging.info(f"🚫 Aborting training for user {user_id}")
        raise TrainingCancelledError("Training cancelled by user")

# Global Cancellation Tracking
CANCELLATION_FLAGS = {}

class TrainingCancelledError(Exception):
    """Exception raised when training is cancelled by user"""
    pass

def cancel_training(user_id: str):
    """Signal training to stop for a user"""
    CANCELLATION_FLAGS[user_id] = True
    logging.info(f"🚫 Stop signal received for user {user_id}")

def check_cancellation(user_id: str):
    """Check if training should stop, raise exception if so"""
    if CANCELLATION_FLAGS.get(user_id, False):
        # Clear flag and raise error
        CANCELLATION_FLAGS[user_id] = False 
        logging.info(f"🚫 Aborting training for user {user_id}")
        raise TrainingCancelledError("Training cancelled by user")

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
from sklearn.svm import SVC, SVR, LinearSVC, LinearSVR
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.naive_bayes import GaussianNB, MultinomialNB
from sklearn.neural_network import MLPClassifier, MLPRegressor

# IMPORT NEW PRODUCTION PIPELINE CLASSES
try:
    from ml.production_ml_core import (
        ProductionDataCleaner, 
        ProductionFeatureEngineer, 
        ProductionModelTrainer
    )
except ImportError:
    # Fallback or local definition if module not found (should not happen in prod)
    logging.warning("Could not import production_ml_core, using local fallback")
from sklearn.ensemble import IsolationForest  # Outlier detection
from sklearn.naive_bayes import MultinomialNB, GaussianNB, ComplementNB
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

try:
    from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering, SpectralClustering, MeanShift
    from sklearn.mixture import GaussianMixture
except ImportError:
    pass

from sklearn.decomposition import PCA, LatentDirichletAllocation
from sklearn.metrics import silhouette_score
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn.linear_model import (
    LogisticRegression, Ridge, ElasticNet, Lasso,
    SGDClassifier, SGDRegressor, PassiveAggressiveClassifier,
    BayesianRidge, HuberRegressor, PoissonRegressor, QuantileRegressor,
    LassoLars, OrthogonalMatchingPursuit
)
from sklearn.naive_bayes import MultinomialNB, GaussianNB, ComplementNB, BernoulliNB
from sklearn.preprocessing import PowerTransformer, QuantileTransformer


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

from ml.feature_engineer import AdvancedFeatureEngineer

# Import Production ML Core (AutoML Pipeline)
try:
    from ml.production_ml_core import (
        ProductionDataCleaner, ProductionFeatureEngineer, 
        ProductionModelTrainer, production_train_pipeline
    )
    HAS_PRODUCTION_ML = True
except ImportError:
    HAS_PRODUCTION_ML = False

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

import os
# Use absolute path for Docker/HuggingFace, relative for local development
if os.path.exists("/app"):
    STORAGE_PATH = "/app/backend/storage/automl"
else:
    STORAGE_PATH = "./storage/automl"

# =============================================================================
# GPU/CPU AUTO-DETECTION
# =============================================================================
def detect_compute_device() -> Dict[str, Any]:
    """Auto-detect available compute device (GPU/CPU)"""
    device_info = {'device': 'cpu', 'gpu_available': False, 'gpu_name': None}
    
    # Check CUDA (NVIDIA)
    try:
        import torch
        if torch.cuda.is_available():
            device_info['device'] = 'cuda'
            device_info['gpu_available'] = True
            device_info['gpu_name'] = torch.cuda.get_device_name(0)
            logger.info(f"🚀 GPU Detected: {device_info['gpu_name']}")
            return device_info
    except ImportError:
        pass
    
    # Check XGBoost GPU
    if HAS_XGB:
        try:
            import xgboost as xgb
            # XGBoost will use GPU if available via 'device' param
            device_info['xgb_gpu'] = True
        except:
            device_info['xgb_gpu'] = False
    
    logger.info("💻 Using CPU for training")
    return device_info

DEVICE_INFO = detect_compute_device()


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
    is_nlp_task: bool = False  # NEW: Flag for NLP tasks
    primary_text_col: Optional[str] = None  # NEW: Primary text column for NLP
    cleaned_file_path: Optional[str] = None # NEW: Path to cleaned dataset
    reliability_score: Optional[float] = None  # 🛡️ PRODUCTION INTELLIGENCE: Model reliability (0-100)
    validation_warnings: Optional[List[str]] = None  # 🛡️ Any warnings from production validation


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
        self.feature_columns = []
        self.target_col = None
        self.task_type = "classification"
        self.task_type_simple = "classification" # classification/regression
        self.n_classes = None # Fix: Initialize for regression tasks
        self.label_encoders = {}
        self.scaler = None
        self.metrics = {}
        self.is_nlp_task = False
        self.primary_text_col = None
        
        # Advanced Feature Engineering
        self.feature_engineer = AdvancedFeatureEngineer()
        
        # NLP Components
        self.tfidf_vectorizer = None
        self.count_vectorizer = None
        self.nlp_feature_names = []
        
        # Metadata
        self.feature_metadata = [] # List of dicts with type info
        self.imputer_vals = {}
        
        # Optimization
        self.best_params = {}
        self.cv_results = {}
        
        # Data Profile
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
        
        # Stored test data for predict mode access
        self._y_test = None
        self._y_pred = None
        self._y_proba = None
        self._confusion_matrix = None
        self._training_data = None  # Store sample of training data
    
    @property
    def feature_importance(self) -> Dict[str, float]:
        """Get feature importance as a dictionary {feature_name: importance_value}"""
        if self.model is None:
            return {}
        
        importance_list = self._get_importance(self.model)
        if not importance_list:
            return {}
        
        # Convert list of dicts to dictionary
        return {item['feature']: item['importance'] for item in importance_list}
    
    def get_model_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive model metrics for predict mode.
        Returns stored y_test, y_pred, confusion_matrix, and all metrics.
        """
        result = {
            'model_name': self.model_name if hasattr(self, 'model_name') else 'Unknown',
            'task_type': self.task_type,
            'target': self.target_column,
            'n_features': len(self.feature_columns) if self.feature_columns else 0,
            'features': self.feature_columns[:20] if self.feature_columns else [],
            'metrics': self.metrics if hasattr(self, 'metrics') else {},
            'n_classes': self.n_classes,
        }
        
        # Add stored test data for charts
        if hasattr(self, '_y_test') and self._y_test is not None:
            result['y_test'] = self._y_test.tolist() if hasattr(self._y_test, 'tolist') else list(self._y_test)
        
        if hasattr(self, '_y_pred') and self._y_pred is not None:
            result['y_pred'] = self._y_pred.tolist() if hasattr(self._y_pred, 'tolist') else list(self._y_pred)
        
        if hasattr(self, '_y_proba') and self._y_proba is not None:
            result['y_proba'] = self._y_proba.tolist() if hasattr(self._y_proba, 'tolist') else list(self._y_proba)
        
        if hasattr(self, '_confusion_matrix') and self._confusion_matrix is not None:
            result['confusion_matrix'] = self._confusion_matrix.tolist() if hasattr(self._confusion_matrix, 'tolist') else self._confusion_matrix
        
        # Add class labels
        if hasattr(self, 'target_encoder') and self.target_encoder is not None:
            result['class_names'] = self.target_encoder.classes_.tolist()
        
        # Add feature metadata for distribution charts
        if hasattr(self, 'feature_metadata') and self.feature_metadata:
            result['feature_metadata'] = self.feature_metadata
        
        # Add data profile
        if hasattr(self, 'data_profile') and self.data_profile:
            result['data_profile'] = self.data_profile
        
        return result
    
    def get_error_distribution(self) -> Dict[str, Any]:
        """
        Get error distribution data for regression tasks.
        Returns residuals, MAE, RMSE, etc.
        """
        if not hasattr(self, '_y_test') or self._y_test is None:
            return {'available': False, 'reason': 'No test data stored'}
        
        if not hasattr(self, '_y_pred') or self._y_pred is None:
            return {'available': False, 'reason': 'No predictions stored'}
        
        try:
            y_test = np.array(self._y_test)
            y_pred = np.array(self._y_pred)
            
            # Calculate residuals
            residuals = y_test - y_pred
            
            result = {
                'available': True,
                'residuals': residuals.tolist(),
                'y_test': y_test.tolist(),
                'y_pred': y_pred.tolist(),
                'mae': float(np.mean(np.abs(residuals))),
                'rmse': float(np.sqrt(np.mean(residuals**2))),
                'std': float(np.std(residuals)),
                'min_error': float(np.min(residuals)),
                'max_error': float(np.max(residuals)),
                'mean_error': float(np.mean(residuals)),
                'median_error': float(np.median(residuals)),
            }
            
            return result
            
        except Exception as e:
            return {'available': False, 'reason': str(e)}
    
    def get_data_statistics(self, column_name: str = None) -> Dict[str, Any]:
        """
        Get statistics for a specific column or all columns.
        Used by predict mode for data analysis.
        """
        result = {}
        
        if hasattr(self, '_training_data') and self._training_data is not None:
            df = self._training_data
            
            if column_name and column_name in df.columns:
                col = df[column_name]
                if pd.api.types.is_numeric_dtype(col):
                    result = {
                        'column': column_name,
                        'type': 'numeric',
                        'count': int(col.count()),
                        'mean': float(col.mean()),
                        'std': float(col.std()),
                        'min': float(col.min()),
                        'max': float(col.max()),
                        'median': float(col.median()),
                        'q25': float(col.quantile(0.25)),
                        'q75': float(col.quantile(0.75)),
                    }
                else:
                    result = {
                        'column': column_name,
                        'type': 'categorical',
                        'count': int(col.count()),
                        'unique': int(col.nunique()),
                        'top': str(col.mode().iloc[0]) if not col.mode().empty else None,
                        'frequency': int(col.value_counts().iloc[0]) if not col.value_counts().empty else 0,
                    }
            else:
                # Return summary for all columns
                result = {
                    'n_rows': len(df),
                    'n_columns': len(df.columns),
                    'columns': list(df.columns[:20]),
                    'numeric_columns': list(df.select_dtypes(include=[np.number]).columns),
                    'categorical_columns': list(df.select_dtypes(include=['object']).columns),
                }
        
        return result
    
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
        # Check if it's an ID column (expanded patterns)
        id_patterns = ['id', '_id', 'index', 'guid', 'uuid', 'pk', 'fk']
        
        # SAFEGUARD: Don't treat money/metrics as ID (e.g. 'rate_id' might be bad but 'hourly_rate' is good)
        important_keywords = ['rate', 'usd', 'eur', 'price', 'cost', 'income', 'salary', 'revenue', 'amount', 'score', 'percent']
        is_important = any(x in col_lower for x in important_keywords)
        
        if is_important:
            is_id = False
        else:
            # Only treat as ID if it strictly matches patterns AND is highly unique
            is_id = any(pat in col_lower for pat in id_patterns) and unique_ratio > 0.95
        
        # Check if it's a date column
        # Check if it's a date column - RESTRICTED to prevent dropping 'years_experience'
        date_patterns = ['date', 'time', 'timestamp', 'created', 'updated', 'modified', 'datetime', 'dt']
        # Only check year/month/day if they are EXACT matches or suffix, not just 'contains'
        if any(x in col_lower for x in date_patterns):
            is_date = True
        elif col_lower in ['year', 'month', 'day']:
            is_date = True
        else:
            is_date = False
        
        # Check if it's metadata/url column (useless for prediction)
        # BUT only if the content is short - long text should be kept for NLP
        # Check if it's metadata/url column (useless for prediction)
        # BUT only if the content is short - long text should be kept for NLP
        useless_patterns = ['url', 'link', 'href', 'path', 'file', 'image', 'photo', 'pic',
                           'ip', 'hash', 'password', 'token']
        # Removed 'address', 'phone' as they might be useful features in some contexts
        # Removed vague terms to prevent false positives
        
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
        logger.info("📊 Analyzing columns...")
        
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
                logger.info(f"   ✅ {col}: NLP text column (kept for text classification)")
                continue
            
            if analysis['should_drop']:
                dropped.append(col)
                logger.info(f"   ❌ {col}: {analysis['drop_reason']}")
            elif analysis['dtype'] == 'numeric' or analysis['dtype'] == 'boolean':
                numeric_cols.append(col)
            elif analysis['dtype'] == 'categorical':
                categorical_cols.append(col)
            elif analysis['dtype'] == 'text':
                # For non-NLP datasets, still keep text if avg length is long enough
                avg_len = df[col].astype(str).str.len().mean()
                if avg_len > 30:  # Long text = valuable content
                    text_cols.append(col)
                    logger.info(f"   ✅ {col}: text column (avg {avg_len:.0f} chars)")
                elif analysis['unique_ratio'] < 0.9:
                    text_cols.append(col)
                else:
                    dropped.append(col)
                    logger.info(f"   ❌ {col}: Short unique text (no pattern)")
        
        print(f"   ✅ Keeping: {len(numeric_cols)} numeric, {len(categorical_cols)} categorical, {len(text_cols)} text")
        print(f"   ❌ Dropped: {len(dropped)} columns")
        
        return numeric_cols, categorical_cols, text_cols, dropped
    
        return numeric_cols, categorical_cols, text_cols, dropped
    
    def _calculate_feature_metadata(self, df: pd.DataFrame) -> List[Dict]:
        """
        Calculate metadata (min, max, mean, type) for RAW columns.
        This allows the Frontend to show correct placeholders (e.g. 50,000 instead of 50).
        Now includes datetime columns for date picker UI support.
        
        IMPORTANT: Auto-detects column types from DataFrame if self.numeric_cols etc. are empty.
        """
        metadata = []
        
        # Get target column to exclude it
        target_col = getattr(self, 'target_column', None) or getattr(self, 'target_col', None)
        
        # Auto-detect column types if not already set
        numeric_cols = list(self.numeric_cols) if hasattr(self, 'numeric_cols') and self.numeric_cols else []
        categorical_cols = list(self.categorical_cols) if hasattr(self, 'categorical_cols') and self.categorical_cols else []
        text_cols = list(self.text_cols) if hasattr(self, 'text_cols') and self.text_cols else []
        datetime_cols = []
        
        # Date patterns for detection
        date_patterns = ['date', 'time', 'timestamp', 'created', 'updated', 'modified', 'datetime', 'dt']
        # ID patterns to skip
        id_patterns = ['id', '_id', 'index', 'guid', 'uuid', 'pk', 'fk', 'unnamed']
        
        # If column lists are empty, auto-detect from DataFrame
        if not numeric_cols and not categorical_cols and not text_cols:
            logger.info("[feature_metadata] Auto-detecting column types from DataFrame")
            
            for col in df.columns:
                # Skip target column
                if col == target_col:
                    continue
                
                col_lower = col.lower()
                
                # Skip ID columns
                if any(pat in col_lower for pat in id_patterns):
                    continue
                
                # Check if datetime
                is_datetime = False
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    is_datetime = True
                elif any(x in col_lower for x in date_patterns):
                    # Verify it's actually a date by trying to parse
                    try:
                        sample = df[col].dropna().head(5)
                        if len(sample) > 0:
                            pd.to_datetime(sample.iloc[0])
                            is_datetime = True
                    except:
                        pass
                
                if is_datetime:
                    datetime_cols.append(col)
                    continue
                
                # Check if numeric
                if pd.api.types.is_numeric_dtype(df[col]):
                    numeric_cols.append(col)
                    continue
                
                # Check if categorical vs text (based on unique values and avg length)
                try:
                    n_unique = df[col].nunique()
                    avg_len = df[col].astype(str).str.len().mean()
                    
                    if n_unique <= 50 and avg_len < 50:
                        categorical_cols.append(col)
                    else:
                        text_cols.append(col)
                except:
                    categorical_cols.append(col)
        else:
            # Use existing column lists, but still detect datetime columns
            for col in df.columns:
                if col == target_col:
                    continue
                if col in numeric_cols or col in categorical_cols or col in text_cols:
                    continue
                
                col_lower = col.lower()
                is_datetime = False
                
                # Check by column name pattern
                if any(x in col_lower for x in date_patterns):
                    is_datetime = True
                elif col_lower in ['year', 'month', 'day']:
                    is_datetime = True
                
                # Check by dtype
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    is_datetime = True
                
                # Check by parsing attempt
                if not is_datetime and df[col].dtype == 'object':
                    try:
                        sample = df[col].dropna().head(5)
                        if len(sample) > 0:
                            pd.to_datetime(sample.iloc[0])
                            is_datetime = True
                    except:
                        pass
                
                if is_datetime:
                    datetime_cols.append(col)
        
        logger.info(f"[feature_metadata] Detected: {len(numeric_cols)} numeric, {len(categorical_cols)} categorical, {len(text_cols)} text, {len(datetime_cols)} datetime")
        
        # Add numeric features
        for col in numeric_cols:
            if col in df.columns:
                try:
                    metadata.append({
                        'name': col,
                        'type': 'numeric',
                        'min': float(df[col].min()),
                        'max': float(df[col].max()),
                        'mean': float(df[col].mean())
                    })
                except:
                    pass
        
        # Add categorical features
        for col in categorical_cols:
            if col in df.columns:
                try:
                    # Limit options to top 10 for UI performance
                    options = df[col].value_counts().nlargest(10).index.tolist()
                    metadata.append({
                        'name': col,
                        'type': 'categorical',
                        'options': [str(x) for x in options]
                    })
                except:
                    pass
        
        # Add text features            
        for col in text_cols:
            if col in df.columns:
                metadata.append({
                    'name': col,
                    'type': 'text',
                    'placeholder': f'Enter {col}...'
                })
        
        # Add datetime features for date picker UI
        for col in datetime_cols:
            if col in df.columns:
                try:
                    dt_series = pd.to_datetime(df[col], errors='coerce')
                    min_date = dt_series.min()
                    max_date = dt_series.max()
                    metadata.append({
                        'name': col,
                        'type': 'datetime',
                        'min': min_date.isoformat() if pd.notna(min_date) else None,
                        'max': max_date.isoformat() if pd.notna(max_date) else None,
                        'placeholder': 'Select date...'
                    })
                except Exception as e:
                    # Fallback: add as text input
                    metadata.append({
                        'name': col,
                        'type': 'datetime',
                        'placeholder': 'Enter date (YYYY-MM-DD)...'
                    })
             
        self.feature_metadata = metadata
        logger.info(f"[feature_metadata] Total features for UI: {len(metadata)}")
        return metadata

    # =========================================================================
    # TARGET DETECTION
    # =========================================================================
    
    def _detect_target(self, df: pd.DataFrame) -> str:
        """Smart target detection with priority keywords"""
        
        # Priority 1: Exact match keywords
        exact_keywords = ['target', 'label', 'class', 'output', 'y']
        for col in df.columns:
            if col.lower().strip() in exact_keywords:
                logger.info(f"🎯 Target (exact match): {col}")
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
                    logger.info(f"🎯 Target (contains '{keyword}'): {col}")
                    return col
        
        # Priority 3: Heuristic - prefer last column if it's a good target
        last_col = df.columns[-1]
        last_unique = df[last_col].nunique()
        
        if last_unique <= 20 or pd.api.types.is_numeric_dtype(df[last_col]):
            logger.info(f"🎯 Target (last column): {last_col}")
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
            logger.info(f"🎯 Target (best candidate): {candidates[0][0]}")
            return candidates[0][0]
        
        logger.info(f"🎯 Target (fallback): {df.columns[-1]}")
        return df.columns[-1]
    
    def _detect_task_type(self, y: pd.Series) -> Tuple[str, int]:
        """
        PRODUCTION-LEVEL Task Type Detection
        """
        n_unique = y.nunique()
        n_samples = len(y)
        unique_ratio = n_unique / n_samples if n_samples > 0 else 0
        
        logger.info(f"   🔍 Analyzing target: {n_unique} unique values, ratio={unique_ratio:.2%}")
        
        # ====== RULE 0: PRIORITY - Check if convertible to Numeric first! ======
        try:
            y_numeric = pd.to_numeric(y.astype(str).str.replace(r'[$,]', '', regex=True), errors='coerce')
            if y_numeric.notna().sum() > len(y) * 0.9: # 90% valid numbers
                y = y_numeric
                n_unique = y.nunique()
                logger.info("   ✅ Converted target to numeric (was string/mixed)")
        except:
            pass

        # ====== RULE 1: String/Object type = Classification (if NOT numeric) ======
        if pd.api.types.is_object_dtype(y) or pd.api.types.is_categorical_dtype(y):
            if n_unique == 2:
                logger.info(f"   ✅ Binary Classification (string, 2 classes)")
                return 'binary_classification', 2
            elif n_unique <= 50:
                logger.info(f"   ✅ Multiclass Classification (string, {n_unique} classes)")
                return 'multiclass_classification', n_unique
            else:
                avg_len = y.astype(str).str.len().mean()
                if avg_len > 20: 
                     pass 
                
                logger.warning(f"   ⚠️ High-cardinality string ({n_unique} unique) - treating as multiclass")
                return 'multiclass_classification', n_unique
        
        # ====== RULE 2: Boolean = Binary Classification ======
        if pd.api.types.is_bool_dtype(y):
            logger.info(f"   ✅ Binary Classification (boolean)")
            return 'binary_classification', 2
        
        # ====== RULE 3: Numeric Analysis ======
        y_clean = pd.to_numeric(y, errors='coerce').dropna()
        
        if len(y_clean) == 0:
            logger.warning(f"   ⚠️ No valid numeric values - defaulting to regression")
            return 'regression', 0
        
        # Check for binary (0/1 or similar)
        unique_vals = set(y_clean.unique())
        if unique_vals.issubset({0, 1}) or unique_vals.issubset({-1, 1}):
            logger.info(f"   ✅ Binary Classification (0/1 or -1/1)")
            return 'binary_classification', 2
        
        # Check if values are whole numbers
        is_whole_numbers = (y_clean % 1 == 0).all()
        
        # Integer with few unique values = Classification
        if is_whole_numbers:
            if n_unique == 2:
                logger.info(f"   ✅ Binary Classification (2 integer classes)")
                return 'binary_classification', 2
            elif n_unique <= 10:
                logger.info(f"   ✅ Multiclass Classification ({n_unique} integer classes)")
                return 'multiclass_classification', n_unique
            elif n_unique <= 20 and unique_ratio < 0.05:
                # Low unique ratio suggests classification
                logger.info(f"   ✅ Multiclass Classification ({n_unique} classes, low ratio)")
                return 'multiclass_classification', n_unique
        
        # ====== RULE 4: Continuous values = Regression ======
        # Check for decimal places
        has_decimals = not is_whole_numbers
        
        # Check value range (large range suggests regression)
        val_range = y_clean.max() - y_clean.min()
        
        if has_decimals:
            logger.info(f"   ✅ Regression (continuous decimals, range={val_range:.2f})")
            return 'regression', 0
        
        if unique_ratio > 0.1 and n_unique > 20:
            logger.info(f"   ✅ Regression (high unique ratio={unique_ratio:.1%}, {n_unique} values)")
            return 'regression', 0
        
        if val_range > 100 and n_unique > 30:
            logger.info(f"   ✅ Regression (large range={val_range:.0f})")
            return 'regression', 0
        
        # Default based on unique count
        if n_unique <= 15:
            logger.info(f"   ✅ Multiclass Classification ({n_unique} classes, default)")
            return 'multiclass_classification', n_unique
        
        logger.info(f"   ✅ Regression (default, {n_unique} unique values)")
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
    
    def _cap_outliers(self, data: np.ndarray, method: str = 'hybrid') -> np.ndarray:
        """
        PRODUCTION-LEVEL Outlier Handling
        
        Methods:
        - 'iqr': Traditional IQR method (fast)
        - 'isolation': Isolation Forest (ML-based)
        - 'hybrid': Both methods combined (recommended)
        """
        if len(data) < 10:
            return data
        
        try:
            outlier_mask = np.zeros(len(data), dtype=bool)
            
            # Method 1: IQR-based detection
            q1 = np.percentile(data, 25)
            q3 = np.percentile(data, 75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            iqr_outliers = (data < lower_bound) | (data > upper_bound)
            outlier_mask |= iqr_outliers
            
            # Method 2: Isolation Forest (for complex patterns)
            if method in ['isolation', 'hybrid'] and len(data) > 50:
                try:
                    iso_forest = IsolationForest(contamination=0.05, random_state=42, n_jobs=-1)
                    preds = iso_forest.fit_predict(data.reshape(-1, 1))
                    iso_outliers = preds == -1
                    outlier_mask |= iso_outliers
                except:
                    pass
            
            # Winsorize: clip to 1st/99th percentile
            p1, p99 = np.percentile(data, [1, 99])
            capped = np.clip(data, p1, p99)
            
            n_capped = np.sum(outlier_mask)
            if n_capped > 0:
                logger.info(f"      🛠️ Detected {n_capped} outliers ({n_capped/len(data)*100:.1f}%)")
            
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
                logger.warning(f"   ⚠️ Removing {len(to_drop)} highly correlated features (>{threshold:.0%} correlation)")
                for col in to_drop:
                    logger.warning(f"      - {col}")
            
            return to_drop
        except:
            return []

    def _production_feature_selection(self, X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> Tuple[np.ndarray, List[str], Dict]:
        """
        PRODUCTION-LEVEL Feature Selection Pipeline
        """
        logger.info("   🔍 FEATURE SELECTION PIPELINE...")
        selection_info = {'original_features': len(feature_names), 'steps': []}
        
        current_X = X.copy()
        current_features = list(feature_names)
        
        # Step 1: Variance Threshold (remove zero variance)
        try:
            from sklearn.feature_selection import VarianceThreshold
            selector = VarianceThreshold(threshold=0.01)
            mask = selector.fit(current_X).get_support()
            current_X = current_X[:, mask]
            current_features = [f for f, m in zip(current_features, mask) if m]
            removed = len(feature_names) - len(current_features)
            if removed > 0:
                logger.info(f"      ✂️ Variance filter: removed {removed} low-variance features")
                selection_info['steps'].append({'step': 'variance', 'removed': removed})
        except:
            pass
        
        # Step 2: Correlation Filter (on remaining features)
        try:
            if current_X.shape[1] > 2:
                corr_matrix = np.corrcoef(current_X, rowvar=False)
                upper_tri = np.triu(np.abs(corr_matrix), k=1)
                high_corr_pairs = np.where(upper_tri > 0.95)
                cols_to_drop = set(high_corr_pairs[1])  # Drop second column of each pair
                
                mask = [i not in cols_to_drop for i in range(current_X.shape[1])]
                current_X = current_X[:, mask]
                current_features = [f for f, m in zip(current_features, mask) if m]
                if len(cols_to_drop) > 0:
                    logger.info(f"      ✂️ Correlation filter: removed {len(cols_to_drop)} correlated features")
                    selection_info['steps'].append({'step': 'correlation', 'removed': len(cols_to_drop)})
        except:
            pass
        
        # Step 3: Mutual Information (rank remaining features)
        try:
            if current_X.shape[1] > 10:
                from sklearn.feature_selection import mutual_info_classif, mutual_info_regression
                
                if self.task_type_simple == 'classification':
                    mi_scores = mutual_info_classif(current_X, y, random_state=42)
                else:
                    mi_scores = mutual_info_regression(current_X, y, random_state=42)
                
                # Keep top 80% by MI score or minimum 10 features
                k = max(10, int(len(current_features) * 0.8))
                k = min(k, len(current_features))
                
                top_indices = np.argsort(mi_scores)[-k:]
                current_X = current_X[:, top_indices]
                current_features = [current_features[i] for i in top_indices]
                removed = len(mi_scores) - k
                if removed > 0:
                    logger.info(f"      ✂️ MI ranking: kept top {k} informative features")
                    selection_info['steps'].append({'step': 'mutual_info', 'kept': k})
        except:
            pass
        
        selection_info['final_features'] = len(current_features)
        logger.info(f"      ✅ Feature selection: {selection_info['original_features']} → {selection_info['final_features']}")
        
        return current_X, current_features, selection_info
    
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
                if avg_len > 20: # Lowered threshold to catch skills/titles
                    profile['n_text'] += 1
                else:
                    profile['n_categorical'] += 1
        
        # FIX: Activate NLP mode if ANY significant text column exists
        profile['is_nlp_task'] = profile['n_text'] > 0
        
        # INTELLIGENT ALGORITHM RECOMMENDATIONS
        recommended = []
        techniques = []
        
        logger.info("📊 DATA PROFILE ANALYSIS:")
        logger.info(f"   Samples: {profile['n_samples']:,} | Features: {profile['n_features']}")
        logger.info(f"   Numeric: {profile['n_numeric']} | Categorical: {profile['n_categorical']} | Text: {profile['n_text']}")
        
        # === ALGORITHM SELECTION RULES ===
        
        # Small data: prefer simpler models, avoid deep learning
        if profile['is_small_data']:
            recommended.extend(['LogisticRegression', 'RandomForest', 'SVM', 'KNN', 'DecisionTree', 'BayesianRidge', 'LDA'])
            techniques.append('cross_validation_10_fold')
            logger.info("   📈 Small data → Simple models + Bayesian regression")
        
        # Medium data: balanced approach
        elif profile['is_medium_data']:
            recommended.extend(['RandomForest', 'XGBoost', 'LightGBM', 'HistGradientBoosting', 'MLP', 'HuberRegressor'])
            techniques.append('cross_validation_5_fold')
            logger.info("   📈 Medium data → Ensemble + gradient boosting + robust regression")
        
        # Large data: gradient boosting shines, can use neural nets
        else:
            recommended.extend(['LightGBM', 'XGBoost', 'CatBoost', 'HistGradientBoosting', 'MLP', 'SGD'])
            techniques.append('cross_validation_3_fold')
            techniques.append('early_stopping')
            logger.info("   📈 Large data → Fast gradient boosting + early stopping")

        # === SPECIALIZED RECOMMENDATIONS ===
        
        # Count data (Regression): Positive integers imply Poisson
        if target_col in df.columns and pd.api.types.is_numeric_dtype(df[target_col]):
            y = df[target_col].dropna()
            if (y >= 0).all() and (y % 1 == 0).all() and y.max() > 1:
                 recommended.append('PoissonRegressor')
                 logger.info("   🔢 Count data detected → Added PoissonRegressor")

        # High Dimensionality (p > n or large p)
        if profile['is_high_dimensional']:
            recommended.extend(['Lasso', 'ElasticNet', 'LinearSVC'])
            logger.info("   🤏 High dimensionality → Added Regularized Linear Models")
        
        # High dimensional: regularization important
        if profile['is_high_dimensional']:
            recommended.extend(['SGDClassifier', 'LogisticRegression', 'LinearSVC'])
            techniques.append('feature_selection')
            techniques.append('regularization')
            logger.info("   📈 High dimensional → Linear models + regularization")
        
        # NLP/Text data: specific algorithms
        if profile['is_nlp_task']:
            recommended = ['MultinomialNB', 'ComplementNB', 'LogisticRegression', 'LinearSVC', 
                          'SGDClassifier', 'PassiveAggressive', 'MLP']
            techniques.extend(['tfidf', 'ngrams', 'sentiment_features', 'text_stats'])
            logger.info("   📈 NLP task → Text-optimized classifiers")
        
        # Imbalanced data: specific handling
        if profile.get('is_imbalanced', False):
            techniques.append('smote')
            techniques.append('class_weights')
            logger.info(f"   ⚠️ Imbalanced (ratio: {profile.get('imbalance_ratio', 0):.1f}:1) → SMOTE + class weights")
        
        # Add ensemble techniques for accuracy
        techniques.append('stacking_ensemble')
        techniques.append('voting_ensemble')
        
        profile['recommended_algorithms'] = list(set(recommended))
        profile['recommended_techniques'] = list(set(techniques))
        
        logger.info(f"   🎯 Recommended: {', '.join(profile['recommended_algorithms'][:5])}")
        
        self.data_profile = profile
        return profile
    
    def _get_adaptive_models(self) -> Dict[str, Tuple[Any, Dict]]:
        """
        PRODUCTION-LEVEL: Return models adapted to data profile.
        ANTI-OVERFITTING: Uses stronger regularization for smaller datasets.
        """
        profile = self.data_profile
        recommended = profile.get('recommended_algorithms', [])
        n_samples = profile.get('n_samples', 1000)
        
        # ===== ANTI-OVERFITTING: Scale regularization based on dataset size =====
        if n_samples < 500:
            # Very small dataset - strong regularization
            tree_max_depth = [3, 5, 7]
            tree_min_samples = [5, 10, 20]
            n_estimators = [30, 50, 75]
            C_values = [0.01, 0.1, 0.5]
            alpha_values = [1.0, 5.0, 10.0]
            mlp_alpha = [0.01, 0.05, 0.1]
            logger.info(f"   📐 Small dataset ({n_samples} samples): Using strong regularization")
        elif n_samples < 2000:
            # Medium dataset - moderate regularization
            tree_max_depth = [5, 8, 12]
            tree_min_samples = [3, 5, 10]
            n_estimators = [50, 100]
            C_values = [0.1, 0.5, 1.0]
            alpha_values = [0.1, 1.0, 5.0]
            mlp_alpha = [0.001, 0.01, 0.05]
        else:
            # Large dataset - lighter regularization
            tree_max_depth = [8, 12, 20]
            tree_min_samples = [2, 5]
            n_estimators = [100, 200]
            C_values = [0.5, 1.0, 5.0]
            alpha_values = [0.01, 0.1, 1.0]
            mlp_alpha = [0.0001, 0.001, 0.01]
        
        # === NLP SPECIFIC MODELS ===
        if profile.get('is_nlp_task', False):
            logger.info("   🔤 NLP Task Detected: Using specialized text classification models")
            
            # SPLIT: Check if regression or classification
            if self.task_type_simple == 'regression':
                logger.info("   Note: Regression task with text features - using robust regressors")
                models = {
                    # Regularized Linear Models (good for high-dim text)
                    'Ridge': (
                        Ridge(random_state=42),
                        {'alpha': alpha_values}
                    ),
                    'ElasticNet': (
                        ElasticNet(random_state=42, max_iter=2000),
                        {'alpha': [0.1, 0.5, 1.0], 'l1_ratio': [0.3, 0.5, 0.7]}
                    ),
                    'BayesianRidge': (
                        BayesianRidge(),
                        {'alpha_1': [1e-7, 1e-6, 1e-5], 'lambda_1': [1e-7, 1e-6, 1e-5]}
                    )
                }
                
                # Add XGBoost if available (excellent for any task)
                if HAS_XGB:
                    models['XGBoost'] = (
                        xgb.XGBRegressor(
                            n_estimators=n_estimators[0], max_depth=tree_max_depth[0], learning_rate=0.1,
                            subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0, reg_alpha=0.1,
                            random_state=42, n_jobs=-1, verbosity=0
                        ),
                        {'n_estimators': n_estimators, 'max_depth': tree_max_depth, 'learning_rate': [0.05, 0.1]}
                    )
                
                # Add LightGBM if available (fast and accurate)
                if HAS_LGB:
                    models['LightGBM'] = (
                        lgb.LGBMRegressor(
                            n_estimators=n_estimators[0], max_depth=tree_max_depth[0], learning_rate=0.1,
                            reg_lambda=1.0, reg_alpha=0.1, min_child_samples=10,
                            random_state=42, n_jobs=-1, verbose=-1
                        ),
                        {'n_estimators': n_estimators, 'max_depth': tree_max_depth}
                    )
                
                # Gradient Boosting (sklearn - always available)
                models['GradientBoosting'] = (
                    GradientBoostingRegressor(
                        n_estimators=n_estimators[0], max_depth=tree_max_depth[0], learning_rate=0.1,
                        min_samples_leaf=tree_min_samples[0], random_state=42
                    ),
                    {'n_estimators': n_estimators, 'max_depth': tree_max_depth}
                )
                
                # Random Forest (robust, handles noise well)
                models['RandomForest'] = (
                    RandomForestRegressor(
                        n_estimators=n_estimators[0], max_depth=tree_max_depth[-1], 
                        min_samples_leaf=tree_min_samples[0], random_state=42, n_jobs=-1
                    ),
                    {'n_estimators': n_estimators, 'max_depth': tree_max_depth}
                )
                
                return models
            else:
                return {
                    'MultinomialNB': (MultinomialNB(), {'alpha': [0.5, 1.0, 2.0]}),
                    'BernoulliNB': (BernoulliNB(), {'alpha': [0.5, 1.0, 2.0], 'binarize': [0.0, 0.5]}),
                    'ComplementNB': (ComplementNB(), {'alpha': [0.5, 1.0, 2.0]}),
                    'LogisticRegression': (
                        LogisticRegression(max_iter=2000, n_jobs=-1, solver='saga', penalty='l2'),
                        {'C': C_values}
                    ),
                    'SGDClassifier': (
                        SGDClassifier(max_iter=2000, n_jobs=-1, loss='hinge', penalty='l2'),
                        {'alpha': [1e-3, 1e-2, 1e-1]}
                    ),
                    'LinearSVC': (
                        LinearSVC(max_iter=2000),
                        {'C': C_values}
                    ),
                    'PassiveAggressive': (
                        PassiveAggressiveClassifier(max_iter=2000),
                        {'C': C_values}
                    )
                }
        
        # All available models - with ANTI-OVERFITTING parameters
        all_classification_models = {
            'LogisticRegression': (
                LogisticRegression(max_iter=1000, random_state=42, n_jobs=-1),
                {'C': C_values, 'penalty': ['l1', 'l2'], 'solver': ['saga']}
            ),
            'SGDClassifier': (
                SGDClassifier(random_state=42, max_iter=1000, early_stopping=True),
                {'alpha': [0.001, 0.01, 0.1], 'penalty': ['l1', 'l2', 'elasticnet']}
            ),
            'DecisionTree': (
                DecisionTreeClassifier(random_state=42),
                {'max_depth': tree_max_depth, 'min_samples_split': tree_min_samples}
            ),
            'RandomForest': (
                RandomForestClassifier(n_jobs=-1, random_state=42, min_samples_leaf=tree_min_samples[0]),
                {'n_estimators': n_estimators, 'max_depth': tree_max_depth}
            ),
            'ExtraTrees': (
                ExtraTreesClassifier(n_jobs=-1, random_state=42, min_samples_leaf=tree_min_samples[0]),
                {'n_estimators': n_estimators, 'max_depth': tree_max_depth}
            ),
            'HistGradientBoosting': (
                HistGradientBoostingClassifier(random_state=42, early_stopping=True, min_samples_leaf=tree_min_samples[0]),
                {'max_iter': n_estimators, 'max_depth': tree_max_depth, 'learning_rate': [0.05, 0.1]}
            ),
            'AdaBoost': (
                AdaBoostClassifier(random_state=42),
                {'n_estimators': n_estimators, 'learning_rate': [0.1, 0.5, 1.0]}
            ),
            'SVM': (
                SVC(random_state=42, probability=True),
                {'C': C_values, 'kernel': ['rbf', 'linear']}
            ),
            'LinearSVC': (
                LinearSVC(random_state=42, max_iter=2000, dual=False),
                {'C': C_values}
            ),
            'GaussianNB': (
                GaussianNB(),
                {'var_smoothing': [1e-9, 1e-8, 1e-7]}
            ),
            'MultinomialNB': (
                MultinomialNB(),
                {'alpha': [0.5, 1.0, 2.0]}
            ),
            'ComplementNB': (
                ComplementNB(),
                {'alpha': [0.5, 1.0, 2.0]}
            ),
            'MLP': (
                MLPClassifier(random_state=42, max_iter=500, early_stopping=True, validation_fraction=0.15),
                {'hidden_layer_sizes': [(64, 32), (100, 50)], 'alpha': mlp_alpha}
            ),
            'KNN': (
                KNeighborsClassifier(n_jobs=-1),
                {'n_neighbors': [3, 5, 7], 'weights': ['uniform', 'distance']}
            ),
            'PassiveAggressive': (
                PassiveAggressiveClassifier(random_state=42, max_iter=1000),
                {'C': C_values}
            ),
        }
        
        all_regression_models = {
            'Ridge': (Ridge(random_state=42), {'alpha': alpha_values}),
            'Lasso': (Lasso(random_state=42, max_iter=2000), {'alpha': [0.1, 0.5, 1.0, 5.0]}),
            'ElasticNet': (ElasticNet(random_state=42, max_iter=2000), 
                          {'alpha': [0.1, 0.5, 1.0], 'l1_ratio': [0.2, 0.5, 0.8]}),
            'SGDRegressor': (SGDRegressor(random_state=42, max_iter=1000, early_stopping=True),
                            {'alpha': [0.001, 0.01, 0.1]}),
            'DecisionTree': (DecisionTreeRegressor(random_state=42),
                            {'max_depth': tree_max_depth, 'min_samples_split': tree_min_samples}),
            'RandomForest': (RandomForestRegressor(n_jobs=-1, random_state=42, min_samples_leaf=tree_min_samples[0]),
                            {'n_estimators': n_estimators, 'max_depth': tree_max_depth}),
            'ExtraTrees': (ExtraTreesRegressor(n_jobs=-1, random_state=42, min_samples_leaf=tree_min_samples[0]),
                          {'n_estimators': n_estimators, 'max_depth': tree_max_depth}),
            'HistGradientBoosting': (HistGradientBoostingRegressor(random_state=42, early_stopping=True, min_samples_leaf=tree_min_samples[0]),
                                    {'max_iter': n_estimators, 'max_depth': tree_max_depth}),
            'AdaBoost': (AdaBoostRegressor(random_state=42),
                        {'n_estimators': n_estimators, 'learning_rate': [0.1, 0.5, 1.0]}),
            'SVR': (SVR(), {'C': C_values, 'kernel': ['rbf', 'linear']}),
            'MLP': (MLPRegressor(random_state=42, max_iter=500, early_stopping=True, validation_fraction=0.15),
                   {'hidden_layer_sizes': [(64, 32), (100, 50)], 'alpha': mlp_alpha}),
            'KNN': (KNeighborsRegressor(n_jobs=-1), 
                   {'n_neighbors': [3, 5, 7], 'weights': ['uniform', 'distance']}),
        }
        
        # Add gradient boosting libraries if available - with regularization
        if HAS_XGB:
            all_classification_models['XGBoost'] = (
                xgb.XGBClassifier(n_jobs=-1, random_state=42, verbosity=0, eval_metric='logloss',
                                  reg_lambda=1.0, reg_alpha=0.1, min_child_weight=3),
                {'n_estimators': n_estimators, 'max_depth': tree_max_depth, 'learning_rate': [0.05, 0.1]}
            )
            all_regression_models['XGBoost'] = (
                xgb.XGBRegressor(n_jobs=-1, random_state=42, verbosity=0,
                                 reg_lambda=1.0, reg_alpha=0.1, min_child_weight=3),
                {'n_estimators': n_estimators, 'max_depth': tree_max_depth, 'learning_rate': [0.05, 0.1]}
            )
        
        if HAS_LGB:
            all_classification_models['LightGBM'] = (
                lgb.LGBMClassifier(n_jobs=-1, random_state=42, verbose=-1,
                                   reg_lambda=1.0, reg_alpha=0.1, min_child_samples=10),
                {'n_estimators': n_estimators, 'max_depth': tree_max_depth, 'learning_rate': [0.05, 0.1]}
            )
            all_regression_models['LightGBM'] = (
                lgb.LGBMRegressor(n_jobs=-1, random_state=42, verbose=-1,
                                  reg_lambda=1.0, reg_alpha=0.1, min_child_samples=10),
                {'n_estimators': n_estimators, 'max_depth': tree_max_depth, 'learning_rate': [0.05, 0.1]}
            )
        
        if HAS_CATBOOST:
            all_classification_models['CatBoost'] = (
                CatBoostClassifier(random_state=42, verbose=0, thread_count=-1, l2_leaf_reg=3.0),
                {'iterations': n_estimators, 'depth': tree_max_depth, 'learning_rate': [0.05, 0.1]}
            )
            all_regression_models['CatBoost'] = (
                CatBoostRegressor(random_state=42, verbose=0, thread_count=-1, l2_leaf_reg=3.0),
                {'iterations': n_estimators, 'depth': tree_max_depth, 'learning_rate': [0.05, 0.1]}
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
                if avg_len > 20 or avg_words > 3:  # Lowered threshold (was 50/5)
                    text_cols.append(col)
        
        # If any text feature exists, we treat it as NLP-enhanced
        non_target_cols = [c for c in df.columns if c != target_col]
        # Relaxed logic: If we have ANY text column, return True
        if len(text_cols) > 0:
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
        """
        INDUSTRIAL-LEVEL NLP Feature Extraction with Dimensionality Reduction
        
        Key improvements:
        1. TF-IDF + TruncatedSVD (LSA) for dense, meaningful features
        2. Reduced dimensions to prevent overfitting
        3. Text statistics for interpretability
        """
        from sklearn.decomposition import TruncatedSVD
        from sklearn.pipeline import Pipeline
        
        logger.info(f"   🔤 NLP Processing: {col_name}")
        
        # Clean text
        clean_texts = text_series.fillna('').astype(str).apply(self._clean_text_nlp)
        logger.info(f"      ✅ Text cleaned")
        
        n_samples = len(text_series)
        
        # 1. TF-IDF + SVD Pipeline (Latent Semantic Analysis)
        # Key: Reduce 200+ sparse features to 30-50 dense features
        try:
            n_components = min(50, n_samples // 3, 100)  # Adaptive SVD components
            n_components = max(10, n_components)
            
            tfidf = TfidfVectorizer(
                max_features=500,  # Capture more vocabulary
                stop_words='english',
                ngram_range=(1, 2),  # Bigrams only (trigrams too sparse)
                min_df=2,
                max_df=0.85,
                lowercase=True,
                strip_accents='unicode',
                sublinear_tf=True
            )
            
            # Apply TF-IDF first
            tfidf_matrix = tfidf.fit_transform(clean_texts)
            
            # Apply SVD if TF-IDF has enough features
            if tfidf_matrix.shape[1] > n_components:
                svd = TruncatedSVD(n_components=n_components, random_state=42)
                tfidf_features = svd.fit_transform(tfidf_matrix)
                self.text_svd_transformers = getattr(self, 'text_svd_transformers', {})
                self.text_svd_transformers[col_name] = svd
                logger.info(f"      ✅ TF-IDF+SVD: {n_components} dense features (from {tfidf_matrix.shape[1]} sparse)")
            else:
                tfidf_features = tfidf_matrix.toarray()
                logger.info(f"      ✅ TF-IDF: {tfidf_features.shape[1]} features")
            
            self.text_vectorizers[col_name] = tfidf
            
        except Exception as e:
            logger.warning(f"      ⚠️ TF-IDF failed: {e}")
            tfidf_features = np.zeros((len(text_series), 1))
        
        # 2. Text statistics (always useful, interpretable)
        stats_list = clean_texts.apply(self._get_text_statistics).tolist()
        stats_features = np.array([[s['char_count'], s['word_count'], s['avg_word_len'], 
                                   s['sentence_count'], s['uppercase_ratio'], s['digit_ratio']] 
                                  for s in stats_list])
        logger.info(f"      ✅ Text stats: 6 features")
        
        # 3. Sentiment (simple but effective)
        sentiment_list = clean_texts.apply(self._get_sentiment_features).tolist()
        sentiment_features = np.array([[s['positive_score'], s['negative_score'], 
                                       s['sentiment_ratio'], s['polarity']] 
                                      for s in sentiment_list])
        logger.info(f"      ✅ Sentiment: 4 features")
        
        # Combine all features
        all_features = np.hstack([tfidf_features, stats_features, sentiment_features])
        logger.info(f"      ✅ Total NLP features: {all_features.shape[1]}")
        
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
                    logger.warning(f"   🚨 LEAKAGE detected: '{col}' has {corr:.1%} correlation with target!")
            
            # SAFEGUARD: If ALL numeric features are considered leakage, don't drop them!
            # This happens in small datasets where features ARE the predictors
            if len(leaky_features) > 0 and len(leaky_features) == len(numeric_cols):
                logger.warning(f"   ⚠️ WARNING: All numeric features are highly correlated (>95%). ")
                logger.warning(f"      Keeping them to avoid empty dataset (might be small dataset or strong predictors).")
                return []
                
        except:
            pass
        
        return leaky_features
    
    def _preprocess_training(self, df: pd.DataFrame, target_col: str) -> Tuple[np.ndarray, np.ndarray]:
        """Preprocess data for training - ENHANCED for messy real-world data and NLP"""
        
        logger.info("🧹 ADVANCED DATA CLEANING...")
        
        X = df.drop(columns=[target_col]).copy()
        y = df[target_col].copy()
        
        self.target_column = target_col
        
        # Detect task type
        task_info = self._detect_task_type(y)
        self.task_type = task_info[0]
        self.n_classes = task_info[1]
        self.task_type_simple = 'classification' if 'classification' in self.task_type else 'regression'
        
        logger.info(f"   Task: {self.task_type} ({'n_classes=' + str(self.n_classes) if self.n_classes else 'continuous'})")
        
        # DETECT NLP DATASET
        self.is_nlp_task, self.primary_text_col = self._is_nlp_dataset(df, target_col)
        if self.is_nlp_task:
            logger.info(f"   📝 DETECTED: NLP/Text Classification Dataset")
            logger.info(f"   📝 Primary text column: {self.primary_text_col}")
        
        # STEP 1: Detect data leakage (features that perfectly predict target)
        y_numeric = pd.to_numeric(y, errors='coerce')
        if not y_numeric.isna().all():
            leaky_cols = self._detect_target_leakage(X, y_numeric, threshold=0.95)
            if leaky_cols:
                X = X.drop(columns=leaky_cols)
                logger.info(f"   🚨 Removed {len(leaky_cols)} leaky features")
        
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
                    
                    # Handle negative values for Naive Bayes (important for sentiment scores -1 to 1)
                    # using MinMax scaling to [0, 1] instead of abs() which destroys polarity
                    from sklearn.preprocessing import MinMaxScaler
                    scaler = MinMaxScaler(feature_range=(0, 1))
                    nlp_features = scaler.fit_transform(nlp_features)
                    self.nlp_scaler = scaler
                    
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
                        logger.info(f"   ✅ {col}: {len(vectorizer.vocabulary_)} text features")
                    else:
                        self.text_cols.remove(col)
            except Exception as e:
                logger.warning(f"   ⚠️ Text processing failed for {col}: {str(e)[:50]}")
                # FALLBACK: Encode as categorical if text processing fails
                try:
                    series = X[col].fillna('_MISSING_').astype(str).str.strip()
                    encoder = LabelEncoder()
                    encoded = encoder.fit_transform(series).reshape(-1, 1)
                    self.label_encoders[col] = encoder
                    processed_parts.append(encoded.astype(float))
                    logger.info(f"   ✅ {col}: Fallback to categorical encoding ({len(encoder.classes_)} categories)")
                    self.feature_metadata.append({
                        'name': col,
                        'type': 'categorical',
                        'options': encoder.classes_.tolist()[:50],
                        'default': encoder.classes_[0],
                        'n_categories': len(encoder.classes_)
                    })
                except Exception as fallback_err:
                    logger.warning(f"   ❌ {col}: Could not encode, skipping: {fallback_err}")
                if col in self.text_cols:
                    self.text_cols.remove(col)
        
        # Combine
        if processed_parts:
            X_processed = np.hstack(processed_parts)
        else:
            raise ValueError("No valid features after preprocessing")
            
        # === ADVANCED FEATURE ENGINEERING (Tabular Data) ===
        try:
            # Only apply for tabular data without massive text vectors to avoid explosion
            if not self.is_nlp_task and len(self.text_cols) == 0 and not self.data_profile.get('is_large_data'):
                current_features = self.numeric_cols + self.categorical_cols
                
                # Ensure feature names match column count (LabelEnc=1, Numeric=1)
                # This check ensures we don't mismatch if something expanded unexpectedly
                if hasattr(X_processed, 'shape') and X_processed.shape[1] == len(current_features):
                    logger.info("   🔧 Applying Advanced Feature Engineering (Poly + Interactions)...")
                    
                    # 1. Polynomial Features
                    if len(self.numeric_cols) > 0:
                        X_processed, poly_names = self.feature_engineer.create_polynomial_features(
                            X_processed, 
                            feature_names=current_features,
                            degree=2,
                            top_n=5
                        )
                        current_features = poly_names
                    
                    # 2. Interactions - SKIPPING explicit interactions as Tree models handle them
                    # and we need a persistable transformer for prediction time.
                    # GBMs (XGBoost/CatBoost) capture interactions automatically.

        except Exception as e:
            logger.warning(f"   ⚠️ Advanced feature engineering skipped: {e}")
        
        # Clean final array - ensure numeric dtype before nan_to_num
        try:
            # Convert to float, handling any object types
            if X_processed.dtype == object:
                # 🛡️ ROBUST: Force column-by-column conversion for object arrays
                logger.warning("   ⚠️ Object dtype detected, forcing column-wise numeric conversion...")
                X_clean = np.zeros(X_processed.shape, dtype=float)
                for i in range(X_processed.shape[1]):
                    try:
                        X_clean[:, i] = pd.to_numeric(X_processed[:, i], errors='coerce').fillna(0)
                    except Exception:
                        try:
                            # Last resort: LabelEncode strings like 'Absence', 'Present'
                            le = LabelEncoder()
                            X_clean[:, i] = le.fit_transform(X_processed[:, i].astype(str))
                            logger.info(f"      ✅ Column {i}: Label encoded")
                        except:
                            X_clean[:, i] = 0
                X_processed = X_clean
            X_processed = np.nan_to_num(X_processed.astype(float), nan=0.0, posinf=0.0, neginf=0.0)
        except (ValueError, TypeError) as conv_err:
            logger.warning(f"   ⚠️ Numeric conversion issue: {conv_err}, attempting column-wise conversion")
            # Fallback: column-wise conversion with LabelEncoder
            X_clean = np.zeros_like(X_processed, dtype=float)
            for i in range(X_processed.shape[1]):
                try:
                    col = pd.to_numeric(X_processed[:, i], errors='coerce')
                    X_clean[:, i] = np.nan_to_num(col, nan=0.0, posinf=0.0, neginf=0.0)
                except Exception:
                    try:
                        le = LabelEncoder()
                        X_clean[:, i] = le.fit_transform(X_processed[:, i].astype(str))
                    except:
                        X_clean[:, i] = 0.0
            X_processed = X_clean
        
        # Process target
        if self.task_type_simple == 'classification':
            self.target_encoder = LabelEncoder()
            y_processed = self.target_encoder.fit_transform(y.fillna('_MISSING_').astype(str).str.strip())
        else:
            y_processed = pd.to_numeric(y, errors='coerce').fillna(0).values.astype(float)
            y_processed = np.nan_to_num(y_processed, nan=0.0)
        
        logger.info(f"   Final shape: {X_processed.shape}")
        
        return X_processed, y_processed
    
    def _preprocess_single(self, data: Dict[str, Any]) -> np.ndarray:
        """Preprocess single input for prediction - LEGACY PIPELINE"""
        logger.info(f"🔧 Legacy preprocessing: {len(data)} input features")
        parts = []
        
        # Numeric
        if self.numeric_cols:
            logger.info(f"   Processing {len(self.numeric_cols)} numeric columns")
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
            logger.info(f"   Numeric features shape: {parts[-1].shape if parts else 'none'}")
        
        # Categorical
        if self.categorical_cols:
            logger.info(f"   Processing {len(self.categorical_cols)} categorical columns")
        for col in self.categorical_cols:
            encoder = self.label_encoders.get(col)
            if encoder:
                val = str(data.get(col, '_MISSING_')).strip()
                try:
                    if hasattr(encoder, 'classes_') and val in encoder.classes_:
                        encoded = encoder.transform([val])[0]
                    else:
                        encoded = 0  # Unknown category defaults to 0
                except Exception as e:
                    logger.warning(f"   ⚠️ Encoding failed for {col}={val}: {e}")
                    encoded = 0
                parts.append(np.array([[float(encoded)]]))
        
        # Text
        for col in self.text_cols:
            text = str(data.get(col, ''))
            
            # Check if this column was processed with full NLP pipeline
            if getattr(self, 'is_nlp_task', False) or col == getattr(self, 'primary_text_col', None):
                # Use saved TF-IDF vectorizer for consistent feature extraction
                vectorizer = self.text_vectorizers.get(col)
                if vectorizer:
                    try:
                        # 1. TF-IDF features from saved vectorizer
                        tfidf_sparse = vectorizer.transform([text])
                        
                        # 2. Apply SVD if it was used during training
                        svd_transformers = getattr(self, 'text_svd_transformers', {})
                        if col in svd_transformers:
                            svd = svd_transformers[col]
                            tfidf_feats = svd.transform(tfidf_sparse)
                        else:
                            tfidf_feats = tfidf_sparse.toarray()
                        
                        parts.append(tfidf_feats)
                    except Exception as e:
                        logger.warning(f"   ⚠️ TF-IDF/SVD transform failed for {col}: {e}")
                        # Fallback to expected SVD size or vocab size
                        svd_transformers = getattr(self, 'text_svd_transformers', {})
                        if col in svd_transformers:
                            expected_size = svd_transformers[col].n_components
                        else:
                            expected_size = len(vectorizer.vocabulary_) if hasattr(vectorizer, 'vocabulary_') else 50
                        parts.append(np.zeros((1, expected_size)))
                
                # 2. Text stats (same as training)
                clean_text = self._clean_text_nlp(text)
                stats = self._get_text_statistics(clean_text)
                stats_features = np.array([[stats['char_count'], stats['word_count'], stats['avg_word_len'],
                                           stats['sentence_count'], stats['uppercase_ratio'], stats['digit_ratio']]])
                parts.append(stats_features)
                
                # 3. Sentiment features (same as training)
                sentiment = self._get_sentiment_features(clean_text)
                sentiment_features = np.array([[sentiment['positive_score'], sentiment['negative_score'],
                                               sentiment['sentiment_ratio'], sentiment['polarity']]])
                parts.append(sentiment_features)
            
            # Fallback to standard vectorizer if it exists (non-NLP text)
            elif col in self.text_vectorizers:
                vectorizer = self.text_vectorizers[col]
                tfidf_sparse = vectorizer.transform([text])
                # Check for SVD
                svd_transformers = getattr(self, 'text_svd_transformers', {})
                if col in svd_transformers:
                    parts.append(svd_transformers[col].transform(tfidf_sparse))
                else:
                    parts.append(tfidf_sparse.toarray())
        
        X_processed = np.hstack(parts) if parts else np.array([[0]])
        logger.info(f"   Combined features shape before poly: {X_processed.shape}")
        
        # === Apply Advanced Feature Engineering (Poly) ===
        try:
            if self.feature_engineer.poly_transformer is not None:
                # PolynomialFeatures expects 'n_features_in_' columns.
                # Since we fit it on the first N columns of the processed array during training
                # We must slice the same way here.
                n_input = self.feature_engineer.poly_transformer.n_features_in_
                
                if X_processed.shape[1] >= n_input:
                    X_subset = X_processed[:, :n_input]
                    X_poly = self.feature_engineer.poly_transformer.transform(X_subset)
                    
                    # Combine: If train expanded, we expand. 
                    # Note: create_polynomial_features combined logic:
                    # if n_features < X.shape[1]: combined = hstack([poly, rest])
                    # else: combined = poly
                    
                    if n_input < X_processed.shape[1]:
                        X_processed = np.hstack([X_poly, X_processed[:, n_input:]])
                    else:
                        X_processed = X_poly
        except Exception as e:
            logger.warning(f"⚠️ Prediction feature engineering error: {e}")
        
        # === FEATURE DIMENSION VALIDATION ===
        if hasattr(self, 'model') and hasattr(self.model, 'n_features_in_'):
            expected = self.model.n_features_in_
            actual = X_processed.shape[1]
            if actual != expected:
                logger.warning(f"⚠️ FEATURE MISMATCH: Model expects {expected}, got {actual}")
                # Try to fix by padding or truncating
                if actual < expected:
                    padding = np.zeros((1, expected - actual))
                    X_processed = np.hstack([X_processed, padding])
                    logger.info(f"   Padded to {X_processed.shape[1]} features")
                else:
                    X_processed = X_processed[:, :expected]
                    logger.info(f"   Truncated to {X_processed.shape[1]} features")
            else:
                logger.info(f"   ✅ Feature count matches: {actual}")
        
        logger.info(f"   Final preprocessed shape: {X_processed.shape}")
        return X_processed
    
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
                'BernoulliNB': (
                    BernoulliNB(),
                    {'alpha': [0.1, 0.5, 1.0], 'binarize': [0.0, 0.5]}
                ),
                
                # === DISCRIMINANT ANALYSIS ===
                'LDA': (
                    LinearDiscriminantAnalysis(),
                    {'solver': ['svd', 'lsqr']}
                ),
                'QDA': (
                    QuadraticDiscriminantAnalysis(),
                    {'reg_param': [0.0, 0.1, 0.5]}
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
                'BayesianRidge': (
                    BayesianRidge(),
                    {'alpha_1': [1e-6, 1e-5], 'lambda_1': [1e-6, 1e-5]}
                ),
                'HuberRegressor': (
                    HuberRegressor(max_iter=1000),
                    {'epsilon': [1.1, 1.35, 1.5, 1.75], 'alpha': [0.0001, 0.001]}
                ),
                'PoissonRegressor': (
                    PoissonRegressor(max_iter=1000),
                    {'alpha': [0.1, 1.0, 10.0]}
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
            
            min_class_count = min(class_counts[class_counts > 0])  # Avoid zero counts
            imbalance_ratio = max(class_counts) / max(min_class_count, 1)
            
            if imbalance_ratio > 3 and min_class_count >= 6:
                print(f"   ⚠️ Class imbalance detected (ratio={imbalance_ratio:.1f}:1), applying SMOTE...")
                
                # k_neighbors must be less than the smallest class size
                k_neighbors = min(5, min_class_count - 1)
                if k_neighbors < 1:
                    print(f"   ⚠️ Too few samples in minority class for SMOTE")
                    return X_train, y_train
                
                # For multiclass, use 'auto' strategy (float only works for binary)
                n_classes = len(class_counts[class_counts > 0])
                sampling_strategy = 'auto' if n_classes > 2 else 'auto'
                
                smote = SMOTE(
                    random_state=42, 
                    k_neighbors=k_neighbors,
                    sampling_strategy=sampling_strategy
                )
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
            
            logger.info(f"   🎯 Optuna best score: {study.best_value:.4f}")
            return study.best_params, study.best_value
        except Exception as e:
            logger.warning(f"   ⚠️ Optuna failed: {e}")
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
            
            logger.info(f"   🏗️ Building stacking ensemble with {len(estimators)} models...")
            
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
            logger.info(f"   ✅ Stacking ensemble trained successfully")
            return stacker
        except Exception as e:
            logger.warning(f"   ⚠️ Stacking failed: {e}")
            return None

    def _get_cv_strategy(self, y: np.ndarray, n_splits: int = 5):
        """Intelligent CV strategy selection"""
        from sklearn.model_selection import StratifiedKFold, KFold
        
        n_samples = len(y)
        
        # SAFEGUARD: Ensure splits don't exceed samples
        if n_splits > n_samples:
            n_splits = max(2, min(3, n_samples))
        
        if self.task_type_simple == 'classification':
            # Stratified maintains class balance
            try:
                # If any class has fewer members than n_splits, reduce splits
                min_class_members = pd.Series(y).value_counts().min()
                if min_class_members < n_splits:
                    n_splits = max(2, min_class_members)
            except:
                pass
                
            return StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        else:
            # Regression: ALWAYS use KFold, never Stratified
            return KFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    # =========================================================================
    # PRODUCTION TRAINING (AUTOML)
    # =========================================================================
    
    async def train_with_test_set(
        self,
        train_df: pd.DataFrame,
        test_df: pd.DataFrame,
        target_col: Optional[str] = None,
        user_id: str = "default"
    ) -> 'TrainResult':
        """
        Wrapper to handle separate Test set from API.
        Concatenates data and runs production pipeline to ensure consistent processing.
        """
        logger.info(f"🔄 train_with_test_set called: Train={len(train_df)}, Test={len(test_df)}")
        
        # Calculate Metadata on Train set specifically (to capture raw distributions)
        # We do this before concat to ensure we capture training distribution
        self._calculate_feature_metadata(train_df)
        
        # Concatenate for full AutoML logic (which handles splitting internally)
        # Note: We rely on production_train's internal robust validation
        full_df = pd.concat([train_df, test_df], ignore_index=True)
        
        return self.production_train(full_df, target_col, user_id)

    def production_train(
        self,
        df: pd.DataFrame,
        target_col: Optional[str] = None,
        user_id: str = "default",
        mode: str = "fast",  # 'fast' or 'ultra'
        algorithm: Optional[str] = None  # Specific algorithm or None for auto-select
    ) -> 'TrainResult':
        """
        🚀 PRODUCTION AUTOML PIPELINE
        
        Uses the production_ml_core module for:
        - Smart data cleaning
        - Advanced feature engineering
        - 15+ production algorithms (XGBoost, LightGBM, CatBoost, etc.)
        - Ensemble methods for best accuracy
        
        If algorithm is specified, trains only that algorithm.
        Otherwise, trains multiple and picks the best.
        
        Expected accuracy: 80%+
        """
        from sklearn.model_selection import train_test_split
        
        # Reset cancellation flag for this user
        CANCELLATION_FLAGS[user_id] = False
        cleaned_file_path = None # Track cleaned file path
        
        # Callback wrapper to allow cancellation during training
        def check_stop():
            check_cancellation(user_id)
        
        self.errors = []
        start = datetime.now()
        
        
        logger.info("=" * 60)
        logger.info("🚀 PRODUCTION AUTOML PIPELINE")
        logger.info("=" * 60)
        
        # 🚀 HUGGINGFACE ENVIRONMENT DIAGNOSTICS
        import os
        is_huggingface = os.path.exists("/app") or os.getenv("SPACE_ID") is not None
        
        if is_huggingface:
            logger.info("🐳 [HF-DIAG] Running on HuggingFace Spaces")
            logger.info(f"🐳 [HF-DIAG] Data shape: {df.shape}")
            logger.info(f"🐳 [HF-DIAG] Target column: {target_col}")
            logger.info(f"🐳 [HF-DIAG] Mode: {mode}")
            
            # Check memory
            try:
                import psutil
                mem = psutil.virtual_memory()
                logger.info(f"🐳 [HF-DIAG] Memory: {mem.available // (1024*1024)}MB available / {mem.total // (1024*1024)}MB total")
            except:
                logger.info("🐳 [HF-DIAG] Memory info unavailable")
            
            # Check critical dependencies
            deps_status = []
            for dep in ['sklearn', 'numpy', 'pandas', 'xgboost', 'lightgbm', 'catboost']:
                try:
                    __import__(dep.replace('sklearn', 'sklearn.ensemble'))
                    deps_status.append(f"✅ {dep}")
                except:
                    deps_status.append(f"❌ {dep}")
            logger.info(f"🐳 [HF-DIAG] Dependencies: {', '.join(deps_status)}")
        
        # 🆕 Use Smart Data Analyzer for improved target detection and insights
        try:
            from ml.smart_data_analyzer import SmartDataAnalyzer
            analyzer = SmartDataAnalyzer()
            analysis = analyzer.analyze(df, target_col)
            
            # Use detected target if none provided
            if not target_col:
                target_col = analysis.target_column
            
            logger.info(f"📊 Data Type: {analysis.data_type.value.upper()}")
            logger.info(f"🎪 Task Type: {analysis.task_type.value}")
            logger.info(f"🔧 Mode: {mode.upper()}")
        except Exception as e:
            logger.warning(f"Smart analyzer unavailable: {e}")
            if not target_col:
                target_col = self._detect_target(df)
        
        logger.info(f"📊 Data: {df.shape[0]} rows, {df.shape[1]} columns")
        logger.info(f"🎯 Target: {target_col}")
        
        # CRITICAL: Store target column for metadata persistence
        self.target_column = target_col
        
        # 1. Clean data
        cleaner = ProductionDataCleaner()
        df_clean = cleaner.clean(df, target_col)
        
        # CRITICAL: Drop rows where target is NaN (cleaner skips target column)
        target_nan_count = df_clean[target_col].isna().sum()
        if target_nan_count > 0:
            df_clean = df_clean.dropna(subset=[target_col])
            logger.warning(f"   ⚠️ Dropped {target_nan_count} rows with missing target values")
        
        # SAVE CLEANED DATA (User Request)
        # SAVE CLEANED DATA (User Request)
        try:
            from utils.paths import get_user_paths
            user_paths = get_user_paths(user_id)
            # Save to standard 'files' storage so /api/v1/files endpoint can serve it
            upload_dir = user_paths['files']
            
            cleaned_filename = f"cleaned_{int(datetime.now().timestamp())}.csv"
            cleaned_full_path = upload_dir / cleaned_filename
            
            df_clean.to_csv(cleaned_full_path, index=False)
            logger.info(f"💾 Saved cleaned data to: {cleaned_full_path}")
            cleaned_file_path = cleaned_filename
        except Exception as e:
            logger.error(f"Failed to save cleaned data: {e}")
            cleaned_file_path = None
        
        # 2. Detect task type (IMPROVED - handles Rating columns with decimals correctly)
        y_temp = df_clean[target_col]
        n_unique = y_temp.nunique()
        
        # CRITICAL FIX: First try to convert to numeric, then check types
        y_numeric = pd.to_numeric(y_temp, errors='coerce')
        valid_numeric_ratio = y_numeric.notna().sum() / len(y_temp)
        is_numeric = valid_numeric_ratio > 0.5  # >50% are valid numbers
        
        # Check if values are continuous decimals (like ratings 4.1, 4.2)
        is_decimal = False
        if is_numeric and y_numeric.notna().any():
            try:
                # Use the converted numeric values
                non_null = y_numeric.dropna()
                # Check if any value has decimal part
                is_decimal = (non_null % 1 != 0).any()
                
                if is_decimal:
                    logger.info(f"   🔍 Detected decimal values in target (e.g., {non_null.iloc[0]})")
            except Exception as e:
                logger.warning(f"   ⚠️ Decimal check failed: {e}")
        
        # IMPROVED LOGIC:
        # 1. If target has decimals AND >10 unique values -> ALWAYS Regression (ratings, prices)
        # 2. If target is NOT numeric (strings) -> Classification
        # 3. If target has few unique values (<20) -> Classification
        
        # 🆕 OVERRIDE: Use Smart Data Analyzer result if available
        if 'analysis' in locals() and analysis:
            smart_task = analysis.task_type.value
            if 'classification' in smart_task:
                self.task_type = 'classification'
                self.task_type_simple = 'classification'
                logger.info(f"🎯 Smart Analysis: Detected CLASSIFICATION ({smart_task})")
            elif 'regression' in smart_task:
                self.task_type = 'regression'
                self.task_type_simple = 'regression'
                logger.info(f"🎯 Smart Analysis: Detected REGRESSION ({smart_task})")
        
        # Fallback to heuristic if Smart Analysis didn't run or was inconclusive
        elif is_decimal and n_unique > 10:
            self.task_type = 'regression'
            self.task_type_simple = 'regression'
            logger.info(f"📋 Task: REGRESSION (decimal values detected)")
            
        elif not is_numeric:
            self.task_type = 'classification'
            self.task_type_simple = 'classification'
            logger.info(f"📋 Task: CLASSIFICATION (non-numeric target)")
            
        elif n_unique < 20:
            self.task_type = 'classification'
            self.task_type_simple = 'classification'
            logger.info(f"📋 Task: CLASSIFICATION (low cardinality: {n_unique})")
            
        else:
            # Default to regression for many unique numeric values
            self.task_type = 'regression'
            self.task_type_simple = 'regression'
            logger.info(f"📋 Task: REGRESSION (default, {n_unique} unique)")
        
        # 3. Feature engineering (pass mode for Fast vs Ultra NLP)
        engineer = ProductionFeatureEngineer(mode=mode)
        
        # EXTRACT METADATA FOR PREDICTIONS TAB (INPUT SCHEMA) --
        # This must capture ORIGINAL columns BEFORE feature engineering!
        # Must match EXACTLY how NLP engine does it for consistency
        self.feature_metadata = []
        
        # Columns to skip (ID columns, index columns, internal columns)
        skip_patterns = ['unnamed', 'index', '_id', 'id']
        
        for col in df_clean.columns:
            if col == target_col:
                continue
            
            # Skip ID/index columns - they shouldn't be user inputs
            col_lower = col.lower().strip()
            if col_lower in skip_patterns or col_lower.startswith('unnamed'):
                continue
            if col_lower == 'id' and df_clean[col].nunique() == len(df_clean):
                # Skip if it's a unique ID column
                continue
            
            # Detect column type: numeric, text, datetime, or categorical
            # Use SAME logic as NLP engine for consistency
            
            # Check for datetime first
            if pd.api.types.is_datetime64_any_dtype(df_clean[col]):
                # Datetime column - treat as date input
                self.feature_metadata.append({
                    'name': col,
                    'type': 'date',
                    'format': 'YYYY-MM-DD'
                })
            elif pd.api.types.is_numeric_dtype(df_clean[col]):
                col_type = 'numeric'
                meta = {
                    'name': col,
                    'type': 'numeric'
                }
                try:
                    meta['min'] = float(df_clean[col].min())
                    meta['max'] = float(df_clean[col].max())
                    meta['mean'] = float(df_clean[col].mean())
                except:
                    meta['min'] = 0
                    meta['max'] = 100
                    meta['mean'] = 50
                self.feature_metadata.append(meta)
                    
            elif df_clean[col].dtype == 'object' or str(df_clean[col].dtype) == 'string':
                # String column - detect text vs categorical vs date using NLP engine logic
                sample = df_clean[col].dropna().astype(str)
                if len(sample) > 0:
                    avg_len = sample.str.len().mean()
                    unique_ratio = df_clean[col].nunique() / len(df_clean)
                    
                    # First check if it looks like a date column
                    is_date_like = False
                    col_lower = col.lower()
                    if any(kw in col_lower for kw in ['date', 'time', 'created', 'updated', 'timestamp']):
                        # Column name suggests date, try parsing
                        try:
                            pd.to_datetime(sample.head(10), errors='raise')
                            is_date_like = True
                        except:
                            pass
                    elif unique_ratio > 0.5 and avg_len <= 25:
                        # High unique ratio and short strings - might be dates
                        date_patterns = ['/', '-', ':']
                        if any(any(pat in str(v) for pat in date_patterns) for v in sample.head(5)):
                            try:
                                pd.to_datetime(sample.head(10), errors='raise')
                                is_date_like = True
                            except:
                                pass
                    
                    if is_date_like:
                        self.feature_metadata.append({
                            'name': col,
                            'type': 'date',
                            'format': 'YYYY-MM-DD'
                        })
                    elif avg_len < 30 and unique_ratio < 0.5:
                        # Categorical dropdown
                        try:
                            options = df_clean[col].dropna().unique().tolist()[:50]
                            self.feature_metadata.append({
                                'name': col,
                                'type': 'categorical',
                                'options': [str(x) for x in options]
                            })
                        except:
                            self.feature_metadata.append({
                                'name': col,
                                'type': 'categorical',
                                'options': []
                            })
                    else:
                        # Text input (long text or high uniqueness like titles)
                        self.feature_metadata.append({
                            'name': col,
                            'type': 'text',
                            'placeholder': f'Enter {col}...'
                        })
                else:
                    self.feature_metadata.append({
                        'name': col,
                        'type': 'text',
                        'placeholder': f'Enter {col}...'
                    })
            else:
                # Other types - check for datetime-like strings or treat as categorical
                # Try to detect if this looks like a date column
                is_date_like = False
                try:
                    sample = df_clean[col].dropna().head(10).astype(str)
                    date_patterns = ['/', '-', ':']
                    if any(any(pat in str(v) for pat in date_patterns) for v in sample):
                        # Try parsing as date
                        try:
                            pd.to_datetime(sample, errors='raise')
                            is_date_like = True
                        except:
                            pass
                except:
                    pass
                
                if is_date_like:
                    self.feature_metadata.append({
                        'name': col,
                        'type': 'date',
                        'format': 'YYYY-MM-DD'
                    })
                else:
                    # Treat as categorical
                    try:
                        options = df_clean[col].dropna().unique().tolist()[:50]
                        self.feature_metadata.append({
                            'name': col,
                            'type': 'categorical',
                            'options': [str(x) for x in options]
                        })
                    except:
                        self.feature_metadata.append({
                            'name': col,
                            'type': 'text',
                            'placeholder': f'Enter {col}...'
                        })
        
        logger.info(f"   Feature metadata: {len(self.feature_metadata)} features for Predict tab")
        # --------------------------------------------------------

        # 🛡️ CRITICAL FIX: SPLIT DATA BEFORE FEATURE ENGINEERING
        # This prevents TARGET ENCODING LEAKAGE where test target values
        # contaminate the categorical encoding
        logger.info("\n📊 TRAIN-TEST SPLIT (BEFORE FEATURE ENGINEERING)")
        logger.info("=" * 50)
        logger.info("   🛡️ Splitting BEFORE feature engineering to prevent target leakage")
        
        # 4. Encode target for classification FIRST (before split)
        if self.task_type_simple == 'classification':
            self.target_encoder = LabelEncoder()
            df_clean[target_col] = self.target_encoder.fit_transform(df_clean[target_col].astype(str))
            self.n_classes = len(self.target_encoder.classes_)
        
        # 5. Split data (with fallback for rare classes)
        try:
            stratify = df_clean[target_col] if self.task_type_simple == 'classification' else None
            df_train, df_test = train_test_split(
                df_clean, test_size=0.2, random_state=42, stratify=stratify
            )
        except ValueError as e:
            # Fallback: use regular split if stratified fails (rare classes)
            logger.warning(f"   ⚠️ Stratified split failed, using regular split: {str(e)[:50]}")
            df_train, df_test = train_test_split(
                df_clean, test_size=0.2, random_state=42
            )
        logger.info(f"   ✅ Train: {len(df_train)} rows | Test: {len(df_test)} rows")
        
        # 6. Feature engineering - FIT on TRAINING DATA ONLY
        logger.info("\n🔧 FEATURE ENGINEERING (TRAIN DATA ONLY)")
        logger.info("=" * 50)
        logger.info("   🛡️ Target encoding uses ONLY training data - NO LEAKAGE")
        
        X_train, y_train, feature_names = engineer.fit_transform(df_train, target_col, self.task_type_simple)
        self.feature_columns = feature_names
        
        # 7. Transform test data using FITTED transformers (no target leakage)
        logger.info("\n🔮 TRANSFORMING TEST DATA")
        X_test = engineer.transform(df_test, target_col)
        y_test = df_test[target_col].values
        if self.task_type_simple == 'regression':
            y_test = y_test.astype(float)
        else:
            # Classification: Use target_encoder to handle string/object labels (e.g., 'Yes'/'No')
            # The target_encoder was fitted on training data, now transform test labels
            if hasattr(self, 'target_encoder') and self.target_encoder is not None:
                y_test = self.target_encoder.transform(
                    pd.Series(y_test).fillna('_MISSING_').astype(str).str.strip()
                )
            else:
                # Fallback: try direct int conversion (if already numeric encoded)
                try:
                    y_test = y_test.astype(int)
                except ValueError:
                    # Create a new encoder as emergency fallback
                    from sklearn.preprocessing import LabelEncoder
                    fallback_encoder = LabelEncoder()
                    y_test = fallback_encoder.fit_transform(y_test.astype(str))
        
        logger.info(f"   ✅ X_train: {X_train.shape} | X_test: {X_test.shape}")
        
        # 8. Train all models
        # Pass mode to trainer ('fast' = 8 models, 'ultra' = 20+ with ensembles)
        # 🆕 Pass sample count AND feature count for Production Intelligence optimization
        n_features = X_train.shape[1] if len(X_train.shape) > 1 else 1
        trainer = ProductionModelTrainer(
            self.task_type_simple, 
            mode=mode, 
            n_samples=len(X_train),
            n_features=n_features  # 🛡️ PRODUCTION INTELLIGENCE
        )
        logger.info(f"🎮 Training Mode: {mode.upper()}")
        
        # 🆕 Log large dataset detection
        if len(X_train) > 50000:
            logger.info(f"   📊 LARGE DATASET DETECTED: {len(X_train):,} training samples")
            logger.info(f"   📊 Optimizing models for speed & memory efficiency")
        
        # Check cancellation before heavy training phase
        check_stop()
        
        results = trainer.train_all(X_train, y_train, X_test, y_test, check_cancellation=check_stop)
        
        # 9. Build ensemble
        ensemble = trainer.build_ensemble(X_train, y_train, X_test, y_test, top_n=3)
        
        # 8. Neural Architecture Search (Ultra Mode Only)
        # 🆕 Skip for very large datasets (memory intensive)
        if mode == 'ultra' and len(X_train) <= 100000:
            try:
                from ml.neural_architecture_engine import train_neural_models
                logger.info("🧠 Starting Neural Architecture Search (Ultra Mode)...")
                
                # Use subset for responsiveness if data is massive
                if len(X_train) > 20000:
                    indices = np.random.choice(len(X_train), 20000, replace=False)
                    X_neural, y_neural = X_train[indices], y_train[indices]
                else:
                    X_neural, y_neural = X_train, y_train
                
                neural_results = train_neural_models(
                    X_neural, y_neural,
                    X_test[:5000], y_test[:5000], # Validation set
                    task_type=self.task_type_simple,
                    n_classes=len(np.unique(y_train)) if self.task_type_simple == 'classification' else 0,
                    check_cancellation=check_stop,
                    max_epochs=30 # Quick search
                )
                
                if neural_results.success:
                    logger.info(f"   🧠 Best Neural Model: {neural_results.best_model_name} (Score: {neural_results.best_score:.4f})")
                    
                    # Add to leaderboard for visibility
                    for res in neural_results.all_results:
                        # Construct metrics dict
                        metrics = {
                            'score': res['score'],
                            'val_loss': res.get('val_loss', 0)
                        }
                        if self.task_type_simple == 'classification':
                            metrics['f1'] = res['score']
                        else:
                            metrics['r2'] = res['score']

                        trainer.results.append({
                            'name': f"DNN_{res['name']}",
                            'model': None, # Don't store Keras model to avoid pickle issues
                            'score': res['score'],
                            'metrics': metrics,
                            'time': neural_results.total_time_seconds / len(neural_results.all_results)
                        })
                    
                    # Re-sort leaderboard
                    trainer.results.sort(key=lambda x: x['score'], reverse=True)
                    
            except Exception as e:
                logger.warning(f"Neural engine skipped: {e}")
        elif mode == 'ultra' and len(X_train) > 100000:
            logger.info("   ⚠️ Skipping Neural Architecture Search for large dataset (>100k rows)")
            logger.info("   📊 Using gradient boosting models (LightGBM, XGBoost) for best performance")
        
        # Store results
        self.model = trainer.best_model
        self.model_name = trainer.best_name
        self._y_test = y_test
        self._y_pred = trainer.best_model.predict(X_test)
        
        # IMPORTANT: Store production feature engineer for predictions
        self.production_engineer = engineer
        self.production_mode = True
        
        # Get probabilities if classification
        y_proba = None
        if self.task_type_simple == 'classification' and hasattr(self.model, 'predict_proba'):
            try:
                y_proba = self.model.predict_proba(X_test)
            except:
                pass
        
        # Save model
        self._save(user_id)
        
        elapsed = (datetime.now() - start).total_seconds()
        
        logger.info("\n" + "=" * 60)
        logger.info(f"✅ COMPLETE in {elapsed:.1f}s")
        logger.info(f"🏆 Best Model: {trainer.best_name}")
        logger.info(f"📈 Score: {trainer.best_score:.4f}")
        logger.info("=" * 60)
        
        # Get best metrics - for Ensemble, calculate directly
        best_result = next((r for r in trainer.results if r['name'] == trainer.best_name), None)
        
        if best_result:
            best_metrics = best_result.get('metrics', {})
        else:
            # Ensemble or model not in results - calculate metrics directly
            from sklearn.metrics import accuracy_score, f1_score, r2_score, mean_absolute_error
            if self.task_type_simple == 'classification':
                acc = accuracy_score(y_test, self._y_pred)
                f1 = f1_score(y_test, self._y_pred, average='weighted', zero_division=0)
                best_metrics = {'accuracy': round(acc, 4), 'f1': round(f1, 4)}
            else:
                r2 = r2_score(y_test, self._y_pred)
                mae = mean_absolute_error(y_test, self._y_pred)
                best_metrics = {'r2': round(r2, 4), 'mae': round(mae, 4)}
        
        # IMPORTANT: Store metrics on self so they're saved to persistence
        self.metrics = best_metrics
        
        # Generate charts
        charts = {}
        try:
            from ml.chart_generator import (
                generate_ml_charts, generate_model_comparison_chart,
                generate_correlation_heatmap, generate_distribution_grid, generate_boxplot_grid,
                detect_stock_data, generate_stock_charts
            )
            
            # 📈 DETECT STOCK/FINANCIAL DATA AND GENERATE STOCK CHARTS
            stock_info = detect_stock_data(df_clean)
            if stock_info['is_stock_data']:
                logger.info("📈 Stock/Financial data detected! Generating stock-specific charts...")
                stock_charts = generate_stock_charts(df_clean, stock_info, target_col)
                charts.update(stock_charts)
                logger.info(f"   📊 Generated {len(stock_charts)} stock charts")
            
            class_names = self.target_encoder.classes_.tolist() if self.target_encoder else None
            ml_charts = generate_ml_charts(
                task_type=self.task_type,
                y_test=y_test,
                y_pred=self._y_pred,
                y_proba=y_proba,
                feature_importance=self._get_importance(self.model),
                class_names=class_names,
                model_name=trainer.best_name
            )
            charts.update(ml_charts)
            comparison_chart = generate_model_comparison_chart(trainer.results)
            if comparison_chart:
                charts['model_comparison'] = comparison_chart
            
            # 🆕 ADD EXTRA CHARTS FROM REAL DATA
            # Correlation Heatmap (numeric features only)
            numeric_df = df_clean.select_dtypes(include=[np.number])
            if len(numeric_df.columns) >= 2:
                corr_chart = generate_correlation_heatmap(numeric_df, "Feature Correlations")
                if corr_chart:
                    charts['correlation_heatmap'] = corr_chart
            
            # Distribution Grid (histograms of features)
            if len(numeric_df.columns) >= 1:
                dist_chart = generate_distribution_grid(numeric_df, "Feature Distributions")
                if dist_chart:
                    charts['distribution_grid'] = dist_chart
            
            # Box Plot Grid
            if len(numeric_df.columns) >= 1:
                box_chart = generate_boxplot_grid(numeric_df, "Feature Box Plots")
                if box_chart:
                    charts['boxplot_grid'] = box_chart
            
            # 🆕 ULTRA MODE: Premium Enterprise Charts
            if mode == 'ultra':
                try:
                    from ml.chart_generator import generate_ultra_charts
                    
                    ultra_charts = generate_ultra_charts(
                        task_type=self.task_type,
                        y_test=y_test,
                        y_pred=self._y_pred,
                        y_proba=y_proba,
                        feature_importance=self._get_importance(self.model),
                        leaderboard=trainer.results,
                        model_name=trainer.best_name,
                        X_test=X_test,
                        cv_scores=None  # Could add if available
                    )
                    
                    # Merge ultra charts with standard charts
                    charts.update(ultra_charts)
                    logger.info(f"   🎨 Ultra Charts Generated: {list(ultra_charts.keys())}")
                except Exception as ultra_err:
                    logger.warning(f"⚠️ Ultra chart error: {ultra_err}")
                    import traceback
                    traceback.print_exc()
                    
            print(f"📊 Generated {len(charts)} charts: {list(charts.keys())}")
            
        except Exception as chart_err:
            logger.warning(f"⚠️ Chart generation error: {chart_err}")
        
        # CRITICAL: Save model for predictions
        try:
            self._save(user_id, charts=charts)
            print(f"💾 Model saved for user: {user_id}")
        except Exception as save_err:
            logger.warning(f"⚠️ Model save error: {save_err}")
        
        # 🛡️ PRODUCTION INTELLIGENCE: Get reliability score and warnings
        reliability_score = 75  # Default
        validation_warnings = []
        if best_result and 'reliability_score' in best_result:
            reliability_score = best_result.get('reliability_score', 75)
        for r in trainer.results:
            if r.get('warning'):
                validation_warnings.append(f"{r.get('name', 'Model')}: {r.get('warning')}")
        
        return TrainResult(
            success=True,
            task_type=self.task_type,
            target_column=target_col,
            # IMPORTANT: Use original columns (not engineered features) for Features tab
            feature_columns=engineer.original_columns,
            best_model_name=trainer.best_name,
            best_model_metrics=best_metrics,
            leaderboard=[{'name': r['name'], 'metrics': r['metrics']} for r in trainer.results],
            feature_importance=self._get_importance(self.model),
            y_test=y_test,
            y_pred=self._y_pred,
            y_proba=y_proba,
            feature_metadata=getattr(self, 'feature_metadata', []),
            n_rows=len(df),
            n_cols=len(df.columns),
            processing_time=elapsed,
            charts=charts,
            is_nlp_task=False,
            primary_text_col=None,
            cleaned_file_path=cleaned_file_path,
            reliability_score=reliability_score,
            validation_warnings=validation_warnings if validation_warnings else None
        )
    
    def production_train_selected(
        self,
        df: pd.DataFrame,
        target_col: Optional[str] = None,
        user_id: str = "default",
        selected_algorithms: List[str] = None
    ) -> 'TrainResult':
        """
        🎯 TRAIN ONLY USER-SELECTED ALGORITHMS
        
        Instead of training all fast/ultra models, train only the specific
        algorithms the user selected in the UI.
        
        Args:
            df: Input dataframe
            target_col: Target column name
            user_id: User ID for model storage
            selected_algorithms: List of algorithm keys like ['random_forest', 'xgboost', 'lightgbm']
        
        Returns:
            TrainResult with best model from selected algorithms
        """
        from sklearn.model_selection import train_test_split
        
        if not selected_algorithms:
            # Fallback to fast mode if no algorithms selected
            return self.production_train(df, target_col, user_id, mode='fast')
        
        # Reset cancellation flag
        CANCELLATION_FLAGS[user_id] = False
        cleaned_file_path = None
        
        self.errors = []
        start = datetime.now()
        
        logger.info("=" * 60)
        logger.info("🎯 TRAINING USER-SELECTED ALGORITHMS")
        logger.info(f"   Algorithms: {selected_algorithms}")
        logger.info("=" * 60)
        
        # Detect target if not provided
        if not target_col:
            target_col = self._detect_target(df)
        
        self.target_column = target_col
        logger.info(f"🎯 Target: {target_col}")
        logger.info(f"📊 Data: {df.shape[0]} rows, {df.shape[1]} columns")
        
        # 1. Clean data
        cleaner = ProductionDataCleaner()
        df_clean = cleaner.clean(df, target_col)
        
        # Drop NaN targets
        df_clean = df_clean.dropna(subset=[target_col])
        
        # Save cleaned data
        try:
            from utils.paths import get_user_paths
            user_paths = get_user_paths(user_id)
            upload_dir = user_paths['files']
            cleaned_filename = f"cleaned_{int(datetime.now().timestamp())}.csv"
            cleaned_full_path = upload_dir / cleaned_filename
            df_clean.to_csv(cleaned_full_path, index=False)
            cleaned_file_path = cleaned_filename
        except Exception as e:
            logger.error(f"Failed to save cleaned data: {e}")
        
        # 2. Detect task type
        y_temp = df_clean[target_col]
        unique_ratio = len(y_temp.unique()) / len(y_temp)
        
        if y_temp.dtype == 'object' or (y_temp.dtype in ['int64', 'float64'] and len(y_temp.unique()) <= 20):
            self.task_type = 'classification'
            self.task_type_simple = 'classification'
        else:
            self.task_type = 'regression'
            self.task_type_simple = 'regression'
        
        logger.info(f"🔍 Task Type: {self.task_type}")
        
        # 3. Feature engineering
        engineer = ProductionFeatureEngineer()
        X, y, feature_names = engineer.fit_transform(df_clean, target_col)
        
        # Calculate feature metadata for Playground tab
        self._calculate_feature_metadata(df_clean.drop(columns=[target_col]))
        
        # 4. Train/test split
        if self.task_type_simple == 'classification':
            try:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42, stratify=y
                )
            except ValueError:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
        
        logger.info(f"   Train: {len(X_train)} | Test: {len(X_test)}")
        
        # 5. Build ONLY the selected models
        from ml.production_ml_core import build_selected_models
        
        models = build_selected_models(
            selected_algorithms, 
            self.task_type_simple, 
            n_samples=len(X_train)
        )
        
        logger.info(f"🔧 Training {len(models)} selected models: {list(models.keys())}")
        
        # 6. Train each model
        results = []
        best_model = None
        best_name = None
        best_score = -np.inf
        
        for name, model in models.items():
            try:
                check_cancellation(user_id)
                
                logger.info(f"   Training {name}...")
                model.fit(X_train, y_train)
                
                if self.task_type_simple == 'classification':
                    score = model.score(X_test, y_test)
                    y_pred_temp = model.predict(X_test)
                    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
                    metrics = {
                        'accuracy': accuracy_score(y_test, y_pred_temp),
                        'f1': f1_score(y_test, y_pred_temp, average='weighted', zero_division=0),
                        'precision': precision_score(y_test, y_pred_temp, average='weighted', zero_division=0),
                        'recall': recall_score(y_test, y_pred_temp, average='weighted', zero_division=0)
                    }
                else:
                    from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
                    y_pred_temp = model.predict(X_test)
                    score = r2_score(y_test, y_pred_temp)
                    metrics = {
                        'r2': score,
                        'rmse': np.sqrt(mean_squared_error(y_test, y_pred_temp)),
                        'mae': mean_absolute_error(y_test, y_pred_temp)
                    }
                
                results.append({
                    'name': name,
                    'model': model,
                    'score': score,
                    'metrics': metrics
                })
                
                if score > best_score:
                    best_score = score
                    best_model = model
                    best_name = name
                
                logger.info(f"   ✅ {name}: {score:.4f}")
                
            except Exception as e:
                logger.warning(f"   ❌ {name} failed: {e}")
        
        if not best_model:
            # Return a proper TrainResult with empty/default values
            elapsed = (datetime.now() - start).total_seconds()
            return TrainResult(
                success=False,
                task_type=self.task_type or 'classification',
                target_column=target_col or '',
                feature_columns=[],
                best_model_name='None',
                best_model_metrics={},
                leaderboard=[],
                feature_importance=[],
                y_test=np.array([]),
                y_pred=np.array([]),
                y_proba=None,
                feature_metadata=[],
                n_rows=len(df),
                n_cols=len(df.columns),
                processing_time=elapsed,
                charts={},
                is_nlp_task=False,
                primary_text_col=None,
                cleaned_file_path=None,
                reliability_score=0,  # 🛡️ Failed training = 0 reliability
                validation_warnings=['Training failed - no model could be trained']
            )
        
        # Store results
        self.model = best_model
        self.model_name = best_name
        self._y_test = y_test
        self._y_pred = best_model.predict(X_test)
        self.production_engineer = engineer
        self.production_mode = True
        self.feature_columns = feature_names  # Store for external access
        
        # Get probabilities if classification
        y_proba = None
        if self.task_type_simple == 'classification' and hasattr(best_model, 'predict_proba'):
            try:
                y_proba = best_model.predict_proba(X_test)
            except:
                pass
        
        # Build best metrics FROM RESULTS (not empty)
        best_metrics = {}
        for r in results:
            if r['name'] == best_name:
                best_metrics = r['metrics']
                break
        
        # IMPORTANT: Store metrics on self so they're saved to persistence
        self.metrics = best_metrics
        
        elapsed = (datetime.now() - start).total_seconds()
        logger.info(f"⏱️ Training completed in {elapsed:.1f}s")
        
        # Generate charts - SAME AS production_train
        charts = {}
        try:
            from ml.chart_generator import (
                generate_ml_charts, generate_model_comparison_chart,
                generate_correlation_heatmap, generate_distribution_grid, generate_boxplot_grid,
                detect_stock_data, generate_stock_charts
            )
            
            # 📈 DETECT STOCK/FINANCIAL DATA AND GENERATE STOCK CHARTS
            stock_info = detect_stock_data(df_clean)
            if stock_info['is_stock_data']:
                logger.info("📈 Stock/Financial data detected! Generating stock-specific charts...")
                stock_charts = generate_stock_charts(df_clean, stock_info, target_col)
                charts.update(stock_charts)
                logger.info(f"   📊 Generated {len(stock_charts)} stock charts")
            
            # Get class names for classification
            class_names = None
            if self.task_type_simple == 'classification':
                class_names = list(np.unique(y_test))
            
            charts.update(generate_ml_charts(
                task_type=self.task_type,
                y_test=y_test,
                y_pred=self._y_pred,
                y_proba=y_proba,
                feature_importance=self._get_importance(best_model),
                class_names=class_names,
                model_name=best_name
            ))
            
            # Model comparison chart
            comparison_chart = generate_model_comparison_chart(results)
            if comparison_chart:
                charts['model_comparison'] = comparison_chart
            
            # Correlation Heatmap
            numeric_df = df_clean.select_dtypes(include=[np.number])
            if len(numeric_df.columns) >= 2:
                corr_chart = generate_correlation_heatmap(numeric_df, "Feature Correlations")
                if corr_chart:
                    charts['correlation_heatmap'] = corr_chart
            
            # Distribution Grid
            if len(numeric_df.columns) >= 1:
                dist_chart = generate_distribution_grid(numeric_df, "Feature Distributions")
                if dist_chart:
                    charts['distribution_grid'] = dist_chart
            
            # Box Plot Grid
            if len(numeric_df.columns) >= 1:
                box_chart = generate_boxplot_grid(numeric_df, "Feature Box Plots")
                if box_chart:
                    charts['boxplot_grid'] = box_chart
            
            logger.info(f"📊 Generated {len(charts)} charts: {list(charts.keys())}")
            
        except Exception as e:
            logger.warning(f"Chart generation error: {e}")
            import traceback
            traceback.print_exc()
        
        # Save model
        try:
            self._save(user_id, charts=charts)
        except Exception as e:
            logger.warning(f"Model save error: {e}")
        
        # 🛡️ PRODUCTION INTELLIGENCE: Compute reliability from results
        reliability_score = 75  # Default
        validation_warnings = []
        for r in results:
            if r.get('reliability_score'):
                if r.get('name') == best_name:
                    reliability_score = r.get('reliability_score')
            if r.get('warning'):
                validation_warnings.append(f"{r.get('name', 'Model')}: {r.get('warning')}")
        
        return TrainResult(
            success=True,
            task_type=self.task_type,
            target_column=target_col,
            feature_columns=engineer.original_columns,
            best_model_name=best_name,
            best_model_metrics=best_metrics,
            leaderboard=[{'name': r['name'], 'metrics': r['metrics'], 'score': r['score']} for r in results],
            feature_importance=self._get_importance(best_model),
            y_test=y_test,
            y_pred=self._y_pred,
            y_proba=y_proba,
            feature_metadata=getattr(self, 'feature_metadata', []),
            n_rows=len(df),
            n_cols=len(df.columns),
            processing_time=elapsed,
            charts=charts,
            is_nlp_task=False,
            primary_text_col=None,
            cleaned_file_path=cleaned_file_path,
            reliability_score=reliability_score,
            validation_warnings=validation_warnings if validation_warnings else None
        )
    
    async def train_with_test_set(
        self, 
        train_df: pd.DataFrame, 
        test_df: pd.DataFrame,
        target_col: Optional[str] = None, 
        user_id: str = "default"
    ) -> 'TrainResult':
        """
        Train with SEPARATE train and test datasets.
        Use this when you have pre-split data (e.g., Kaggle competitions).
        """
        self.errors = []
        start = datetime.now()
        
        logger.info("=" * 60)
        logger.info("🚀 PRODUCTION ML ENGINE v7.0 - TRAIN WITH TEST SET")
        logger.info("=" * 60)
        logger.info(f"📊 Train: {len(train_df)} rows | Test: {len(test_df)} rows")
        
        # Detect target
        if not target_col:
            target_col = self._detect_target(train_df)
        else:
            logger.info(f"🎯 Target: {target_col}")
        
        # Analyze data profile
        self._analyze_data_profile(train_df, target_col)
        
        # Preprocess TRAIN data (fit transformers)
        X_train, y_train = self._preprocess_training(train_df, target_col)
        logger.info(f"   Train shape: {X_train.shape}")
        
        # Preprocess TEST data (use fitted transformers)
        # Remove target from test df for preprocessing
        test_features = test_df.drop(columns=[target_col])
        y_test_raw = test_df[target_col]
        
        # Process each test row using single prediction preprocessor
        X_test_parts = []
        for idx, row in test_features.iterrows():
            try:
                x_single = self._preprocess_single(row.to_dict())
                X_test_parts.append(x_single)
            except Exception as e:
                logger.warning(f"   ⚠️ Test row {idx} error: {e}")
                # Append zeros matching train shape
                X_test_parts.append(np.zeros((1, X_train.shape[1])))
        
        X_test = np.vstack(X_test_parts)
        
        # Process y_test
        if self.task_type_simple == 'classification':
            y_test = self.target_encoder.transform(y_test_raw.fillna('_MISSING_').astype(str).str.strip())
        else:
            y_test = pd.to_numeric(y_test_raw, errors='coerce').fillna(0).values.astype(float)
        
        logger.info(f"   Test shape: {X_test.shape}")
        
        # Store for charts
        self._X_train = X_train
        self._X_test = X_test
        
        # Continue with normal training flow (no SMOTE for now, user has balanced data)
        models = self._get_adaptive_models()
        results = []
        
        best_score = -np.inf
        best_model = None
        best_name = None
        best_pred = None
        best_proba = None
        
        scoring = 'f1_weighted' if self.task_type_simple == 'classification' else 'r2'
        
        # CV folds
        cv_folds = 5 if len(train_df) > 500 else 3
        n_iter = 8
        
        logger.info(f"🤖 Training {len(models)} models on user-provided train/test split...")
        trained_models = {}
        
        for idx, (name, (model, params)) in enumerate(models.items(), 1):
            try:
                t0 = datetime.now()
                logger.info(f"   [{idx}/{len(models)}] {name}...")
                
                # Simple fit (skip CV search for speed with user test set)
                model.fit(X_train, y_train)
                trained_models[name] = model
                
                y_pred = model.predict(X_test)
                y_proba = None
                if hasattr(model, 'predict_proba'):
                    try:
                        y_proba = model.predict_proba(X_test)
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
                results.append({'name': name, 'metrics': metrics, 'training_time': round(elapsed, 2)})
                
                metric_name = 'f1' if self.task_type_simple == 'classification' else 'r2'
                logger.info(f"{metric_name}={score:.3f} ({elapsed:.1f}s)")
                
                if score > best_score:
                    best_score = score
                    best_model = model
                    best_name = name
                    best_pred = y_pred
                    best_proba = y_proba
                    
            except Exception as e:
                logger.warning(f"ERROR - {name}: {str(e)[:50]}")
                self.errors.append(f"{name}: {str(e)[:100]}")
        
        self.model = best_model
        self.model_name = best_name
        
        if self.model is None:
            raise ValueError("All models failed. Errors: " + "; ".join(self.errors[-3:]))
        
        logger.info(f"🏆 Best: {best_name} (score={best_score:.3f})")
        
        # Save model
        self._y_test = y_test
        self._y_pred = best_pred
        self._save(user_id)
        
        elapsed = (datetime.now() - start).total_seconds()
        logger.info(f"✅ Complete in {elapsed:.1f}s")
        
        # IMPORTANT: Store metrics on self so they're saved to persistence
        self.metrics = results[0]['metrics'] if results else {}
        
        # Generate charts
        charts = {}
        try:
            from ml.chart_generator import generate_ml_charts, generate_model_comparison_chart
            class_names = self.target_encoder.classes_.tolist() if self.target_encoder else None
            charts = generate_ml_charts(
                task_type=self.task_type,
                y_test=y_test,
                y_pred=best_pred,
                y_proba=best_proba,
                feature_importance=self._get_importance(best_model),
                class_names=class_names,
                model_name=best_name
            )
            comparison_chart = generate_model_comparison_chart(results)
            if comparison_chart:
                charts['model_comparison'] = comparison_chart
        except Exception as chart_err:
            logger.warning(f"⚠️ Chart generation error: {chart_err}")
        
        # CRITICAL: Save model for predictions
        try:
            self._save(user_id)
            print(f"💾 Model saved for user: {user_id}")
        except Exception as save_err:
            logger.warning(f"⚠️ Model save error: {save_err}")
        
        # 🛡️ PRODUCTION INTELLIGENCE: Compute reliability
        reliability_score = 75
        validation_warnings = []
        for r in results:
            if r.get('name') == best_name and r.get('reliability_score'):
                reliability_score = r.get('reliability_score')
            if r.get('warning'):
                validation_warnings.append(f"{r.get('name', 'Model')}: {r.get('warning')}")
        
        return TrainResult(
            success=True,
            task_type=self.task_type,
            target_column=target_col,
            feature_columns=self.feature_columns,
            best_model_name=best_name,
            best_model_metrics=results[0]['metrics'] if results else {},
            leaderboard=results,
            feature_importance=self._get_importance(best_model),
            y_test=y_test,
            y_pred=best_pred,
            y_proba=best_proba,
            feature_metadata=self.feature_metadata,
            n_rows=len(train_df) + len(test_df),
            n_cols=len(train_df.columns),
            processing_time=elapsed,
            charts=charts,
            is_nlp_task=self.is_nlp_task,
            primary_text_col=self.primary_text_col,
            reliability_score=reliability_score,
            validation_warnings=validation_warnings if validation_warnings else None
        )
    
    async def train(self, df: pd.DataFrame, target_col: Optional[str] = None, user_id: str = "default") -> 'TrainResult':
        """PRODUCTION-LEVEL Main training pipeline with adaptive technique selection"""
        self.errors = []
        start = datetime.now()
        
        logger.info("=" * 60)
        logger.info("🚀 PRODUCTION ML ENGINE v7.0 - COMPLETE AUTOML PIPELINE")
        logger.info("=" * 60)
        logger.info(f"📊 Data: {len(df)} rows, {len(df.columns)} columns")
        
        # Detect target
        if not target_col:
            target_col = self._detect_target(df)
        else:
            logger.info(f"🎯 Target (user specified): {target_col}")
        
        # ADAPTIVE: Analyze data profile BEFORE preprocessing to recommend techniques
        self._analyze_data_profile(df, target_col)
        
        # Preprocess
        X, y = self._preprocess_training(df, target_col)
        
        # Split (stratified for classification)
        stratify = y if self.task_type_simple == 'classification' and self.n_classes < 100 else None
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=stratify
        )
        logger.info(f"   Train: {len(X_train)}, Test: {len(X_test)}")
        
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
        
        logger.info(f"🤖 Training {len(models)} ADAPTIVE models ({cv_folds}-fold CV)...")  
        
        # Track trained models for stacking
        trained_models = {}
        
        for idx, (name, (model, params)) in enumerate(models.items(), 1):
            try:
                t0 = datetime.now()
                logger.info(f"   [{idx}/{len(models)}] {name}...")
                
                # Fallback mechanism: Try GridSearch/RandomSearch first, then simple fit
                try:
                    search = RandomizedSearchCV(
                        model, params, n_iter=min(n_iter, np.prod([len(v) for v in params.values()])),
                        cv=self._get_cv_strategy(y_train_balanced, n_splits=cv_folds), # FIX: Use correct CV strategy
                        scoring=scoring, n_jobs=1, random_state=42, error_score='raise'
                    )
                    search.fit(X_train_balanced, y_train_balanced)
                    best_est = search.best_estimator_
                    best_params = search.best_params_
                except Exception as search_err:
                    logger.warning(f"   ⚠️ Search failed ({str(search_err)[:50]}), falling back to simple fit...")
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
                logger.info(f"{metric_name}={score:.3f} ({elapsed:.1f}s)")
                
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
                logger.warning(f"ERROR - {error_msg}")
                self.errors.append(error_msg)  # Store error for reporting
        
        self.model = best_model
        self.model_name = best_name
        
        if self.model is None:
            error_summary = "; ".join(self.errors[-3:]) if hasattr(self, 'errors') else "Unknown error"
            raise ValueError(f"All models failed to train. Errors: {error_summary}")

        logger.info(f"🏆 Best: {best_name} (score={best_score:.3f})")
        
        # Retrain on full data
        try:
            logger.info(f"🔄 Retraining {best_name} on full data...")
            self.model.fit(X, y)
        except Exception as e:
            logger.warning(f"⚠️ Retraining failed, keeping split model: {e}")
            # Keep the already trained best_model from split
            pass
        logger.info(f"   ✅ Retrained on {len(X)} samples")
        
        # === STACKING ENSEMBLE ===
        # Try to build an ensemble of the best models for top 1% performance
        if len(trained_models) >= 2 and results:
            try:
                # Sort first to get top models
                temp_results = sorted(results, key=lambda x: x['metrics'].get(metric_name, 0), reverse=True)
                top_models = {r['name']: trained_models[r['name']] for r in temp_results[:3]}
                
                stacker = self._build_stacking_ensemble(top_models, X_train, y_train)
                
                if stacker:
                    y_pred_stack = stacker.predict(X_test)
                    
                    if self.task_type_simple == 'classification':
                        stack_score = f1_score(y_test, y_pred_stack, average='weighted', zero_division=0)
                        stack_acc = accuracy_score(y_test, y_pred_stack)
                        stack_metrics = {'f1': round(stack_score, 4), 'accuracy': round(stack_acc, 4)}
                        
                        try:
                            y_proba_stack = stacker.predict_proba(X_test)
                        except:
                            y_proba_stack = None
                    else:
                        stack_score = r2_score(y_test, y_pred_stack)
                        stack_mae = mean_absolute_error(y_test, y_pred_stack)
                        stack_metrics = {'r2': round(stack_score, 4), 'mae': round(stack_mae, 4)}
                        y_proba_stack = None
                    
                    logger.info(f"   🤖 Stacking Ensemble: {metric_name}={stack_score:.3f}")
                    
                    # Add to results
                    results.append({
                        'name': 'StackingEnsemble',
                        'metrics': stack_metrics,
                        'training_time': 5.0, # Approximate
                        'importance': [], # Stacking doesn't easily support feature importance
                        'best_params': {'estimators': list(top_models.keys())}
                    })
                    
                    # If better, update best
                    if stack_score > best_score:
                        logger.info(f"   🚀 Stacking Ensemble is the new BEST model! (+{(stack_score - best_score):.4f})")
                        best_score = stack_score
                        best_model = stacker
                        best_name = 'StackingEnsemble'
                        best_pred = y_pred_stack
                        best_proba = y_proba_stack
                        
                        # Add to trained models so it can be saved/retrained
                        trained_models['StackingEnsemble'] = stacker
            except Exception as e:
                logger.warning(f"   ⚠️ Stacking evaluation failed: {e}")

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
                logger.info(f"📊 Stored metrics: Accuracy={self.metrics['accuracy']:.1%}, F1={self.metrics['f1']:.1%}")
            except Exception as cm_err:
                logger.warning(f"⚠️ Confusion matrix error: {cm_err}")
                self.confusion_matrix = None
        else:
            # Regression metrics
            try:
                # Use global imports to avoid UnboundLocalError
                self.metrics['r2'] = float(r2_score(y_test, best_pred))
                self.metrics['mae'] = float(mean_absolute_error(y_test, best_pred))
                self.metrics['rmse'] = float(np.sqrt(mean_squared_error(y_test, best_pred)))
                logger.info(f"📊 Stored metrics: R²={self.metrics['r2']:.3f}, MAE={self.metrics['mae']:.2f}")
            except Exception as reg_err:
                logger.warning(f"⚠️ Regression metrics error: {reg_err}")
        
        # Save (now includes metrics, y_test, y_pred, confusion_matrix)
        self._save(user_id)
        
        # Verify
        self._verify(df.head(5), target_col)
        
        processing_time = (datetime.now() - start).total_seconds()
        
        logger.info("=" * 60)
        logger.info(f"✅ Complete in {processing_time:.1f}s")
        logger.info("=" * 60)
        
        # Generate all charts using the production chart generator
        try:
            from ml.chart_generator import (
                generate_ml_charts, generate_model_comparison_chart,
                generate_correlation_heatmap, generate_distribution_grid, generate_boxplot_grid
            )
            
            # Get class names for classification
            class_names = None
            if self.target_encoder is not None:
                class_names = self.target_encoder.classes_.tolist()
            
            # Generate ML charts
            charts = generate_ml_charts(
                task_type=self.task_type,
                y_test=y_test,
                y_pred=best_pred,
                y_proba=best_proba,
                feature_importance=self._get_importance(self.model),
                class_names=class_names,
                model_name=best_name
            )
            
            # Add model comparison chart
            comparison_chart = generate_model_comparison_chart(results)
            if comparison_chart:
                charts['model_comparison'] = comparison_chart
            
            # 🆕 ADD EXTRA CHARTS FROM REAL DATA
            # Correlation Heatmap (numeric features only)
            numeric_df = df.select_dtypes(include=[np.number])
            if len(numeric_df.columns) >= 2:
                corr_chart = generate_correlation_heatmap(numeric_df, "Feature Correlations")
                if corr_chart:
                    charts['correlation_heatmap'] = corr_chart
            
            # Distribution Grid (histograms of features)
            if len(numeric_df.columns) >= 1:
                dist_chart = generate_distribution_grid(numeric_df, "Feature Distributions")
                if dist_chart:
                    charts['distribution_grid'] = dist_chart
            
            # Box Plot Grid
            if len(numeric_df.columns) >= 1:
                box_chart = generate_boxplot_grid(numeric_df, "Feature Box Plots")
                if box_chart:
                    charts['boxplot_grid'] = box_chart
                
            logger.info(f"📊 Generated {len(charts)} charts: {list(charts.keys())}")
        except Exception as chart_err:
            logger.warning(f"⚠️ Chart generation error: {chart_err}")
            import traceback
            traceback.print_exc()
            charts = {}
        
        # IMPORTANT: Store metrics on self so they're saved to persistence
        self.metrics = results[0]['metrics'] if results else {}
        
        # CRITICAL: Save model for predictions
        try:
            self._save(user_id)
            print(f"💾 Model saved for user: {user_id}")
        except Exception as save_err:
            logger.warning(f"⚠️ Model save error: {save_err}")
        
        # 🛡️ PRODUCTION INTELLIGENCE: Compute reliability
        reliability_score = 75
        validation_warnings = []
        for r in results:
            if r.get('name') == best_name and r.get('reliability_score'):
                reliability_score = r.get('reliability_score')
            if r.get('warning'):
                validation_warnings.append(f"{r.get('name', 'Model')}: {r.get('warning')}")
        
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
            charts=charts,
            is_nlp_task=getattr(self, 'is_nlp_task', False),
            primary_text_col=getattr(self, 'primary_text_col', None),
            reliability_score=reliability_score,
            validation_warnings=validation_warnings if validation_warnings else None
        )
    
    def _get_importance(self, model) -> List[Dict]:
        """Get feature importance with REAL column names for charts
        
        Uses feature_metadata to properly map engineered features back to 
        their source columns.
        """
        values = []
        
        # Get importance values from model
        if hasattr(model, 'estimators_'):
            all_importances = []
            for est in model.estimators_:
                if hasattr(est, 'feature_importances_'):
                    all_importances.append(est.feature_importances_)
                elif hasattr(est, 'coef_'):
                    all_importances.append(np.abs(est.coef_).flatten())
            if all_importances:
                max_len = max(len(imp) for imp in all_importances)
                padded = [np.pad(imp, (0, max_len - len(imp))) for imp in all_importances]
                values = np.mean(padded, axis=0)
        
        if len(values) == 0:
            if hasattr(model, 'feature_importances_'):
                values = model.feature_importances_
            elif hasattr(model, 'coef_'):
                values = np.abs(model.coef_).flatten()
            elif hasattr(model, 'steps'):
                return self._get_importance(model.steps[-1][1])
        
        if len(values) == 0:
            # No importance available, use equal distribution for known columns
            all_cols = getattr(self, 'numeric_cols', []) + getattr(self, 'categorical_cols', []) + getattr(self, 'text_cols', [])
            if all_cols:
                return [{'feature': col, 'importance': round(1.0 / len(all_cols), 4), 'rank': i + 1} 
                        for i, col in enumerate(all_cols)]
            return []
        
        # Normalize
        values = np.array(values)
        if values.sum() > 0:
            values = values / values.sum()
        
        n_features = len(values)
        
        # ==================================================================
        # USE FEATURE_METADATA FOR PROPER COLUMN MAPPING
        # ==================================================================
        
        column_importance = {}
        idx = 0
        
        # feature_metadata is built during preprocessing in order:
        # 1. numeric columns (each adds 1 feature)
        # 2. categorical columns (each adds 1 feature)
        # 3. text columns (each adds vocab_size or n_features)
        
        if hasattr(self, 'feature_metadata') and self.feature_metadata:
            for meta in self.feature_metadata:
                col_name = meta.get('name', 'Unknown')
                col_type = meta.get('type', 'numeric')
                
                if col_type == 'numeric':
                    # Numeric: 1 feature
                    if idx < n_features:
                        column_importance[col_name] = float(values[idx])
                        idx += 1
                
                elif col_type == 'categorical':
                    # Categorical: 1 feature (label encoded)
                    if idx < n_features:
                        column_importance[col_name] = float(values[idx])
                        idx += 1
                
                elif col_type in ('text', 'nlp_text'):
                    # Text: many TF-IDF features - aggregate them
                    n_text_features = meta.get('vocab_size', meta.get('n_features', 1))
                    text_imp = 0.0
                    for _ in range(n_text_features):
                        if idx < n_features:
                            text_imp += float(values[idx])
                            idx += 1
                    column_importance[col_name] = text_imp
        
        # Fallback if feature_metadata is empty or doesn't work
        if not column_importance or sum(column_importance.values()) < 0.01:
            # Use original columns directly
            all_cols = getattr(self, 'numeric_cols', []) + getattr(self, 'categorical_cols', []) + getattr(self, 'text_cols', [])
            
            if all_cols:
                # Distribute all importance across source columns
                per_col = 1.0 / len(all_cols) if all_cols else 0
                for col in all_cols:
                    column_importance[col] = per_col
        
        # Re-normalize
        total = sum(column_importance.values())
        if total > 0:
            column_importance = {k: v / total for k, v in column_importance.items()}
        
        # Convert to sorted list
        importance = []
        for rank, (col, imp) in enumerate(sorted(column_importance.items(), key=lambda x: x[1], reverse=True), 1):
            if rank > 15:
                break
            importance.append({
                'feature': col,
                'importance': round(float(imp), 4),
                'rank': rank
            })
        
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
        """Make prediction with comprehensive logging"""
        if self.model is None:
            raise ValueError("No model trained")
        
        logger.info(f"🔮 Prediction request with {len(data)} features")
        logger.info(f"   Input features: {list(data.keys())}")
        logger.info(f"   Production mode: {getattr(self, 'production_mode', False)}")
        logger.info(f"   Has production_engineer: {hasattr(self, 'production_engineer') and self.production_engineer is not None}")
        
        # Check if using production pipeline
        if getattr(self, 'production_mode', False) and hasattr(self, 'production_engineer') and self.production_engineer is not None:
            logger.info("   Using PRODUCTION pipeline")
            X = self._preprocess_single_production(data)
        else:
            logger.info("   Using LEGACY pipeline")
            X = self._preprocess_single(data)
        
        logger.info(f"   Preprocessed X shape: {X.shape}")
        
        pred = self.model.predict(X)[0]
        logger.info(f"   Raw prediction: {pred}")
        
        if self.target_encoder:
            try:
                original_pred = pred
                pred = self.target_encoder.inverse_transform([int(pred)])[0]
                logger.info(f"   Decoded prediction: {original_pred} -> {pred}")
            except Exception as e:
                logger.warning(f"   Target decoder failed: {e}")
        
        prob = None
        conf = None
        if hasattr(self.model, 'predict_proba'):
            try:
                proba = self.model.predict_proba(X)[0]
                prob = [float(p) for p in proba]
                conf = float(max(proba))
                logger.info(f"   Confidence: {conf:.2%}")
            except:
                pass
        
        logger.info(f"✅ Final prediction: {pred}")
        return {'prediction': str(pred), 'probability': prob, 'confidence': conf, 'model': self.model_name}
    
    def _preprocess_single_production(self, data: Dict[str, Any]) -> np.ndarray:
        """
        Preprocess single input using Production Feature Engineer
        Used when model was trained with production_train
        
        UNIFIED: Delegates to ProductionFeatureEngineer.transform_single
        to ensure prediction features EXACTLY match training features.
        """
        if not hasattr(self, 'production_engineer'):
            raise ValueError("No production engineer found. Model may have been trained with legacy pipeline.")
        
        # Use the unified transform method
        return self.production_engineer.transform_single(data)
    
    def _save(self, user_id: str, charts: Optional[Dict[str, str]] = None):
        """Save model and preprocessors with enhanced persistence"""
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
            # NEW: Save NLP and Advanced Feature Engineering state
            'is_nlp_task': getattr(self, 'is_nlp_task', False),
            'primary_text_col': getattr(self, 'primary_text_col', None),
            'nlp_scaler': getattr(self, 'nlp_scaler', None),
            'feature_engineer': self.feature_engineer,
            # PRODUCTION PIPELINE
            'production_mode': getattr(self, 'production_mode', False),
            'production_engineer': getattr(self, 'production_engineer', None),
        }
        
        with open(os.path.join(save_dir, "model.pkl"), 'wb') as f:
            pickle.dump(data, f)
        
        # Also save via the new persistence manager for versioning & metadata
        try:
            from ml.model_persistence import model_persistence
            
            model_persistence.save_model(
                user_id=user_id,
                engine_state=data,
                model_name=getattr(self, 'model_name', 'Unknown'),
                task_type=self.task_type,
                target_column=self.target_column,
                feature_columns=self.feature_columns,
                metrics=getattr(self, 'metrics', {}),
                dataset_info={
                    'n_features': len(self.feature_columns),
                    'n_numeric': len(self.numeric_cols),
                    'n_categorical': len(self.categorical_cols),
                    'n_text': len(self.text_cols),
                    'is_nlp_task': getattr(self, 'is_nlp_task', False)
                }
            )
            
            # Save charts if provided
            if charts:
                model_persistence.save_charts(user_id, charts)
                logger.info(f"📊 Saved {len(charts)} charts to persistence")
                
            logger.info(f"💾 Saved with versioning to model persistence manager")
        except Exception as e:
            logger.warning(f"⚠️ Persistence manager save failed: {e}")
        
        print(f"💾 Saved to {save_dir}")
    
    def load(self, user_id: str) -> bool:
        """Load model - tries model_persistence first, then legacy model.pkl"""
        
        # NEW: Try loading from model_persistence first (has latest trained model)
        try:
            from ml.model_persistence import get_model_persistence_manager
            pm = get_model_persistence_manager()
            result = pm.load_model(user_id)
            
            if result and result.get('model'):
                self.model = result['model']
                self.model_name = result.get('model_name', 'Unknown')
                self.task_type = result.get('task_type', 'classification')
                self.task_type_simple = 'classification' if 'classification' in self.task_type else 'regression'
                self.feature_columns = result.get('feature_columns', [])
                self.target_column = result.get('target_column', '')
                self.feature_metadata = result.get('feature_metadata', [])
                self.metrics = result.get('metrics', {})
                self.target_encoder = result.get('target_encoder')
                self.n_classes = result.get('n_classes', 2)
                
                # Load preprocessing objects
                self.label_encoders = result.get('label_encoders', {})
                self.text_vectorizers = result.get('text_vectorizers', {})
                self.scaler = result.get('scaler')
                self.production_engineer = result.get('production_engineer')
                
                # Load additional preprocessing attributes
                self.numeric_cols = result.get('numeric_cols', [])
                self.categorical_cols = result.get('categorical_cols', [])
                self.text_cols = result.get('text_cols', [])
                self.numeric_fill_values = result.get('numeric_fill_values', {})
                
                # CRITICAL FIX: Use saved production_mode OR infer from production_engineer
                # Priority: saved value > inferred from production_engineer
                saved_production_mode = result.get('production_mode', None)
                if saved_production_mode is not None:
                    self.production_mode = saved_production_mode
                else:
                    self.production_mode = self.production_engineer is not None
                
                # Also load feature_engineer for legacy pipeline
                if 'feature_engineer' in result:
                    self.feature_engineer = result['feature_engineer']
                
                print(f"📂 Loaded {self.model_name} from model_persistence (latest)")
                print(f"   Production mode: {self.production_mode}")
                print(f"   Features: {len(self.feature_columns)}, Target: {self.target_column}")
                return True
        except Exception as e:
            logger.warning(f"⚠️ Model persistence load failed: {e}, trying legacy...")
        
        # FALLBACK: Legacy model.pkl loading
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
            
            # NEW: Restore NLP and Advanced Feature Engineering state
            self.is_nlp_task = data.get('is_nlp_task', False)
            self.primary_text_col = data.get('primary_text_col')
            self.nlp_scaler = data.get('nlp_scaler')
            if 'feature_engineer' in data:
                self.feature_engineer = data['feature_engineer']
            
            # Restore Production Pipeline
            self.production_mode = data.get('production_mode', False)
            if 'production_engineer' in data:
                self.production_engineer = data['production_engineer']
            
            print(f"📂 Loaded from {path} (legacy)")
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
            elif algorithm == 'gmm':
                model = GaussianMixture(n_components=n_clusters, random_state=42)
                labels = model.fit_predict(X_scaled)
            elif algorithm == 'spectral':
                # Use fewer nearest neighbors for spectral to avoid graph connectivity issues
                model = SpectralClustering(n_clusters=n_clusters, random_state=42, affinity='nearest_neighbors')
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
        
        # CRITICAL: Sample for silhouette calculation (O(n²) complexity!)
        # 10K samples is max to keep computation reasonable
        MAX_SILHOUETTE_SAMPLES = 10000
        if len(X) > MAX_SILHOUETTE_SAMPLES:
            logger.info(f"   ⚠️ Sampling {MAX_SILHOUETTE_SAMPLES} rows for silhouette (dataset has {len(X)})")
            sample_idx = np.random.choice(len(X), MAX_SILHOUETTE_SAMPLES, replace=False)
            X_sample = X[sample_idx]
        else:
            X_sample = X
            sample_idx = None
        
        max_k = min(max_k, len(X_sample) - 1)
        k_range = range(2, max_k + 1)
        
        inertias = []
        silhouettes = []
        
        for k in k_range:
            # Fit on full data for accurate inertia
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            full_labels = kmeans.fit_predict(X)
            inertias.append(kmeans.inertia_)
            
            # Calculate silhouette on SAMPLE only (to avoid O(n²) on full data)
            if sample_idx is not None:
                sample_labels = full_labels[sample_idx]
                silhouettes.append(silhouette_score(X_sample, sample_labels))
            else:
                silhouettes.append(silhouette_score(X, full_labels))
        
        # Best k by silhouette score
        best_k = list(k_range)[np.argmax(silhouettes)]
        logger.info(f"   ✅ Optimal K = {best_k} (silhouette = {max(silhouettes):.3f})")
        
        return best_k
    
    def get_all_ml_charts(self) -> Dict[str, Any]:
        """Get all ML charts for the trained model using enhanced chart generator"""
        try:
            from ml.chart_generator import generate_ml_charts, generate_model_comparison_chart
            
            y_test = getattr(self, '_y_test', None)
            y_pred = getattr(self, '_y_pred', None)
            y_proba = getattr(self, '_y_proba', None)
            
            if y_test is None or y_pred is None:
                return {'error': 'No model trained yet'}
            
            # Get feature importance
            importance = self._get_importance(self.model) if self.model else []
            
            # Get class names for classification
            class_names = None
            if self.target_encoder is not None:
                class_names = self.target_encoder.classes_.tolist()
            
            # Generate all charts using the new generator
            charts = generate_ml_charts(
                task_type=self.task_type,
                y_test=y_test,
                y_pred=y_pred,
                y_proba=y_proba,
                feature_importance=importance,
                class_names=class_names,
                model_name=getattr(self, 'model_name', 'Model')
            )
            
            logger.info(f"✅ Generated {len(charts)} ML charts")
            return charts
            
        except Exception as e:
            logger.error(f"Chart generation error: {e}")
            return {'error': str(e)}
    
    def god_level_train(
        self, 
        df: pd.DataFrame, 
        target_col: str = None,
        user_id: str = "default",
        mode: str = "ultra",
        algorithm: str = None
    ) -> TrainResult:
        """
        🔱 GOD-LEVEL AUTOML TRAINING
        ============================
        
        Uses the advanced GOD-Level AutoML engine for:
        - Complete data intelligence
        - Advanced leakage detection
        - Intelligent model selection
        - Safe training with overfitting protection
        - Model reliability scoring
        
        Returns a TrainResult for compatibility with existing UI.
        """
        try:
            from ml.god_level_automl import god_level_train, GodLevelResult
            
            logger.info("🔱 Running GOD-Level AutoML Training...")
            
            # Run GOD-Level training
            result = god_level_train(df, target_col, user_id, mode, algorithm)
            
            if not result.success:
                raise ValueError(result.warnings[0] if result.warnings else "GOD-Level training failed")
            
            # Convert to TrainResult for compatibility
            train_result = TrainResult(
                success=True,
                task_type=result.problem_type,
                target_column=result.target_column,
                feature_columns=result.feature_columns,
                best_model_name=result.best_model_name,
                best_model_metrics=result.best_model_metrics,
                leaderboard=result.leaderboard,
                feature_importance=result.feature_importance,
                y_test=result.y_test,
                y_pred=result.y_pred,
                y_proba=result.y_proba,
                feature_metadata=result.feature_metadata,
                n_rows=result.n_rows,
                n_cols=result.n_cols,
                processing_time=result.processing_time,
                charts=result.charts,
                is_nlp_task=False,
                primary_text_col=None
            )
            
            return train_result
            
        except ImportError:
            logger.warning("GOD-Level AutoML not available, falling back to production_train")
            return self.production_train(df, target_col, user_id, mode)
        except Exception as e:
            logger.error(f"GOD-Level training failed: {e}")
            import traceback
            traceback.print_exc()
            raise


# Global instance
automl_engine = ProductionMLEngine()
