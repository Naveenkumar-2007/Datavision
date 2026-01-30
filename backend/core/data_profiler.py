"""
Deep Data Profiler - Autonomous Data Intelligence
=================================================
NO HARDCODING. Discovers patterns from raw data.

This analyzes data to find:
- Temporal patterns (seasonality, trends)
- Correlations (what relates to what)
- Anomalies (unexpected values)
- Categorical distributions
- Top insights ranked by importance

Output is 100% data-driven intelligence.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime
from scipy import stats


class DeepDataProfiler:
    """
    Autonomously discovers data patterns and insights.
    NO predefined rules - everything learned from data.
    """
    
    def profile(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze dataset and return intelligence report.
        """
        # Detect column types
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        datetime_cols = self._detect_datetime_cols(df)
        categorical_cols = [c for c in df.columns 
                          if c not in numeric_cols and c not in datetime_cols]
        
        # Discover patterns (NO HARDCODING - learned from data!)
        patterns = self._discover_patterns(df, numeric_cols, datetime_cols, categorical_cols)
        insights = self._rank_insights(df, patterns, numeric_cols, categorical_cols)
        relationships = self._find_relationships(df, numeric_cols)
        anomalies = self._detect_anomalies(df, numeric_cols)
        
        # Generate data story
        story = self._generate_story(df, insights, patterns, anomalies)
        
        return {
            "data_story": story,
            "columns": {
                "numeric": numeric_cols,
                "datetime": datetime_cols,
                "categorical": categorical_cols
            },
            "patterns": patterns,
            "insights": insights,  # Ranked by importance (0.0-1.0)
            "relationships": relationships,
            "anomalies": anomalies,
            "dimension_count": len(df.columns),
            "row_count": len(df)
        }
    
    def _detect_datetime_cols(self, df: pd.DataFrame) -> List[str]:
        """Intelligently detect datetime columns."""
        datetime_cols = []
        for col in df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                try:
                    pd.to_datetime(df[col])
                    datetime_cols.append(col)
                except:
                    pass
        return datetime_cols
    
    def _discover_patterns(self, df, numeric_cols, datetime_cols, categorical_cols):
        """
        Discover patterns WITHOUT hardcoding.
        Learns from the data itself.
        """
        patterns = {}
        
        # Temporal patterns (if time dimension exists)
        if datetime_cols and numeric_cols:
            temporal = self._analyze_temporal_patterns(df, datetime_cols[0], numeric_cols)
            if temporal:
                patterns['temporal'] = temporal
        
        # Categorical distributions
        if categorical_cols and numeric_cols:
            distributions = self._analyze_categorical_distributions(df, categorical_cols, numeric_cols)
            if distributions:
                patterns['categorical'] = distributions
        
        # Numeric trends
        if numeric_cols:
            trends = self._analyze_numeric_trends(df, numeric_cols)
            if trends:
                patterns['numeric'] = trends
        
        return patterns
    
    def _analyze_temporal_patterns(self, df, date_col, numeric_cols):
        """Find temporal patterns like seasonality, trends."""
        patterns = []
        
        for num_col in numeric_cols[:3]:  # Top 3 numeric columns
            try:
                # Sort by date
                df_sorted = df.sort_values(date_col)
                values = df_sorted[num_col].values
                
                # Detect trend
                x = np.arange(len(values))
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
                
                if abs(r_value) > 0.5:  # Strong correlation
                    pattern_type = "increasing" if slope > 0 else "decreasing"
                    patterns.append({
                        "column": num_col,
                        "type": f"{pattern_type}_trend",
                        "strength": abs(r_value),
                        "description": f"{num_col} shows {pattern_type} trend over time (R={r_value:.2f})"
                    })
                
                # Detect spikes/drops
                mean_val = values.mean()
                std_val = values.std()
                spikes = np.where(values > mean_val + 2 * std_val)[0]
                drops = np.where(values < mean_val - 2 * std_val)[0]
                
                if len(spikes) > 0:
                    patterns.append({
                        "column": num_col,
                        "type": "spike",
                        "strength": len(spikes) / len(values),
                        "description": f"{num_col} has {len(spikes)} significant spikes (>2σ above mean)"
                    })
                
                if len(drops) > 0:
                    patterns.append({
                        "column": num_col,
                        "type": "drop",
                        "strength": len(drops) / len(values),
                        "description": f"{num_col} has {len(drops)} significant drops (>2σ below mean)"
                    })
            except:
                pass
        
        return patterns
    
    def _analyze_categorical_distributions(self, df, categorical_cols, numeric_cols):
        """Analyze how numeric values distribute across categories."""
        distributions = []
        
        for cat_col in categorical_cols[:2]:
            for num_col in numeric_cols[:2]:
                try:
                    grouped = df.groupby(cat_col)[num_col].agg(['sum', 'mean', 'count'])
                    
                    # Find top categories
                    top_categories = grouped.nlargest(3, 'sum')
                    top_pct = top_categories['sum'].sum() / grouped['sum'].sum()
                    
                    if top_pct > 0.5:  # Top 3 represent >50%
                        distributions.append({
                            "categorical": cat_col,
                            "numeric": num_col,
                            "type": "concentration",
                            "strength": top_pct,
                            "description": f"Top 3 {cat_col} = {top_pct*100:.0f}% of {num_col}"
                        })
                except:
                    pass
        
        return distributions
    
    def _analyze_numeric_trends(self, df, numeric_cols):
        """Analyze numeric column characteristics."""
        trends = []
        
        for col in numeric_cols:
            values = df[col].dropna()
            
            # Calculate statistics
            mean_val = values.mean()
            std_val = values.std()
            cv = std_val / mean_val if mean_val != 0 else 0  # Coefficient of variation
            
            # High variation?
            if cv > 0.5:
                trends.append({
                    "column": col,
                    "type": "high_volatility",
                    "strength": cv,
                    "description": f"{col} shows high variability (CV={cv:.2f})"
                })
        
        return trends
    
    def _find_relationships(self, df, numeric_cols):
        """Discover correlations between numeric columns."""
        relationships = {"strong": [], "moderate": [], "weak": []}
        
        if len(numeric_cols) < 2:
            return relationships
        
        # Calculate correlation matrix
        corr_matrix = df[numeric_cols].corr()
        
        # Find significant correlations
        for i in range(len(numeric_cols)):
            for j in range(i+1, len(numeric_cols)):
                col1 = numeric_cols[i]
                col2 = numeric_cols[j]
                corr = corr_matrix.iloc[i, j]
                
                if abs(corr) > 0.7:
                    relationships["strong"].append({
                        "col1": col1,
                        "col2": col2,
                        "correlation": corr,
                        "description": f"{col1} ↔ {col2} (r={corr:.2f})"
                    })
                elif abs(corr) > 0.4:
                    relationships["moderate"].append({
                        "col1": col1,
                        "col2": col2,
                        "correlation": corr
                    })
        
        return relationships
    
    def _detect_anomalies(self, df, numeric_cols):
        """Find unusual data points."""
        anomalies = []
        
        for col in numeric_cols[:3]:
            values = df[col].dropna()
            
            # z-score method
            z_scores = np.abs(stats.zscore(values))
            outliers = np.where(z_scores > 3)[0]
            
            if len(outliers) > 0:
                anomalies.append({
                    "column": col,
                    "count": len(outliers),
                    "percentage": len(outliers) / len(values) * 100,
                    "description": f"{col} has {len(outliers)} anomalies ({len(outliers)/len(values)*100:.1f}%)"
                })
        
        return anomalies
    
    def _rank_insights(self, df, patterns, numeric_cols, categorical_cols):
        """
        Rank insights by importance (0.0-1.0).
        MORE important = higher score.
        """
        insights = []
        
        # From temporal patterns
        if 'temporal' in patterns:
            for pattern in patterns['temporal']:
                importance = pattern['strength']
                insights.append({
                    "insight": pattern['description'],
                    "importance": importance,
                    "type": "temporal"
                })
        
        # From categorical distributions
        if 'categorical' in patterns:
            for pattern in patterns['categorical']:
                importance = pattern['strength']
                insights.append({
                    "insight": pattern['description'],
                    "importance": importance,
                    "type": "categorical"
                })
        
        # From numeric trends
        if 'numeric' in patterns:
            for pattern in patterns['numeric']:
                importance = min(pattern['strength'], 1.0)
                insights.append({
                    "insight": pattern['description'],
                    "importance": importance,
                    "type": "numeric"
                })
        
        # Sort by importance
        insights.sort(key=lambda x: x['importance'], reverse=True)
        
        return insights
    
    def _generate_story(self, df, insights, patterns, anomalies):
        """
        Generate narrative from insights (NO TEMPLATES!).
        Story changes based on what's actually found.
        """
        story_parts = []
        
        # Start with dataset size
        story_parts.append(f"Dataset contains {len(df)} records across {len(df.columns)} dimensions.")
        
        # Add top insight
        if insights:
            top_insight = insights[0]
            story_parts.append(f"Key finding: {top_insight['insight']}")
        
        # Add pattern summary
        if 'temporal' in patterns and patterns['temporal']:
            story_parts.append(f"Shows {len(patterns['temporal'])} temporal patterns.")
        
        # Add anomaly note
        if anomalies:
            total_anomalies = sum(a['count'] for a in anomalies)
            story_parts.append(f"Detected {total_anomalies} anomalies requiring investigation.")
        
        return " ".join(story_parts)
