"""
Data Behavior Scorer - Pure Mathematical Analysis
==================================================
Computes numeric behavior scores for any dataset without domain assumptions.

Scores:
- density: metric pressure (0-1)
- complexity: relationship depth (0-1)
- volatility: variance/noise (0-1)
- temporal: time dominance (0-1)
- sparsity: missing/uneven signals (0-1)

NO DOMAIN LOGIC. Only mathematical properties of the DataFrame.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any
from scipy.stats import variation
from sklearn.preprocessing import StandardScaler
import hashlib


@dataclass
class BehaviorScores:
    """Pure mathematical behavior scores"""
    density: float          # 0-1: metric pressure
    complexity: float       # 0-1: relationship depth
    volatility: float       # 0-1: variance/noise
    temporal: float         # 0-1: time dominance
    sparsity: float         # 0-1: missing signals
    
    # Metadata for debugging
    num_numeric_cols: int
    num_datetime_cols: int
    num_categorical_cols: int
    total_rows: int
    total_cols: int
    correlation_matrix_rank: int
    data_fingerprint: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "density": round(self.density, 3),
            "complexity": round(self.complexity, 3),
            "volatility": round(self.volatility, 3),
            "temporal": round(self.temporal, 3),
            "sparsity": round(self.sparsity, 3),
            "metadata": {
                "num_numeric_cols": int(self.num_numeric_cols),
                "num_datetime_cols": int(self.num_datetime_cols),
                "num_categorical_cols": int(self.num_categorical_cols),
                "total_rows": int(self.total_rows),
                "total_cols": int(self.total_cols),
                "correlation_matrix_rank": int(self.correlation_matrix_rank),
                "data_fingerprint": self.data_fingerprint
            }
        }


class DataBehaviorScorer:
    """
    Pure mathematical analyzer - NO domain assumptions.
    
    Example:
        scorer = DataBehaviorScorer()
        behavior = scorer.score(df)
        # Returns: BehaviorScores(density=0.82, complexity=0.47, ...)
    """
    
    def score(self, df: pd.DataFrame) -> BehaviorScores:
        """
        Compute all behavior scores for a dataset.
        
        Args:
            df: Any pandas DataFrame
            
        Returns:
            BehaviorScores object with all metrics
        """
        if df is None or df.empty:
            return self._empty_scores()
        
        # Detect column types (pure type detection, no semantics)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        
        # Try to detect datetime columns from string columns
        for col in df.select_dtypes(include=['object']).columns:
            try:
                pd.to_datetime(df[col], errors='raise')
                datetime_cols.append(col)
            except:
                pass
        
        categorical_cols = [c for c in df.columns 
                          if c not in numeric_cols and c not in datetime_cols]
        
        # Calculate scores
        density_score = self._calculate_density(df, numeric_cols)
        complexity_score = self._calculate_complexity(df, numeric_cols)
        volatility_score = self._calculate_volatility(df, numeric_cols)
        temporal_score = self._calculate_temporal(df, datetime_cols, numeric_cols)
        sparsity_score = self._calculate_sparsity(df)
        
        # Correlation matrix rank for complexity
        corr_rank = 0
        if len(numeric_cols) > 1:
            try:
                corr_matrix = df[numeric_cols].corr().fillna(0)
                corr_rank = np.linalg.matrix_rank(corr_matrix)
            except:
                corr_rank = len(numeric_cols)
        
        # Data fingerprint
        fingerprint = self._generate_fingerprint(df)
        
        return BehaviorScores(
            density=density_score,
            complexity=complexity_score,
            volatility=volatility_score,
            temporal=temporal_score,
            sparsity=sparsity_score,
            num_numeric_cols=len(numeric_cols),
            num_datetime_cols=len(datetime_cols),
            num_categorical_cols=len(categorical_cols),
            total_rows=len(df),
            total_cols=len(df.columns),
            correlation_matrix_rank=corr_rank,
            data_fingerprint=fingerprint
        )
    
    def _calculate_density(self, df: pd.DataFrame, numeric_cols: list) -> float:
        """
        Density = metric pressure
        Formula: (num_numeric / total_cols) * mean_normalized_range
        
        High density = many numeric columns with wide value ranges
        """
        if len(numeric_cols) == 0:
            return 0.0
        
        total_cols = len(df.columns)
        col_ratio = len(numeric_cols) / total_cols
        
        # Calculate mean normalized range
        ranges = []
        for col in numeric_cols:
            col_data = df[col].dropna()
            if len(col_data) > 0:
                col_min, col_max = col_data.min(), col_data.max()
                if col_max != col_min:
                    # Normalize by coefficient of variation
                    cv = variation(col_data.values, nan_policy='omit')
                    ranges.append(min(cv, 2.0))  # Cap at 2.0
        
        mean_range = np.mean(ranges) if ranges else 0.0
        
        # Combine: more numeric cols + wider ranges = higher density
        density = col_ratio * min(mean_range / 2.0, 1.0)
        
        return float(np.clip(density, 0.0, 1.0))
    
    def _calculate_complexity(self, df: pd.DataFrame, numeric_cols: list) -> float:
        """
        Complexity = relationship depth
        Formula: Average absolute correlation * (rank / max_rank)
        
        High complexity = many strong correlations between columns
        """
        if len(numeric_cols) < 2:
            return 0.0
        
        try:
            # Calculate correlation matrix
            corr_matrix = df[numeric_cols].corr().fillna(0)
            
            # Get upper triangle (exclude diagonal)
            mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
            correlations = corr_matrix.where(mask).stack().values
            
            # Average absolute correlation
            mean_abs_corr = np.mean(np.abs(correlations))
            
            # Matrix rank (measures linear independence)
            rank = np.linalg.matrix_rank(corr_matrix)
            max_rank = len(numeric_cols)
            rank_ratio = rank / max_rank
            
            # Complexity = strong correlations + high rank
            complexity = mean_abs_corr * rank_ratio
            
            return float(np.clip(complexity, 0.0, 1.0))
        
        except Exception as e:
            # Fallback: use number of numeric columns as proxy
            return min(len(numeric_cols) / 10.0, 1.0)
    
    def _calculate_volatility(self, df: pd.DataFrame, numeric_cols: list) -> float:
        """
        Volatility = variance/noise
        Formula: Mean coefficient of variation across numeric columns
        
        High volatility = high variance, noisy data
        """
        if len(numeric_cols) == 0:
            return 0.0
        
        cvs = []
        for col in numeric_cols:
            col_data = df[col].dropna()
            if len(col_data) > 1:
                cv = variation(col_data.values, nan_policy='omit')
                if not np.isnan(cv) and not np.isinf(cv):
                    cvs.append(cv)
        
        if not cvs:
            return 0.0
        
        # Mean CV, normalized to 0-1 range
        mean_cv = np.mean(cvs)
        volatility = min(mean_cv / 2.0, 1.0)  # Assume CV > 2 is very volatile
        
        return float(np.clip(volatility, 0.0, 1.0))
    
    def _calculate_temporal(self, df: pd.DataFrame, datetime_cols: list, 
                           numeric_cols: list) -> float:
        """
        Temporal = time dominance
        Formula: (has_datetime * regularity * time_coverage)
        
        High temporal = regular time series with good coverage
        """
        if len(datetime_cols) == 0:
            return 0.0
        
        # Base score: has datetime column(s)
        has_datetime = 1.0
        
        # Check regularity of first datetime column
        regularity = 0.5  # Default
        time_coverage = 0.5  # Default
        
        try:
            # Convert to datetime if needed
            time_col = df[datetime_cols[0]]
            if not pd.api.types.is_datetime64_any_dtype(time_col):
                time_col = pd.to_datetime(time_col, errors='coerce')
            
            time_col = time_col.dropna().sort_values()
            
            if len(time_col) > 2:
                # Calculate time gaps
                gaps = time_col.diff().dropna()
                
                # Regularity = consistency of gaps (lower std = more regular)
                gap_cv = variation(gaps.dt.total_seconds(), nan_policy='omit')
                regularity = 1.0 / (1.0 + gap_cv) if not np.isnan(gap_cv) else 0.5
                
                # Time coverage = % of rows with valid timestamps
                time_coverage = len(time_col) / len(df)
        
        except Exception as e:
            pass
        
        # Temporal score combines all factors
        temporal = has_datetime * regularity * time_coverage
        
        return float(np.clip(temporal, 0.0, 1.0))
    
    def _calculate_sparsity(self, df: pd.DataFrame) -> float:
        """
        Sparsity = missing/uneven signals
        Formula: (null_ratio + zero_ratio + duplicate_ratio) / 3
        
        High sparsity = lots of missing, zero, or duplicate values
        """
        total_cells = df.shape[0] * df.shape[1]
        
        # Null ratio
        null_count = df.isnull().sum().sum()
        null_ratio = null_count / total_cells
        
        # Zero ratio (for numeric columns)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        zero_count = (df[numeric_cols] == 0).sum().sum() if len(numeric_cols) > 0 else 0
        total_numeric_cells = len(df) * len(numeric_cols) if len(numeric_cols) > 0 else 1
        zero_ratio = zero_count / total_numeric_cells
        
        # Duplicate ratio
        duplicate_count = df.duplicated().sum()
        duplicate_ratio = duplicate_count / len(df)
        
        # Average sparsity
        sparsity = (null_ratio + zero_ratio + duplicate_ratio) / 3.0
        
        return float(np.clip(sparsity, 0.0, 1.0))
    
    def _generate_fingerprint(self, df: pd.DataFrame) -> str:
        """
        Generate unique fingerprint for the dataset structure.
        Formula: hash(column_names + column_types)
        """
        columns_str = "_".join(df.columns.tolist())
        types_str = "_".join(df.dtypes.astype(str).tolist())
        combined = f"{columns_str}::{types_str}"
        
        hash_obj = hashlib.md5(combined.encode())
        return hash_obj.hexdigest()[:16]
    
    def _empty_scores(self) -> BehaviorScores:
        """Return zero scores for empty dataframe"""
        return BehaviorScores(
            density=0.0,
            complexity=0.0,
            volatility=0.0,
            temporal=0.0,
            sparsity=1.0,  # Empty = fully sparse
            num_numeric_cols=0,
            num_datetime_cols=0,
            num_categorical_cols=0,
            total_rows=0,
            total_cols=0,
            correlation_matrix_rank=0,
            data_fingerprint="empty"
        )


# Example usage
if __name__ == "__main__":
    # Test with sample data
    test_data = pd.DataFrame({
        'date': pd.date_range('2023-01-01', periods=100),
        'revenue': np.random.normal(10000, 2000, 100),
        'customers': np.random.poisson(50, 100),
        'category': np.random.choice(['A', 'B', 'C'], 100)
    })
    
    scorer = DataBehaviorScorer()
    behavior = scorer.score(test_data)
    
    print("Data Behavior Scores:")
    print(f"  Density:    {behavior.density:.3f}")
    print(f"  Complexity: {behavior.complexity:.3f}")
    print(f"  Volatility: {behavior.volatility:.3f}")
    print(f"  Temporal:   {behavior.temporal:.3f}")
    print(f"  Sparsity:   {behavior.sparsity:.3f}")
    print(f"\nFingerprint: {behavior.data_fingerprint}")
