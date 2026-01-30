"""
🧠 SMART ALGORITHM SELECTOR v1.0
================================

Intelligently selects algorithms based on dataset characteristics:
- Data type (tabular, text, time-series)
- Dataset size (small/medium/large)
- Feature types (numeric, categorical, text)
- Task type (classification, regression)
- Imbalance level

This ensures Ultra Mode trains ONLY relevant algorithms,
not wasting time on inappropriate models.

Author: AI Business Analyst Team
Version: 1.0.0
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# ALGORITHM DEFINITIONS
# =============================================================================

class AlgorithmCategory(Enum):
    """Categories of ML algorithms"""
    TREE_BASED = "tree_based"
    LINEAR = "linear"
    SVM = "svm"
    NEURAL_NET = "neural_net"
    ENSEMBLE = "ensemble"
    NAIVE_BAYES = "naive_bayes"
    NEIGHBORS = "neighbors"
    DEEP_LEARNING = "deep_learning"


@dataclass  
class AlgorithmInfo:
    """Information about an algorithm"""
    name: str
    category: AlgorithmCategory
    supports_class_weight: bool
    min_samples: int  # Minimum samples needed
    good_for_text: bool
    good_for_timeseries: bool
    good_for_tabular: bool
    training_speed: str  # 'fast', 'medium', 'slow'


# Algorithm database
ALGORITHMS = {
    # === TREE-BASED (Great for tabular) ===
    'RandomForest': AlgorithmInfo(
        'RandomForest', AlgorithmCategory.TREE_BASED,
        supports_class_weight=True, min_samples=50,
        good_for_text=False, good_for_timeseries=True, good_for_tabular=True,
        training_speed='medium'
    ),
    'XGBoost': AlgorithmInfo(
        'XGBoost', AlgorithmCategory.TREE_BASED,
        supports_class_weight=True, min_samples=100,
        good_for_text=False, good_for_timeseries=True, good_for_tabular=True,
        training_speed='medium'
    ),
    'LightGBM': AlgorithmInfo(
        'LightGBM', AlgorithmCategory.TREE_BASED,
        supports_class_weight=True, min_samples=100,
        good_for_text=False, good_for_timeseries=True, good_for_tabular=True,
        training_speed='fast'
    ),
    'CatBoost': AlgorithmInfo(
        'CatBoost', AlgorithmCategory.TREE_BASED,
        supports_class_weight=True, min_samples=100,
        good_for_text=False, good_for_timeseries=True, good_for_tabular=True,
        training_speed='slow'
    ),
    'GradientBoosting': AlgorithmInfo(
        'GradientBoosting', AlgorithmCategory.TREE_BASED,
        supports_class_weight=False, min_samples=50,
        good_for_text=False, good_for_timeseries=True, good_for_tabular=True,
        training_speed='medium'
    ),
    'ExtraTrees': AlgorithmInfo(
        'ExtraTrees', AlgorithmCategory.TREE_BASED,
        supports_class_weight=True, min_samples=50,
        good_for_text=False, good_for_timeseries=True, good_for_tabular=True,
        training_speed='medium'
    ),
    'DecisionTree': AlgorithmInfo(
        'DecisionTree', AlgorithmCategory.TREE_BASED,
        supports_class_weight=True, min_samples=20,
        good_for_text=False, good_for_timeseries=True, good_for_tabular=True,
        training_speed='fast'
    ),
    
    # === LINEAR MODELS ===
    'LogisticRegression': AlgorithmInfo(
        'LogisticRegression', AlgorithmCategory.LINEAR,
        supports_class_weight=True, min_samples=20,
        good_for_text=True, good_for_timeseries=False, good_for_tabular=True,
        training_speed='fast'
    ),
    'RidgeClassifier': AlgorithmInfo(
        'RidgeClassifier', AlgorithmCategory.LINEAR,
        supports_class_weight=True, min_samples=20,
        good_for_text=True, good_for_timeseries=False, good_for_tabular=True,
        training_speed='fast'
    ),
    'SGD': AlgorithmInfo(
        'SGD', AlgorithmCategory.LINEAR,
        supports_class_weight=True, min_samples=100,
        good_for_text=True, good_for_timeseries=False, good_for_tabular=True,
        training_speed='fast'
    ),
    
    # === SVM ===
    'SVM': AlgorithmInfo(
        'SVM', AlgorithmCategory.SVM,
        supports_class_weight=True, min_samples=50,
        good_for_text=True, good_for_timeseries=False, good_for_tabular=True,
        training_speed='slow'  # O(n^2) complexity
    ),
    
    # === NEURAL NETWORKS (sklearn) ===
    'MLP': AlgorithmInfo(
        'MLP', AlgorithmCategory.NEURAL_NET,
        supports_class_weight=False, min_samples=500,
        good_for_text=False, good_for_timeseries=False, good_for_tabular=True,
        training_speed='medium'
    ),
    
    # === DEEP LEARNING (TensorFlow) ===
    'DeepANN': AlgorithmInfo(
        'DeepANN', AlgorithmCategory.DEEP_LEARNING,
        supports_class_weight=True, min_samples=1000,
        good_for_text=False, good_for_timeseries=False, good_for_tabular=True,
        training_speed='slow'
    ),
    'LSTM': AlgorithmInfo(
        'LSTM', AlgorithmCategory.DEEP_LEARNING,
        supports_class_weight=True, min_samples=500,
        good_for_text=True, good_for_timeseries=True, good_for_tabular=False,
        training_speed='slow'
    ),
    'TextCNN': AlgorithmInfo(
        'TextCNN', AlgorithmCategory.DEEP_LEARNING,
        supports_class_weight=True, min_samples=1000,
        good_for_text=True, good_for_timeseries=False, good_for_tabular=False,
        training_speed='slow'
    ),
    
    # === NAIVE BAYES ===
    'GaussianNB': AlgorithmInfo(
        'GaussianNB', AlgorithmCategory.NAIVE_BAYES,
        supports_class_weight=False, min_samples=20,
        good_for_text=False, good_for_timeseries=False, good_for_tabular=True,
        training_speed='fast'
    ),
    'BernoulliNB': AlgorithmInfo(
        'BernoulliNB', AlgorithmCategory.NAIVE_BAYES,
        supports_class_weight=False, min_samples=20,
        good_for_text=True, good_for_timeseries=False, good_for_tabular=False,
        training_speed='fast'
    ),
    
    # === NEIGHBORS ===
    'KNN': AlgorithmInfo(
        'KNN', AlgorithmCategory.NEIGHBORS,
        supports_class_weight=False, min_samples=50,
        good_for_text=False, good_for_timeseries=False, good_for_tabular=True,
        training_speed='fast'  # But slow at prediction for large datasets
    ),
    
    # === ENSEMBLE ===
    'AdaBoost': AlgorithmInfo(
        'AdaBoost', AlgorithmCategory.ENSEMBLE,
        supports_class_weight=False, min_samples=100,
        good_for_text=False, good_for_timeseries=False, good_for_tabular=True,
        training_speed='medium'
    ),
    'Bagging': AlgorithmInfo(
        'Bagging', AlgorithmCategory.ENSEMBLE,
        supports_class_weight=False, min_samples=100,
        good_for_text=False, good_for_timeseries=False, good_for_tabular=True,
        training_speed='medium'
    ),
    'HistGradientBoosting': AlgorithmInfo(
        'HistGradientBoosting', AlgorithmCategory.ENSEMBLE,
        supports_class_weight=True, min_samples=1000,
        good_for_text=False, good_for_timeseries=False, good_for_tabular=True,
        training_speed='fast'  # Histogram-based, very fast!
    ),
}


# =============================================================================
# SMART ALGORITHM SELECTOR
# =============================================================================

class SmartAlgorithmSelector:
    """
    🧠 Intelligently selects algorithms based on dataset characteristics
    """
    
    def __init__(self):
        self.algorithms = ALGORITHMS
    
    def select_algorithms(
        self,
        data_type: str,  # 'tabular', 'text_heavy', 'time_series', 'mixed'
        task_type: str,  # 'classification', 'regression'
        n_rows: int,
        n_features: int,
        is_imbalanced: bool = False,
        imbalance_ratio: float = 1.0,
        mode: str = 'fast'  # 'fast' or 'ultra'
    ) -> Dict[str, List[str]]:
        """
        Select optimal algorithms for the given dataset
        
        Returns:
            Dict with 'selected' (list of algorithm names) and 'skipped' (with reasons)
        """
        logger.info(f"🧠 Smart Algorithm Selection for {data_type.upper()} data")
        logger.info(f"   📊 Rows: {n_rows}, Features: {n_features}")
        logger.info(f"   🎪 Task: {task_type}, Mode: {mode.upper()}")
        
        selected = []
        skipped = {}
        
        # Determine which algorithms to consider
        if mode == 'fast':
            # Fast mode: Only essential, fast algorithms
            candidates = ['LogisticRegression', 'RandomForest', 'GradientBoosting', 
                         'KNN', 'GaussianNB', 'XGBoost', 'LightGBM']
        else:
            # Ultra mode: All algorithms
            candidates = list(self.algorithms.keys())
        
        for name in candidates:
            algo = self.algorithms.get(name)
            if not algo:
                continue
            
            # Check minimum samples
            if n_rows < algo.min_samples:
                skipped[name] = f"Need {algo.min_samples}+ samples (have {n_rows})"
                continue
            
            # Check data type compatibility
            if data_type == 'tabular' and not algo.good_for_tabular:
                skipped[name] = "Not suitable for tabular data"
                continue
            elif data_type == 'text_heavy' and not algo.good_for_text:
                skipped[name] = "Not suitable for text data"
                continue
            elif data_type == 'time_series' and not algo.good_for_timeseries:
                skipped[name] = "Not suitable for time-series data"
                continue
            
            # For imbalanced data, prefer models with class_weight
            if is_imbalanced and imbalance_ratio > 20:
                if not algo.supports_class_weight:
                    # Still include but note limitation
                    logger.info(f"   ⚠️ {name}: No class_weight (will use sampling)")
            
            # SVM is too slow for large datasets
            if name == 'SVM' and n_rows > 10000:
                skipped[name] = f"Too slow for {n_rows} samples (O(n²))"
                continue
            
            # KNN is slow at prediction for large datasets
            if name == 'KNN' and n_rows > 50000:
                skipped[name] = f"Slow predictions for {n_rows} samples"
                continue
            
            # Deep learning needs TensorFlow
            if algo.category == AlgorithmCategory.DEEP_LEARNING:
                try:
                    import tensorflow as tf
                    selected.append(name)
                except ImportError:
                    skipped[name] = "TensorFlow not installed"
                    continue
            else:
                selected.append(name)
        
        # Log results
        logger.info(f"   ✅ Selected: {len(selected)} algorithms")
        logger.info(f"   ⏭️ Skipped: {len(skipped)} algorithms")
        
        for name in selected[:5]:  # Show first 5
            logger.info(f"      ✓ {name}")
        if len(selected) > 5:
            logger.info(f"      ... and {len(selected) - 5} more")
        
        return {
            'selected': selected,
            'skipped': skipped
        }
    
    def get_algorithm_info(self, name: str) -> Optional[AlgorithmInfo]:
        """Get info about a specific algorithm"""
        return self.algorithms.get(name)


# =============================================================================
# TENSORFLOW NEURAL NETWORK MODELS
# =============================================================================

def create_deep_ann_classifier(
    input_dim: int,
    n_classes: int,
    hidden_layers: tuple = (256, 128, 64, 32),
    dropout_rate: float = 0.3
):
    """
    Create a Deep ANN classifier using TensorFlow/Keras
    
    Architecture:
    - Input → Dense(256) → BatchNorm → Dropout
    - Dense(128) → BatchNorm → Dropout
    - Dense(64) → BatchNorm → Dropout
    - Dense(32) → Output
    """
    try:
        import tensorflow as tf
        from tensorflow import keras
        from tensorflow.keras import layers
        
        model = keras.Sequential([
            # Input layer
            layers.InputLayer(input_shape=(input_dim,)),
            
            # Hidden layers with batch normalization and dropout
            layers.Dense(hidden_layers[0], activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(dropout_rate),
            
            layers.Dense(hidden_layers[1], activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(dropout_rate),
            
            layers.Dense(hidden_layers[2], activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(dropout_rate / 2),
            
            layers.Dense(hidden_layers[3], activation='relu'),
            
            # Output layer
            layers.Dense(n_classes, activation='softmax' if n_classes > 2 else 'sigmoid')
        ])
        
        # Compile with appropriate loss
        if n_classes > 2:
            loss = 'sparse_categorical_crossentropy'
        else:
            loss = 'binary_crossentropy'
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss=loss,
            metrics=['accuracy']
        )
        
        return model
        
    except ImportError:
        logger.warning("TensorFlow not available, skipping DeepANN")
        return None


def create_lstm_classifier(
    seq_length: int,
    n_features: int,
    n_classes: int,
    hidden_units: int = 64
):
    """
    Create an LSTM classifier for time-series/sequential data
    """
    try:
        import tensorflow as tf
        from tensorflow import keras
        from tensorflow.keras import layers
        
        model = keras.Sequential([
            layers.InputLayer(input_shape=(seq_length, n_features)),
            layers.LSTM(hidden_units, return_sequences=True),
            layers.Dropout(0.2),
            layers.LSTM(hidden_units // 2),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            layers.Dense(n_classes, activation='softmax' if n_classes > 2 else 'sigmoid')
        ])
        
        if n_classes > 2:
            loss = 'sparse_categorical_crossentropy'
        else:
            loss = 'binary_crossentropy'
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss=loss,
            metrics=['accuracy']
        )
        
        return model
        
    except ImportError:
        logger.warning("TensorFlow not available, skipping LSTM")
        return None


def create_text_cnn_classifier(
    vocab_size: int,
    embed_dim: int = 128,
    n_classes: int = 2,
    max_length: int = 500,
    num_filters: int = 128
):
    """
    Create a 1D CNN classifier for text classification
    
    Uses multiple filter sizes (3, 4, 5) to capture different n-gram patterns
    """
    try:
        import tensorflow as tf
        from tensorflow import keras
        from tensorflow.keras import layers
        
        # Input
        inputs = layers.Input(shape=(max_length,))
        
        # Embedding
        x = layers.Embedding(vocab_size, embed_dim)(inputs)
        
        # Multiple Conv1D with different filter sizes
        conv_outputs = []
        for filter_size in [3, 4, 5]:
            conv = layers.Conv1D(num_filters, filter_size, activation='relu')(x)
            pool = layers.GlobalMaxPooling1D()(conv)
            conv_outputs.append(pool)
        
        # Concatenate all conv outputs
        concat = layers.Concatenate()(conv_outputs)
        
        # Dense layers
        x = layers.Dropout(0.5)(concat)
        x = layers.Dense(64, activation='relu')(x)
        
        # Output
        if n_classes > 2:
            outputs = layers.Dense(n_classes, activation='softmax')(x)
            loss = 'sparse_categorical_crossentropy'
        else:
            outputs = layers.Dense(1, activation='sigmoid')(x)
            loss = 'binary_crossentropy'
        
        model = keras.Model(inputs, outputs)
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss=loss,
            metrics=['accuracy']
        )
        
        return model
        
    except ImportError:
        logger.warning("TensorFlow not available, skipping TextCNN")
        return None


# =============================================================================
# SKLEARN WRAPPER FOR KERAS MODELS
# =============================================================================

class KerasClassifierWrapper:
    """
    Wrapper to make Keras models sklearn-compatible
    """
    
    def __init__(self, model, epochs=50, batch_size=32, class_weight=None):
        self.model = model
        self.epochs = epochs
        self.batch_size = batch_size
        self.class_weight = class_weight
        self._is_fitted = False
    
    def fit(self, X, y):
        """Train the model"""
        try:
            import tensorflow as tf
            
            # Early stopping
            early_stop = tf.keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=5,
                restore_best_weights=True
            )
            
            # Calculate class weights for imbalanced data
            if self.class_weight == 'balanced':
                from sklearn.utils.class_weight import compute_class_weight
                import numpy as np
                classes = np.unique(y)
                weights = compute_class_weight('balanced', classes=classes, y=y)
                self.class_weight = dict(zip(classes, weights))
            
            # Train with validation split
            self.model.fit(
                X, y,
                epochs=self.epochs,
                batch_size=self.batch_size,
                validation_split=0.2,
                callbacks=[early_stop],
                class_weight=self.class_weight,
                verbose=0
            )
            
            self._is_fitted = True
            return self
            
        except Exception as e:
            logger.error(f"Keras training error: {e}")
            raise
    
    def predict(self, X):
        """Make predictions"""
        import numpy as np
        proba = self.model.predict(X, verbose=0)
        if proba.shape[1] == 1:
            return (proba > 0.5).astype(int).flatten()
        return np.argmax(proba, axis=1)
    
    def predict_proba(self, X):
        """Get prediction probabilities"""
        import numpy as np
        proba = self.model.predict(X, verbose=0)
        if proba.shape[1] == 1:
            return np.hstack([1 - proba, proba])
        return proba
    
    @property
    def classes_(self):
        """Return class labels"""
        import numpy as np
        n_classes = self.model.output_shape[-1]
        if n_classes == 1:
            return np.array([0, 1])
        return np.arange(n_classes)


# Global instance
smart_selector = SmartAlgorithmSelector()
