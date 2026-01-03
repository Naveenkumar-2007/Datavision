"""
🚀 PRODUCTION ML ENGINE - Simple & Correct
===========================================

This is a simplified, correct ML pipeline that:
1. Uses pandas for all preprocessing (no sklearn ColumnTransformer complexity)
2. Stores EXACT column order and preprocessing steps
3. Guarantees same preprocessing for train and predict
4. Can reproduce predictions on training data

NO COMPLEX ABSTRACTIONS. Just correct, working ML.
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
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, 
    r2_score, mean_absolute_error, mean_squared_error, roc_auc_score
)

# Models
from sklearn.ensemble import (
    RandomForestClassifier, RandomForestRegressor,
    GradientBoostingClassifier, GradientBoostingRegressor,
    ExtraTreesClassifier, ExtraTreesRegressor
)
from sklearn.linear_model import LogisticRegression, Ridge

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

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

STORAGE_PATH = "./storage/automl"


@dataclass
class TrainResult:
    """Complete training result"""
    success: bool
    task_type: str  # 'classification' or 'regression'
    target_column: str
    feature_columns: List[str]
    
    # Best model info
    best_model_name: str
    best_model_metrics: Dict[str, float]
    
    # All models
    leaderboard: List[Dict]
    
    # Feature importance
    feature_importance: List[Dict]
    
    # For charts
    y_test: np.ndarray
    y_pred: np.ndarray
    y_proba: Optional[np.ndarray]
    
    # Feature metadata for UI
    feature_metadata: List[Dict]
    
    # Data info
    n_rows: int
    n_cols: int
    
    # Timing
    processing_time: float


class SimpleMLEngine:
    """
    Simple, correct ML engine that works.
    
    Key principles:
    1. Store EVERYTHING needed for prediction
    2. Use same preprocessing for train and predict
    3. Debug-friendly (print statements, simple data flow)
    """
    
    def __init__(self):
        # Model state
        self.model = None
        self.model_name = None
        
        # Preprocessing state - stored for prediction
        self.feature_columns: List[str] = []
        self.target_column: str = ""
        self.task_type: str = ""
        
        # Encoding info
        self.label_encoders: Dict[str, LabelEncoder] = {}  # For categorical features
        self.target_encoder: Optional[LabelEncoder] = None  # For classification target
        
        # Feature stats for UI
        self.feature_metadata: List[Dict] = []
        
        # Numeric fill values (median)
        self.numeric_fill_values: Dict[str, float] = {}
        
        # For verification
        self.training_data_sample: Optional[pd.DataFrame] = None
    
    def _detect_task_type(self, y: pd.Series) -> str:
        """Detect if classification or regression"""
        n_unique = y.nunique()
        
        if pd.api.types.is_object_dtype(y) or pd.api.types.is_categorical_dtype(y):
            return 'classification'
        if n_unique <= 10:
            return 'classification'
        return 'regression'
    
    def _detect_target(self, df: pd.DataFrame) -> str:
        """Auto-detect target column"""
        for col in df.columns:
            c = col.lower()
            if any(x in c for x in ['target', 'label', 'class', 'churn', 'fraud', 'price', 'closeusd', 'salary']):
                return col
        return df.columns[-1]
    
    def _preprocess_training(self, df: pd.DataFrame, target_col: str) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Preprocess data for training.
        CRITICAL: Store all preprocessing info for later prediction.
        """
        print("🔧 Preprocessing...")
        
        # Separate features and target
        X = df.drop(columns=[target_col]).copy()
        y = df[target_col].copy()
        
        # Store target column
        self.target_column = target_col
        self.task_type = self._detect_task_type(y)
        
        # Identify column types
        numeric_cols = []
        categorical_cols = []
        
        for col in X.columns:
            if pd.api.types.is_numeric_dtype(X[col]):
                numeric_cols.append(col)
            else:
                # Only keep categorical with <= 50 unique values
                if X[col].nunique() <= 50:
                    categorical_cols.append(col)
                else:
                    print(f"   ⚠️ Dropping high-cardinality: {col}")
        
        # Store feature columns (ordered!)
        self.feature_columns = numeric_cols + categorical_cols
        
        print(f"   Features: {len(self.feature_columns)} ({len(numeric_cols)} numeric, {len(categorical_cols)} categorical)")
        
        # Process features
        processed = []
        self.feature_metadata = []
        
        # Numeric features
        for col in numeric_cols:
            series = X[col].astype(float)
            median_val = series.median()
            # Handle case where median is NaN (all values missing)
            if pd.isna(median_val):
                median_val = 0.0
            self.numeric_fill_values[col] = median_val
            filled = series.fillna(median_val)
            processed.append(filled.values.reshape(-1, 1))
            
            # Safe conversion for metadata (handle NaN/inf)
            def safe_float(v, default=0.0):
                try:
                    f = float(v)
                    return f if not (pd.isna(f) or np.isinf(f)) else default
                except:
                    return default
            
            self.feature_metadata.append({
                'name': col,
                'type': 'numeric',
                'min': safe_float(series.min()),
                'max': safe_float(series.max()),
                'mean': safe_float(series.mean())
            })
        
        # Categorical features - Label encode
        for col in categorical_cols:
            series = X[col].fillna('_MISSING_').astype(str)
            encoder = LabelEncoder()
            encoded = encoder.fit_transform(series)
            self.label_encoders[col] = encoder
            processed.append(encoded.reshape(-1, 1))
            
            self.feature_metadata.append({
                'name': col,
                'type': 'categorical',
                'options': encoder.classes_.tolist()[:30]
            })
        
        # Combine
        X_processed = np.hstack(processed) if processed else np.array([])
        
        # Process target
        if self.task_type == 'classification':
            self.target_encoder = LabelEncoder()
            y_processed = self.target_encoder.fit_transform(y.astype(str))
        else:
            y_processed = y.values.astype(float)
        
        # Store sample for verification
        self.training_data_sample = df.head(10).copy()
        
        return X_processed, y_processed, self.feature_columns
    
    def _preprocess_single(self, data: Dict[str, Any]) -> np.ndarray:
        """
        Preprocess a single prediction input.
        Uses EXACT same steps as training.
        """
        processed = []
        
        for col in self.feature_columns:
            value = data.get(col)
            
            if col in self.numeric_fill_values:
                # Numeric feature
                try:
                    val = float(value) if value is not None else self.numeric_fill_values[col]
                except (ValueError, TypeError):
                    val = self.numeric_fill_values[col]
                processed.append(val)
            else:
                # Categorical feature
                encoder = self.label_encoders.get(col)
                if encoder is not None:
                    str_val = str(value) if value is not None else '_MISSING_'
                    if str_val in encoder.classes_:
                        encoded = encoder.transform([str_val])[0]
                    else:
                        encoded = 0  # Unknown category
                    processed.append(float(encoded))
                else:
                    processed.append(0.0)
        
        return np.array([processed])
    
    def _get_models(self) -> Dict[str, Any]:
        """Get model pool based on task type"""
        if self.task_type == 'classification':
            models = {
                'LogisticRegression': LogisticRegression(max_iter=500, n_jobs=-1, random_state=42),
                'RandomForest': RandomForestClassifier(n_estimators=100, max_depth=12, n_jobs=-1, random_state=42),
                'ExtraTrees': ExtraTreesClassifier(n_estimators=100, max_depth=12, n_jobs=-1, random_state=42),
                'GradientBoosting': GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42),
            }
            if HAS_XGB:
                models['XGBoost'] = xgb.XGBClassifier(n_estimators=100, max_depth=6, n_jobs=-1, random_state=42, eval_metric='logloss', verbosity=0)
            if HAS_LGB:
                models['LightGBM'] = lgb.LGBMClassifier(n_estimators=100, max_depth=6, verbose=-1, random_state=42)
        else:
            models = {
                'Ridge': Ridge(random_state=42),
                'RandomForest': RandomForestRegressor(n_estimators=200, max_depth=None, n_jobs=-1, random_state=42),
                'ExtraTrees': ExtraTreesRegressor(n_estimators=200, max_depth=None, n_jobs=-1, random_state=42),
                'GradientBoosting': GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42),
            }
            if HAS_XGB:
                models['XGBoost'] = xgb.XGBRegressor(n_estimators=200, max_depth=20, n_jobs=-1, random_state=42, verbosity=0)
            if HAS_LGB:
                models['LightGBM'] = lgb.LGBMRegressor(n_estimators=200, max_depth=20, verbose=-1, random_state=42)
        
        return models
    
    async def train(self, df: pd.DataFrame, target_col: Optional[str] = None, user_id: str = "default") -> TrainResult:
        """Train models on data"""
        start = datetime.now()
        
        print("=" * 60)
        print("🚀 SIMPLE ML ENGINE - Training")
        print("=" * 60)
        
        # Auto-detect target
        if not target_col:
            target_col = self._detect_target(df)
            print(f"🎯 Auto-detected target: {target_col}")
        
        # Drop date columns (usually not useful for ML)
        for col in df.columns:
            if 'date' in col.lower():
                print(f"   ⚠️ Dropping date column: {col}")
                df = df.drop(columns=[col])
        
        # Preprocess
        X, y, feature_cols = self._preprocess_training(df, target_col)
        
        print(f"   Task type: {self.task_type}")
        print(f"   Data shape: {X.shape}")
        
        # Split
        if self.task_type == 'classification':
            stratify = y
        else:
            stratify = None
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=stratify
        )
        print(f"   Train: {len(X_train)}, Test: {len(X_test)}")
        
        # Train models
        models = self._get_models()
        results = []
        
        best_score = -np.inf
        best_model = None
        best_name = None
        best_pred = None
        best_proba = None
        
        print(f"🤖 Training {len(models)} models...")
        
        for name, model in models.items():
            try:
                t0 = datetime.now()
                
                # Fit
                model.fit(X_train, y_train)
                
                # Predict
                y_pred = model.predict(X_test)
                y_proba = None
                if hasattr(model, 'predict_proba'):
                    try:
                        y_proba = model.predict_proba(X_test)
                    except:
                        pass
                
                # Metrics
                if self.task_type == 'classification':
                    score = f1_score(y_test, y_pred, average='weighted', zero_division=0)
                    metrics = {
                        'f1': round(score, 4),
                        'accuracy': round(accuracy_score(y_test, y_pred), 4),
                    }
                else:
                    score = r2_score(y_test, y_pred)
                    metrics = {
                        'r2': round(score, 4),
                        'mae': round(mean_absolute_error(y_test, y_pred), 4),
                    }
                
                elapsed = (datetime.now() - t0).total_seconds()
                
                # Feature importance
                importance = self._get_importance(model, feature_cols)
                
                results.append({
                    'name': name,
                    'metrics': metrics,
                    'training_time': elapsed,
                    'importance': importance
                })
                
                metric_name = 'f1' if self.task_type == 'classification' else 'r2'
                print(f"   {name}: {metric_name}={score:.3f} ({elapsed:.1f}s)")
                
                if score > best_score:
                    best_score = score
                    best_model = model
                    best_name = name
                    best_pred = y_pred
                    best_proba = y_proba
                    
            except Exception as e:
                print(f"   {name}: ERROR - {e}")
        
        # Store best model
        self.model = best_model
        self.model_name = best_name
        
        print(f"🏆 Best: {best_name} (score={best_score:.3f})")
        
        # PRODUCTION STEP: Retrain best model on FULL data for deployment
        print(f"🔄 Retraining {best_name} on FULL data...")
        final_model = self._get_models()[best_name]
        final_model.fit(X, y)  # Train on ALL data, not just train split
        self.model = final_model
        print(f"   ✅ Model retrained on {len(X)} samples")
        
        # Sort results
        metric_key = 'f1' if self.task_type == 'classification' else 'r2'
        results.sort(key=lambda x: x['metrics'].get(metric_key, 0), reverse=True)
        
        # Save model
        self._save(user_id)
        
        # Verify predictions on training sample
        self._verify_predictions(df.head(5), target_col)
        
        processing_time = (datetime.now() - start).total_seconds()
        
        print("=" * 60)
        print(f"✅ Training complete in {processing_time:.1f}s")
        print("=" * 60)
        
        return TrainResult(
            success=True,
            task_type=self.task_type,
            target_column=target_col,
            feature_columns=feature_cols,
            best_model_name=best_name,
            best_model_metrics=results[0]['metrics'] if results else {},
            leaderboard=results,
            feature_importance=results[0].get('importance', []) if results else [],
            y_test=y_test,
            y_pred=best_pred,
            y_proba=best_proba[:, 1] if best_proba is not None and self.task_type == 'classification' and len(best_proba.shape) > 1 else None,
            feature_metadata=self.feature_metadata,
            n_rows=len(df),
            n_cols=len(df.columns),
            processing_time=processing_time
        )
    
    def _get_importance(self, model, feature_cols: List[str]) -> List[Dict]:
        """Get feature importance"""
        if hasattr(model, 'feature_importances_'):
            values = model.feature_importances_
        elif hasattr(model, 'coef_'):
            values = np.abs(model.coef_).flatten()
        else:
            return []
        
        if len(values) != len(feature_cols):
            return []
        
        if values.sum() > 0:
            values = values / values.sum()
        
        importance = []
        for rank, (name, val) in enumerate(sorted(zip(feature_cols, values), key=lambda x: x[1], reverse=True), 1):
            importance.append({'feature': name, 'importance': round(float(val), 4), 'rank': rank})
        
        return importance[:15]
    
    def _verify_predictions(self, df: pd.DataFrame, target_col: str):
        """Verify model can predict training data correctly"""
        print("\n📋 Verification - Predicting on training sample:")
        
        for i in range(min(5, len(df))):
            row = df.iloc[i]
            actual = row[target_col]
            
            # Build input dict
            input_data = {col: row[col] for col in self.feature_columns if col in row.index}
            
            try:
                pred = self.predict(input_data)
                pred_val = pred['prediction']
                
                if self.task_type == 'regression':
                    error = abs(float(pred_val) - float(actual))
                    pct = error / abs(float(actual)) * 100 if float(actual) != 0 else 0
                    print(f"   Row {i}: Actual={actual:.2f}, Pred={float(pred_val):.2f}, Error={pct:.1f}%")
                else:
                    match = "✅" if str(pred_val) == str(actual) else "❌"
                    print(f"   Row {i}: Actual={actual}, Pred={pred_val} {match}")
            except Exception as e:
                print(f"   Row {i}: ERROR - {e}")
    
    def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction"""
        if self.model is None:
            raise ValueError("No model trained")
        
        X = self._preprocess_single(data)
        prediction = self.model.predict(X)[0]
        
        # Decode if classification
        if self.target_encoder is not None:
            try:
                prediction = self.target_encoder.inverse_transform([int(prediction)])[0]
            except:
                pass
        
        # Probability
        probability = None
        confidence = None
        if hasattr(self.model, 'predict_proba'):
            try:
                proba = self.model.predict_proba(X)[0]
                probability = proba.tolist()
                confidence = float(max(proba))
            except:
                pass
        
        return {
            'prediction': str(prediction),
            'probability': probability,
            'confidence': confidence,
            'model': self.model_name
        }
    
    def _save(self, user_id: str):
        """Save model and all preprocessing state"""
        save_dir = os.path.join(STORAGE_PATH, user_id)
        os.makedirs(save_dir, exist_ok=True)
        
        save_path = os.path.join(save_dir, "model.pkl")
        
        data = {
            'model': self.model,
            'model_name': self.model_name,
            'feature_columns': self.feature_columns,
            'target_column': self.target_column,
            'task_type': self.task_type,
            'label_encoders': self.label_encoders,
            'target_encoder': self.target_encoder,
            'numeric_fill_values': self.numeric_fill_values,
            'feature_metadata': self.feature_metadata,
        }
        
        with open(save_path, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"💾 Saved to {save_path}")
    
    def load(self, user_id: str) -> bool:
        """Load model and preprocessing state"""
        load_path = os.path.join(STORAGE_PATH, user_id, "model.pkl")
        
        if not os.path.exists(load_path):
            return False
        
        try:
            with open(load_path, 'rb') as f:
                data = pickle.load(f)
            
            self.model = data['model']
            self.model_name = data['model_name']
            self.feature_columns = data['feature_columns']
            self.target_column = data['target_column']
            self.task_type = data['task_type']
            self.label_encoders = data['label_encoders']
            self.target_encoder = data['target_encoder']
            self.numeric_fill_values = data['numeric_fill_values']
            self.feature_metadata = data['feature_metadata']
            
            print(f"📂 Loaded from {load_path}")
            return True
        except Exception as e:
            print(f"⚠️ Load failed: {e}")
            return False
    
    def get_feature_metadata(self) -> List[Dict]:
        """Get feature metadata for UI"""
        return self.feature_metadata


# Global instance
automl_engine = SimpleMLEngine()
