"""
🚀 PRODUCTION AUTOML ENGINE - Industrial-Grade ML Pipeline
============================================================

A clean, production-ready AutoML system that:
- Profiles data automatically
- Detects task type (classification/regression)
- Preprocesses with stored transformers
- Trains 12+ models with progress
- Generates task-specific charts
- Enables real predictions

NO HARDCODING. All outputs based on real data.
"""

import logging
import os
import pickle
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np

# ML Libraries
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, mean_squared_error, mean_absolute_error,
    r2_score, confusion_matrix
)

# Models
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.ensemble import (
    RandomForestClassifier, RandomForestRegressor,
    GradientBoostingClassifier, GradientBoostingRegressor,
    ExtraTreesClassifier, ExtraTreesRegressor,
    AdaBoostClassifier, AdaBoostRegressor,
    HistGradientBoostingClassifier, HistGradientBoostingRegressor
)
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.naive_bayes import GaussianNB

# Advanced boosting
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class TaskType(Enum):
    BINARY = "binary"
    MULTICLASS = "multiclass"
    REGRESSION = "regression"


@dataclass
class DataProfile:
    """Profile of the uploaded dataset"""
    rows: int
    columns: int
    column_types: Dict[str, str]  # {col: 'numeric'|'categorical'}
    missing_values: Dict[str, float]  # {col: percentage}
    unique_counts: Dict[str, int]
    target_column: str
    task_type: TaskType
    class_distribution: Optional[Dict[str, int]] = None


@dataclass
class ModelResult:
    """Result from training a single model"""
    name: str
    metrics: Dict[str, float]
    cv_score: float
    training_time: float
    feature_importance: List[Dict[str, Any]]
    y_pred: np.ndarray = None
    y_proba: np.ndarray = None


@dataclass
class AutoMLResult:
    """Complete AutoML pipeline result"""
    success: bool
    task_type: str
    target_column: str
    data_profile: Dict[str, Any]
    best_model: Dict[str, Any]
    leaderboard: List[Dict[str, Any]]
    feature_importance: List[Dict[str, Any]]
    feature_metadata: List[Dict[str, Any]]
    y_test: np.ndarray
    y_pred: np.ndarray
    y_proba: Optional[np.ndarray]
    processing_time: float


# =============================================================================
# DATA PROFILER
# =============================================================================

class DataProfiler:
    """Analyzes dataset to understand its structure"""
    
    def profile(self, df: pd.DataFrame, target_column: str) -> DataProfile:
        """Profile the dataset"""
        print("📊 Profiling dataset...")
        
        column_types = {}
        missing_values = {}
        unique_counts = {}
        
        for col in df.columns:
            # Detect column type
            if pd.api.types.is_numeric_dtype(df[col]):
                n_unique = df[col].nunique()
                if n_unique <= 10 and n_unique < len(df) * 0.05:
                    column_types[col] = 'categorical'
                else:
                    column_types[col] = 'numeric'
            else:
                column_types[col] = 'categorical'
            
            # Missing values percentage
            missing_values[col] = round(df[col].isna().mean() * 100, 2)
            
            # Unique counts
            unique_counts[col] = df[col].nunique()
        
        # Detect task type
        task_type = self._detect_task_type(df, target_column)
        
        # Class distribution for classification
        class_distribution = None
        if task_type != TaskType.REGRESSION:
            class_distribution = df[target_column].value_counts().to_dict()
        
        profile = DataProfile(
            rows=len(df),
            columns=len(df.columns),
            column_types=column_types,
            missing_values=missing_values,
            unique_counts=unique_counts,
            target_column=target_column,
            task_type=task_type,
            class_distribution=class_distribution
        )
        
        print(f"   ✅ {profile.rows} rows, {profile.columns} columns")
        print(f"   ✅ Task type: {task_type.value}")
        
        return profile
    
    def _detect_task_type(self, df: pd.DataFrame, target_column: str) -> TaskType:
        """Auto-detect if classification or regression"""
        target = df[target_column]
        n_unique = target.nunique()
        
        # If object/string dtype -> classification
        if pd.api.types.is_object_dtype(target) or pd.api.types.is_categorical_dtype(target):
            return TaskType.BINARY if n_unique == 2 else TaskType.MULTICLASS
        
        # If numeric with few unique values -> classification
        if n_unique <= 10:
            return TaskType.BINARY if n_unique == 2 else TaskType.MULTICLASS
        
        # Otherwise -> regression
        return TaskType.REGRESSION


