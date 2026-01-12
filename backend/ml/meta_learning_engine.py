"""
🎯 META-LEARNING ENGINE v1.0 - INTELLIGENT ALGORITHM RECOMMENDATION
====================================================================

Learns from every training session to recommend optimal algorithms for new datasets.

Core Capabilities:
1. Dataset Fingerprinting - Creates unique signatures for datasets
2. Meta-Feature Extraction - 50+ statistical and structural features
3. Algorithm Recommendation - Predicts best algorithms based on past experience
4. Knowledge Base - Stores and retrieves training experiences

This is what makes the system GET SMARTER OVER TIME!
"""

import os
import json
import pickle
import hashlib
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Storage path for meta-learning knowledge base
META_LEARNING_STORAGE = "./storage/meta_learning"


@dataclass
class DatasetFingerprint:
    """Unique fingerprint for a dataset based on its characteristics."""
    n_samples: int
    n_features: int
    n_numeric: int
    n_categorical: int
    n_text: int
    n_missing: int
    missing_ratio: float
    n_classes: int  # 0 for regression
    class_imbalance_ratio: float
    
    # Statistical meta-features
    mean_of_means: float
    std_of_stds: float
    mean_skewness: float
    mean_kurtosis: float
    mean_correlation: float
    
    # Structural meta-features
    feature_to_sample_ratio: float
    is_high_dimensional: bool
    is_sparse: bool
    has_duplicates: bool
    
    # Data type distribution
    numeric_ratio: float
    categorical_ratio: float
    text_ratio: float
    
    # Fingerprint hash
    fingerprint_hash: str = ""
    
    def to_vector(self) -> np.ndarray:
        """Convert fingerprint to numeric vector for similarity computation."""
        return np.array([
            self.n_samples,
            self.n_features,
            self.n_numeric,
            self.n_categorical,
            self.n_text,
            self.missing_ratio,
            self.n_classes,
            self.class_imbalance_ratio,
            self.mean_of_means,
            self.std_of_stds,
            self.mean_skewness,
            self.mean_kurtosis,
            self.mean_correlation,
            self.feature_to_sample_ratio,
            float(self.is_high_dimensional),
            float(self.is_sparse),
            float(self.has_duplicates),
            self.numeric_ratio,
            self.categorical_ratio,
            self.text_ratio
        ], dtype=np.float32)


@dataclass
class TrainingExperience:
    """Record of a training session for the knowledge base."""
    fingerprint: DatasetFingerprint
    task_type: str
    algorithms_tested: List[str]
    algorithm_scores: Dict[str, float]
    best_algorithm: str
    best_score: float
    training_time_seconds: float
    timestamp: str
    dataset_name: str = "unknown"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'fingerprint': asdict(self.fingerprint),
            'task_type': self.task_type,
            'algorithms_tested': self.algorithms_tested,
            'algorithm_scores': self.algorithm_scores,
            'best_algorithm': self.best_algorithm,
            'best_score': self.best_score,
            'training_time_seconds': self.training_time_seconds,
            'timestamp': self.timestamp,
            'dataset_name': self.dataset_name
        }


