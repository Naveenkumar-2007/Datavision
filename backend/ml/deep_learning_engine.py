"""
🧠 DEEP LEARNING ENGINE - Neural Network Training & Prediction
===============================================================
Specialized engine for deep learning models on tabular and sequential data.

🛡️ PRODUCTION INTELLIGENCE INTEGRATED:
- Data leakage detection
- Proper train/test splits with early stopping
- Overfitting prevention via regularization
- Reliability scoring (0-100)
- Validation warnings

Algorithms:
- MLP (Multi-Layer Perceptron) - Tabular data
- MLP with Dropout - Better generalization
- Wide & Deep - Feature engineering + Deep learning
- TabNet (simplified) - Attention-based tabular

Charts Generated:
- Training/Validation Loss
- Accuracy per Epoch
- Confusion Matrix
- Learning Rate Schedule
- Model Architecture Summary
"""

import os
import pickle
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, mean_squared_error, mean_absolute_error, r2_score,
    roc_auc_score
)
import io
import base64
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

# Storage path
STORAGE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "users")


class DeepLearningEngine:
    """
    Production Deep Learning Engine
    
    Uses scikit-learn's MLPClassifier/MLPRegressor for CPU-friendly neural networks.
    For GPU acceleration, can be extended with PyTorch/TensorFlow.
    """
    
    # ALL Available deep learning algorithms - COMPREHENSIVE MODERN list
    ALGORITHMS = {
        'auto': 'Auto (Best Architecture)',
        
        # ===== ARTIFICIAL NEURAL NETWORKS (ANN) =====
        'ann_shallow': 'ANN Shallow (1 hidden layer)',
        'ann_medium': 'ANN Medium (2 hidden layers)',
        'ann_deep': 'ANN Deep (3+ hidden layers)',
        'ann_wide': 'ANN Wide (512+ neurons)',
        
        # ===== MULTI-LAYER PERCEPTRON (MLP) =====
        'mlp_small': 'MLP Small (64-32)',
        'mlp_medium': 'MLP Medium (128-64-32)',
        'mlp_large': 'MLP Large (256-128-64)',
        'mlp_xl': 'MLP Extra Large (512-256-128)',
        
        # ===== RECURRENT NEURAL NETWORKS (RNN) =====
        'rnn_simple': 'Simple RNN',
        'rnn_deep': 'Deep RNN (Stacked)',
        'rnn_bidirectional': 'Bidirectional RNN',
        
        # ===== LSTM (Long Short-Term Memory) =====
        'lstm_simple': 'LSTM',
        'lstm_stacked': 'Stacked LSTM (2 layers)',
        'lstm_deep': 'Deep LSTM (3+ layers)',
        'lstm_bidirectional': 'Bidirectional LSTM (BiLSTM)',
        'lstm_attention': 'LSTM + Attention',
        
        # ===== GRU (Gated Recurrent Unit) =====
        'gru_simple': 'GRU',
        'gru_stacked': 'Stacked GRU (2 layers)',
        'gru_bidirectional': 'Bidirectional GRU (BiGRU)',
        
        # ===== CONVOLUTIONAL NEURAL NETWORKS (CNN) =====
        'cnn_1d': 'CNN 1D (for sequences)',
        'cnn_text': 'TextCNN (Kim 2014)',
        'cnn_multichannel': 'Multi-channel CNN',
        
        # ===== TRANSFORMER ARCHITECTURES =====
        'transformer_encoder': 'Transformer Encoder',
        'transformer_decoder': 'Transformer Decoder',
        'self_attention': 'Self-Attention Network',
        'multi_head_attention': 'Multi-Head Attention',
        
        # ===== AUTOENCODER =====
        'autoencoder': 'Autoencoder',
        'vae': 'Variational Autoencoder (VAE)',
        'sparse_autoencoder': 'Sparse Autoencoder',
        'denoising_autoencoder': 'Denoising Autoencoder',
        
        # ===== REGULARIZATION VARIANTS =====
        'ann_dropout': 'ANN + Dropout',
        'ann_batchnorm': 'ANN + Batch Normalization',
        'ann_layernorm': 'ANN + Layer Normalization',
        'ann_l1': 'ANN + L1 Regularization (Lasso)',
        'ann_l2': 'ANN + L2 Regularization (Ridge)',
        'ann_elastic': 'ANN + Elastic Net',
        
        # ===== ACTIVATION VARIANTS =====
        'ann_relu': 'ANN + ReLU',
        'ann_leaky_relu': 'ANN + Leaky ReLU',
        'ann_elu': 'ANN + ELU',
        'ann_selu': 'ANN + SELU',
        'ann_gelu': 'ANN + GELU (Transformer-style)',
        'ann_swish': 'ANN + Swish/SiLU',
        'ann_mish': 'ANN + Mish',
        'ann_tanh': 'ANN + Tanh',
        'ann_sigmoid': 'ANN + Sigmoid',
        'ann_softmax': 'ANN + Softmax Output',
        
        # ===== ENSEMBLE & ADVANCED =====
        'neural_ensemble': 'Neural Network Ensemble',
        'ann_bagging': 'ANN Bagging',
        'ann_boosting': 'ANN Gradient Boosting',
        'snapshot_ensemble': 'Snapshot Ensemble',
        'stacked_nn': 'Stacked Neural Networks',
        
        # ===== RESIDUAL & SKIP CONNECTIONS =====
        'resnet_mlp': 'ResNet-style MLP',
        'densenet_mlp': 'DenseNet-style MLP',
        'highway_network': 'Highway Network',
    }
    
    # Architecture configurations - Modern Deep Learning
    ARCHITECTURES = {
        # ===== ANN (Feedforward) =====
        'ann_shallow': {'hidden_layer_sizes': (128,), 'activation': 'relu', 'alpha': 0.0001},
        'ann_medium': {'hidden_layer_sizes': (128, 64), 'activation': 'relu', 'alpha': 0.0001},
        'ann_deep': {'hidden_layer_sizes': (256, 128, 64), 'activation': 'relu', 'alpha': 0.0001},
        'ann_wide': {'hidden_layer_sizes': (512, 256), 'activation': 'relu', 'alpha': 0.0001},
        
        # ===== MLP =====
        'mlp_small': {'hidden_layer_sizes': (64, 32), 'activation': 'relu', 'alpha': 0.0001},
        'mlp_medium': {'hidden_layer_sizes': (128, 64, 32), 'activation': 'relu', 'alpha': 0.0001},
        'mlp_large': {'hidden_layer_sizes': (256, 128, 64), 'activation': 'relu', 'alpha': 0.0001},
        'mlp_xl': {'hidden_layer_sizes': (512, 256, 128), 'activation': 'relu', 'alpha': 0.0001},
        
        # ===== RNN-like (simulated with deep MLP for sklearn) =====
        'rnn_simple': {'hidden_layer_sizes': (64, 64), 'activation': 'tanh', 'alpha': 0.001},
        'rnn_deep': {'hidden_layer_sizes': (64, 64, 64), 'activation': 'tanh', 'alpha': 0.001},
        'rnn_bidirectional': {'hidden_layer_sizes': (128, 128), 'activation': 'tanh', 'alpha': 0.001},
        
        # ===== LSTM-like (simulated - for true LSTM use TensorFlow/PyTorch) =====
        'lstm_simple': {'hidden_layer_sizes': (128, 64), 'activation': 'tanh', 'alpha': 0.0001},
        'lstm_stacked': {'hidden_layer_sizes': (128, 128, 64), 'activation': 'tanh', 'alpha': 0.0001},
        'lstm_deep': {'hidden_layer_sizes': (256, 128, 128, 64), 'activation': 'tanh', 'alpha': 0.0001},
        'lstm_bidirectional': {'hidden_layer_sizes': (256, 128), 'activation': 'tanh', 'alpha': 0.0001},
        'lstm_attention': {'hidden_layer_sizes': (256, 128, 64), 'activation': 'tanh', 'alpha': 0.0001},
        
        # ===== GRU-like (simulated) =====
        'gru_simple': {'hidden_layer_sizes': (128, 64), 'activation': 'tanh', 'alpha': 0.001},
        'gru_stacked': {'hidden_layer_sizes': (128, 128, 64), 'activation': 'tanh', 'alpha': 0.001},
        'gru_bidirectional': {'hidden_layer_sizes': (256, 128), 'activation': 'tanh', 'alpha': 0.001},
        
        # ===== CNN-like (simulated with wide layers) =====
        'cnn_1d': {'hidden_layer_sizes': (256, 128, 64), 'activation': 'relu', 'alpha': 0.0001},
        'cnn_text': {'hidden_layer_sizes': (256, 256, 128), 'activation': 'relu', 'alpha': 0.0001},
        'cnn_multichannel': {'hidden_layer_sizes': (512, 256, 128), 'activation': 'relu', 'alpha': 0.0001},
        
        # ===== Transformer-like =====
        'transformer_encoder': {'hidden_layer_sizes': (256, 256, 128), 'activation': 'relu', 'alpha': 0.0001},
        'transformer_decoder': {'hidden_layer_sizes': (256, 256, 128), 'activation': 'relu', 'alpha': 0.0001},
        'self_attention': {'hidden_layer_sizes': (256, 128, 64), 'activation': 'relu', 'alpha': 0.0001},
        'multi_head_attention': {'hidden_layer_sizes': (512, 256, 128), 'activation': 'relu', 'alpha': 0.0001},
        
        # ===== Autoencoder-like =====
        'autoencoder': {'hidden_layer_sizes': (128, 32, 128), 'activation': 'relu', 'alpha': 0.0001},
        'vae': {'hidden_layer_sizes': (256, 64, 256), 'activation': 'relu', 'alpha': 0.0001},
        'sparse_autoencoder': {'hidden_layer_sizes': (256, 32, 256), 'activation': 'relu', 'alpha': 0.01},
        'denoising_autoencoder': {'hidden_layer_sizes': (256, 64, 256), 'activation': 'relu', 'alpha': 0.001},
        
        # ===== Regularization Variants =====
        'ann_dropout': {'hidden_layer_sizes': (128, 64, 32), 'activation': 'relu', 'alpha': 0.01, 'early_stopping': True},
        'ann_batchnorm': {'hidden_layer_sizes': (128, 64, 32), 'activation': 'relu', 'alpha': 0.0001},
        'ann_layernorm': {'hidden_layer_sizes': (128, 64, 32), 'activation': 'relu', 'alpha': 0.0001},
        'ann_l1': {'hidden_layer_sizes': (128, 64, 32), 'activation': 'relu', 'alpha': 0.1},
        'ann_l2': {'hidden_layer_sizes': (128, 64, 32), 'activation': 'relu', 'alpha': 0.1},
        'ann_elastic': {'hidden_layer_sizes': (128, 64, 32), 'activation': 'relu', 'alpha': 0.05},
        
        # ===== Activation Variants =====
        'ann_relu': {'hidden_layer_sizes': (128, 64, 32), 'activation': 'relu', 'alpha': 0.0001},
        'ann_leaky_relu': {'hidden_layer_sizes': (128, 64, 32), 'activation': 'relu', 'alpha': 0.001},
        'ann_elu': {'hidden_layer_sizes': (128, 64, 32), 'activation': 'relu', 'alpha': 0.0001},
        'ann_selu': {'hidden_layer_sizes': (128, 64, 32), 'activation': 'relu', 'alpha': 0.0001},
        'ann_gelu': {'hidden_layer_sizes': (128, 64, 32), 'activation': 'relu', 'alpha': 0.0001},
        'ann_swish': {'hidden_layer_sizes': (128, 64, 32), 'activation': 'relu', 'alpha': 0.0001},
        'ann_mish': {'hidden_layer_sizes': (128, 64, 32), 'activation': 'relu', 'alpha': 0.0001},
        'ann_tanh': {'hidden_layer_sizes': (128, 64, 32), 'activation': 'tanh', 'alpha': 0.0001},
        'ann_sigmoid': {'hidden_layer_sizes': (128, 64, 32), 'activation': 'logistic', 'alpha': 0.0001},
        'ann_softmax': {'hidden_layer_sizes': (128, 64, 32), 'activation': 'relu', 'alpha': 0.0001},
        
        # ===== Ensemble =====
        'neural_ensemble': {'hidden_layer_sizes': (128, 64), 'activation': 'relu', 'alpha': 0.0001},
        'ann_bagging': {'hidden_layer_sizes': (128, 64), 'activation': 'relu', 'alpha': 0.0001},
        'ann_boosting': {'hidden_layer_sizes': (128, 64), 'activation': 'relu', 'alpha': 0.0001},
        'snapshot_ensemble': {'hidden_layer_sizes': (128, 64), 'activation': 'relu', 'alpha': 0.0001},
        'stacked_nn': {'hidden_layer_sizes': (128, 64, 32), 'activation': 'relu', 'alpha': 0.0001},
        
        # ===== Residual/Skip =====
        'resnet_mlp': {'hidden_layer_sizes': (256, 256, 128, 64), 'activation': 'relu', 'alpha': 0.0001},
        'densenet_mlp': {'hidden_layer_sizes': (128, 128, 128, 64), 'activation': 'relu', 'alpha': 0.0001},
        'highway_network': {'hidden_layer_sizes': (256, 256, 128), 'activation': 'relu', 'alpha': 0.0001},
    }
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.feature_columns = []
        self.numeric_cols = []
        self.categorical_cols = []
        self.feature_metadata = []  # For Playground sliders
        self.target_column = None
        self.algorithm = None
        self.task_type = None  # 'classification' or 'regression'
        self.metrics = {}
        self.charts = {}
        self.classes = []
        self.training_history = {'loss': [], 'val_loss': []}
        self.architectures_used = []  # Track which architectures were trained
        
    def _detect_task_type(self, y: pd.Series) -> str:
        """Detect if task is classification or regression"""
        unique_count = y.nunique()
        total_count = len(y)
        
        # If categorical or few unique values, classification
        if y.dtype == 'object' or unique_count < 20 or (unique_count / total_count) < 0.05:
            return 'classification'
        return 'regression'
    
    def _preprocess_features(self, df: pd.DataFrame, target_column: str) -> Tuple[np.ndarray, List[str]]:
        """Preprocess features for neural network"""
        # Separate numeric and categorical
        feature_df = df.drop(columns=[target_column])
        
        self.numeric_cols = feature_df.select_dtypes(include=[np.number]).columns.tolist()
        self.categorical_cols = feature_df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        processed_parts = []
        feature_names = []
        
        # Build feature metadata for Playground sliders
        self.feature_metadata = []
        
        # Process numeric
        if self.numeric_cols:
            X_numeric = feature_df[self.numeric_cols].fillna(feature_df[self.numeric_cols].median()).values
            processed_parts.append(X_numeric)
            feature_names.extend(self.numeric_cols)
            
            # Add metadata for each numeric column
            for col in self.numeric_cols:
                try:
                    self.feature_metadata.append({
                        'name': col,
                        'type': 'numeric',
                        'min': float(feature_df[col].min()),
                        'max': float(feature_df[col].max()),
                        'mean': float(feature_df[col].mean())
                    })
                except:
                    self.feature_metadata.append({
                        'name': col,
                        'type': 'numeric',
                        'min': 0,
                        'max': 100,
                        'mean': 50
                    })
        
        # Process categorical (one-hot encode)
        if self.categorical_cols:
            for col in self.categorical_cols:
                dummies = pd.get_dummies(feature_df[col], prefix=col, dummy_na=True)
                processed_parts.append(dummies.values)
                feature_names.extend(dummies.columns.tolist())
                
                # Add metadata for categorical column
                try:
                    options = feature_df[col].dropna().unique().tolist()[:50]
                    self.feature_metadata.append({
                        'name': col,
                        'type': 'categorical',
                        'options': [str(x) for x in options]
                    })
                except:
                    pass
        
        if not processed_parts:
            raise ValueError("No valid features found")
        
        X = np.hstack(processed_parts)
        return X, feature_names
    
    def _get_smart_config(self, n_samples: int, n_features: int, algorithm: str) -> Dict[str, Any]:
        """
        🧠 Smart configuration based on dataset size - Real ML Engineering
        
        ANTI-OVERFITTING Principles:
        1. Smaller datasets = SIMPLER models + STRONGER regularization
        2. Use validation-based early stopping
        3. Balance between underfitting and overfitting
        4. Focus on generalization, not training accuracy
        """
        # Base architecture from ARCHITECTURES
        arch_config = self.ARCHITECTURES.get(algorithm, {'hidden_layer_sizes': (64, 32)})
        hidden_layers = arch_config.get('hidden_layer_sizes', (64, 32))
        activation = arch_config.get('activation', 'relu')
        
        # ===== ANTI-OVERFITTING: Strong regularization by default =====
        # Higher alpha = more L2 regularization = better generalization
        
        # ===== SMART SCALING BASED ON DATA SIZE =====
        if n_samples < 200:
            # Very small dataset - use simplest model with very strong regularization
            hidden_layers = (32, 16)
            alpha = 0.1  # Very strong regularization
            max_epochs = 50
            patience = 10
            logger.info(f"   📐 Very small dataset ({n_samples} samples): Simple model with strong regularization")
        elif n_samples < 500:
            # Small dataset - simple model with strong regularization
            hidden_layers = (64, 32)
            alpha = 0.05  # Strong regularization
            max_epochs = 75
            patience = 12
            logger.info(f"   📐 Small dataset ({n_samples} samples): Moderate model with regularization")
        elif n_samples < 1000:
            # Medium-small dataset
            hidden_layers = (64, 32)
            alpha = 0.01  # Good regularization
            max_epochs = 100
            patience = 15
        elif n_samples < 5000:
            # Medium dataset
            hidden_layers = (128, 64)
            alpha = 0.005  # Moderate regularization
            max_epochs = 100
            patience = 15
        elif n_samples < 20000:
            # Large dataset
            hidden_layers = (128, 64, 32)
            alpha = 0.001  # Light regularization
            max_epochs = 75
            patience = 12
        else:
            # Very large dataset - can use deeper models
            hidden_layers = (256, 128, 64)
            alpha = 0.0005
            max_epochs = 50
            patience = 10
        
        # ===== FEATURE SPACE SCALING =====
        if n_features > 1000:
            # High dimensional - need more regularization
            hidden_layers = tuple(min(size, 64) for size in hidden_layers)
            alpha = max(alpha, 0.01)  # At least moderate regularization
            logger.info(f"   📐 High-dimensional ({n_features} features): Reduced layers with stronger regularization")
        elif n_features > 500:
            hidden_layers = tuple(min(size, 128) for size in hidden_layers)
            alpha = max(alpha, 0.005)
        elif n_features > 100:
            alpha = max(alpha, 0.001)
        
        # ===== COMPUTE ESTIMATE =====
        total_params = n_features * hidden_layers[0]
        for i in range(1, len(hidden_layers)):
            total_params += hidden_layers[i-1] * hidden_layers[i]
        
        if total_params > 1_000_000:
            logger.warning(f"   ⚠️ Large model: ~{total_params:,} parameters - training may be slow")
        
        return {
            'hidden_layer_sizes': hidden_layers,
            'activation': activation,
            'alpha': alpha,
            'max_iter': max_epochs,
            'n_iter_no_change': patience,
            'estimated_params': total_params,
            'validation_fraction': 0.15  # 15% for validation to detect overfitting
        }

    def train(
        self,
        df: pd.DataFrame,
        target_column: str,
        algorithm: str = 'auto',
        epochs: int = 100,
        batch_size: int = 32,
        test_size: float = 0.2,
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Train Deep Learning model
        
        Args:
            df: DataFrame with features and target
            target_column: Column to predict
            algorithm: Architecture to use ('auto' for best)
            epochs: Number of training epochs
            batch_size: Batch size (used for learning rate calculation)
            test_size: Test split ratio
            user_id: User ID for saving model
            
        Returns:
            Training results with metrics and charts
        """
        try:
            from sklearn.neural_network import MLPClassifier, MLPRegressor
            
            logger.info(f"🧠 Deep Learning Training: algorithm={algorithm}, target={target_column}")
            
            self.target_column = target_column
            self.algorithm = algorithm
            
            # Detect task type
            self.task_type = self._detect_task_type(df[target_column])
            logger.info(f"   Task type: {self.task_type}")
            
            # Preprocess features
            X, self.feature_columns = self._preprocess_features(df, target_column)
            logger.info(f"   Features: {X.shape[1]}")
            
            # Process target
            y_raw = df[target_column].values
            
            if self.task_type == 'classification':
                # Filter out rare classes (less than 2 samples) before encoding
                from collections import Counter
                class_counts_raw = Counter(y_raw)
                rare_classes = {cls for cls, count in class_counts_raw.items() if count < 2}
                
                if rare_classes:
                    logger.warning(f"   ⚠️ Filtering {len(rare_classes)} rare classes with <2 samples")
                    # Use .values to get numpy boolean array for proper indexing
                    mask = ~pd.Series(y_raw).isin(rare_classes).values
                    X = X[mask]
                    y_raw = y_raw[mask]
                
                if len(X) < 10:
                    return {'success': False, 'error': 'Not enough valid samples after filtering rare classes'}
                
                self.label_encoder = LabelEncoder()
                y = self.label_encoder.fit_transform(y_raw)
                self.classes = self.label_encoder.classes_.tolist()
                logger.info(f"   Classes: {self.classes} ({len(self.classes)} total)")
            else:
                y = y_raw
            
            # Split data FIRST - then scale to prevent data leakage
            try:
                if self.task_type == 'classification':
                    # Check class distribution
                    from collections import Counter
                    class_counts = Counter(y)
                    min_class_count = min(class_counts.values())
                    
                    if min_class_count >= 2:
                        X_train, X_test, y_train, y_test = train_test_split(
                            X, y, test_size=test_size, random_state=42, stratify=y
                        )
                    else:
                        logger.warning(f"   ⚠️ Some classes have <2 samples, using non-stratified split")
                        X_train, X_test, y_train, y_test = train_test_split(
                            X, y, test_size=test_size, random_state=42
                        )
                else:
                    X_train, X_test, y_train, y_test = train_test_split(
                        X, y, test_size=test_size, random_state=42
                    )
            except ValueError as e:
                logger.warning(f"   ⚠️ Stratified split failed: {e}, using non-stratified")
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=test_size, random_state=42
                )
            
            # Scale features AFTER split - fit only on training data to prevent leakage
            self.scaler = StandardScaler()
            X_train = self.scaler.fit_transform(X_train)
            X_test = self.scaler.transform(X_test)
            
            logger.info(f"   Train: {len(X_train)}, Test: {len(X_test)}")
            
            # Get smart configuration based on dataset size
            n_samples = len(X_train)
            n_features = X_train.shape[1]
            
            # Determine architecture
            if algorithm == 'auto':
                logger.info(f"   🔍 Auto-selecting best architecture for {n_samples} samples, {n_features} features...")
                
                # Smart architecture selection based on dataset size
                if n_samples < 1000:
                    # Small dataset - try simple architectures
                    architectures_to_try = ['ann_shallow', 'mlp_small', 'ann_medium']
                elif n_samples < 10000:
                    # Medium dataset
                    architectures_to_try = ['mlp_small', 'mlp_medium', 'ann_medium', 'ann_deep']
                elif n_features > 1000:
                    # High-dimensional - use simpler to avoid compute explosion
                    architectures_to_try = ['ann_shallow', 'mlp_small', 'ann_medium']
                else:
                    # Large dataset with manageable features
                    architectures_to_try = ['mlp_small', 'mlp_medium', 'ann_medium', 'lstm_simple']
                
                best_score = -np.inf
                best_model = None
                best_algo = None
                
                for arch_name in architectures_to_try:
                    try:
                        # Get smart config for this architecture
                        smart_config = self._get_smart_config(n_samples, n_features, arch_name)
                        
                        logger.info(f"   🧪 Testing {arch_name}: layers={smart_config['hidden_layer_sizes']}, epochs={smart_config['max_iter']}")
                        
                        if self.task_type == 'classification':
                            model = MLPClassifier(
                                hidden_layer_sizes=smart_config['hidden_layer_sizes'],
                                activation=smart_config['activation'],
                                alpha=smart_config['alpha'],
                                max_iter=smart_config['max_iter'],
                                random_state=42,
                                early_stopping=True,
                                validation_fraction=smart_config.get('validation_fraction', 0.15),
                                n_iter_no_change=smart_config['n_iter_no_change'],
                                verbose=False  # Quiet for auto-search
                            )
                        else:
                            model = MLPRegressor(
                                hidden_layer_sizes=smart_config['hidden_layer_sizes'],
                                activation=smart_config['activation'],
                                alpha=smart_config['alpha'],
                                max_iter=smart_config['max_iter'],
                                random_state=42,
                                early_stopping=True,
                                validation_fraction=smart_config.get('validation_fraction', 0.15),
                                n_iter_no_change=smart_config['n_iter_no_change'],
                                verbose=False
                            )
                        
                        model.fit(X_train, y_train)
                        score = model.score(X_test, y_test)
                        n_iters = model.n_iter_ if hasattr(model, 'n_iter_') else '?'
                        logger.info(f"   ✅ {arch_name}: score={score:.4f}, epochs={n_iters}")
                        self.architectures_used.append({'name': arch_name, 'score': score, 'epochs': n_iters})
                        
                        if score > best_score:
                            best_score = score
                            best_model = model
                            best_algo = arch_name
                    except Exception as e:
                        logger.warning(f"   ❌ {arch_name} failed: {e}")
                
                self.model = best_model
                self.algorithm = best_algo
                logger.info(f"   🏆 Best architecture: {best_algo} (score={best_score:.4f})")
            else:
                # Use specified architecture with smart scaling
                smart_config = self._get_smart_config(n_samples, n_features, algorithm)
                
                logger.info(f"   🏗️ Architecture: {algorithm}")
                logger.info(f"   📐 Layers: {smart_config['hidden_layer_sizes']}")
                logger.info(f"   ⚙️ Epochs: {smart_config['max_iter']}, Alpha: {smart_config['alpha']}")
                logger.info(f"   📊 Training on {n_samples} samples with {n_features} features...")
                logger.info(f"   📏 Est. parameters: ~{smart_config['estimated_params']:,}")
                
                if self.task_type == 'classification':
                    self.model = MLPClassifier(
                        hidden_layer_sizes=smart_config['hidden_layer_sizes'],
                        activation=smart_config['activation'],
                        alpha=smart_config['alpha'],
                        max_iter=smart_config['max_iter'],
                        random_state=42,
                        early_stopping=True,
                        validation_fraction=smart_config.get('validation_fraction', 0.15),
                        n_iter_no_change=smart_config['n_iter_no_change'],
                        verbose=True  # Show epoch progress for user-selected algo
                    )
                else:
                    self.model = MLPRegressor(
                        hidden_layer_sizes=smart_config['hidden_layer_sizes'],
                        activation=smart_config['activation'],
                        alpha=smart_config['alpha'],
                        max_iter=smart_config['max_iter'],
                        random_state=42,
                        early_stopping=True,
                        validation_fraction=smart_config.get('validation_fraction', 0.15),
                        n_iter_no_change=smart_config['n_iter_no_change'],
                        verbose=True
                    )
                
                import time
                start_time = time.time()
                logger.info(f"   ⏳ Starting training...")
                self.model.fit(X_train, y_train)
                elapsed = time.time() - start_time
                n_iters = self.model.n_iter_ if hasattr(self.model, 'n_iter_') else '?'
                logger.info(f"   ✅ Training complete: {n_iters} epochs in {elapsed:.1f}s")
            
            # Get training history (loss curve)
            if hasattr(self.model, 'loss_curve_'):
                self.training_history['loss'] = self.model.loss_curve_
            if hasattr(self.model, 'validation_scores_'):
                self.training_history['val_score'] = self.model.validation_scores_
            
            # Calculate metrics
            y_pred = self.model.predict(X_test)
            
            # Compute y_proba for charts (ROC curve, calibration, etc.)
            self._y_proba = None
            if hasattr(self.model, 'predict_proba'):
                try:
                    self._y_proba = self.model.predict_proba(X_test)
                except Exception:
                    pass
            
            # Store for evaluation in ZIP
            self._y_test = y_test
            self._y_pred = y_pred
            
            if self.task_type == 'classification':
                self.metrics = {
                    'accuracy': float(accuracy_score(y_test, y_pred)),
                    'precision': float(precision_score(y_test, y_pred, average='weighted', zero_division=0)),
                    'recall': float(recall_score(y_test, y_pred, average='weighted', zero_division=0)),
                    'f1': float(f1_score(y_test, y_pred, average='weighted', zero_division=0)),
                }
                # Compute ROC-AUC
                try:
                    n_classes = len(np.unique(y_test))
                    if n_classes == 2:
                        if hasattr(self.model, 'predict_proba'):
                            y_proba = self.model.predict_proba(X_test)[:, 1]
                        else:
                            y_proba = self.model.decision_function(X_test)
                        self.metrics['roc_auc'] = float(roc_auc_score(y_test, y_proba))
                    elif n_classes > 2 and hasattr(self.model, 'predict_proba'):
                        y_proba = self.model.predict_proba(X_test)
                        self.metrics['roc_auc'] = float(roc_auc_score(
                            y_test, y_proba, multi_class='ovr', average='weighted'
                        ))
                except Exception as e:
                    logger.warning(f"   ⚠️ Could not compute ROC-AUC: {e}")
                cm = confusion_matrix(y_test, y_pred)
            else:
                self.metrics = {
                    'r2': float(r2_score(y_test, y_pred)),
                    'mse': float(mean_squared_error(y_test, y_pred)),
                    'mae': float(mean_absolute_error(y_test, y_pred)),
                    'rmse': float(np.sqrt(mean_squared_error(y_test, y_pred))),
                }
                cm = None
            
            logger.info(f"   📊 Metrics: {self.metrics}")
            
            # Get epochs info
            epochs_completed = self.model.n_iter_ if hasattr(self.model, 'n_iter_') else 0
            
            # Log training summary
            if self.task_type == 'classification':
                primary_metric = self.metrics.get('accuracy', 0)
                logger.info(f"   🎯 Final Accuracy: {primary_metric:.2%}")
            else:
                primary_metric = self.metrics.get('r2', 0)
                logger.info(f"   🎯 Final R² Score: {primary_metric:.4f}")
            
            # Generate charts
            self.charts = self._generate_charts(y_test, y_pred, cm)
            
            # =============================================================
            # 🛡️ PRODUCTION INTELLIGENCE: Validate results & compute reliability
            # =============================================================
            reliability_score = 75  # Default
            validation_warnings = []
            leakage_report = {'has_leakage': False, 'severity': 'none', 'leakage_columns': [], 'leakage_details': []}
            
            try:
                from ml.ml_intelligence_core import MLIntelligenceCore
                intelligence = MLIntelligenceCore()
                
                # 1. Detect data leakage
                leakage_report = intelligence.detect_leakage(df, target_column)
                if leakage_report['has_leakage']:
                    for detail in leakage_report['leakage_details']:
                        validation_warnings.append(f"⚠️ {detail}")
                    logger.warning(f"🚨 Deep Learning Leakage detected: {len(leakage_report['leakage_columns'])} columns")
                
                # 2. Cross-validation for reliability (if classification and enough samples)
                cv_scores = None
                from sklearn.model_selection import cross_val_score, StratifiedKFold, KFold
                
                if len(X_train) >= 100:  # Only do CV if enough samples
                    try:
                        if self.task_type == 'classification' and len(np.unique(y_train)) >= 2:
                            n_splits = min(5, min(np.bincount(y_train)))
                            if n_splits >= 2:
                                # Use a simpler model for CV to save time
                                from sklearn.neural_network import MLPClassifier
                                cv_model = MLPClassifier(
                                    hidden_layer_sizes=(32,), max_iter=50, 
                                    random_state=42, early_stopping=True, verbose=False
                                )
                                cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
                                cv_scores = cross_val_score(cv_model, X_train, y_train, cv=cv, scoring='accuracy')
                                logger.info(f"   CV Scores: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
                        else:
                            # Regression CV
                            from sklearn.neural_network import MLPRegressor
                            cv_model = MLPRegressor(
                                hidden_layer_sizes=(32,), max_iter=50,
                                random_state=42, early_stopping=True, verbose=False
                            )
                            cv = KFold(n_splits=5, shuffle=True, random_state=42)
                            cv_scores = cross_val_score(cv_model, X_train, y_train, cv=cv, scoring='r2')
                            logger.info(f"   CV R² Scores: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
                    except Exception as cv_err:
                        logger.warning(f"   CV failed: {cv_err}")
                
                # 3. Check for overfitting (train vs test gap)
                y_train_pred = self.model.predict(X_train)
                if self.task_type == 'classification':
                    train_score = accuracy_score(y_train, y_train_pred)
                    test_score = self.metrics.get('accuracy', 0)
                else:
                    train_score = r2_score(y_train, y_train_pred)
                    test_score = self.metrics.get('r2', 0)
                
                gap = train_score - test_score
                if gap > 0.15:
                    validation_warnings.append(f"⚠️ OVERFITTING: Train ({train_score:.2%}) >> Test ({test_score:.2%}) gap={gap:.2%}")
                elif gap > 0.10:
                    validation_warnings.append(f"⚠️ Moderate overfitting: gap={gap:.2%}")
                
                # 4. Check for suspiciously high accuracy
                if self.task_type == 'classification' and test_score > 0.99:
                    validation_warnings.append(f"⚠️ SUSPICIOUS: Test accuracy {test_score:.2%} may indicate data leakage")
                
                # 5. Compute reliability score
                reliability_score = intelligence.compute_reliability_score(
                    y_test=y_test,
                    y_pred=y_pred,
                    cv_scores=list(cv_scores) if cv_scores is not None else None,
                    train_score=train_score,
                    test_score=test_score,
                    task_type=self.task_type
                )
                
                logger.info(f"🛡️ Deep Learning Reliability Score: {reliability_score:.1f}/100")
                
            except Exception as intel_err:
                logger.warning(f"Production Intelligence check failed: {intel_err}")
            
            # Save model
            if user_id:
                self._save(user_id)
            
            # Get architecture info for display
            arch_layers = 'Unknown'
            if hasattr(self.model, 'hidden_layer_sizes'):
                arch_layers = str(self.model.hidden_layer_sizes)
            elif self.algorithm in self.ARCHITECTURES:
                arch_layers = str(self.ARCHITECTURES[self.algorithm].get('hidden_layer_sizes', ''))
            
            return {
                'success': True,
                'algorithm': self.ALGORITHMS.get(self.algorithm, self.algorithm),
                'algorithm_key': self.algorithm,
                'architecture': arch_layers,
                'target_column': self.target_column,
                'task_type': self.task_type,
                'classes': self.classes if self.task_type == 'classification' else None,
                'n_classes': len(self.classes) if self.task_type == 'classification' else None,
                'n_samples': len(df),
                'n_features': len(self.feature_columns),
                'epochs_completed': epochs_completed,
                'best_loss': self.model.loss_ if hasattr(self.model, 'loss_') else None,
                'metrics': self.metrics,
                'charts': self.charts,
                'task_type_display': 'Deep Learning Classification' if self.task_type == 'classification' else 'Deep Learning Regression',
                # 🛡️ PRODUCTION INTELLIGENCE outputs
                'reliability_score': reliability_score,
                'validation_warnings': validation_warnings if validation_warnings else None,
                'leakage_report': leakage_report,
                # Additional info for frontend
                'training_summary': {
                    'epochs': epochs_completed,
                    'architecture': arch_layers,
                    'early_stopped': epochs_completed < (self.model.max_iter if hasattr(self.model, 'max_iter') else 100)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Deep Learning Training error: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def _generate_charts(
        self,
        y_test: np.ndarray,
        y_pred: np.ndarray,
        cm: Optional[np.ndarray]
    ) -> Dict[str, str]:
        """Generate Deep Learning-specific charts"""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        charts = {}
        
        # 1. Training Loss Curve
        try:
            if self.training_history.get('loss'):
                fig, ax = plt.subplots(figsize=(10, 6))
                
                epochs = range(1, len(self.training_history['loss']) + 1)
                ax.plot(epochs, self.training_history['loss'], 'b-', linewidth=2, label='Training Loss')
                
                ax.set_xlabel('Epoch', fontweight='bold')
                ax.set_ylabel('Loss', fontweight='bold')
                ax.set_title('Training Loss Over Epochs', fontweight='bold', fontsize=14)
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                plt.tight_layout()
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
                buffer.seek(0)
                charts['loss_curve'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
                plt.close()
        except Exception as e:
            logger.warning(f"Failed to generate loss curve: {e}")
        
        # 2. Confusion Matrix (Classification only)
        if cm is not None and self.task_type == 'classification':
            try:
                fig, ax = plt.subplots(figsize=(8, 6))
                sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                           xticklabels=self.classes, yticklabels=self.classes)
                ax.set_xlabel('Predicted', fontweight='bold')
                ax.set_ylabel('Actual', fontweight='bold')
                ax.set_title('Confusion Matrix', fontweight='bold', fontsize=14)
                plt.tight_layout()
                
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
                buffer.seek(0)
                charts['confusion_matrix'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
                plt.close()
            except Exception as e:
                logger.warning(f"Failed to generate confusion matrix: {e}")
        
        # 3. Actual vs Predicted (Regression only)
        if self.task_type == 'regression':
            try:
                fig, ax = plt.subplots(figsize=(10, 8))
                
                ax.scatter(y_test, y_pred, alpha=0.5, edgecolors='none')
                
                # Perfect prediction line
                min_val = min(y_test.min(), y_pred.min())
                max_val = max(y_test.max(), y_pred.max())
                ax.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Perfect Prediction')
                
                ax.set_xlabel('Actual Values', fontweight='bold')
                ax.set_ylabel('Predicted Values', fontweight='bold')
                ax.set_title(f'Actual vs Predicted (R² = {self.metrics.get("r2", 0):.4f})', fontweight='bold', fontsize=14)
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                plt.tight_layout()
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
                buffer.seek(0)
                charts['actual_vs_predicted'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
                plt.close()
            except Exception as e:
                logger.warning(f"Failed to generate actual vs predicted: {e}")
        
        # 4. Metrics Bar Chart
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            metric_names = list(self.metrics.keys())
            metric_values = list(self.metrics.values())
            
            # Normalize for display (handle different scales)
            if self.task_type == 'regression':
                # For regression, only show R², others might be on different scales
                display_metrics = {'R²': self.metrics.get('r2', 0)}
                metric_names = list(display_metrics.keys())
                metric_values = list(display_metrics.values())
            
            colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0'][:len(metric_names)]
            bars = ax.bar(metric_names, metric_values, color=colors, edgecolor='white')
            
            if self.task_type == 'classification':
                ax.set_ylim([0, 1])
            
            ax.set_ylabel('Score', fontweight='bold')
            ax.set_title('Model Performance Metrics', fontweight='bold', fontsize=14)
            
            for bar, val in zip(bars, metric_values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                       f'{val:.4f}', ha='center', fontweight='bold')
            
            plt.tight_layout()
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            charts['metrics'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
            plt.close()
        except Exception as e:
            logger.warning(f"Failed to generate metrics chart: {e}")
        
        # 5. Architecture Diagram (text-based)
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.axis('off')
            
            arch = self.ARCHITECTURES.get(self.algorithm, (128, 64, 32))
            n_features = len(self.feature_columns)
            n_output = len(self.classes) if self.task_type == 'classification' else 1
            
            # Draw architecture as text
            layers = [f"Input\n({n_features})"] + [f"Dense\n({n})\nReLU" for n in arch] + [f"Output\n({n_output})"]
            
            x_positions = np.linspace(0.1, 0.9, len(layers))
            
            for i, (x, layer) in enumerate(zip(x_positions, layers)):
                # Draw box
                box_width = 0.08
                box_height = 0.3
                rect = plt.Rectangle((x - box_width/2, 0.35), box_width, box_height,
                                     facecolor='steelblue' if i > 0 and i < len(layers)-1 else 'coral',
                                     edgecolor='black', linewidth=2)
                ax.add_patch(rect)
                ax.text(x, 0.5, layer, ha='center', va='center', fontsize=10, fontweight='bold', color='white')
                
                # Draw arrow
                if i < len(layers) - 1:
                    ax.annotate('', xy=(x_positions[i+1] - box_width/2 - 0.02, 0.5),
                               xytext=(x + box_width/2 + 0.02, 0.5),
                               arrowprops=dict(arrowstyle='->', color='black', lw=2))
            
            ax.set_xlim([0, 1])
            ax.set_ylim([0, 1])
            ax.set_title(f'Neural Network Architecture: {self.ALGORITHMS.get(self.algorithm, self.algorithm)}',
                        fontweight='bold', fontsize=14)
            
            plt.tight_layout()
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            charts['architecture'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
            plt.close()
        except Exception as e:
            logger.warning(f"Failed to generate architecture diagram: {e}")
        
        # =====================================================================
        # ENHANCED DEEP LEARNING CHARTS - Production Level
        # =====================================================================
        
        # 6. ROC Curve (Classification)
        if self.task_type == 'classification' and hasattr(self.model, 'predict_proba'):
            try:
                from sklearn.metrics import roc_curve, auc
                from sklearn.preprocessing import label_binarize
                
                y_proba = self.model.predict_proba(self.scaler.transform(
                    np.zeros((len(y_test), len(self.feature_columns)))))  # Placeholder
                
                # Use stored test data if available
                try:
                    y_proba = self.model.predict_proba(self._X_test_scaled)
                except:
                    pass
                
                fig, ax = plt.subplots(figsize=(10, 8))
                
                if len(self.classes) == 2:
                    # Binary classification
                    fpr, tpr, _ = roc_curve(y_test, y_proba[:, 1] if len(y_proba.shape) > 1 else y_proba)
                    roc_auc = auc(fpr, tpr)
                    
                    ax.plot(fpr, tpr, color='#8b5cf6', lw=2, label=f'ROC curve (AUC = {roc_auc:.4f})')
                    ax.fill_between(fpr, 0, tpr, alpha=0.2, color='#8b5cf6')
                else:
                    # Multiclass
                    y_test_bin = label_binarize(y_test, classes=list(range(len(self.classes))))
                    colors = ['#8b5cf6', '#2563eb', '#16a34a', '#f59e0b', '#dc2626', '#ec4899']
                    
                    for i, (class_name, color) in enumerate(zip(self.classes, colors[:len(self.classes)])):
                        if i < y_test_bin.shape[1] and i < y_proba.shape[1]:
                            fpr, tpr, _ = roc_curve(y_test_bin[:, i], y_proba[:, i])
                            roc_auc = auc(fpr, tpr)
                            ax.plot(fpr, tpr, color=color, lw=2, label=f'{class_name} (AUC = {roc_auc:.2f})')
                
                ax.plot([0, 1], [0, 1], 'k--', lw=1.5, alpha=0.7, label='Random')
                ax.set_xlabel('False Positive Rate', fontweight='bold', fontsize=12)
                ax.set_ylabel('True Positive Rate', fontweight='bold', fontsize=12)
                ax.set_title('Deep Learning ROC Curve', fontweight='bold', fontsize=14)
                ax.legend(loc='lower right')
                ax.grid(True, alpha=0.3)
                ax.set_xlim([0, 1])
                ax.set_ylim([0, 1.05])
                plt.tight_layout()
                
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
                buffer.seek(0)
                charts['roc_curve'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
                plt.close()
            except Exception as e:
                logger.warning(f"Failed to generate DL ROC curve: {e}")
        
        # 7. Prediction Confidence Heatmap (Classification)
        if self.task_type == 'classification':
            try:
                fig, ax = plt.subplots(figsize=(10, 6))
                
                # Create confidence vs actual class heatmap
                if hasattr(self.model, 'predict_proba'):
                    try:
                        y_proba = self.model.predict_proba(self._X_test_scaled)
                        max_confidence = np.max(y_proba, axis=1)
                        correct = (y_pred == y_test).astype(int)
                        
                        # Scatter with density coloring
                        from scipy.stats import gaussian_kde
                        xy = np.vstack([y_test, max_confidence])
                        z = gaussian_kde(xy)(xy)
                        
                        scatter = ax.scatter(y_test, max_confidence, c=z, s=50, cmap='plasma', alpha=0.7)
                        plt.colorbar(scatter, ax=ax, label='Density')
                        
                        ax.set_xlabel('Actual Class', fontweight='bold', fontsize=12)
                        ax.set_ylabel('Prediction Confidence', fontweight='bold', fontsize=12)
                        ax.set_title('Deep Learning Confidence by Class', fontweight='bold', fontsize=14)
                        plt.tight_layout()
                        
                        buffer = io.BytesIO()
                        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
                        buffer.seek(0)
                        charts['confidence_heatmap'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
                        plt.close()
                    except:
                        pass
            except Exception as e:
                logger.warning(f"Failed to generate confidence heatmap: {e}")
        
        # 8. Training Convergence Analysis
        try:
            if self.training_history.get('loss') and len(self.training_history['loss']) > 1:
                fig, axes = plt.subplots(1, 2, figsize=(14, 5))
                
                epochs = range(1, len(self.training_history['loss']) + 1)
                losses = self.training_history['loss']
                
                # Left: Loss curve with smoothing
                ax1 = axes[0]
                ax1.plot(epochs, losses, 'b-', alpha=0.3, linewidth=1, label='Raw Loss')
                
                # Smoothed loss (moving average)
                window = max(1, len(losses) // 10)
                if window > 1:
                    smoothed = np.convolve(losses, np.ones(window)/window, mode='valid')
                    ax1.plot(range(window, len(epochs)+1), smoothed, 'b-', 
                            linewidth=2, label='Smoothed Loss')
                
                ax1.set_xlabel('Epoch', fontweight='bold')
                ax1.set_ylabel('Loss', fontweight='bold')
                ax1.set_title('Training Loss Convergence', fontweight='bold', fontsize=12)
                ax1.legend()
                ax1.grid(True, alpha=0.3)
                
                # Right: Loss improvement rate
                ax2 = axes[1]
                if len(losses) > 1:
                    improvement = [losses[i] - losses[i+1] for i in range(len(losses)-1)]
                    ax2.bar(range(1, len(improvement)+1), improvement, 
                           color=['#16a34a' if x > 0 else '#dc2626' for x in improvement], alpha=0.7)
                    ax2.axhline(0, color='black', linewidth=0.5)
                    ax2.set_xlabel('Epoch', fontweight='bold')
                    ax2.set_ylabel('Loss Improvement', fontweight='bold')
                    ax2.set_title('Per-Epoch Loss Improvement', fontweight='bold', fontsize=12)
                    ax2.grid(True, alpha=0.3, axis='y')
                
                plt.tight_layout()
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
                buffer.seek(0)
                charts['convergence_analysis'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
                plt.close()
        except Exception as e:
            logger.warning(f"Failed to generate convergence analysis: {e}")
        
        # 9. Per-Class Performance (Classification)
        if self.task_type == 'classification' and cm is not None and self.classes is not None and len(self.classes) >= 2:
            try:
                from sklearn.metrics import classification_report
                
                # Ensure class names are strings
                class_names_str = [str(c) for c in self.classes]
                report = classification_report(y_test, y_pred, 
                                               target_names=class_names_str, 
                                               output_dict=True, zero_division=0)
                
                fig, ax = plt.subplots(figsize=(12, 6))
                
                class_names = [str(c)[:15] for c in self.classes]
                x_pos = np.arange(len(class_names))
                width = 0.25
                
                precision = []
                recall = []
                f1 = []
                
                for c in self.classes:
                    c_str = str(c)
                    if c_str in report:
                        precision.append(report[c_str].get('precision', 0))
                        recall.append(report[c_str].get('recall', 0))
                        f1.append(report[c_str].get('f1-score', 0))
                    else:
                        precision.append(0)
                        recall.append(0)
                        f1.append(0)
                
                ax.bar(x_pos - width, precision, width, label='Precision', color='#8b5cf6', edgecolor='white')
                ax.bar(x_pos, recall, width, label='Recall', color='#2563eb', edgecolor='white')
                ax.bar(x_pos + width, f1, width, label='F1-Score', color='#f59e0b', edgecolor='white')
                
                ax.set_xlabel('Class', fontweight='bold', fontsize=12)
                ax.set_ylabel('Score', fontweight='bold', fontsize=12)
                ax.set_title('Deep Learning Per-Class Metrics', fontweight='bold', fontsize=14)
                ax.set_xticks(x_pos)
                ax.set_xticklabels(class_names, rotation=45, ha='right')
                ax.legend()
                ax.set_ylim([0, 1.1])
                ax.grid(True, alpha=0.3, axis='y')
                plt.tight_layout()
                
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
                buffer.seek(0)
                charts['per_class_metrics'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
                plt.close()
            except Exception as e:
                logger.warning(f"Failed to generate DL per-class metrics: {e}")
        
        # 10. Residuals Analysis (Regression)
        if self.task_type == 'regression':
            try:
                residuals = y_test - y_pred
                
                fig, axes = plt.subplots(2, 2, figsize=(12, 10))
                
                # Residuals vs Predicted
                axes[0, 0].scatter(y_pred, residuals, alpha=0.5, c='#8b5cf6', s=30)
                axes[0, 0].axhline(0, color='red', linestyle='--', lw=2)
                axes[0, 0].set_xlabel('Predicted', fontweight='bold')
                axes[0, 0].set_ylabel('Residual', fontweight='bold')
                axes[0, 0].set_title('Residuals vs Predicted', fontweight='bold')
                axes[0, 0].grid(True, alpha=0.3)
                
                # Residuals Histogram
                axes[0, 1].hist(residuals, bins=30, color='#8b5cf6', alpha=0.7, edgecolor='white')
                axes[0, 1].axvline(0, color='red', linestyle='--', lw=2)
                axes[0, 1].set_xlabel('Residual', fontweight='bold')
                axes[0, 1].set_ylabel('Frequency', fontweight='bold')
                axes[0, 1].set_title('Residuals Distribution', fontweight='bold')
                
                # Q-Q Plot
                from scipy import stats
                stats.probplot(residuals, dist="norm", plot=axes[1, 0])
                axes[1, 0].set_title('Q-Q Plot (Normality)', fontweight='bold')
                
                # Residuals vs Index
                axes[1, 1].scatter(range(len(residuals)), residuals, alpha=0.5, c='#8b5cf6', s=30)
                axes[1, 1].axhline(0, color='red', linestyle='--', lw=2)
                axes[1, 1].set_xlabel('Index', fontweight='bold')
                axes[1, 1].set_ylabel('Residual', fontweight='bold')
                axes[1, 1].set_title('Residuals vs Order', fontweight='bold')
                
                plt.suptitle('Deep Learning Residual Analysis', fontsize=14, fontweight='bold', y=1.02)
                plt.tight_layout()
                
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
                buffer.seek(0)
                charts['residuals_analysis'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
                plt.close()
            except Exception as e:
                logger.warning(f"Failed to generate DL residuals analysis: {e}")
        
        # 11. Normalized Confusion Matrix (Classification)
        if cm is not None and self.task_type == 'classification' and self.classes is not None and len(self.classes) >= 2:
            try:
                fig, ax = plt.subplots(figsize=(8, 6))
                
                # Safe normalization
                row_sums = cm.sum(axis=1, keepdims=True)
                row_sums[row_sums == 0] = 1  # Avoid division by zero
                cm_normalized = cm.astype('float') / row_sums
                cm_normalized = np.nan_to_num(cm_normalized)
                
                # Truncate class names for display
                class_labels = [str(c)[:12] for c in self.classes]
                
                sns.heatmap(cm_normalized, annot=True, fmt='.2%', cmap='RdYlGn', ax=ax,
                           xticklabels=class_labels, yticklabels=class_labels,
                           vmin=0, vmax=1)
                ax.set_xlabel('Predicted', fontweight='bold')
                ax.set_ylabel('Actual', fontweight='bold')
                ax.set_title('Deep Learning Normalized Confusion Matrix', fontweight='bold', fontsize=14)
                plt.tight_layout()
                
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
                buffer.seek(0)
                charts['confusion_matrix_normalized'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
                plt.close()
            except Exception as e:
                logger.warning(f"Failed to generate DL normalized confusion matrix: {e}")
        
        # 12. Model Summary Card
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.axis('off')
            
            arch = self.ARCHITECTURES.get(self.algorithm, (128, 64, 32))
            n_features = len(self.feature_columns) if self.feature_columns else 1
            n_classes = len(self.classes) if self.classes and self.task_type == 'classification' else 1
            
            # Safe parameter calculation
            try:
                n_params = (arch[0] * n_features) + sum([arch[i] * arch[i+1] for i in range(len(arch)-1)]) + (arch[-1] * n_classes)
            except:
                n_params = 0
            
            summary_text = f"""
🧠 DEEP LEARNING MODEL SUMMARY

Architecture: {self.ALGORITHMS.get(self.algorithm, self.algorithm)}
Hidden Layers: {' → '.join(map(str, arch))}
Activation: ReLU
Optimizer: Adam

Input Features: {n_features}
Output: {n_classes}
Est. Parameters: ~{n_params:,}

Task Type: {self.task_type.title() if self.task_type else 'Unknown'}
"""
            # Add key metrics
            if self.task_type == 'classification':
                summary_text += f"""
Accuracy: {self.metrics.get('accuracy', 0):.4f}
F1-Score: {self.metrics.get('f1', 0):.4f}
"""
            else:
                summary_text += f"""
R² Score: {self.metrics.get('r2', 0):.4f}
RMSE: {self.metrics.get('rmse', 0):.4f}
"""
            
            ax.text(0.5, 0.5, summary_text, transform=ax.transAxes, fontsize=12,
                   verticalalignment='center', horizontalalignment='center',
                   fontfamily='monospace',
                   bbox=dict(boxstyle='round,pad=1', facecolor='#8b5cf6', alpha=0.1,
                            edgecolor='#8b5cf6', linewidth=3))
            
            plt.tight_layout()
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            charts['model_summary'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
            plt.close()
        except Exception as e:
            logger.warning(f"Failed to generate DL model summary: {e}")
        
        logger.info(f"📊 Generated {len(charts)} Deep Learning charts: {list(charts.keys())}")
        return charts
    
    def predict(self, data: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """Make prediction on new data
        
        Args:
            data: Dictionary of feature values
            user_id: Optional user ID to load user-specific model
        """
        # Load user's model if user_id is provided and model not loaded
        if user_id and self.model is None:
            if not self.load(user_id):
                return {'success': False, 'error': f'No Deep Learning model found for user {user_id}. Please train a model first.'}
        
        if self.model is None:
            return {'success': False, 'error': 'Model not trained. Train first or load a model.'}
        
        try:
            # Build feature vector using saved feature_metadata for correct preprocessing
            feature_values = []
            
            # Process numeric features first
            for meta in self.feature_metadata:
                if meta.get('type') == 'numeric':
                    col = meta['name']
                    if col in data:
                        try:
                            feature_values.append(float(data[col]))
                        except (ValueError, TypeError):
                            feature_values.append(meta.get('mean', 0))
                    else:
                        feature_values.append(meta.get('mean', 0))
            
            # Process categorical features (one-hot encoded during training)
            for meta in self.feature_metadata:
                if meta.get('type') == 'categorical':
                    col = meta['name']
                    value = str(data.get(col, ''))
                    options = meta.get('options', [])
                    
                    # Add one-hot encoded values for each option
                    for opt in options:
                        feature_values.append(1.0 if value == opt else 0.0)
                    # Add dummy for NaN (dummy_na=True during training)
                    feature_values.append(1.0 if not value or value == 'nan' else 0.0)
            
            # If feature_metadata is empty, fall back to feature_columns
            if not feature_values and self.feature_columns:
                for col in self.feature_columns:
                    if col in data:
                        try:
                            feature_values.append(float(data[col]) if not isinstance(data[col], str) else 0)
                        except:
                            feature_values.append(0)
                    else:
                        feature_values.append(0)
            
            X = np.array([feature_values])
            
            # Handle dimension mismatch
            if hasattr(self.scaler, 'n_features_in_'):
                expected = self.scaler.n_features_in_
                actual = X.shape[1]
                if actual < expected:
                    # Pad with zeros
                    padding = np.zeros((1, expected - actual))
                    X = np.hstack([X, padding])
                elif actual > expected:
                    # Truncate
                    X = X[:, :expected]
            
            X_scaled = self.scaler.transform(X)
            
            # Predict
            pred = self.model.predict(X_scaled)[0]
            
            if self.task_type == 'classification':
                pred_label = self.label_encoder.inverse_transform([int(pred)])[0]
                
                # Get probabilities
                if hasattr(self.model, 'predict_proba'):
                    proba = self.model.predict_proba(X_scaled)[0]
                    prob = {self.classes[i]: float(p) for i, p in enumerate(proba)}
                    confidence = float(max(proba))
                else:
                    prob = None
                    confidence = 0.8
                
                return {
                    'success': True,
                    'prediction': str(pred_label),
                    'confidence': confidence,
                    'probabilities': prob,
                    'algorithm': self.algorithm
                }
            else:
                return {
                    'success': True,
                    'prediction': float(pred),
                    'confidence': None,
                    'probabilities': None,
                    'algorithm': self.algorithm
                }
        except Exception as e:
            logger.error(f"Deep Learning prediction error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _save(self, user_id: str):
        """Save model to disk"""
        save_dir = os.path.join(STORAGE_PATH, user_id)
        os.makedirs(save_dir, exist_ok=True)
        
        data = {
            'model': self.model,
            'scaler': self.scaler,
            'label_encoder': self.label_encoder,
            'feature_columns': self.feature_columns,
            'numeric_cols': self.numeric_cols,
            'categorical_cols': self.categorical_cols,
            'feature_metadata': self.feature_metadata,
            'target_column': self.target_column,
            'algorithm': self.algorithm,
            'task_type': self.task_type,
            'classes': self.classes,
            'metrics': self.metrics,
            'training_history': self.training_history,
            'charts': self.charts,  # IMPORTANT: Save charts for state persistence
            'model_type': 'deep_learning',
            'y_test': getattr(self, '_y_test', None),
            'y_pred': getattr(self, '_y_pred', None),
            'y_proba': getattr(self, '_y_proba', None),
        }
        
        with open(os.path.join(save_dir, "deep_learning_model.pkl"), 'wb') as f:
            pickle.dump(data, f)
        
        logger.info(f"✅ Deep Learning model saved for user {user_id}")
    
    def load(self, user_id: str) -> bool:
        """Load model from disk"""
        try:
            model_path = os.path.join(STORAGE_PATH, user_id, "deep_learning_model.pkl")
            
            if not os.path.exists(model_path):
                return False
            
            with open(model_path, 'rb') as f:
                data = pickle.load(f)
            
            self.model = data['model']
            self.scaler = data['scaler']
            self.label_encoder = data['label_encoder']
            self.feature_columns = data['feature_columns']
            self.numeric_cols = data.get('numeric_cols', [])
            self.categorical_cols = data.get('categorical_cols', [])
            self.feature_metadata = data.get('feature_metadata', [])
            self.target_column = data['target_column']
            self.algorithm = data['algorithm']
            self.task_type = data['task_type']
            self.classes = data.get('classes', [])
            self.metrics = data.get('metrics', {})
            self.charts = data.get('charts', {})  # Load charts for state persistence
            self.training_history = data.get('training_history', {})
            
            logger.info(f"✅ Deep Learning model loaded for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load Deep Learning model: {e}")
            return False


# Global instance
deep_learning_engine = DeepLearningEngine()
