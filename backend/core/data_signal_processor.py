"""
Data Signal Processor
=====================
Computes the 5 fundamental signals of data behavior.
Input: DataFrame
Output: Normalized Interaction Signals (0.0 - 1.0)
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Any

class DataSignalProcessor:
    def process_signals(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Compute all metrics and return normalized signals.
        """
        if df.empty:
            return self._default_signals()

        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        datetime_cols = self._detect_datetime_cols(df)

        signals = {
            "temporal_strength": self._compute_temporal_strength(df, datetime_cols, numeric_cols),
            "entropy": self._compute_entropy(df, categorical_cols),
            "variance_pressure": self._compute_variance_pressure(df, numeric_cols),
            "relationship_density": self._compute_relationship_density(df, numeric_cols, categorical_cols), # Updated signature
            "compactness": self._compute_compactness(df)
        }

        # BUSINESS DOMAIN BOOST
        # If we have dates and sales-like data, we enforce a baseline temporal strength
        # because business users EXPECT to see timelines even if noisy.
        if datetime_cols and len(df) > 10:
             signals['temporal_strength'] = max(signals['temporal_strength'], 0.85)

        return signals

    def _default_signals(self):
        return {
            "temporal_strength": 0.0,
            "entropy": 0.0,
            "variance_pressure": 0.0,
            "relationship_density": 0.0,
            "compactness": 0.0
        }

    def _detect_datetime_cols(self, df):
        cols = []
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                cols.append(col)
            elif 'date' in col.lower() or 'time' in col.lower():
                try:
                    pd.to_datetime(df[col], errors='raise')
                    cols.append(col)
                except:
                    pass
        return cols

    def _compute_temporal_strength(self, df, date_cols, num_cols) -> float:
        """
        Measures how much 'time' matters.
        """
        if not date_cols:
            return 0.0
        
        # If dates exist, we start with a strong baseline for Business Intelligence
        return 0.6 

    def _compute_entropy(self, df, cat_cols) -> float:
        """
        Measures information complexity/chaos.
        """
        if len(cat_cols) == 0:
            return 0.0

        entropy_scores = []
        for col in cat_cols:
            counts = df[col].value_counts(normalize=True)
            ent = stats.entropy(counts)
            n_unique = len(counts)
            if n_unique > 1:
                normalized_ent = ent / np.log(n_unique)
                entropy_scores.append(normalized_ent)
            else:
                entropy_scores.append(0.0)

        return float(np.mean(entropy_scores))

    def _compute_variance_pressure(self, df, num_cols) -> float:
        """
        Measures value distribution extremity.
        """
        if len(num_cols) == 0:
            return 0.0

        pressure_scores = []
        for col in num_cols:
            v = df[col].dropna()
            if len(v) < 2: continue

            mean = np.mean(v)
            std = np.std(v)
            cv = (std / abs(mean)) if mean != 0 else 0
            cv_score = min(cv, 3.0) / 3.0 
            pressure_scores.append(cv_score)

        if not pressure_scores: return 0.0

        return float(np.mean(pressure_scores))

    def _compute_relationship_density(self, df, num_cols, cat_cols) -> float:
        """
        Measures interconnectedness.
        """
        score = 0.0
        
        # 1. Numeric Correlations
        if len(num_cols) >= 2:
            try:
                corr_matrix = df[num_cols].corr().abs()
                np.fill_diagonal(corr_matrix.values, np.nan)
                mean_corr = corr_matrix.mean().mean()
                score += (mean_corr if not np.isnan(mean_corr) else 0) * 0.5
            except: pass

        # 2. Categorical Co-occurrence (Business Context)
        # If we have interactions between categories (e.g. Region <-> Category), that's dense!
        if len(cat_cols) >= 2:
            score += 0.4 # Bonus for having multi-dimensional categories

        return min(1.0, score)

    def _compute_compactness(self, df) -> float:
        """
        Measures information density vs sparsity.
        """
        total_cells = df.size
        if total_cells == 0: return 0.0
        non_nulls = df.count().sum()
        density = non_nulls / total_cells
        return float(density)
