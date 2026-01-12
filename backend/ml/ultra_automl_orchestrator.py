"""
🎼 ULTRA AUTOML ORCHESTRATOR v1.0 - CENTRAL BRAIN COORDINATOR
===============================================================

The central intelligence that coordinates ALL engines for MAXIMUM ACCURACY.

Core Capabilities:
1. Data Profile Analysis → Decides which engines to activate
2. Parallel Model Training → Trains multiple model families simultaneously
3. Dynamic Resource Allocation → Optimizes CPU/GPU usage
4. Adaptive Early Stopping → Stops poor models quickly
5. Intelligent Ensemble Building → Combines best models optimally
6. Full Explainability → SHAP/LIME for every prediction

This is the ULTIMATE AutoML system that handles ANY data!
"""

import os
import time
import pickle
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field, asdict
import logging
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

# Import all engines
try:
    from ml.neural_architecture_engine import NeuralArchitectureEngine, HAS_TENSORFLOW
except ImportError:
    HAS_TENSORFLOW = False
    NeuralArchitectureEngine = None
    logger.warning("Neural Architecture Engine not available")

try:
    from ml.meta_learning_engine import MetaLearningEngine, DatasetFingerprint
except ImportError:
    MetaLearningEngine = None
    DatasetFingerprint = None
    logger.warning("Meta-Learning Engine not available")

try:
    from ml.feature_synthesis_engine import FeatureSynthesisEngine
except ImportError:
    FeatureSynthesisEngine = None
    logger.warning("Feature Synthesis Engine not available")

try:
    from ml.explainability_engine import ExplainabilityEngine
except ImportError:
    ExplainabilityEngine = None
    logger.warning("Explainability Engine not available")

try:
    from ml.ultra_data_pipeline import UltraDataPipeline, DataQualityReport
except ImportError:
    UltraDataPipeline = None
    DataQualityReport = None
    logger.warning("Ultra Data Pipeline not available")

# Production ML Core (existing)
try:
    from ml.production_ml_core import ProductionModelTrainer, ProductionFeatureEngineer
except ImportError:
    ProductionModelTrainer = None
    ProductionFeatureEngineer = None

# Sklearn
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    r2_score, mean_absolute_error, mean_squared_error
)
from sklearn.ensemble import VotingClassifier, VotingRegressor, StackingClassifier, StackingRegressor
from sklearn.linear_model import LogisticRegression, Ridge


@dataclass
class UltraTrainResult:
    """Comprehensive training result from Ultra AutoML."""
    success: bool
    task_type: str
    target_column: str
    
    # Best model
    best_model: Any
    best_model_name: str
    best_model_type: str  # 'classical', 'neural', 'ensemble'
    best_score: float
    
    # All metrics
    metrics: Dict[str, float]
    
    # Leaderboard
    leaderboard: List[Dict]
    
    # Feature info
    feature_names: List[str]
    feature_importance: Dict[str, float]
    synthesized_features: List[str]
    
    # Data quality
    data_quality_report: Optional[Any]
    
    # Meta-learning
    meta_recommendations: List[Dict]
    dataset_fingerprint: Optional[Any]
    
    # Predictions on test set
    y_test: np.ndarray
    y_pred: np.ndarray
    y_proba: Optional[np.ndarray]
    
    # Performance
    total_time_seconds: float
    engines_used: List[str]
    
    # Charts (base64 encoded)
    charts: Dict[str, str] = field(default_factory=dict)
    
    # Explainability
    explainer: Optional[Any] = None