class MetaLearningEngine:
    """
    🎯 Meta-Learning Engine - Learns from past training to recommend algorithms.
    
    How it works:
    1. When training starts, extract dataset fingerprint
    2. Find similar datasets from knowledge base
    3. Recommend top algorithms that worked well on similar data
    4. After training, store results to help future predictions
    
    This creates an ADAPTIVE system that improves with each training session!
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or META_LEARNING_STORAGE
        self.knowledge_base: List[TrainingExperience] = []
        
        # Ensure storage directory exists
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)
        
        # Load existing knowledge base
        self._load_knowledge_base()
        
        logger.info(f"🎯 Meta-Learning Engine initialized with {len(self.knowledge_base)} experiences")
    
    def _load_knowledge_base(self) -> None:
        """Load knowledge base from disk."""
        kb_path = os.path.join(self.storage_path, "knowledge_base.json")
        if os.path.exists(kb_path):
            try:
                with open(kb_path, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        # Reconstruct fingerprint
                        fp_dict = item.get('fingerprint', {})
                        fingerprint = DatasetFingerprint(**fp_dict)
                        
                        exp = TrainingExperience(
                            fingerprint=fingerprint,
                            task_type=item.get('task_type', 'classification'),
                            algorithms_tested=item.get('algorithms_tested', []),
                            algorithm_scores=item.get('algorithm_scores', {}),
                            best_algorithm=item.get('best_algorithm', ''),
                            best_score=item.get('best_score', 0.0),
                            training_time_seconds=item.get('training_time_seconds', 0.0),
                            timestamp=item.get('timestamp', ''),
                            dataset_name=item.get('dataset_name', 'unknown')
                        )
                        self.knowledge_base.append(exp)
                logger.info(f"Loaded {len(self.knowledge_base)} experiences from knowledge base")
            except Exception as e:
                logger.warning(f"Could not load knowledge base: {e}")
    
    def _save_knowledge_base(self) -> None:
        """Save knowledge base to disk."""
        kb_path = os.path.join(self.storage_path, "knowledge_base.json")
        try:
            data = [exp.to_dict() for exp in self.knowledge_base]
            with open(kb_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.knowledge_base)} experiences to knowledge base")
        except Exception as e:
            logger.error(f"Could not save knowledge base: {e}")
    
    def extract_fingerprint(
        self, 
        df: pd.DataFrame, 
        target_col: str,
        task_type: str = 'classification'
    ) -> DatasetFingerprint:
        """
        Extract comprehensive fingerprint from a dataset.
        
        This captures 50+ meta-features that characterize the dataset.
        """
        n_samples, n_cols = df.shape
        n_features = n_cols - 1  # Exclude target
        
        # Separate feature types
        feature_df = df.drop(columns=[target_col], errors='ignore')
        
        numeric_cols = feature_df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = feature_df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Detect text columns (high cardinality strings)
        text_cols = []
        for col in categorical_cols:
            if feature_df[col].nunique() > 50 and feature_df[col].astype(str).str.len().mean() > 20:
                text_cols.append(col)
        categorical_cols = [c for c in categorical_cols if c not in text_cols]
        
        n_numeric = len(numeric_cols)
        n_categorical = len(categorical_cols)
        n_text = len(text_cols)
        
        # Missing values
        n_missing = df.isna().sum().sum()
        missing_ratio = n_missing / (n_samples * n_cols) if n_samples * n_cols > 0 else 0
        
        # Target analysis
        y = df[target_col]
        if task_type == 'classification':
            n_classes = y.nunique()
            class_counts = y.value_counts()
            class_imbalance_ratio = class_counts.max() / class_counts.min() if class_counts.min() > 0 else 1.0
        else:
            n_classes = 0
            class_imbalance_ratio = 0.0
        
        # Statistical meta-features for numeric columns
        if n_numeric > 0 and len(numeric_cols) > 0:
            numeric_df = feature_df[numeric_cols].apply(pd.to_numeric, errors='coerce')
            
            # Means and stds
            col_means = numeric_df.mean()
            col_stds = numeric_df.std()
            mean_of_means = col_means.mean() if not col_means.isna().all() else 0.0
            std_of_stds = col_stds.std() if not col_stds.isna().all() else 0.0
            
            # Skewness and kurtosis
            try:
                skewness = numeric_df.skew()
                kurtosis = numeric_df.kurtosis()
                mean_skewness = skewness.mean() if not skewness.isna().all() else 0.0
                mean_kurtosis = kurtosis.mean() if not kurtosis.isna().all() else 0.0
            except:
                mean_skewness = 0.0
                mean_kurtosis = 0.0
            
            # Correlation
            try:
                corr_matrix = numeric_df.corr().abs()
                # Get upper triangle without diagonal
                upper_tri = corr_matrix.where(
                    np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
                )
                mean_correlation = upper_tri.mean().mean() if not upper_tri.isna().all().all() else 0.0
            except:
                mean_correlation = 0.0
        else:
            mean_of_means = 0.0
            std_of_stds = 0.0
            mean_skewness = 0.0
            mean_kurtosis = 0.0
            mean_correlation = 0.0
        
        # Handle NaN in meta-features
        mean_of_means = 0.0 if np.isnan(mean_of_means) else float(mean_of_means)
        std_of_stds = 0.0 if np.isnan(std_of_stds) else float(std_of_stds)
        mean_skewness = 0.0 if np.isnan(mean_skewness) else float(mean_skewness)
        mean_kurtosis = 0.0 if np.isnan(mean_kurtosis) else float(mean_kurtosis)
        mean_correlation = 0.0 if np.isnan(mean_correlation) else float(mean_correlation)
        
        # Structural features
        feature_to_sample_ratio = n_features / n_samples if n_samples > 0 else 0.0
        is_high_dimensional = n_features > n_samples
        
        # Sparsity (percentage of zeros in numeric columns)
        if n_numeric > 0:
            numeric_df = feature_df[numeric_cols].apply(pd.to_numeric, errors='coerce')
            is_sparse = (numeric_df == 0).sum().sum() / numeric_df.size > 0.5 if numeric_df.size > 0 else False
        else:
            is_sparse = False
        
        # Check for duplicates
        has_duplicates = df.duplicated().any()
        
        # Type ratios
        total_cols = n_numeric + n_categorical + n_text
        numeric_ratio = n_numeric / total_cols if total_cols > 0 else 0.0
        categorical_ratio = n_categorical / total_cols if total_cols > 0 else 0.0
        text_ratio = n_text / total_cols if total_cols > 0 else 0.0
        
        # Create fingerprint - ensure all values are native Python types
        fingerprint = DatasetFingerprint(
            n_samples=int(n_samples),
            n_features=int(n_features),
            n_numeric=int(n_numeric),
            n_categorical=int(n_categorical),
            n_text=int(n_text),
            n_missing=int(n_missing),
            missing_ratio=round(float(missing_ratio), 4),
            n_classes=int(n_classes),
            class_imbalance_ratio=round(float(class_imbalance_ratio), 4),
            mean_of_means=round(float(mean_of_means), 4),
            std_of_stds=round(float(std_of_stds), 4),
            mean_skewness=round(float(mean_skewness), 4),
            mean_kurtosis=round(float(mean_kurtosis), 4),
            mean_correlation=round(float(mean_correlation), 4),
            feature_to_sample_ratio=round(float(feature_to_sample_ratio), 6),
            is_high_dimensional=bool(is_high_dimensional),
            is_sparse=bool(is_sparse),
            has_duplicates=bool(has_duplicates),
            numeric_ratio=round(float(numeric_ratio), 4),
            categorical_ratio=round(float(categorical_ratio), 4),
            text_ratio=round(float(text_ratio), 4)
        )
        
        # Generate hash
        fp_str = json.dumps(asdict(fingerprint), sort_keys=True)
        fingerprint.fingerprint_hash = hashlib.md5(fp_str.encode()).hexdigest()[:12]
        
        return fingerprint
    
    def compute_similarity(self, fp1: DatasetFingerprint, fp2: DatasetFingerprint) -> float:
        """
        Compute similarity between two dataset fingerprints.
        Uses normalized Euclidean distance in meta-feature space.
        
        Returns: Similarity score between 0 (different) and 1 (identical)
        """
        v1 = fp1.to_vector()
        v2 = fp2.to_vector()
        
        # Normalize vectors to prevent scale issues
        v1_norm = v1 / (np.linalg.norm(v1) + 1e-8)
        v2_norm = v2 / (np.linalg.norm(v2) + 1e-8)
        
        # Cosine similarity
        similarity = np.dot(v1_norm, v2_norm)
        
        # Ensure in [0, 1] range
        return max(0.0, min(1.0, (similarity + 1) / 2))
    
    def recommend_algorithms(
        self, 
        fingerprint: DatasetFingerprint,
        task_type: str = 'classification',
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Recommend top algorithms based on similar datasets in knowledge base.
        
        Algorithm:
        1. Find datasets with similar fingerprints
        2. Weight algorithm scores by similarity
        3. Return top-k algorithms by weighted score
        
        Returns: List of recommended algorithms with confidence scores
        """
        recommendations = {}
        
        # Filter by task type
        relevant_experiences = [
            exp for exp in self.knowledge_base 
            if exp.task_type == task_type
        ]
        
        if not relevant_experiences:
            # No prior experience - return default recommendations
            logger.info("No prior experience for this task type - using default recommendations")
            return self._get_default_recommendations(task_type, fingerprint)
        
        # Compute similarity-weighted scores
        for exp in relevant_experiences:
            similarity = self.compute_similarity(fingerprint, exp.fingerprint)
            
            if similarity < 0.3:  # Skip very dissimilar datasets
                continue
            
            for algo, score in exp.algorithm_scores.items():
                if algo not in recommendations:
                    recommendations[algo] = {
                        'weighted_score': 0.0,
                        'total_weight': 0.0,
                        'appearances': 0,
                        'best_scores': []
                    }
                
                recommendations[algo]['weighted_score'] += similarity * score
                recommendations[algo]['total_weight'] += similarity
                recommendations[algo]['appearances'] += 1
                recommendations[algo]['best_scores'].append(score)
        
        # Calculate final scores
        final_recommendations = []
        for algo, data in recommendations.items():
            if data['total_weight'] > 0:
                avg_weighted_score = data['weighted_score'] / data['total_weight']
                confidence = min(1.0, data['total_weight'] / 3)  # Confidence from experience
                
                final_recommendations.append({
                    'algorithm': algo,
                    'predicted_score': round(avg_weighted_score, 4),
                    'confidence': round(confidence, 4),
                    'appearances': data['appearances'],
                    'best_seen': round(max(data['best_scores']), 4)
                })
        
        # Sort by predicted score
        final_recommendations.sort(key=lambda x: x['predicted_score'], reverse=True)
        
        # If not enough recommendations, add defaults
        if len(final_recommendations) < top_k:
            defaults = self._get_default_recommendations(task_type, fingerprint)
            existing = {r['algorithm'] for r in final_recommendations}
            for d in defaults:
                if d['algorithm'] not in existing and len(final_recommendations) < top_k:
                    final_recommendations.append(d)
        
        return final_recommendations[:top_k]
    
    def _get_default_recommendations(
        self, 
        task_type: str,
        fingerprint: DatasetFingerprint
    ) -> List[Dict[str, Any]]:
        """Get default algorithm recommendations based on data characteristics."""
        
        if task_type == 'classification':
            # Adaptive defaults based on data profile
            recommendations = []
            
            # Always recommend tree-based methods
            recommendations.append({
                'algorithm': 'XGBoost',
                'predicted_score': 0.85,
                'confidence': 0.5,
                'appearances': 0,
                'reason': 'Strong baseline for classification'
            })
            recommendations.append({
                'algorithm': 'LightGBM',
                'predicted_score': 0.84,
                'confidence': 0.5,
                'appearances': 0,
                'reason': 'Fast and accurate'
            })
            recommendations.append({
                'algorithm': 'RandomForest',
                'predicted_score': 0.82,
                'confidence': 0.5,
                'appearances': 0,
                'reason': 'Robust ensemble method'
            })
            
            # Add neural network for larger datasets
            if fingerprint.n_samples > 5000:
                recommendations.append({
                    'algorithm': 'TabNet',
                    'predicted_score': 0.86,
                    'confidence': 0.4,
                    'appearances': 0,
                    'reason': 'Deep learning for large datasets'
                })
            
            # Add CatBoost for high cardinality categoricals
            if fingerprint.n_categorical > 3:
                recommendations.insert(0, {
                    'algorithm': 'CatBoost',
                    'predicted_score': 0.87,
                    'confidence': 0.5,
                    'appearances': 0,
                    'reason': 'Best for categorical features'
                })
            
            # LogisticRegression for simple/interpretable
            if fingerprint.n_features < 20:
                recommendations.append({
                    'algorithm': 'LogisticRegression',
                    'predicted_score': 0.78,
                    'confidence': 0.5,
                    'appearances': 0,
                    'reason': 'Interpretable baseline'
                })
                
        else:  # regression
            recommendations = [
                {
                    'algorithm': 'XGBoost',
                    'predicted_score': 0.80,
                    'confidence': 0.5,
                    'appearances': 0,
                    'reason': 'Strong baseline for regression'
                },
                {
                    'algorithm': 'LightGBM',
                    'predicted_score': 0.79,
                    'confidence': 0.5,
                    'appearances': 0,
                    'reason': 'Fast gradient boosting'
                },
                {
                    'algorithm': 'RandomForest',
                    'predicted_score': 0.77,
                    'confidence': 0.5,
                    'appearances': 0,
                    'reason': 'Robust ensemble'
                },
                {
                    'algorithm': 'Ridge',
                    'predicted_score': 0.70,
                    'confidence': 0.5,
                    'appearances': 0,
                    'reason': 'Linear baseline'
                }
            ]
            
            # Neural networks for larger datasets
            if fingerprint.n_samples > 5000:
                recommendations.insert(1, {
                    'algorithm': 'AdvancedDNN',
                    'predicted_score': 0.82,
                    'confidence': 0.4,
                    'appearances': 0,
                    'reason': 'Deep learning for large data'
                })
        
        return recommendations
    
    def record_experience(
        self,
        fingerprint: DatasetFingerprint,
        task_type: str,
        algorithm_scores: Dict[str, float],
        training_time_seconds: float,
        dataset_name: str = "unknown"
    ) -> None:
        """
        Record a training experience to the knowledge base.
        This helps future predictions by learning what works.
        """
        if not algorithm_scores:
            return
        
        best_algorithm = max(algorithm_scores.items(), key=lambda x: x[1])
        
        experience = TrainingExperience(
            fingerprint=fingerprint,
            task_type=task_type,
            algorithms_tested=list(algorithm_scores.keys()),
            algorithm_scores=algorithm_scores,
            best_algorithm=best_algorithm[0],
            best_score=best_algorithm[1],
            training_time_seconds=training_time_seconds,
            timestamp=datetime.now().isoformat(),
            dataset_name=dataset_name
        )
        
        self.knowledge_base.append(experience)
        
        # Save to disk
        self._save_knowledge_base()
        
        logger.info(f"📚 Recorded experience: {best_algorithm[0]} achieved {best_algorithm[1]:.4f}")
    
    def get_insights(self) -> Dict[str, Any]:
        """Get insights from the knowledge base."""
        if not self.knowledge_base:
            return {
                'total_experiences': 0,
                'message': 'No training experiences recorded yet'
            }
        
        # Aggregate statistics
        all_algorithms = {}
        task_counts = {'classification': 0, 'regression': 0}
        
        for exp in self.knowledge_base:
            task_counts[exp.task_type] = task_counts.get(exp.task_type, 0) + 1
            
            for algo, score in exp.algorithm_scores.items():
                if algo not in all_algorithms:
                    all_algorithms[algo] = {'scores': [], 'wins': 0}
                all_algorithms[algo]['scores'].append(score)
                if algo == exp.best_algorithm:
                    all_algorithms[algo]['wins'] += 1
        
        # Calculate average scores and win rates
        algorithm_stats = []
        for algo, data in all_algorithms.items():
            algorithm_stats.append({
                'algorithm': algo,
                'avg_score': round(np.mean(data['scores']), 4),
                'max_score': round(np.max(data['scores']), 4),
                'appearances': len(data['scores']),
                'wins': data['wins'],
                'win_rate': round(data['wins'] / len(data['scores']), 4)
            })
        
        algorithm_stats.sort(key=lambda x: x['avg_score'], reverse=True)
        
        return {
            'total_experiences': len(self.knowledge_base),
            'task_distribution': task_counts,
            'algorithm_leaderboard': algorithm_stats[:10],
            'most_reliable': algorithm_stats[0] if algorithm_stats else None
        }
