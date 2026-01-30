"""
🔍 SMART DATA ANALYZER v1.0
============================

Automatically analyzes dataset to determine the best ML approach:
- TABULAR: Standard ML (RandomForest, XGBoost, etc.)
- TEXT_HEAVY: NLP Pipeline (TF-IDF, Word2Vec, BERT)
- TIME_SERIES: Time-aware models (LSTM, Prophet)
- MIXED: Hybrid approach

Used by both Fast and Ultra modes to select the optimal pipeline.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DataType(Enum):
    """Dataset primary type"""
    TABULAR = "tabular"
    TEXT_HEAVY = "text_heavy"
    TIME_SERIES = "time_series"
    MIXED = "mixed"


class TaskType(Enum):
    """ML task type"""
    BINARY_CLASSIFICATION = "binary_classification"
    MULTICLASS_CLASSIFICATION = "multiclass_classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    ANOMALY_DETECTION = "anomaly_detection"


@dataclass
class DataAnalysis:
    """Complete analysis of a dataset"""
    data_type: DataType
    task_type: TaskType
    target_column: str
    
    # Column breakdown
    numeric_columns: List[str]
    categorical_columns: List[str]
    text_columns: List[str]
    datetime_columns: List[str]
    id_columns: List[str]
    
    # Statistics
    n_rows: int
    n_cols: int
    n_classes: Optional[int]
    class_balance: Optional[Dict[str, float]]
    missing_ratio: float
    
    # Recommendations
    recommended_pipeline: str
    recommended_models: List[str]
    preprocessing_notes: List[str]
    
    # Complexity score (1-10)
    complexity_score: int
    estimated_training_time: str
    
    # Imbalance detection (for fraud, churn, rare events) - DEFAULTS MUST BE LAST
    imbalance_ratio: float = 1.0  # majority/minority class ratio
    is_imbalanced: bool = False  # True if ratio > 10


class SmartDataAnalyzer:
    """
    🔍 Smart Data Analyzer - Auto-detect best ML approach
    
    Analyzes dataset characteristics to determine:
    1. Data type (tabular, text, time-series)
    2. Task type (classification, regression)
    3. Best models to use
    4. Preprocessing requirements
    """
    
    def __init__(self):
        # Column name patterns for detection
        self.id_patterns = ['id', 'uid', 'uuid', 'key', 'index', 'idx', 'code', 'number']
        self.target_patterns = ['target', 'label', 'class', 'y', 'outcome', 'result', 
                               'price', 'amount', 'cost', 'revenue', 'sales', 'rating',
                               'score', 'status', 'category', 'type']
        self.date_patterns = ['date', 'time', 'datetime', 'timestamp', 'created', 'updated',
                             'year', 'month', 'day', 'hour']
    
    def analyze(self, df: pd.DataFrame, target_col: Optional[str] = None) -> DataAnalysis:
        """
        Comprehensive dataset analysis
        
        Args:
            df: Input DataFrame
            target_col: Target column (auto-detected if None)
        
        Returns:
            DataAnalysis with all insights
        """
        print("🔍 SMART DATA ANALYZER - Analyzing dataset...")
        print("=" * 50)
        
        n_rows, n_cols = df.shape
        print(f"   📊 Shape: {n_rows} rows × {n_cols} columns")
        
        # 1. Detect target column if not provided
        if not target_col:
            target_col = self._detect_target(df)
        print(f"   🎯 Target: {target_col}")
        
        # 2. Classify all columns
        id_cols, numeric_cols, categorical_cols, text_cols, datetime_cols = \
            self._classify_columns(df, target_col)
        
        print(f"   📈 Numeric: {len(numeric_cols)} | Categorical: {len(categorical_cols)}")
        print(f"   📝 Text: {len(text_cols)} | DateTime: {len(datetime_cols)}")
        print(f"   🔑 IDs (dropped): {len(id_cols)}")
        
        # 3. Detect data type
        data_type = self._detect_data_type(df, text_cols, datetime_cols, n_cols)
        print(f"   📂 Data Type: {data_type.value.upper()}")
        
        # 4. Detect task type
        task_type, n_classes, class_balance = self._detect_task_type(df[target_col])
        print(f"   🎪 Task: {task_type.value.upper()}")
        if n_classes:
            print(f"   📊 Classes: {n_classes}")
        
        # 5. Calculate missing ratio
        missing_ratio = df.isnull().sum().sum() / (n_rows * n_cols)
        print(f"   ❓ Missing: {missing_ratio:.1%}")
        
        # 5.5 Calculate imbalance ratio for classification
        imbalance_ratio = 1.0
        is_imbalanced = False
        if task_type in [TaskType.BINARY_CLASSIFICATION, TaskType.MULTICLASS_CLASSIFICATION]:
            class_counts = df[target_col].value_counts()
            if len(class_counts) >= 2:
                imbalance_ratio = class_counts.max() / class_counts.min()
                is_imbalanced = imbalance_ratio > 10
                if is_imbalanced:
                    severity = "EXTREME" if imbalance_ratio > 100 else "HIGH" if imbalance_ratio > 50 else "MODERATE"
                    print(f"   ⚠️ Imbalance: {imbalance_ratio:.1f}:1 ratio ({severity})")
        
        # 6. Get recommendations
        pipeline, models, notes = self._get_recommendations(
            data_type, task_type, n_rows, text_cols, datetime_cols
        )
        print(f"   🚀 Recommended: {pipeline}")
        
        # 7. Estimate complexity
        complexity = self._estimate_complexity(
            n_rows, n_cols, len(text_cols), missing_ratio, n_classes
        )
        
        # Estimate time (Fast mode)
        if n_rows < 1000:
            time_est = "< 30 seconds"
        elif n_rows < 10000:
            time_est = "30-60 seconds"
        elif n_rows < 100000:
            time_est = "1-3 minutes"
        else:
            time_est = "3-10 minutes"
        
        print(f"   ⏱️ Estimated: {time_est}")
        print("=" * 50)
        
        return DataAnalysis(
            data_type=data_type,
            task_type=task_type,
            target_column=target_col,
            numeric_columns=numeric_cols,
            categorical_columns=categorical_cols,
            text_columns=text_cols,
            datetime_columns=datetime_cols,
            id_columns=id_cols,
            n_rows=n_rows,
            n_cols=n_cols,
            n_classes=n_classes,
            class_balance=class_balance,
            missing_ratio=missing_ratio,
            imbalance_ratio=imbalance_ratio,
            is_imbalanced=is_imbalanced,
            recommended_pipeline=pipeline,
            recommended_models=models,
            preprocessing_notes=notes,
            complexity_score=complexity,
            estimated_training_time=time_est
        )
    
    def _detect_target(self, df: pd.DataFrame) -> str:
        """Auto-detect target column"""
        cols = df.columns.tolist()
        
        # Check for common target patterns
        for pattern in self.target_patterns:
            for col in cols:
                if pattern == col.lower():
                    return col
                if pattern in col.lower() and col.lower() not in ['id', 'date']:
                    return col
        
        # Last column heuristic
        last_col = cols[-1]
        
        # Check if last column is not an ID
        if not any(p in last_col.lower() for p in self.id_patterns):
            return last_col
        
        # Fallback: first non-ID column with few unique values
        for col in reversed(cols):
            if not any(p in col.lower() for p in self.id_patterns):
                if df[col].nunique() < len(df) / 2:
                    return col
        
        return last_col
    
    def _classify_columns(
        self, df: pd.DataFrame, target_col: str
    ) -> Tuple[List[str], List[str], List[str], List[str], List[str]]:
        """Classify columns by type"""
        id_cols = []
        numeric_cols = []
        categorical_cols = []
        text_cols = []
        datetime_cols = []
        
        for col in df.columns:
            if col == target_col:
                continue
            
            col_lower = col.lower()
            series = df[col]
            
            # Check for ID columns
            is_id = any(p in col_lower for p in self.id_patterns)
            unique_ratio = series.nunique() / len(series) if len(series) > 0 else 0
            
            if is_id and unique_ratio > 0.9:
                id_cols.append(col)
                continue
            
            # Check for datetime
            if any(p in col_lower for p in self.date_patterns):
                datetime_cols.append(col)
                continue
            
            if pd.api.types.is_datetime64_any_dtype(series):
                datetime_cols.append(col)
                continue
            
            # Check if numeric
            if pd.api.types.is_numeric_dtype(series):
                numeric_cols.append(col)
                continue
            
            # String column - text or categorical?
            if series.dtype == object or series.dtype.name == 'string':
                avg_len = series.astype(str).str.len().mean()
                nunique = series.nunique()
                
                # Long text or high cardinality = text column
                if avg_len > 50 or nunique > 100:
                    text_cols.append(col)
                else:
                    categorical_cols.append(col)
        
        return id_cols, numeric_cols, categorical_cols, text_cols, datetime_cols
    
    def _detect_data_type(
        self, df: pd.DataFrame, text_cols: List[str], 
        datetime_cols: List[str], n_cols: int
    ) -> DataType:
        """Determine primary data type"""
        
        text_ratio = len(text_cols) / max(1, n_cols - 1)  # -1 for target
        datetime_ratio = len(datetime_cols) / max(1, n_cols - 1)
        
        # Calculate average text length if text columns exist
        avg_text_len = 0
        if text_cols:
            for col in text_cols:
                avg_text_len += df[col].astype(str).str.len().mean()
            avg_text_len /= len(text_cols)
        
        # Decision logic
        if text_ratio > 0.3 or (text_ratio > 0.1 and avg_text_len > 100):
            return DataType.TEXT_HEAVY
        
        if datetime_ratio > 0.2:
            return DataType.TIME_SERIES
        
        if text_ratio > 0 and datetime_ratio > 0:
            return DataType.MIXED
        
        return DataType.TABULAR
    
    def _detect_task_type(
        self, target_series: pd.Series
    ) -> Tuple[TaskType, Optional[int], Optional[Dict[str, float]]]:
        """Detect if classification or regression"""
        
        # Try to convert to numeric
        numeric_target = pd.to_numeric(target_series, errors='coerce')
        valid_ratio = numeric_target.notna().sum() / len(target_series)
        
        n_unique = target_series.nunique()
        
        # Classification indicators
        is_string = target_series.dtype == object
        is_low_cardinality = n_unique <= 20
        is_integer_like = valid_ratio > 0.9 and numeric_target.dropna().apply(lambda x: x == int(x)).all() if valid_ratio > 0.9 else False
        
        if is_string or (is_low_cardinality and is_integer_like):
            # Classification
            class_balance = target_series.value_counts(normalize=True).to_dict()
            class_balance = {str(k): float(v) for k, v in class_balance.items()}
            
            if n_unique == 2:
                return TaskType.BINARY_CLASSIFICATION, 2, class_balance
            else:
                return TaskType.MULTICLASS_CLASSIFICATION, n_unique, class_balance
        
        # Regression
        return TaskType.REGRESSION, None, None
    
    def _get_recommendations(
        self, data_type: DataType, task_type: TaskType,
        n_rows: int, text_cols: List[str], datetime_cols: List[str]
    ) -> Tuple[str, List[str], List[str]]:
        """Get pipeline and model recommendations"""
        
        notes = []
        
        # Base models by task type
        if task_type in [TaskType.BINARY_CLASSIFICATION, TaskType.MULTICLASS_CLASSIFICATION]:
            base_models = ['XGBoost', 'LightGBM', 'RandomForest', 'LogisticRegression']
        else:
            base_models = ['XGBoost', 'LightGBM', 'RandomForest', 'Ridge']
        
        # Adjust based on data type
        if data_type == DataType.TEXT_HEAVY:
            pipeline = "NLP + ML"
            models = ['MultinomialNB', 'LogisticRegression', 'XGBoost', 'SVM']
            notes.append("Text preprocessing: TF-IDF with SVD")
            notes.append("Consider BERT embeddings for Ultra mode")
            
        elif data_type == DataType.TIME_SERIES:
            pipeline = "Time-Series ML"
            models = base_models + ['LSTM', 'Prophet']
            notes.append("Extract datetime features (hour, day, month)")
            notes.append("Consider lag features for time-series")
            
        elif data_type == DataType.MIXED:
            pipeline = "Hybrid ML"
            models = base_models
            notes.append("Combined text + numeric + temporal features")
        
        # Task-specific overrides for clustering/anomaly
        elif task_type == TaskType.CLUSTERING:
            pipeline = "Clustering Pipeline"
            models = ['KMeans', 'DBSCAN', 'GaussianMixture', 'AgglomerativeClustering']
            notes.append("Using silhouette score for cluster evaluation")
            notes.append("Optimal k will be determined automatically")
        
        elif task_type == TaskType.ANOMALY_DETECTION:
            pipeline = "Anomaly Detection Pipeline"
            models = ['IsolationForest', 'OneClassSVM', 'LocalOutlierFactor', 'EllipticEnvelope']
            notes.append("Using contamination rate of 10% as default")
            notes.append("Anomalies labeled as -1, normal as 1")
            
        else:
            pipeline = "Standard ML"
            models = base_models
            if n_rows > 10000:
                notes.append("Large dataset - will use sampling")
            if n_rows < 100:
                notes.append("Small dataset - using simpler models")
        
        return pipeline, models, notes
    
    def _estimate_complexity(
        self, n_rows: int, n_cols: int, 
        n_text_cols: int, missing_ratio: float,
        n_classes: Optional[int]
    ) -> int:
        """Estimate complexity score 1-10"""
        score = 3  # Base score
        
        # Size factors
        if n_rows > 100000:
            score += 3
        elif n_rows > 10000:
            score += 2
        elif n_rows > 1000:
            score += 1
        
        # Feature factors
        if n_cols > 100:
            score += 2
        elif n_cols > 20:
            score += 1
        
        # Text complexity
        if n_text_cols > 0:
            score += 1
        
        # Missing data complexity
        if missing_ratio > 0.3:
            score += 1
        
        # Multiclass complexity
        if n_classes and n_classes > 10:
            score += 1
        
        return min(10, score)


# Convenience function
def analyze_dataset(df: pd.DataFrame, target_col: Optional[str] = None) -> DataAnalysis:
    """Quick dataset analysis"""
    analyzer = SmartDataAnalyzer()
    return analyzer.analyze(df, target_col)


# Singleton instance
smart_analyzer = SmartDataAnalyzer()