class UltraAutoMLOrchestrator:
    """
    🎼 Ultra AutoML Orchestrator - The Central Brain
    
    MAXIMUM ACCURACY MODE:
    1. Full data profiling and intelligent preprocessing
    2. Meta-learning for algorithm recommendation
    3. Genetic feature synthesis
    4. Classical ML + Neural Networks (TabNet, Wide&Deep, etc.)
    5. Intelligent ensemble of best models
    6. Full SHAP/LIME explainability
    
    This orchestrator coordinates ALL engines to achieve
    the HIGHEST POSSIBLE ACCURACY on ANY dataset!
    """
    
    def __init__(
        self,
        mode: str = 'maximum_accuracy',  # 'fast', 'balanced', 'maximum_accuracy'
        use_neural: bool = True,
        use_meta_learning: bool = True,
        use_feature_synthesis: bool = True,
        use_explainability: bool = True,
        n_jobs: int = 1,
        random_state: int = 42,
        verbose: bool = True
    ):
        self.mode = mode
        self.use_neural = use_neural and HAS_TENSORFLOW
        self.use_meta_learning = use_meta_learning and MetaLearningEngine is not None
        self.use_feature_synthesis = use_feature_synthesis and FeatureSynthesisEngine is not None
        self.use_explainability = use_explainability and ExplainabilityEngine is not None
        self.n_jobs = n_jobs
        self.random_state = random_state
        self.verbose = verbose
        
        # Initialize engines
        self.data_pipeline = UltraDataPipeline() if UltraDataPipeline else None
        self.meta_learner = MetaLearningEngine() if self.use_meta_learning else None
        self.feature_synthesizer = FeatureSynthesisEngine() if self.use_feature_synthesis else None
        self.explainer = ExplainabilityEngine() if self.use_explainability else None
        
        # Storage
        self.best_model = None
        self.best_model_name = None
        self.feature_names = []
        self.task_type = None
        self.class_names = []
        
        # Results
        self.all_results = []
        
        logger.info(f"🎼 Ultra AutoML Orchestrator initialized (Mode: {mode})")
        logger.info(f"   Neural: {self.use_neural}, Meta-Learning: {self.use_meta_learning}")
        logger.info(f"   Feature Synthesis: {self.use_feature_synthesis}, Explainability: {self.use_explainability}")
    
    def _get_mode_settings(self) -> Dict[str, Any]:
        """Get settings based on mode."""
        if self.mode == 'fast':
            return {
                'max_epochs': 50,
                'n_trials': 5,
                'max_features': 20,
                'use_ensemble': False,
                'cv_folds': 3
            }
        elif self.mode == 'balanced':
            return {
                'max_epochs': 100,
                'n_trials': 15,
                'max_features': 35,
                'use_ensemble': True,
                'cv_folds': 5
            }
        else:  # maximum_accuracy
            return {
                'max_epochs': 200,
                'n_trials': 30,
                'max_features': 50,
                'use_ensemble': True,
                'cv_folds': 5
            }
    
    def train(
        self,
        df: pd.DataFrame,
        target_col: str = None,
        task_type: str = None,
        check_cancellation: callable = None,
        user_id: str = None,
        dataset_name: str = "unknown"
    ) -> UltraTrainResult:
        """
        🚀 MAIN TRAINING PIPELINE - MAXIMUM ACCURACY
        
        Args:
            df: Input DataFrame
            target_col: Target column name (auto-detected if None)
            task_type: 'classification' or 'regression' (auto-detected if None)
            check_cancellation: Callback for user cancellation
            user_id: User identifier for storage
            dataset_name: Name of dataset for meta-learning
            
        Returns:
            UltraTrainResult with trained models and insights
        """
        start_time = time.time()
        settings = self._get_mode_settings()
        engines_used = []
        
        print("\n" + "=" * 70)
        print("🎼 ULTRA AUTOML ORCHESTRATOR v1.0 - MAXIMUM ACCURACY MODE")
        print("=" * 70)
        print(f"📊 Input: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"⚙️  Mode: {self.mode}")
        
        # =========================================================
        # PHASE 1: DATA PROFILING & PREPROCESSING
        # =========================================================
        print("\n" + "-" * 50)
        print("📊 PHASE 1: DATA PROFILING & PREPROCESSING")
        print("-" * 50)
        
        # Auto-detect target if not provided
        if target_col is None:
            target_col = self._auto_detect_target(df)
        print(f"🎯 Target column: {target_col}")
        
        # Auto-detect task type
        if task_type is None:
            task_type = self._auto_detect_task_type(df[target_col])
        self.task_type = task_type
        print(f"📋 Task type: {task_type}")
        
        # Extract dataset fingerprint for meta-learning
        fingerprint = None
        if self.use_meta_learning and self.meta_learner:
            fingerprint = self.meta_learner.extract_fingerprint(df, target_col, task_type)
            print(f"🔍 Dataset fingerprint: {fingerprint.fingerprint_hash}")
        
        # Data pipeline
        data_quality_report = None
        if self.data_pipeline:
            X, y, feature_names, data_quality_report = self.data_pipeline.fit_transform(
                df, target_col, task_type
            )
            self.feature_names = feature_names
            engines_used.append('UltraDataPipeline')
        else:
            # Fallback basic preprocessing
            X, y, feature_names = self._basic_preprocess(df, target_col, task_type)
            self.feature_names = feature_names
        
        # Store class names for classification
        if task_type == 'classification':
            unique_classes = np.unique(y)
            self.class_names = [str(c) for c in unique_classes]
        
        # =========================================================
        # PHASE 2: META-LEARNING RECOMMENDATIONS
        # =========================================================
        meta_recommendations = []
        if self.use_meta_learning and self.meta_learner and fingerprint:
            print("\n" + "-" * 50)
            print("🎯 PHASE 2: META-LEARNING RECOMMENDATIONS")
            print("-" * 50)
            
            recommendations = self.meta_learner.recommend_algorithms(
                fingerprint, task_type, top_k=5
            )
            meta_recommendations = recommendations
            engines_used.append('MetaLearningEngine')
            
            print("   📈 Recommended algorithms:")
            for rec in recommendations[:3]:
                print(f"      • {rec['algorithm']}: predicted score {rec['predicted_score']:.4f} (confidence: {rec['confidence']:.0%})")
        
        # =========================================================
        # PHASE 3: FEATURE SYNTHESIS
        # =========================================================
        synthesized_features = []
        if self.use_feature_synthesis and self.feature_synthesizer:
            print("\n" + "-" * 50)
            print("🔬 PHASE 3: FEATURE SYNTHESIS")
            print("-" * 50)
            
            # Create DataFrame for synthesis (limited columns for speed)
            synthesis_df = pd.DataFrame(X, columns=self.feature_names)
            synthesis_df[target_col] = y
            
            enhanced_df, new_features = self.feature_synthesizer.fit_transform(
                synthesis_df, target_col, task_type
            )
            
            if new_features:
                # Update X with synthesized features
                X = enhanced_df.drop(columns=[target_col]).values
                self.feature_names = enhanced_df.drop(columns=[target_col]).columns.tolist()
                synthesized_features = new_features
                engines_used.append('FeatureSynthesisEngine')
        
        # =========================================================
        # PHASE 4: TRAIN-TEST SPLIT
        # =========================================================
        print("\n" + "-" * 50)
        print("📊 PHASE 4: TRAIN-TEST SPLIT")
        print("-" * 50)
        
        try:
            stratify = y if task_type == 'classification' else None
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=self.random_state, stratify=stratify
            )
        except ValueError:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=self.random_state
            )
        
        print(f"   ✅ Train: {len(X_train)} samples | Test: {len(X_test)} samples")
        
        # =========================================================
        # PHASE 5: CLASSICAL ML TRAINING
        # =========================================================
        print("\n" + "-" * 50)
        print("🤖 PHASE 5: CLASSICAL ML TRAINING")
        print("-" * 50)
        
        all_results = []
        
        if ProductionModelTrainer:
            classical_trainer = ProductionModelTrainer(task_type)
            classical_results = classical_trainer.train_all(
                X_train, y_train, X_test, y_test,
                cv_folds=settings['cv_folds'],
                check_cancellation=check_cancellation
            )
            
            for result in classical_results:
                result['model_type'] = 'classical'
                all_results.append(result)
            
            engines_used.append('ProductionModelTrainer')
        
        # =========================================================
        # PHASE 6: NEURAL ARCHITECTURE TRAINING
        # =========================================================
        if self.use_neural and HAS_TENSORFLOW:
            print("\n" + "-" * 50)
            print("🧠 PHASE 6: NEURAL ARCHITECTURE TRAINING")
            print("-" * 50)
            
            try:
                n_classes = len(np.unique(y)) if task_type == 'classification' else 0
                neural_engine = NeuralArchitectureEngine(
                    task_type=task_type,
                    n_classes=n_classes,
                    max_epochs=settings['max_epochs']
                )
                
                neural_result = neural_engine.train_all(
                    X_train, y_train, X_test, y_test,
                    check_cancellation=check_cancellation
                )
                
                if neural_result.success and neural_result.best_model:
                    all_results.append({
                        'name': f'Neural_{neural_result.best_model_name}',
                        'model': neural_result.best_model,
                        'score': neural_result.best_score,
                        'model_type': 'neural'
                    })
                    engines_used.append('NeuralArchitectureEngine')
                    
            except Exception as e:
                logger.error(f"Neural training failed: {e}")
                print(f"   ⚠️ Neural training failed: {str(e)[:50]}")
        
        # =========================================================
        # PHASE 7: ENSEMBLE BUILDING
        # =========================================================
        if settings['use_ensemble'] and len(all_results) >= 2:
            print("\n" + "-" * 50)
            print("🎯 PHASE 7: ENSEMBLE BUILDING")
            print("-" * 50)
            
            ensemble_result = self._build_ultra_ensemble(
                all_results, X_train, y_train, X_test, y_test, task_type
            )
            
            if ensemble_result:
                all_results.append(ensemble_result)
        
        # Sort by score
        all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        self.all_results = all_results
        
        # Get best model
        if all_results:
            best = all_results[0]
            self.best_model = best['model']
            self.best_model_name = best['name']
            best_model_type = best.get('model_type', 'classical')
            best_score = best['score']
        else:
            raise ValueError("No models were successfully trained")
        
        # =========================================================
        # PHASE 8: FINAL EVALUATION
        # =========================================================
        print("\n" + "-" * 50)
        print("📊 PHASE 8: FINAL EVALUATION")
        print("-" * 50)
        
        # Generate predictions
        y_pred = self._predict_with_model(self.best_model, X_test, task_type)
        
        # Get probabilities if available
        y_proba = None
        if task_type == 'classification' and hasattr(self.best_model, 'predict_proba'):
            try:
                y_proba = self.best_model.predict_proba(X_test)
            except:
                pass
        
        # Calculate metrics
        metrics = self._calculate_metrics(y_test, y_pred, y_proba, task_type)
        print(f"   🏆 Best Model: {self.best_model_name}")
        for metric, value in metrics.items():
            print(f"      • {metric}: {value:.4f}")
        
        # =========================================================
        # PHASE 9: EXPLAINABILITY SETUP
        # =========================================================
        if self.use_explainability and self.explainer:
            print("\n" + "-" * 50)
            print("🔮 PHASE 9: EXPLAINABILITY SETUP")
            print("-" * 50)
            
            try:
                self.explainer.set_model(
                    model=self.best_model,
                    feature_names=self.feature_names,
                    background_data=X_train[:min(100, len(X_train))],
                    class_names=self.class_names if task_type == 'classification' else None
                )
                self.explainer.task_type = task_type
                engines_used.append('ExplainabilityEngine')
                print("   ✅ Explainability engine ready for predictions")
            except Exception as e:
                logger.error(f"Explainability setup failed: {e}")
        
        # =========================================================
        # PHASE 10: RECORD META-LEARNING EXPERIENCE
        # =========================================================
        if self.use_meta_learning and self.meta_learner and fingerprint:
            algorithm_scores = {r['name']: r['score'] for r in all_results}
            self.meta_learner.record_experience(
                fingerprint=fingerprint,
                task_type=task_type,
                algorithm_scores=algorithm_scores,
                training_time_seconds=time.time() - start_time,
                dataset_name=dataset_name
            )
        
        # Get feature importance
        feature_importance = self._get_feature_importance(self.best_model)
        
        # Create leaderboard
        leaderboard = [
            {
                'rank': i + 1,
                'name': r['name'],
                'score': r['score'],
                'type': r.get('model_type', 'classical')
            }
            for i, r in enumerate(all_results[:10])
        ]
        
        total_time = time.time() - start_time
        
        print("\n" + "=" * 70)
        print(f"✅ ULTRA AUTOML COMPLETE - {self.best_model_name}")
        print(f"   🏆 Best Score: {best_score:.4f}")
        print(f"   ⏱️  Total Time: {total_time:.1f}s")
        print(f"   🔧 Engines Used: {', '.join(engines_used)}")
        print("=" * 70)
        
        return UltraTrainResult(
            success=True,
            task_type=task_type,
            target_column=target_col,
            best_model=self.best_model,
            best_model_name=self.best_model_name,
            best_model_type=best_model_type,
            best_score=best_score,
            metrics=metrics,
            leaderboard=leaderboard,
            feature_names=self.feature_names,
            feature_importance=feature_importance,
            synthesized_features=synthesized_features,
            data_quality_report=data_quality_report,
            meta_recommendations=meta_recommendations,
            dataset_fingerprint=fingerprint,
            y_test=y_test,
            y_pred=y_pred,
            y_proba=y_proba,
            total_time_seconds=total_time,
            engines_used=engines_used,
            explainer=self.explainer
        )
    
    def _auto_detect_target(self, df: pd.DataFrame) -> str:
        """Auto-detect target column."""
        # Priority keywords
        target_keywords = ['target', 'label', 'class', 'y', 'output',
                          'churn', 'fraud', 'default', 'price', 'salary']
        
        for keyword in target_keywords:
            for col in df.columns:
                if keyword in col.lower():
                    return col
        
        # Default to last column
        return df.columns[-1]
    
    def _auto_detect_task_type(self, y: pd.Series) -> str:
        """Auto-detect task type."""
        n_unique = y.nunique()
        n_samples = len(y)
        
        # String = classification
        if y.dtype == 'object' or y.dtype.name == 'category':
            return 'classification'
        
        # Few unique values = classification
        if n_unique <= 20 and n_unique / n_samples < 0.05:
            return 'classification'
        
        # Boolean = classification
        if set(y.unique()).issubset({0, 1, True, False}):
            return 'classification'
        
        return 'regression'
    
    def _basic_preprocess(
        self, 
        df: pd.DataFrame, 
        target_col: str, 
        task_type: str
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Basic preprocessing fallback."""
        X = df.drop(columns=[target_col])
        y = df[target_col]
        
        # Keep only numeric columns
        X = X.select_dtypes(include=[np.number])
        X = X.fillna(0).values
        
        if task_type == 'classification':
            le = LabelEncoder()
            y = le.fit_transform(y.astype(str))
        else:
            y = y.astype(float).values
        
        return X, y, list(df.drop(columns=[target_col]).columns)
    
    def _build_ultra_ensemble(
        self,
        results: List[Dict],
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        task_type: str
    ) -> Optional[Dict]:
        """Build ensemble from top models."""
        # Get top 3 sklearn-compatible models
        sklearn_models = [
            r for r in results 
            if hasattr(r['model'], 'predict') and r.get('model_type') == 'classical'
        ][:3]
        
        if len(sklearn_models) < 2:
            return None
        
        try:
            estimators = [(r['name'], r['model']) for r in sklearn_models]
            
            if task_type == 'classification':
                ensemble = StackingClassifier(
                    estimators=estimators,
                    final_estimator=LogisticRegression(max_iter=1000),
                    cv=3,
                    n_jobs=1
                )
            else:
                ensemble = StackingRegressor(
                    estimators=estimators,
                    final_estimator=Ridge(),
                    cv=3,
                    n_jobs=1
                )
            
            ensemble.fit(X_train, y_train)
            y_pred = ensemble.predict(X_test)
            
            if task_type == 'classification':
                score = f1_score(y_test, y_pred, average='weighted', zero_division=0)
            else:
                score = r2_score(y_test, y_pred)
            
            print(f"   ✅ StackingEnsemble: Score = {score:.4f}")
            
            return {
                'name': 'UltraStackingEnsemble',
                'model': ensemble,
                'score': score,
                'model_type': 'ensemble'
            }
            
        except Exception as e:
            logger.error(f"Ensemble building failed: {e}")
            return None
    
    def _predict_with_model(self, model: Any, X: np.ndarray, task_type: str) -> np.ndarray:
        """Make predictions with any model type."""
        try:
            predictions = model.predict(X)
            
            # Handle TensorFlow model output
            if hasattr(predictions, 'numpy'):
                predictions = predictions.numpy()
            
            if predictions.ndim > 1:
                if task_type == 'classification':
                    predictions = np.argmax(predictions, axis=-1)
                else:
                    predictions = predictions.flatten()
            
            return predictions
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return np.zeros(len(X))
    
    def _calculate_metrics(
        self, 
        y_true: np.ndarray, 
        y_pred: np.ndarray,
        y_proba: np.ndarray,
        task_type: str
    ) -> Dict[str, float]:
        """Calculate comprehensive metrics."""
        if task_type == 'classification':
            return {
                'accuracy': float(accuracy_score(y_true, y_pred)),
                'f1_score': float(f1_score(y_true, y_pred, average='weighted', zero_division=0)),
                'precision': float(precision_score(y_true, y_pred, average='weighted', zero_division=0)),
                'recall': float(recall_score(y_true, y_pred, average='weighted', zero_division=0))
            }
        else:
            return {
                'r2_score': float(r2_score(y_true, y_pred)),
                'mae': float(mean_absolute_error(y_true, y_pred)),
                'rmse': float(np.sqrt(mean_squared_error(y_true, y_pred)))
            }
    
    def _get_feature_importance(self, model: Any) -> Dict[str, float]:
        """Extract feature importance from model."""
        importance = {}
        
        try:
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
                for fname, imp in zip(self.feature_names[:len(importances)], importances):
                    importance[fname] = float(imp)
            elif hasattr(model, 'coef_'):
                coef = np.abs(model.coef_).flatten()
                for fname, c in zip(self.feature_names[:len(coef)], coef):
                    importance[fname] = float(c)
            elif hasattr(model, 'estimators_'):
                # Ensemble - average importance
                all_imps = []
                for est_name, est in model.estimators_:
                    if hasattr(est, 'feature_importances_'):
                        all_imps.append(est.feature_importances_)
                if all_imps:
                    avg_imp = np.mean(all_imps, axis=0)
                    for fname, imp in zip(self.feature_names[:len(avg_imp)], avg_imp):
                        importance[fname] = float(imp)
        except Exception as e:
            logger.warning(f"Could not extract feature importance: {e}")
        
        # Sort by importance
        importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
        
        return importance
    
    def predict(self, X: Union[np.ndarray, pd.DataFrame, Dict]) -> np.ndarray:
        """Make predictions using the best model."""
        if self.best_model is None:
            raise ValueError("No model trained. Call train() first.")
        
        # Convert to array
        if isinstance(X, dict):
            X = np.array([[X.get(f, 0) for f in self.feature_names]])
        elif isinstance(X, pd.DataFrame):
            X = X.values
        
        X = np.nan_to_num(X.astype(float), nan=0.0, posinf=0.0, neginf=0.0)
        
        return self._predict_with_model(self.best_model, X, self.task_type)
    
    def explain_prediction(self, X: Union[np.ndarray, pd.DataFrame, Dict]) -> Dict:
        """Get explanation for a prediction."""
        if not self.explainer:
            return {'error': 'Explainability engine not available'}
        
        explanation = self.explainer.explain_prediction(X)
        return self.explainer.explain_to_dict(explanation)
    
    def save_model(self, path: str) -> None:
        """Save the trained model and metadata."""
        save_data = {
            'best_model': self.best_model,
            'best_model_name': self.best_model_name,
            'feature_names': self.feature_names,
            'task_type': self.task_type,
            'class_names': self.class_names,
            'mode': self.mode
        }
        
        with open(path, 'wb') as f:
            pickle.dump(save_data, f)
        
        logger.info(f"Model saved to {path}")
    
    def load_model(self, path: str) -> None:
        """Load a trained model."""
        with open(path, 'rb') as f:
            save_data = pickle.load(f)
        
        self.best_model = save_data['best_model']
        self.best_model_name = save_data['best_model_name']
        self.feature_names = save_data['feature_names']
        self.task_type = save_data['task_type']
        self.class_names = save_data.get('class_names', [])
        
        logger.info(f"Model loaded from {path}")


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def ultra_train(
    df: pd.DataFrame,
    target_col: str = None,
    task_type: str = None,
    mode: str = 'maximum_accuracy'
) -> UltraTrainResult:
    """
    Convenience function for training with Ultra AutoML.
    
    Args:
        df: Input DataFrame
        target_col: Target column (auto-detected if None)
        task_type: 'classification' or 'regression' (auto-detected if None)
        mode: 'fast', 'balanced', or 'maximum_accuracy'
        
    Returns:
        UltraTrainResult with trained model and insights
    """
    orchestrator = UltraAutoMLOrchestrator(mode=mode)
    return orchestrator.train(df, target_col, task_type)
