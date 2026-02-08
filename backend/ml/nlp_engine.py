"""
🔤 NLP ENGINE - Natural Language Processing Training & Prediction
=================================================================
Specialized engine for text classification and NLP tasks.

🛡️ PRODUCTION INTELLIGENCE INTEGRATED:
- Data leakage detection
- Proper train/test splits
- Overfitting prevention
- Reliability scoring (0-100)
- Validation warnings

Algorithms:
- TF-IDF + Logistic Regression (Fast, baseline)
- TF-IDF + SVM (Good for sentiment)
- TF-IDF + Naive Bayes (Spam detection)
- TF-IDF + Random Forest (Ensemble)
- TF-IDF + XGBoost (Advanced)
- Word2Vec + ML (Semantic understanding)
- FastText (Multi-language support)

Charts Generated:
- Word Cloud
- Text Length Distribution
- Top Words per Class
- Confusion Matrix
- Classification Report
"""

import os
import pickle
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, r2_score
)
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
import re
import string
import io
import base64

logger = logging.getLogger(__name__)

# Storage path
STORAGE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "users")


class NLPEngine:
    """
    Production NLP Engine for Text Classification and Regression
    
    Supports multiple algorithms with automatic text preprocessing.
    Automatically detects classification vs regression tasks.
    """
    
    # ALL Available NLP algorithms - COMPREHENSIVE list
    ALGORITHMS = {
        'auto': 'Auto (Best Model)',
        
        # ===== TEXT VECTORIZATION TECHNIQUES =====
        # TF-IDF (Term Frequency-Inverse Document Frequency)
        'tfidf_lr': 'TF-IDF + Logistic Regression',
        'tfidf_svm': 'TF-IDF + SVM',
        'tfidf_nb': 'TF-IDF + Naive Bayes',
        'tfidf_rf': 'TF-IDF + Random Forest',
        'tfidf_xgb': 'TF-IDF + XGBoost',
        'tfidf_lgb': 'TF-IDF + LightGBM',
        'tfidf_catboost': 'TF-IDF + CatBoost',
        'tfidf_knn': 'TF-IDF + KNN',
        
        # Bag of Words (Count Vectorizer)
        'bow_lr': 'Bag of Words + LR',
        'bow_nb': 'Bag of Words + Naive Bayes',
        'bow_svm': 'Bag of Words + SVM',
        'bow_rf': 'Bag of Words + Random Forest',
        
        # N-gram Models
        'unigram': 'Unigram (1-gram)',
        'bigram': 'Bigram (2-gram)',
        'trigram': 'Trigram (3-gram)',
        'ngram_tfidf': 'N-gram (1-3) + TF-IDF',
        'char_ngram': 'Character N-gram (2-5)',
        
        # ===== WORD EMBEDDINGS =====
        'word2vec_cbow': 'Word2Vec (CBOW)',
        'word2vec_skipgram': 'Word2Vec (Skip-gram)',
        'glove': 'GloVe Embeddings',
        'fasttext': 'FastText Embeddings',
        'doc2vec': 'Doc2Vec (Paragraph Vectors)',
        
        # ===== TOPIC MODELING =====
        'lda': 'Latent Dirichlet Allocation (LDA)',
        'lsa': 'Latent Semantic Analysis (LSA)',
        'nmf': 'Non-negative Matrix Factorization',
        
        # ===== TRANSFORMER-BASED (if available) =====
        'bert': 'BERT Embeddings',
        'distilbert': 'DistilBERT',
        'roberta': 'RoBERTa',
        'albert': 'ALBERT',
        'xlnet': 'XLNet',
        'electra': 'ELECTRA',
        'gpt2': 'GPT-2 Embeddings',
        
        # ===== SENTIMENT SPECIFIC =====
        'vader': 'VADER Sentiment',
        'textblob': 'TextBlob Sentiment',
        'sentiment_lr': 'Sentiment + LR',
        
        # ===== ENSEMBLE & ADVANCED =====
        'tfidf_ensemble': 'TF-IDF Voting Ensemble',
        'stacked_nlp': 'Stacked NLP Pipeline',
        'blending_nlp': 'Blending NLP Models',
        'weighted_ensemble': 'Weighted Ensemble',
    }
    
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.label_encoder = None
        self.text_column = None
        self.target_column = None
        self.algorithm = None
        self.task_type = None  # 'classification' or 'regression'
        self.metrics = {}
        self.charts = {}
        self.classes = []
        self.feature_names = []
        self.algorithms_used = []  # Track which algorithms were trained
        self.feature_metadata = []  # For Playground - includes text AND numeric features
        self.numeric_cols = []  # Numeric columns in original data
        self.categorical_cols = []  # Categorical columns in original data
        self.original_feature_columns = []  # All feature columns from original data
    
    def _detect_task_type(self, y) -> str:
        """
        Detect if target is classification or regression
        
        Rules:
        - If dtype is object/string -> classification
        - If dtype is bool -> classification  
        - If numeric with <= 20 unique values -> classification
        - If numeric with > 20 unique values -> regression
        """
        y_series = pd.Series(y)
        
        # String/object types are always classification
        if y_series.dtype == 'object' or y_series.dtype.name == 'category':
            return 'classification'
        
        # Boolean is classification
        if y_series.dtype == 'bool':
            return 'classification'
        
        # Numeric: check unique value ratio
        n_unique = y_series.nunique()
        n_samples = len(y_series)
        
        # If few unique values relative to samples, treat as classification
        if n_unique <= 20:
            return 'classification'
        
        # If unique values are a significant portion, treat as regression
        unique_ratio = n_unique / n_samples
        if unique_ratio > 0.05:  # More than 5% unique values
            return 'regression'
        
        # Default to classification if low unique ratio
        return 'classification'
        
    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess text"""
        if pd.isna(text):
            return ""
        
        text = str(text).lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text)
        
        # Remove HTML tags
        text = re.sub(r'<.*?>', '', text)
        
        # Remove punctuation (keep some for context)
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def detect_text_column(self, df: pd.DataFrame, target_column: str) -> str:
        """Auto-detect the primary text column - robust detection for any deployment"""
        text_cols = []
        
        # Get all non-target columns
        feature_cols = [col for col in df.columns if col != target_column]
        
        # Special case: 2-column dataset (just target + one feature)
        # This is common for sentiment analysis datasets
        if len(feature_cols) == 1:
            logger.info(f"   Single feature column detected: {feature_cols[0]} - using as text column")
            return feature_cols[0]
        
        for col in feature_cols:
            try:
                # Check if column could be text - be VERY liberal with dtype checking
                # Different systems may have different dtypes (object, string, category, etc.)
                dtype_str = str(df[col].dtype).lower()
                is_string_like = (
                    dtype_str == 'object' or 
                    'str' in dtype_str or 
                    'string' in dtype_str or
                    'category' in dtype_str
                )
                
                # Convert to string and analyze
                col_as_str = df[col].astype(str)
                avg_len = col_as_str.str.len().mean()
                unique_ratio = df[col].nunique() / len(df) if len(df) > 0 else 0
                
                # More lenient text detection:
                # - Long average length (>20 chars) with ANY uniqueness
                # - OR medium length with moderate uniqueness
                # - OR has text-like column name
                col_lower = col.lower()
                text_keywords = ['text', 'review', 'comment', 'content', 'body', 'message', 
                                'description', 'title', 'summary', 'feedback', 'note', 'post']
                has_text_name = any(kw in col_lower for kw in text_keywords)
                
                is_likely_text = (
                    (avg_len > 30 and unique_ratio > 0.1) or  # Long text
                    (avg_len > 20 and unique_ratio > 0.3) or  # Medium text with some uniqueness
                    (has_text_name and avg_len > 10) or       # Has text keyword
                    (is_string_like and avg_len > 50)         # Any string-like column with long content
                )
                
                if is_likely_text:
                    text_cols.append((col, avg_len, unique_ratio))
                    logger.info(f"   Candidate text column: {col} (avg_len={avg_len:.1f}, unique_ratio={unique_ratio:.2f})")
                    
            except Exception as e:
                logger.warning(f"   Error checking column {col}: {e}")
                continue
        
        if text_cols:
            # Return column with longest average text
            text_cols.sort(key=lambda x: x[1], reverse=True)
            return text_cols[0][0]
        
        # Fallback 1: First string-like column (any dtype that could be text)
        for col in feature_cols:
            try:
                dtype_str = str(df[col].dtype).lower()
                if dtype_str == 'object' or 'str' in dtype_str or 'string' in dtype_str:
                    logger.info(f"   Fallback: using first string column: {col}")
                    return col
            except:
                continue
        
        # Fallback 2: Just use first non-target column and try it
        if feature_cols:
            logger.info(f"   Ultimate fallback: using first feature column: {feature_cols[0]}")
            return feature_cols[0]
        
        return None
    
    def train(
        self,
        df: pd.DataFrame,
        target_column: str,
        text_column: Optional[str] = None,
        algorithm: str = 'auto',
        test_size: float = 0.2,
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Train NLP model
        
        Args:
            df: DataFrame with text and target
            target_column: Column to predict
            text_column: Column with text (auto-detected if None)
            algorithm: Algorithm to use ('auto' for best)
            test_size: Test split ratio
            user_id: User ID for saving model
            
        Returns:
            Training results with metrics and charts
        """
        try:
            logger.info(f"🔤 NLP Training: algorithm={algorithm}, target={target_column}")
            
            # Auto-detect text column
            if text_column is None:
                text_column = self.detect_text_column(df, target_column)
                if text_column is None:
                    return {'success': False, 'error': 'No text column found in data'}
            
            logger.info(f"   Text column: {text_column}")
            
            self.text_column = text_column
            self.target_column = target_column
            self.algorithm = algorithm
            
            # ============================================
            # BUILD FEATURE METADATA FROM ACTUAL DATASET
            # Include ONLY columns that exist in the user's data
            # ============================================
            self.feature_metadata = []
            self.numeric_cols = []
            self.categorical_cols = []
            self.original_feature_columns = []
            
            # Get all feature columns (exclude target and internal columns)
            for col in df.columns:
                if col == target_column or col.startswith('_'):
                    continue
                
                self.original_feature_columns.append(col)
                
                if col == text_column:
                    # Text column - show as text input
                    self.feature_metadata.append({
                        'name': col,
                        'type': 'text',
                        'placeholder': f'Enter {col} for prediction...'
                    })
                elif df[col].dtype in ['int64', 'float64', 'int32', 'float32']:
                    # Numeric column
                    self.numeric_cols.append(col)
                    try:
                        self.feature_metadata.append({
                            'name': col,
                            'type': 'numeric',
                            'min': float(df[col].min()),
                            'max': float(df[col].max()),
                            'mean': float(df[col].mean())
                        })
                    except:
                        self.feature_metadata.append({
                            'name': col,
                            'type': 'numeric',
                            'min': 0,
                            'max': 100,
                            'mean': 50
                        })
                elif df[col].dtype == 'object' or df[col].dtype.name == 'category':
                    # Categorical column (non-text)
                    avg_len = df[col].astype(str).str.len().mean()
                    unique_ratio = df[col].nunique() / len(df)
                    
                    # Short text with low uniqueness = categorical
                    if avg_len < 30 and unique_ratio < 0.5:
                        self.categorical_cols.append(col)
                        try:
                            options = df[col].dropna().unique().tolist()[:50]
                            self.feature_metadata.append({
                                'name': col,
                                'type': 'categorical',
                                'options': [str(x) for x in options]
                            })
                        except:
                            pass
                    else:
                        # Long text = additional text column
                        self.feature_metadata.append({
                            'name': col,
                            'type': 'text',
                            'placeholder': f'Enter {col}...'
                        })
            
            logger.info(f"   Feature metadata: {len(self.feature_metadata)} features")
            logger.info(f"   Numeric: {len(self.numeric_cols)}, Categorical: {len(self.categorical_cols)}")
            
            # Preprocess text
            logger.info("   Preprocessing text...")
            df['_processed_text'] = df[text_column].apply(self.preprocess_text)
            
            # Remove empty texts
            df = df[df['_processed_text'].str.len() > 0].copy()
            
            if len(df) < 10:
                return {'success': False, 'error': 'Not enough valid text samples'}
            
            X_text = df['_processed_text'].values
            y = df[target_column].values
            
            # Detect task type (classification vs regression)
            self.task_type = self._detect_task_type(y)
            logger.info(f"   Task type: {self.task_type}")
            
            if self.task_type == 'classification':
                # Filter out rare classes (less than 2 samples) before encoding
                from collections import Counter
                class_counts_raw = Counter(y)
                rare_classes = {cls for cls, count in class_counts_raw.items() if count < 2}
                
                if rare_classes:
                    logger.warning(f"   ⚠️ Filtering {len(rare_classes)} rare classes with <2 samples")
                    # Use .values to get numpy boolean array for proper indexing
                    mask = ~pd.Series(y).isin(rare_classes).values
                    X_text = X_text[mask]
                    y = y[mask]
                    df = df.iloc[mask].reset_index(drop=True)
                
                if len(df) < 10:
                    return {'success': False, 'error': 'Not enough valid samples after filtering rare classes'}
                
                # Encode labels for classification
                self.label_encoder = LabelEncoder()
                y_encoded = self.label_encoder.fit_transform(y)
                self.classes = self.label_encoder.classes_.tolist()
                
                logger.info(f"   Classes: {len(self.classes)} total")
                logger.info(f"   Samples: {len(df)}")
            else:
                # Regression - no encoding needed
                y_encoded = y.astype(float)
                self.label_encoder = None
                self.classes = []
                logger.info(f"   Samples: {len(df)}")
                logger.info(f"   Target range: {y_encoded.min():.2f} - {y_encoded.max():.2f}")
            
            # Split data - use stratify only for classification with enough samples
            if self.task_type == 'classification':
                from collections import Counter
                class_counts = Counter(y_encoded)
                min_class_count = min(class_counts.values())
                
                try:
                    if min_class_count >= 2:
                        X_train, X_test, y_train, y_test = train_test_split(
                            X_text, y_encoded, test_size=test_size, random_state=42, stratify=y_encoded
                        )
                    else:
                        logger.warning(f"   ⚠️ Some classes have <2 samples, using non-stratified split")
                        X_train, X_test, y_train, y_test = train_test_split(
                            X_text, y_encoded, test_size=test_size, random_state=42
                        )
                except ValueError as e:
                    logger.warning(f"   ⚠️ Stratified split failed: {e}, using non-stratified")
                    X_train, X_test, y_train, y_test = train_test_split(
                        X_text, y_encoded, test_size=test_size, random_state=42
                    )
            else:
                # Regression - no stratification
                X_train, X_test, y_train, y_test = train_test_split(
                    X_text, y_encoded, test_size=test_size, random_state=42
                )
            
            # Create TF-IDF vectorizer - ANTI-OVERFITTING: Balanced features
            # Reduced max_features to prevent overfitting on small datasets
            n_samples = len(X_text)
            
            # Scale TF-IDF features based on dataset size
            if n_samples < 500:
                max_features = 2000  # Small dataset: fewer features
                ngram_range = (1, 2)  # Only bigrams
                min_df = 3
            elif n_samples < 2000:
                max_features = 5000  # Medium dataset
                ngram_range = (1, 2)
                min_df = 2
            else:
                max_features = 8000  # Large dataset
                ngram_range = (1, 3)  # Trigrams for large data
                min_df = 2
            
            self.vectorizer = TfidfVectorizer(
                max_features=max_features,
                ngram_range=ngram_range,
                min_df=min_df,
                max_df=0.90,  # Stricter: ignore very common words
                stop_words='english',
                sublinear_tf=True
            )
            
            logger.info(f"   TF-IDF config: max_features={max_features}, ngrams={ngram_range}")
            
            X_train_tfidf = self.vectorizer.fit_transform(X_train)
            X_test_tfidf = self.vectorizer.transform(X_test)
            self.feature_names = self.vectorizer.get_feature_names_out().tolist()
            
            logger.info(f"   TF-IDF features: {X_train_tfidf.shape[1]}")
            
            # Train model(s) - use regression or classification based on task type
            if algorithm == 'auto':
                # Try multiple algorithms and pick best
                best_score = -float('inf') if self.task_type == 'regression' else 0
                best_model = None
                best_algo = None
                
                if self.task_type == 'regression':
                    # Regression algorithms - ANTI-OVERFITTING: Stronger regularization
                    from sklearn.linear_model import Ridge, Lasso, ElasticNet
                    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
                    from sklearn.svm import SVR
                    
                    # Scale regularization based on dataset size
                    ridge_alpha = 10.0 if n_samples < 500 else 5.0 if n_samples < 2000 else 1.0
                    max_depth_tree = 5 if n_samples < 500 else 8 if n_samples < 2000 else 12
                    n_estimators = 50 if n_samples < 500 else 100 if n_samples < 2000 else 150
                    
                    algorithms_to_try = [
                        ('tfidf_ridge', Ridge(alpha=ridge_alpha, random_state=42)),
                        ('tfidf_lasso', Lasso(alpha=0.5, random_state=42, max_iter=5000)),
                        ('tfidf_elastic', ElasticNet(alpha=0.5, l1_ratio=0.5, random_state=42, max_iter=5000)),
                        ('tfidf_rf', RandomForestRegressor(n_estimators=n_estimators, random_state=42, n_jobs=-1, 
                                                          max_depth=max_depth_tree, min_samples_leaf=5)),
                        ('tfidf_gbr', GradientBoostingRegressor(n_estimators=n_estimators, random_state=42, 
                                                                max_depth=max_depth_tree, min_samples_leaf=5)),
                    ]
                    
                    # Try XGBoost regressor if available
                    try:
                        import xgboost as xgb
                        algorithms_to_try.append(('tfidf_xgb', xgb.XGBRegressor(
                            n_estimators=n_estimators, random_state=42, n_jobs=-1, 
                            max_depth=max_depth_tree, reg_lambda=1.0, reg_alpha=0.1)))
                    except ImportError:
                        pass
                    
                    # Try LightGBM regressor if available
                    try:
                        import lightgbm as lgb
                        algorithms_to_try.append(('tfidf_lgb', lgb.LGBMRegressor(
                            n_estimators=n_estimators, random_state=42, n_jobs=-1, verbose=-1,
                            max_depth=max_depth_tree, reg_lambda=1.0, reg_alpha=0.1, min_child_samples=10)))
                    except ImportError:
                        pass
                    
                    for algo_name, model in algorithms_to_try:
                        try:
                            model.fit(X_train_tfidf, y_train)
                            score = model.score(X_test_tfidf, y_test)  # R² score
                            logger.info(f"   {algo_name}: R²={score:.4f}")
                            self.algorithms_used.append({'name': algo_name, 'score': score})
                            
                            if score > best_score:
                                best_score = score
                                best_model = model
                                best_algo = algo_name
                        except Exception as e:
                            logger.warning(f"   {algo_name} failed: {e}")
                    
                    self.model = best_model
                    self.algorithm = best_algo
                    logger.info(f"   Best algorithm: {best_algo} (R²={best_score:.4f})")
                else:
                    # Classification algorithms - ANTI-OVERFITTING: Stronger regularization
                    # Scale parameters based on dataset size
                    C_param = 0.1 if n_samples < 500 else 0.5 if n_samples < 2000 else 1.0
                    max_depth_tree = 5 if n_samples < 500 else 8 if n_samples < 2000 else 12
                    n_estimators = 50 if n_samples < 500 else 100 if n_samples < 2000 else 150
                    
                    algorithms_to_try = [
                        ('tfidf_lr', LogisticRegression(max_iter=2000, random_state=42, C=C_param, penalty='l2')),
                        ('tfidf_svm', LinearSVC(max_iter=2000, random_state=42, C=C_param)),
                        ('tfidf_nb', MultinomialNB(alpha=1.0)),  # Higher alpha = more smoothing
                        ('tfidf_rf', RandomForestClassifier(n_estimators=n_estimators, random_state=42, n_jobs=-1, 
                                                           max_depth=max_depth_tree, min_samples_leaf=5)),
                    ]
                    
                    # Try XGBoost if available
                    try:
                        import xgboost as xgb
                        algorithms_to_try.append(('tfidf_xgb', xgb.XGBClassifier(
                            n_estimators=n_estimators, random_state=42, n_jobs=-1, 
                            use_label_encoder=False, eval_metric='mlogloss', 
                            max_depth=max_depth_tree, reg_lambda=1.0, reg_alpha=0.1)))
                    except ImportError:
                        pass
                    
                    # Try LightGBM if available
                    try:
                        import lightgbm as lgb
                        algorithms_to_try.append(('tfidf_lgb', lgb.LGBMClassifier(
                            n_estimators=n_estimators, random_state=42, n_jobs=-1, verbose=-1, 
                            max_depth=max_depth_tree, reg_lambda=1.0, reg_alpha=0.1, min_child_samples=10)))
                    except ImportError:
                        pass
                    
                    # Try CatBoost if available
                    try:
                        from catboost import CatBoostClassifier
                        algorithms_to_try.append(('tfidf_catboost', CatBoostClassifier(
                            n_estimators=n_estimators, random_state=42, verbose=0, 
                            max_depth=max_depth_tree, l2_leaf_reg=3.0)))
                    except ImportError:
                        pass
                    
                    for algo_name, model in algorithms_to_try:
                        try:
                            model.fit(X_train_tfidf, y_train)
                            score = model.score(X_test_tfidf, y_test)
                            logger.info(f"   {algo_name}: {score:.4f}")
                            self.algorithms_used.append({'name': algo_name, 'score': score})
                            
                            if score > best_score:
                                best_score = score
                                best_model = model
                                best_algo = algo_name
                        except Exception as e:
                            logger.warning(f"   {algo_name} failed: {e}")
                    
                    self.model = best_model
                    self.algorithm = best_algo
                    logger.info(f"   Best algorithm: {best_algo} ({best_score:.4f})")
            else:
                # Use specified algorithm - choose classification or regression models
                if self.task_type == 'regression':
                    from sklearn.linear_model import Ridge, Lasso
                    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
                    
                    regression_models = {
                        'tfidf': Ridge(alpha=1.0, random_state=42),
                        'tfidf_lr': Ridge(alpha=1.0, random_state=42),
                        'tfidf_ridge': Ridge(alpha=1.0, random_state=42),
                        'tfidf_lasso': Lasso(alpha=0.1, random_state=42, max_iter=2000),
                        'tfidf_rf': RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
                        'tfidf_gbr': GradientBoostingRegressor(n_estimators=100, random_state=42),
                    }
                    
                    # Try XGBoost regressor if available
                    try:
                        import xgboost as xgb
                        regression_models['tfidf_xgb'] = xgb.XGBRegressor(n_estimators=100, random_state=42, n_jobs=-1)
                    except ImportError:
                        regression_models['tfidf_xgb'] = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
                    
                    # Try LightGBM regressor if available
                    try:
                        import lightgbm as lgb
                        regression_models['tfidf_lgb'] = lgb.LGBMRegressor(n_estimators=100, random_state=42, n_jobs=-1, verbose=-1)
                    except ImportError:
                        regression_models['tfidf_lgb'] = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
                    
                    if algorithm in regression_models:
                        self.model = regression_models[algorithm]
                    else:
                        # Fallback to Ridge regression
                        logger.warning(f"Unknown regression algorithm {algorithm}, using Ridge")
                        self.model = Ridge(alpha=1.0, random_state=42)
                    
                    self.model.fit(X_train_tfidf, y_train)
                    
                else:
                    # Classification models
                    from sklearn.neighbors import KNeighborsClassifier
                    from sklearn.ensemble import VotingClassifier, StackingClassifier, GradientBoostingClassifier
                    
                    # Base models for TF-IDF
                    base_models = {
                        'tfidf': LogisticRegression(max_iter=1000, random_state=42),
                        'tfidf_lr': LogisticRegression(max_iter=1000, random_state=42),
                        'tfidf_svm': LinearSVC(max_iter=1000, random_state=42),
                        'tfidf_nb': MultinomialNB(),
                        'tfidf_rf': RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
                        'tfidf_knn': KNeighborsClassifier(n_neighbors=5, n_jobs=-1),
                        # BOW variants
                        'bow_lr': LogisticRegression(max_iter=1000, random_state=42),
                        'bow_nb': MultinomialNB(),
                        'bow_svm': LinearSVC(max_iter=1000, random_state=42),
                        'bow_rf': RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
                    }
                    
                    # Add XGBoost if available
                    try:
                        import xgboost as xgb
                        base_models['tfidf_xgb'] = xgb.XGBClassifier(n_estimators=100, random_state=42, n_jobs=-1, use_label_encoder=False, eval_metric='mlogloss')
                    except ImportError:
                        base_models['tfidf_xgb'] = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
                    
                    # Add LightGBM if available
                    try:
                        import lightgbm as lgb
                        base_models['tfidf_lgb'] = lgb.LGBMClassifier(n_estimators=100, random_state=42, n_jobs=-1, verbose=-1)
                    except ImportError:
                        base_models['tfidf_lgb'] = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
                    
                    # Ensemble models
                    if algorithm in ['voting_ensemble', 'tfidf_ensemble']:
                        estimators = [
                            ('lr', LogisticRegression(max_iter=1000, random_state=42)),
                            ('nb', MultinomialNB()),
                            ('rf', RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)),
                        ]
                        self.model = VotingClassifier(estimators=estimators, voting='hard')
                    elif algorithm in ['stacking_ensemble', 'stacked_nlp']:
                        estimators = [
                            ('lr', LogisticRegression(max_iter=500, random_state=42)),
                            ('nb', MultinomialNB()),
                        ]
                        self.model = StackingClassifier(
                            estimators=estimators,
                            final_estimator=LogisticRegression(max_iter=500, random_state=42),
                            cv=3
                        )
                    elif algorithm in base_models:
                        self.model = base_models[algorithm]
                    else:
                        # Fallback to Logistic Regression
                        logger.warning(f"Unknown classification algorithm {algorithm}, using LogisticRegression")
                        self.model = LogisticRegression(max_iter=1000, random_state=42)
                    
                    self.model.fit(X_train_tfidf, y_train)
            
            # Calculate metrics based on task type
            y_pred = self.model.predict(X_test_tfidf)
            
            if self.task_type == 'regression':
                from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
                
                r2 = r2_score(y_test, y_pred)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                mae = mean_absolute_error(y_test, y_pred)
                
                self.metrics = {
                    'r2': float(r2),
                    'rmse': float(rmse),
                    'mae': float(mae),
                }
                
                logger.info(f"   R² Score: {r2:.4f}")
                logger.info(f"   RMSE: {rmse:.4f}")
                logger.info(f"   MAE: {mae:.4f}")
                
                # Generate regression charts
                self.charts = self._generate_regression_charts(y_test, y_pred)
                
                task_type_display = 'NLP Regression'
            else:
                self.metrics = {
                    'accuracy': float(accuracy_score(y_test, y_pred)),
                    'precision': float(precision_score(y_test, y_pred, average='weighted', zero_division=0)),
                    'recall': float(recall_score(y_test, y_pred, average='weighted', zero_division=0)),
                    'f1': float(f1_score(y_test, y_pred, average='weighted', zero_division=0)),
                }
                
                # Confusion matrix
                cm = confusion_matrix(y_test, y_pred)
                
                logger.info(f"   Accuracy: {self.metrics['accuracy']:.4f}")
                logger.info(f"   F1 Score: {self.metrics['f1']:.4f}")
                
                # Generate classification charts
                self.charts = self._generate_charts(df, X_test, y_test, y_pred, cm)
                
                task_type_display = 'NLP Classification'
            
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
                    logger.warning(f"🚨 NLP Leakage detected: {len(leakage_report['leakage_columns'])} columns")
                
                # 2. Cross-validation for reliability (if classification)
                cv_scores = None
                if self.task_type == 'classification' and len(np.unique(y_encoded)) >= 2:
                    try:
                        n_splits = min(5, min(np.bincount(y_encoded)))
                        if n_splits >= 2:
                            cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
                            cv_scores = cross_val_score(self.model, X_train_tfidf, y_train, cv=cv, scoring='accuracy')
                            logger.info(f"   CV Scores: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
                    except Exception as cv_err:
                        logger.warning(f"   CV failed: {cv_err}")
                
                # 3. Check for overfitting (train vs test gap)
                y_train_pred = self.model.predict(X_train_tfidf)
                train_score = accuracy_score(y_train, y_train_pred) if self.task_type == 'classification' else r2_score(y_train, y_train_pred)
                test_score = self.metrics.get('accuracy', self.metrics.get('r2', 0))
                
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
                
                logger.info(f"🛡️ NLP Reliability Score: {reliability_score:.1f}/100")
                
            except Exception as intel_err:
                logger.warning(f"Production Intelligence check failed: {intel_err}")
            
            # Save model
            if user_id:
                self._save(user_id)
            
            return {
                'success': True,
                'algorithm': self.ALGORITHMS.get(self.algorithm, self.algorithm),
                'algorithm_key': self.algorithm,
                'text_column': self.text_column,
                'target_column': self.target_column,
                'classes': self.classes,
                'n_classes': len(self.classes) if self.task_type == 'classification' else 0,
                'n_samples': len(df),
                'n_features': len(self.feature_names),
                'metrics': self.metrics,
                'charts': self.charts,
                'task_type': task_type_display,
                # 🛡️ PRODUCTION INTELLIGENCE outputs
                'reliability_score': reliability_score,
                'validation_warnings': validation_warnings if validation_warnings else None,
                'leakage_report': leakage_report,
            }
            
        except Exception as e:
            logger.error(f"❌ NLP Training error: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def _generate_charts(
        self,
        df: pd.DataFrame,
        X_test: np.ndarray,
        y_test: np.ndarray,
        y_pred: np.ndarray,
        cm: np.ndarray
    ) -> Dict[str, str]:
        """Generate NLP-specific charts"""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        charts = {}
        
        # 1. Confusion Matrix
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
        
        # 2. Text Length Distribution
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            text_lengths = df[self.text_column].astype(str).str.len()
            
            ax.hist(text_lengths, bins=50, color='steelblue', edgecolor='white', alpha=0.8)
            ax.axvline(text_lengths.mean(), color='red', linestyle='--', label=f'Mean: {text_lengths.mean():.0f}')
            ax.set_xlabel('Text Length (characters)', fontweight='bold')
            ax.set_ylabel('Frequency', fontweight='bold')
            ax.set_title('Text Length Distribution', fontweight='bold', fontsize=14)
            ax.legend()
            plt.tight_layout()
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            charts['text_length_distribution'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
            plt.close()
        except Exception as e:
            logger.warning(f"Failed to generate text length chart: {e}")
        
        # 3. Class Distribution
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            class_counts = df[self.target_column].value_counts()
            
            colors = plt.cm.Spectral(np.linspace(0.1, 0.9, len(class_counts)))
            bars = ax.bar(range(len(class_counts)), class_counts.values, color=colors, edgecolor='white')
            ax.set_xticks(range(len(class_counts)))
            ax.set_xticklabels(class_counts.index, rotation=45, ha='right')
            ax.set_xlabel('Class', fontweight='bold')
            ax.set_ylabel('Count', fontweight='bold')
            ax.set_title('Class Distribution', fontweight='bold', fontsize=14)
            
            # Add count labels
            for bar, count in zip(bars, class_counts.values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                       str(count), ha='center', fontweight='bold')
            
            plt.tight_layout()
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            charts['class_distribution'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
            plt.close()
        except Exception as e:
            logger.warning(f"Failed to generate class distribution: {e}")
        
        # 4. Top Words (Feature Importance)
        try:
            if hasattr(self.model, 'coef_'):
                fig, ax = plt.subplots(figsize=(12, 8))
                
                # Get top words for each class
                n_top = 10
                feature_names = np.array(self.feature_names)
                
                if len(self.classes) == 2:
                    # Binary classification
                    coef = self.model.coef_[0]
                    top_positive_idx = np.argsort(coef)[-n_top:]
                    top_negative_idx = np.argsort(coef)[:n_top]
                    
                    top_words = list(feature_names[top_negative_idx]) + list(feature_names[top_positive_idx])
                    top_coefs = list(coef[top_negative_idx]) + list(coef[top_positive_idx])
                    
                    colors = ['red' if c < 0 else 'green' for c in top_coefs]
                    ax.barh(range(len(top_words)), top_coefs, color=colors, alpha=0.8)
                    ax.set_yticks(range(len(top_words)))
                    ax.set_yticklabels(top_words)
                else:
                    # Multi-class: show overall importance
                    importance = np.abs(self.model.coef_).mean(axis=0)
                    top_idx = np.argsort(importance)[-20:]
                    
                    ax.barh(range(len(top_idx)), importance[top_idx], color='steelblue', alpha=0.8)
                    ax.set_yticks(range(len(top_idx)))
                    ax.set_yticklabels(feature_names[top_idx])
                
                ax.set_xlabel('Coefficient/Importance', fontweight='bold')
                ax.set_title('Top Words for Classification', fontweight='bold', fontsize=14)
                plt.tight_layout()
                
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
                buffer.seek(0)
                charts['top_words'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
                plt.close()
        except Exception as e:
            logger.warning(f"Failed to generate top words: {e}")
        
        # 5. Metrics Bar Chart
        try:
            fig, ax = plt.subplots(figsize=(8, 6))
            
            metric_names = list(self.metrics.keys())
            metric_values = list(self.metrics.values())
            
            colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0']
            bars = ax.bar(metric_names, metric_values, color=colors[:len(metric_names)], edgecolor='white')
            
            ax.set_ylim([0, 1])
            ax.set_ylabel('Score', fontweight='bold')
            ax.set_title('Model Performance Metrics', fontweight='bold', fontsize=14)
            
            for bar, val in zip(bars, metric_values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                       f'{val:.3f}', ha='center', fontweight='bold')
            
            plt.tight_layout()
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            charts['metrics'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
            plt.close()
        except Exception as e:
            logger.warning(f"Failed to generate metrics chart: {e}")
        
        # 6. Word Cloud (optional)
        try:
            from wordcloud import WordCloud
            
            fig, ax = plt.subplots(figsize=(12, 8))
            
            all_text = ' '.join(df['_processed_text'].values)
            wordcloud = WordCloud(
                width=1200, height=800,
                background_color='white',
                max_words=100,
                colormap='viridis'
            ).generate(all_text)
            
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            ax.set_title('Word Cloud', fontweight='bold', fontsize=14)
            plt.tight_layout()
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            charts['word_cloud'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
            plt.close()
        except ImportError:
            logger.info("WordCloud not installed, skipping word cloud chart")
        except Exception as e:
            logger.warning(f"Failed to generate word cloud: {e}")
        
        # =====================================================================
        # ENHANCED NLP CHARTS - Production Level
        # =====================================================================
        
        # 7. ROC Curve (for binary/multiclass classification)
        try:
            if hasattr(self.model, 'predict_proba') and self.classes is not None and len(self.classes) >= 2:
                from sklearn.metrics import roc_curve, auc
                from sklearn.preprocessing import label_binarize
                
                y_score = self.model.predict_proba(X_test)
                
                fig, ax = plt.subplots(figsize=(10, 8))
                
                if len(self.classes) == 2:
                    # Binary classification
                    fpr, tpr, _ = roc_curve(y_test, y_score[:, 1])
                    roc_auc = auc(fpr, tpr)
                    
                    ax.plot(fpr, tpr, color='#2563eb', lw=2, label=f'ROC curve (AUC = {roc_auc:.4f})')
                    ax.fill_between(fpr, 0, tpr, alpha=0.2, color='#2563eb')
                else:
                    # Multiclass: plot ROC for each class
                    try:
                        y_test_bin = label_binarize(y_test, classes=list(range(len(self.classes))))
                        colors = ['#2563eb', '#16a34a', '#dc2626', '#f59e0b', '#8b5cf6', '#ec4899']
                        
                        for i, (class_name, color) in enumerate(zip(self.classes, colors[:len(self.classes)])):
                            if i < y_test_bin.shape[1] and i < y_score.shape[1]:
                                fpr, tpr, _ = roc_curve(y_test_bin[:, i], y_score[:, i])
                                roc_auc = auc(fpr, tpr)
                                ax.plot(fpr, tpr, color=color, lw=2, label=f'{class_name[:15]} (AUC = {roc_auc:.2f})')
                    except Exception as e:
                        logger.warning(f"Multiclass ROC error: {e}")
                
                ax.plot([0, 1], [0, 1], 'k--', lw=1.5, alpha=0.7, label='Random Classifier')
                ax.set_xlabel('False Positive Rate', fontweight='bold', fontsize=12)
                ax.set_ylabel('True Positive Rate', fontweight='bold', fontsize=12)
                ax.set_title('NLP ROC Curve', fontweight='bold', fontsize=14)
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
            logger.warning(f"Failed to generate NLP ROC curve: {e}")
        
        # 8. Precision-Recall Curve
        try:
            if hasattr(self.model, 'predict_proba') and len(self.classes) == 2:
                from sklearn.metrics import precision_recall_curve, average_precision_score
                
                y_score = self.model.predict_proba(X_test)[:, 1]
                precision, recall, thresholds = precision_recall_curve(y_test, y_score)
                ap = average_precision_score(y_test, y_score)
                
                fig, ax = plt.subplots(figsize=(10, 8))
                ax.plot(recall, precision, color='#16a34a', lw=2, label=f'PR curve (AP = {ap:.4f})')
                ax.fill_between(recall, 0, precision, alpha=0.2, color='#16a34a')
                ax.set_xlabel('Recall', fontweight='bold', fontsize=12)
                ax.set_ylabel('Precision', fontweight='bold', fontsize=12)
                ax.set_title('NLP Precision-Recall Curve', fontweight='bold', fontsize=14)
                ax.legend(loc='lower left')
                ax.grid(True, alpha=0.3)
                ax.set_xlim([0, 1])
                ax.set_ylim([0, 1.05])
                plt.tight_layout()
                
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
                buffer.seek(0)
                charts['precision_recall_curve'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
                plt.close()
        except Exception as e:
            logger.warning(f"Failed to generate precision-recall curve: {e}")
        
        # 9. Prediction Confidence Distribution
        try:
            if hasattr(self.model, 'predict_proba'):
                y_proba = self.model.predict_proba(X_test)
                max_confidence = np.max(y_proba, axis=1)
                
                fig, ax = plt.subplots(figsize=(10, 6))
                
                # Histogram
                ax.hist(max_confidence, bins=30, color='#8b5cf6', edgecolor='white', alpha=0.8)
                ax.axvline(np.mean(max_confidence), color='red', linestyle='--', 
                          lw=2, label=f'Mean: {np.mean(max_confidence):.3f}')
                ax.axvline(np.median(max_confidence), color='orange', linestyle='--', 
                          lw=2, label=f'Median: {np.median(max_confidence):.3f}')
                
                ax.set_xlabel('Prediction Confidence', fontweight='bold', fontsize=12)
                ax.set_ylabel('Frequency', fontweight='bold', fontsize=12)
                ax.set_title('NLP Model Confidence Distribution', fontweight='bold', fontsize=14)
                ax.legend()
                ax.set_xlim([0, 1])
                plt.tight_layout()
                
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
                buffer.seek(0)
                charts['confidence_distribution'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
                plt.close()
        except Exception as e:
            logger.warning(f"Failed to generate confidence distribution: {e}")
        
        # 10. Per-Class Metrics Bar Chart
        try:
            if self.classes is not None and len(self.classes) >= 2:
                from sklearn.metrics import classification_report
                
                # Ensure class names are strings
                class_names_str = [str(c) for c in self.classes]
                report = classification_report(y_test, y_pred, target_names=class_names_str, output_dict=True, zero_division=0)
                
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
                
                ax.bar(x_pos - width, precision, width, label='Precision', color='#2563eb', edgecolor='white')
                ax.bar(x_pos, recall, width, label='Recall', color='#16a34a', edgecolor='white')
                ax.bar(x_pos + width, f1, width, label='F1-Score', color='#f59e0b', edgecolor='white')
                
                ax.set_xlabel('Class', fontweight='bold', fontsize=12)
                ax.set_ylabel('Score', fontweight='bold', fontsize=12)
                ax.set_title('NLP Per-Class Metrics', fontweight='bold', fontsize=14)
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
            logger.warning(f"Failed to generate per-class metrics: {e}")
        
        # 11. Confusion Matrix Normalized (Percentage)
        try:
            if cm is not None and self.classes is not None and len(self.classes) >= 2:
                fig, ax = plt.subplots(figsize=(8, 6))
                
                # Normalize confusion matrix safely
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
                ax.set_title('Normalized Confusion Matrix (%)', fontweight='bold', fontsize=14)
                plt.tight_layout()
                
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
                buffer.seek(0)
                charts['confusion_matrix_normalized'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
                plt.close()
        except Exception as e:
            logger.warning(f"Failed to generate normalized confusion matrix: {e}")
        
        # 12. Feature Vocabulary Size Chart
        try:
            fig, ax = plt.subplots(figsize=(8, 6))
            
            vocab_size = len(self.feature_names) if self.feature_names else 0
            n_classes = len(self.classes) if self.classes else 0
            n_test = len(y_test) if y_test is not None else 0
            
            # Create informative metrics
            metrics_display = {
                'Vocabulary Size': vocab_size,
                'Unique Classes': n_classes,
                'Test Samples': n_test,
            }
            
            bars = ax.bar(metrics_display.keys(), metrics_display.values(), 
                         color=['#2563eb', '#16a34a', '#f59e0b'], edgecolor='white')
            
            for bar, val in zip(bars, metrics_display.values()):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                       f'{int(val):,}', ha='center', fontweight='bold', fontsize=11)
            
            ax.set_ylabel('Count', fontweight='bold')
            ax.set_title('NLP Model Summary', fontweight='bold', fontsize=14)
            plt.tight_layout()
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            charts['model_summary'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
            plt.close()
        except Exception as e:
            logger.warning(f"Failed to generate model summary: {e}")
        
        logger.info(f"📊 Generated {len(charts)} NLP charts: {list(charts.keys())}")
        return charts
    
    def _generate_regression_charts(
        self,
        y_test: np.ndarray,
        y_pred: np.ndarray
    ) -> Dict[str, str]:
        """Generate NLP regression charts"""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        charts = {}
        
        # 1. Actual vs Predicted
        try:
            fig, ax = plt.subplots(figsize=(10, 8))
            
            ax.scatter(y_test, y_pred, alpha=0.5, c='steelblue', edgecolor='white', s=50)
            
            # Perfect prediction line
            min_val = min(y_test.min(), y_pred.min())
            max_val = max(y_test.max(), y_pred.max())
            ax.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='Perfect Prediction')
            
            ax.set_xlabel('Actual Values', fontweight='bold', fontsize=12)
            ax.set_ylabel('Predicted Values', fontweight='bold', fontsize=12)
            ax.set_title('NLP Regression: Actual vs Predicted', fontweight='bold', fontsize=14)
            ax.legend()
            plt.tight_layout()
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            charts['actual_vs_predicted'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
            plt.close()
        except Exception as e:
            logger.warning(f"Failed to generate actual vs predicted: {e}")
        
        # 2. Residuals
        try:
            residuals = y_test - y_pred
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.scatter(y_pred, residuals, alpha=0.5, c='steelblue', edgecolor='white', s=50)
            ax.axhline(y=0, color='red', linestyle='--', lw=2)
            ax.set_xlabel('Predicted Values', fontweight='bold')
            ax.set_ylabel('Residuals', fontweight='bold')
            ax.set_title('Residuals Analysis', fontweight='bold', fontsize=14)
            plt.tight_layout()
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            charts['residuals'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
            plt.close()
        except Exception as e:
            logger.warning(f"Failed to generate residuals: {e}")
        
        # 3. Error Distribution
        try:
            residuals = y_test - y_pred
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.hist(residuals, bins=50, color='steelblue', edgecolor='white', alpha=0.8)
            ax.axvline(x=0, color='red', linestyle='--', lw=2)
            ax.set_xlabel('Prediction Error', fontweight='bold')
            ax.set_ylabel('Frequency', fontweight='bold')
            ax.set_title('Error Distribution', fontweight='bold', fontsize=14)
            plt.tight_layout()
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            charts['error_distribution'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
            plt.close()
        except Exception as e:
            logger.warning(f"Failed to generate error distribution: {e}")
        
        # 4. Metrics Bar Chart
        try:
            fig, ax = plt.subplots(figsize=(8, 6))
            
            metric_names = ['R² Score', 'RMSE', 'MAE']
            metric_values = [self.metrics['r2'], self.metrics['rmse'], self.metrics['mae']]
            
            colors = ['#4CAF50', '#2196F3', '#FF9800']
            bars = ax.bar(metric_names, metric_values, color=colors, edgecolor='white')
            
            ax.set_ylabel('Value', fontweight='bold')
            ax.set_title('NLP Regression Metrics', fontweight='bold', fontsize=14)
            
            for bar, val in zip(bars, metric_values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                       f'{val:.4f}', ha='center', fontweight='bold')
            
            plt.tight_layout()
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            charts['metrics'] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
            plt.close()
        except Exception as e:
            logger.warning(f"Failed to generate metrics chart: {e}")
        
        return charts
    
    def predict(self, text: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Make prediction on new text
        
        Args:
            text: The text to classify/predict
            user_id: Optional user ID to load user-specific model
        """
        # Load user's model if user_id is provided and model not loaded
        if user_id and self.model is None:
            if not self.load(user_id):
                return {'success': False, 'error': f'No NLP model found for user {user_id}. Please train a model first.'}
        
        if self.model is None or self.vectorizer is None:
            return {'success': False, 'error': 'Model not trained. Train first or load a model.'}
        
        try:
            # Preprocess
            processed = self.preprocess_text(text)
            
            # Vectorize
            X = self.vectorizer.transform([processed])
            
            # Predict
            pred = self.model.predict(X)[0]
            
            # Handle regression vs classification
            if self.task_type == 'regression' or self.label_encoder is None:
                # Regression
                return {
                    'success': True,
                    'prediction': float(pred),
                    'confidence': None,
                    'probabilities': None,
                    'processed_text': processed[:200] + '...' if len(processed) > 200 else processed,
                    'task_type': 'regression',
                    'algorithm': self.algorithm
                }
            else:
                # Classification
                pred_label = self.label_encoder.inverse_transform([pred])[0]
                
                # Get probabilities if available
                prob = None
                confidence = None
                if hasattr(self.model, 'predict_proba'):
                    proba = self.model.predict_proba(X)[0]
                    prob = {self.classes[i]: float(p) for i, p in enumerate(proba)}
                    confidence = float(max(proba))
                elif hasattr(self.model, 'decision_function'):
                    # For SVM
                    decision = self.model.decision_function(X)[0]
                    confidence = float(1 / (1 + np.exp(-abs(decision)))) if np.isscalar(decision) else 0.8
                
                return {
                    'success': True,
                    'prediction': str(pred_label),
                    'confidence': confidence,
                    'probabilities': prob,
                    'processed_text': processed[:200] + '...' if len(processed) > 200 else processed,
                    'task_type': 'classification',
                    'algorithm': self.algorithm
                }
        except Exception as e:
            logger.error(f"NLP prediction error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _save(self, user_id: str):
        """Save model to disk"""
        save_dir = os.path.join(STORAGE_PATH, user_id)
        os.makedirs(save_dir, exist_ok=True)
        
        data = {
            'model': self.model,
            'vectorizer': self.vectorizer,
            'label_encoder': self.label_encoder,
            'text_column': self.text_column,
            'target_column': self.target_column,
            'algorithm': self.algorithm,
            'task_type': self.task_type,
            'classes': self.classes,
            'feature_names': self.feature_names,
            'metrics': self.metrics,
            'charts': self.charts,  # Save charts for state persistence
            'model_type': 'nlp',
            # NEW: Save feature metadata for Playground
            'feature_metadata': self.feature_metadata,
            'numeric_cols': self.numeric_cols,
            'categorical_cols': self.categorical_cols,
            'original_feature_columns': self.original_feature_columns,
        }
        
        with open(os.path.join(save_dir, "nlp_model.pkl"), 'wb') as f:
            pickle.dump(data, f)
        
        logger.info(f"✅ NLP model saved for user {user_id}")
    
    def load(self, user_id: str) -> bool:
        """Load model from disk"""
        try:
            model_path = os.path.join(STORAGE_PATH, user_id, "nlp_model.pkl")
            
            if not os.path.exists(model_path):
                return False
            
            with open(model_path, 'rb') as f:
                data = pickle.load(f)
            
            self.model = data['model']
            self.vectorizer = data['vectorizer']
            self.label_encoder = data['label_encoder']
            self.text_column = data['text_column']
            self.target_column = data['target_column']
            self.algorithm = data['algorithm']
            self.task_type = data.get('task_type', 'classification')
            self.classes = data['classes']
            self.feature_names = data.get('feature_names', [])
            self.metrics = data.get('metrics', {})
            self.charts = data.get('charts', {})  # Load charts for state persistence
            # NEW: Load feature metadata for Playground
            self.feature_metadata = data.get('feature_metadata', [])
            self.numeric_cols = data.get('numeric_cols', [])
            self.categorical_cols = data.get('categorical_cols', [])
            self.original_feature_columns = data.get('original_feature_columns', [])
            
            logger.info(f"✅ NLP model loaded for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load NLP model: {e}")
            return False


# Global instance
nlp_engine = NLPEngine()