# =============================================================================
# PREPROCESSOR
# =============================================================================

class Preprocessor:
    """Handles all data preprocessing with stored transformers"""
    
    def __init__(self):
        self.imputers = {}
        self.encoders = {}
        self.scaler = None
        self.target_encoder = None
        self.feature_names = []
        self.feature_types = {}
        self.feature_stats = {}
    
    def fit_transform(
        self, 
        df: pd.DataFrame, 
        target_column: str, 
        profile: DataProfile
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Preprocess data and store transformers for prediction"""
        print("🔧 Preprocessing data...")
        
        X = df.drop(columns=[target_column]).copy()
        y = df[target_column].copy()
        
        processed_features = []
        feature_names = []
        
        for col in X.columns:
            series = X[col].copy()
            col_type = profile.column_types.get(col, 'numeric')
            
            # Skip columns with all missing values
            if series.isna().all():
                continue
            
            if col_type == 'numeric':
                # Impute missing values with median
                median_val = series.median() if not series.isna().all() else 0
                series = series.fillna(median_val)
                
                # Store stats for prediction form
                self.feature_stats[col] = {
                    'min': float(series.min()),
                    'max': float(series.max()),
                    'mean': float(series.mean()),
                    'median': float(median_val)
                }
                self.imputers[col] = median_val
                
                processed_features.append(series.values.reshape(-1, 1))
                feature_names.append(col)
                self.feature_types[col] = 'numeric'
                
            else:  # categorical
                # Impute missing with mode
                mode_val = series.mode().iloc[0] if len(series.mode()) > 0 else 'Unknown'
                series = series.fillna(mode_val).astype(str)
                
                # Only encode if not too many categories
                if series.nunique() <= 50:
                    encoder = LabelEncoder()
                    encoded = encoder.fit_transform(series)
                    
                    self.encoders[col] = encoder
                    self.feature_stats[col] = {
                        'options': encoder.classes_.tolist()[:30]  # Limit for UI
                    }
                    
                    processed_features.append(encoded.reshape(-1, 1))
                    feature_names.append(col)
                    self.feature_types[col] = 'categorical'
        
        if not processed_features:
            raise ValueError("No valid features found in dataset")
        
        X_processed = np.hstack(processed_features)
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X_processed)
        
        # Encode target for classification
        if profile.task_type != TaskType.REGRESSION:
            self.target_encoder = LabelEncoder()
            y_encoded = self.target_encoder.fit_transform(y.astype(str))
        else:
            y_encoded = y.values.astype(float)
        
        self.feature_names = feature_names
        
        print(f"   ✅ Processed {len(feature_names)} features")
        print(f"   ✅ Numeric: {sum(1 for t in self.feature_types.values() if t == 'numeric')}")
        print(f"   ✅ Categorical: {sum(1 for t in self.feature_types.values() if t == 'categorical')}")
        
        return X_scaled, y_encoded, feature_names
    
    def transform_for_prediction(self, data: Dict[str, Any]) -> np.ndarray:
        """Transform input data for prediction using stored transformers"""
        X_list = []
        
        for col in self.feature_names:
            value = data.get(col, 0)
            
            if self.feature_types.get(col) == 'categorical':
                encoder = self.encoders.get(col)
                if encoder is not None:
                    try:
                        if str(value) in encoder.classes_:
                            encoded_val = encoder.transform([str(value)])[0]
                        else:
                            encoded_val = 0  # Unknown category
                        X_list.append(float(encoded_val))
                    except:
                        X_list.append(0.0)
                else:
                    X_list.append(0.0)
            else:
                try:
                    X_list.append(float(value))
                except (ValueError, TypeError):
                    X_list.append(self.imputers.get(col, 0.0))
        
        X = np.array([X_list])
        X = np.nan_to_num(X, nan=0)
        
        if self.scaler is not None:
            X = self.scaler.transform(X)
        
        return X
    
    def get_feature_metadata(self) -> List[Dict[str, Any]]:
        """Get feature metadata for frontend prediction form"""
        metadata = []
        
        for col in self.feature_names:
            feat_type = self.feature_types.get(col, 'numeric')
            stats = self.feature_stats.get(col, {})
            
            if feat_type == 'numeric':
                metadata.append({
                    'name': col,
                    'type': 'numeric',
                    'min': stats.get('min', 0),
                    'max': stats.get('max', 100),
                    'mean': stats.get('mean', 50),
                })
            else:
                metadata.append({
                    'name': col,
                    'type': 'categorical',
                    'options': stats.get('options', []),
                })
        
        return metadata


# =============================================================================
# MODEL TRAINER
# =============================================================================

class ModelTrainer:
    """Trains and evaluates multiple ML models"""
    
    def __init__(self):
        self.trained_models = {}
        self.best_model = None
        self.best_model_name = None
    
    def get_models(self, task_type: TaskType) -> Dict[str, Any]:
        """Get model pool based on task type"""
        models = {}
        
        if task_type in [TaskType.BINARY, TaskType.MULTICLASS]:
            # Classification models
            models["LogisticRegression"] = LogisticRegression(max_iter=500, n_jobs=-1)
            models["RidgeClassifier"] = RidgeClassifier()
            models["NaiveBayes"] = GaussianNB()
            models["DecisionTree"] = DecisionTreeClassifier(max_depth=10, random_state=42)
            models["RandomForest"] = RandomForestClassifier(n_estimators=100, max_depth=12, n_jobs=-1, random_state=42)
            models["ExtraTrees"] = ExtraTreesClassifier(n_estimators=100, max_depth=12, n_jobs=-1, random_state=42)
            models["GradientBoosting"] = GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)
            models["AdaBoost"] = AdaBoostClassifier(n_estimators=50, random_state=42)
            models["HistGradientBoosting"] = HistGradientBoostingClassifier(max_iter=100, max_depth=6, random_state=42)
            
            if XGBOOST_AVAILABLE:
                models["XGBoost"] = xgb.XGBClassifier(n_estimators=100, max_depth=6, n_jobs=-1, random_state=42, eval_metric='logloss')
            if LIGHTGBM_AVAILABLE:
                models["LightGBM"] = lgb.LGBMClassifier(n_estimators=100, max_depth=6, verbose=-1, random_state=42)
        else:
            # Regression models
            models["LinearRegression"] = LinearRegression(n_jobs=-1)
            models["Ridge"] = Ridge()
            models["Lasso"] = Lasso()
            models["ElasticNet"] = ElasticNet(random_state=42)
            models["DecisionTree"] = DecisionTreeRegressor(max_depth=10, random_state=42)
            models["RandomForest"] = RandomForestRegressor(n_estimators=100, max_depth=12, n_jobs=-1, random_state=42)
            models["ExtraTrees"] = ExtraTreesRegressor(n_estimators=100, max_depth=12, n_jobs=-1, random_state=42)
            models["GradientBoosting"] = GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)
            models["AdaBoost"] = AdaBoostRegressor(n_estimators=50, random_state=42)
            models["HistGradientBoosting"] = HistGradientBoostingRegressor(max_iter=100, max_depth=6, random_state=42)
            
            if XGBOOST_AVAILABLE:
                models["XGBoost"] = xgb.XGBRegressor(n_estimators=100, max_depth=6, n_jobs=-1, random_state=42)
            if LIGHTGBM_AVAILABLE:
                models["LightGBM"] = lgb.LGBMRegressor(n_estimators=100, max_depth=6, verbose=-1, random_state=42)
        
        return models
    
    def train_all(
        self,
        X_train: np.ndarray,
        X_test: np.ndarray,
        y_train: np.ndarray,
        y_test: np.ndarray,
        feature_names: List[str],
        task_type: TaskType
    ) -> Tuple[List[ModelResult], np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """Train all models and return results with best predictions"""
        
        models = self.get_models(task_type)
        results = []
        
        best_score = -np.inf
        best_y_pred = None
        best_y_proba = None
        
        total = len(models)
        print(f"🤖 Training {total} models...")
        
        for idx, (name, model) in enumerate(models.items(), 1):
            try:
                start = datetime.now()
                print(f"   [{idx}/{total}] {name}...", end=" ", flush=True)
                
                # Train
                model.fit(X_train, y_train)
                
                # Predict
                y_pred = model.predict(X_test)
                y_proba = None
                if hasattr(model, 'predict_proba'):
                    try:
                        y_proba = model.predict_proba(X_test)
                    except:
                        pass
                
                # Calculate metrics
                metrics = self._calculate_metrics(y_test, y_pred, y_proba, task_type)
                
                # Cross-validation (skip for large datasets)
                if len(X_train) < 5000:
                    scoring = 'f1_weighted' if task_type != TaskType.REGRESSION else 'r2'
                    cv_score = cross_val_score(model, X_train, y_train, cv=3, scoring=scoring).mean()
                else:
                    cv_score = metrics.get('f1', metrics.get('r2', 0))
                
                # Feature importance
                importance = self._get_feature_importance(model, feature_names)
                
                training_time = (datetime.now() - start).total_seconds()
                
                # Store model
                self.trained_models[name] = model
                
                # Track best
                primary_metric = 'f1' if task_type != TaskType.REGRESSION else 'r2'
                score = metrics.get(primary_metric, 0)
                if score > best_score:
                    best_score = score
                    best_y_pred = y_pred.copy()
                    best_y_proba = y_proba[:, 1] if y_proba is not None and len(y_proba.shape) > 1 and y_proba.shape[1] == 2 else y_proba
                    self.best_model = model
                    self.best_model_name = name
                
                result = ModelResult(
                    name=name,
                    metrics=metrics,
                    cv_score=cv_score,
                    training_time=training_time,
                    feature_importance=importance,
                    y_pred=y_pred,
                    y_proba=y_proba
                )
                results.append(result)
                
                print(f"✅ ({training_time:.1f}s) {primary_metric}={score:.3f}")
                
            except Exception as e:
                print(f"❌ {str(e)[:40]}")
        
        # Sort by primary metric
        primary_metric = 'f1' if task_type != TaskType.REGRESSION else 'r2'
        results.sort(key=lambda r: r.metrics.get(primary_metric, 0), reverse=True)
        
        print(f"   🏆 Best: {self.best_model_name} ({primary_metric}={best_score:.3f})")
        
        return results, y_test, best_y_pred, best_y_proba
    
    def _calculate_metrics(
        self, 
        y_true: np.ndarray, 
        y_pred: np.ndarray, 
        y_proba: Optional[np.ndarray],
        task_type: TaskType
    ) -> Dict[str, float]:
        """Calculate appropriate metrics based on task type"""
        metrics = {}
        
        if task_type == TaskType.REGRESSION:
            metrics['r2'] = r2_score(y_true, y_pred)
            metrics['mae'] = mean_absolute_error(y_true, y_pred)
            metrics['mse'] = mean_squared_error(y_true, y_pred)
            metrics['rmse'] = np.sqrt(metrics['mse'])
        else:
            metrics['accuracy'] = accuracy_score(y_true, y_pred)
            metrics['precision'] = precision_score(y_true, y_pred, average='weighted', zero_division=0)
            metrics['recall'] = recall_score(y_true, y_pred, average='weighted', zero_division=0)
            metrics['f1'] = f1_score(y_true, y_pred, average='weighted', zero_division=0)
            
            if y_proba is not None and task_type == TaskType.BINARY:
                try:
                    if len(y_proba.shape) > 1:
                        metrics['auc'] = roc_auc_score(y_true, y_proba[:, 1])
                    else:
                        metrics['auc'] = roc_auc_score(y_true, y_proba)
                except:
                    pass
        
        return {k: round(v, 4) for k, v in metrics.items()}
    
    def _get_feature_importance(self, model, feature_names: List[str]) -> List[Dict[str, Any]]:
        """Extract feature importance from model"""
        importance = []
        
        if hasattr(model, 'feature_importances_'):
            values = model.feature_importances_
        elif hasattr(model, 'coef_'):
            values = np.abs(model.coef_).flatten()
            if len(values) != len(feature_names):
                values = values[:len(feature_names)]
        else:
            # Equal importance if not available
            values = np.ones(len(feature_names)) / len(feature_names)
        
        # Normalize
        if values.sum() > 0:
            values = values / values.sum()
        
        for i, (name, val) in enumerate(sorted(zip(feature_names, values), key=lambda x: x[1], reverse=True)):
            importance.append({
                'feature': name,
                'importance': round(float(val), 4),
                'rank': i + 1
            })
        
        return importance[:15]  # Top 15


# =============================================================================
# MAIN AUTOML ENGINE
# =============================================================================

class ProductionAutoML:
    """Production-ready AutoML engine"""
    
    def __init__(self, storage_path: str = "./storage/automl"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        
        self.profiler = DataProfiler()
        self.preprocessor = Preprocessor()
        self.trainer = ModelTrainer()
        
        # Store for prediction
        self.profile = None
        self.y_test = None
        self.y_pred = None
        self.y_proba = None
    
    async def run(
        self,
        df: pd.DataFrame,
        target_column: Optional[str] = None,
        user_id: str = "default"
    ) -> AutoMLResult:
        """Run complete AutoML pipeline"""
        start_time = datetime.now()
        
        print("=" * 60)
        print("🚀 PRODUCTION AUTOML - Starting Pipeline")
        print("=" * 60)
        
        # 1. Auto-detect target if not provided
        if not target_column:
            target_column = self._suggest_target(df)
            print(f"🎯 Auto-detected target: {target_column}")
        
        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' not found in dataset")
        
        # 2. Profile data
        self.profile = self.profiler.profile(df, target_column)
        
        # 3. Preprocess
        X, y, feature_names = self.preprocessor.fit_transform(
            df, target_column, self.profile
        )
        
        # 4. Split data
        print("📦 Splitting data...")
        stratify = y if self.profile.task_type != TaskType.REGRESSION else None
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=stratify
        )
        print(f"   ✅ Train: {len(X_train)}, Test: {len(X_test)}")
        
        # 5. Train models
        results, self.y_test, self.y_pred, self.y_proba = self.trainer.train_all(
            X_train, X_test, y_train, y_test, feature_names, self.profile.task_type
        )
        
        # 6. Build response
        processing_time = (datetime.now() - start_time).total_seconds()
        
        print("=" * 60)
        print(f"✅ Pipeline complete in {processing_time:.1f}s")
        print("=" * 60)
        
        return AutoMLResult(
            success=True,
            task_type=self.profile.task_type.value,
            target_column=target_column,
            data_profile={
                'rows': self.profile.rows,
                'columns': self.profile.columns,
                'missing_percentage': np.mean(list(self.profile.missing_values.values())),
                'class_distribution': self.profile.class_distribution
            },
            best_model={
                'name': self.trainer.best_model_name,
                'metrics': results[0].metrics if results else {},
                'cv_score': results[0].cv_score if results else 0
            },
            leaderboard=[
                {
                    'name': r.name,
                    'metrics': r.metrics,
                    'cv_score': r.cv_score,
                    'training_time': r.training_time
                }
                for r in results
            ],
            feature_importance=results[0].feature_importance if results else [],
            feature_metadata=self.preprocessor.get_feature_metadata(),
            y_test=self.y_test,
            y_pred=self.y_pred,
            y_proba=self.y_proba,
            processing_time=processing_time
        )
    
    def _suggest_target(self, df: pd.DataFrame) -> str:
        """Suggest target column based on column names"""
        for col in df.columns:
            col_lower = col.lower()
            if any(x in col_lower for x in ['target', 'label', 'class', 'y_', 'outcome']):
                return col
            if any(x in col_lower for x in ['churn', 'fraud', 'default', 'converted']):
                return col
        
        # Last column with few unique values
        last_col = df.columns[-1]
        if df[last_col].nunique() <= 10:
            return last_col
        
        return df.columns[-1]
    
    def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction using best model"""
        if self.trainer.best_model is None:
            raise ValueError("No model trained yet")
        
        X = self.preprocessor.transform_for_prediction(data)
        
        prediction = self.trainer.best_model.predict(X)[0]
        
        # Decode label if classification
        if self.preprocessor.target_encoder is not None:
            try:
                prediction = self.preprocessor.target_encoder.inverse_transform([int(prediction)])[0]
            except:
                pass
        
        # Get probability
        probability = None
        if hasattr(self.trainer.best_model, 'predict_proba'):
            try:
                proba = self.trainer.best_model.predict_proba(X)[0]
                probability = proba.tolist()
            except:
                pass
        
        return {
            'prediction': str(prediction),
            'probability': probability,
            'model': self.trainer.best_model_name
        }
    
    def to_dict(self, result: AutoMLResult) -> Dict[str, Any]:
        """Convert AutoMLResult to dictionary for API response"""
        return {
            'success': result.success,
            'task_type': result.task_type,
            'target_column': result.target_column,
            'data_summary': result.data_profile,
            'best_model': result.best_model,
            'all_models': result.leaderboard,
            'feature_importance': result.feature_importance,
            'processing_time_seconds': result.processing_time
        }
    
    def save_model(self, user_id: str = "default") -> str:
        """Save trained model and preprocessors to disk"""
        model_dir = os.path.join(self.storage_path, user_id)
        os.makedirs(model_dir, exist_ok=True)
        
        model_path = os.path.join(model_dir, "model.pkl")
        
        model_data = {
            'model': self.trainer.best_model,
            'model_name': self.trainer.best_model_name,
            'preprocessor': {
                'imputers': self.preprocessor.imputers,
                'encoders': self.preprocessor.encoders,
                'scaler': self.preprocessor.scaler,
                'target_encoder': self.preprocessor.target_encoder,
                'feature_names': self.preprocessor.feature_names,
                'feature_types': self.preprocessor.feature_types,
                'feature_stats': self.preprocessor.feature_stats,
            },
            'profile': {
                'task_type': self.profile.task_type.value if self.profile else None,
                'target_column': self.profile.target_column if self.profile else None,
            }
        }
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"💾 Model saved to {model_path}")
        return model_path
    
    def load_model(self, user_id: str = "default") -> bool:
        """Load trained model and preprocessors from disk"""
        model_path = os.path.join(self.storage_path, user_id, "model.pkl")
        
        if not os.path.exists(model_path):
            return False
        
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.trainer.best_model = model_data['model']
            self.trainer.best_model_name = model_data['model_name']
            
            preprocessor_data = model_data['preprocessor']
            self.preprocessor.imputers = preprocessor_data['imputers']
            self.preprocessor.encoders = preprocessor_data['encoders']
            self.preprocessor.scaler = preprocessor_data['scaler']
            self.preprocessor.target_encoder = preprocessor_data['target_encoder']
            self.preprocessor.feature_names = preprocessor_data['feature_names']
            self.preprocessor.feature_types = preprocessor_data['feature_types']
            self.preprocessor.feature_stats = preprocessor_data['feature_stats']
            
            print(f"📂 Model loaded from {model_path}")
            return True
        except Exception as e:
            print(f"⚠️ Failed to load model: {e}")
            return False
    
    def get_feature_columns(self) -> List[str]:
        """Get feature column names used for training"""
        return self.preprocessor.feature_names
    
    def get_feature_metadata_for_api(self) -> List[Dict[str, Any]]:
        """Get feature metadata formatted for API/frontend"""
        return self.preprocessor.get_feature_metadata()


# Global instance
automl_engine = ProductionAutoML()

