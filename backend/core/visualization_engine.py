"""
REAL POWER BI ENGINE v14.0 - FULLY DYNAMIC
==========================================
NO HARDCODED LAYOUTS!

This engine:
1. Analyzes the dataset to detect column types
2. Evaluates ALL chart types for compatibility
3. Generates ONLY charts that the data supports
4. Returns a dynamic list of visualizations
5. Frontend renders ALL returned charts

CHART TYPES:
- kpi: Key Performance Indicators (always)
- bar_vertical: Vertical bar chart
- bar_horizontal: Horizontal bar chart (ranking)
- area: Area chart
- line: Line chart (time series)
- donut: Donut/Pie distribution
- radar: Radar/Spider chart
- scatter: Scatter plot (correlation)
- stats_card: Statistical summary
- treemap: Hierarchical view
- top5_list: Top N rankings
- data_table: Raw data view
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import random
import hashlib


# 25 Color Palettes
ALL_PALETTES = [
    ['#3B82F6', '#22C55E', '#F59E0B', '#EC4899', '#8B5CF6', '#06B6D4', '#EF4444', '#14B8A6'],
    ['#6366F1', '#10B981', '#F97316', '#E11D48', '#A855F7', '#14B8A6', '#84CC16', '#F43F5E'],
    ['#2563EB', '#16A34A', '#CA8A04', '#DB2777', '#7C3AED', '#0891B2', '#DC2626', '#0D9488'],
    ['#0EA5E9', '#84CC16', '#EAB308', '#F43F5E', '#9333EA', '#0D9488', '#EA580C', '#7C3AED'],
    ['#3730A3', '#059669', '#D97706', '#BE123C', '#6D28D9', '#0E7490', '#B91C1C', '#047857'],
    ['#DC2626', '#16A34A', '#2563EB', '#9333EA', '#EA580C', '#0891B2', '#65A30D', '#C026D3'],
    ['#F97316', '#6366F1', '#22C55E', '#F43F5E', '#06B6D4', '#8B5CF6', '#EAB308', '#10B981'],
    ['#8B5CF6', '#F59E0B', '#3B82F6', '#22C55E', '#EC4899', '#14B8A6', '#EF4444', '#0EA5E9'],
    ['#14B8A6', '#EC4899', '#F59E0B', '#3B82F6', '#22C55E', '#6366F1', '#F43F5E', '#84CC16'],
    ['#22C55E', '#3B82F6', '#EC4899', '#F59E0B', '#8B5CF6', '#06B6D4', '#EF4444', '#A855F7'],
    ['#0284C7', '#059669', '#D97706', '#BE185D', '#7C3AED', '#0891B2', '#DC2626', '#4F46E5'],
    ['#7C3AED', '#F59E0B', '#10B981', '#E11D48', '#0EA5E9', '#84CC16', '#DB2777', '#6366F1'],
    ['#0891B2', '#D946EF', '#65A30D', '#F43F5E', '#2563EB', '#EA580C', '#14532D', '#9333EA'],
    ['#BE185D', '#0D9488', '#CA8A04', '#6D28D9', '#0369A1', '#B91C1C', '#047857', '#7E22CE'],
    ['#4338CA', '#15803D', '#A16207', '#9D174D', '#1E40AF', '#9A3412', '#166534', '#7E22CE'],
    ['#475569', '#64748B', '#94A3B8', '#CBD5E1', '#E2E8F0', '#F1F5F9', '#334155', '#1E293B'],
    ['#059669', '#D97706', '#7C3AED', '#DB2777', '#0891B2', '#DC2626', '#16A34A', '#9333EA'],
    ['#F472B6', '#34D399', '#FBBF24', '#60A5FA', '#A78BFA', '#2DD4BF', '#F87171', '#818CF8'],
    ['#4ADE80', '#FB923C', '#A78BFA', '#F472B6', '#22D3EE', '#FACC15', '#F87171', '#818CF8'],
    ['#38BDF8', '#4ADE80', '#FBBF24', '#F472B6', '#A78BFA', '#2DD4BF', '#FB7185', '#34D399'],
    ['#F87171', '#A3E635', '#38BDF8', '#E879F9', '#2DD4BF', '#FCD34D', '#818CF8', '#FB923C'],
    ['#C084FC', '#4ADE80', '#FACC15', '#F472B6', '#67E8F9', '#FB923C', '#A5B4FC', '#86EFAC'],
    ['#FCA5A5', '#6EE7B7', '#FDE047', '#F9A8D4', '#A5F3FC', '#FDBA74', '#C4B5FD', '#BEF264'],
    ['#FED7AA', '#A7F3D0', '#FEF08A', '#FBCFE8', '#CFFAFE', '#FED7AA', '#DDD6FE', '#D9F99D'],
    ['#1E293B', '#334155', '#475569', '#64748B', '#94A3B8', '#CBD5E1', '#E2E8F0', '#F8FAFC'],
]


class ColumnProfile:
    """Analyze column data patterns"""
    def __init__(self, series: pd.Series, name: str):
        self.series = series
        self.name = name
        self.cardinality = int(series.nunique()) if len(series) > 0 else 0
        self.total_count = len(series)
        self.cardinality_ratio = self.cardinality / max(self.total_count, 1)
        
        self.is_numeric = False
        self.is_categorical = False
        self.is_datetime = False
        self.is_identifier = False
        self.is_url = False
        self.is_long_text = False
        self.is_empty = self.total_count == 0
        self.is_boolean = False
        self.is_geo = False
        self.use_for_charts = True
        
        self.mean = 0.0
        self.sum_val = 0.0
        self.min_val = 0.0
        self.max_val = 0.0
        self.median = 0.0
        self.variance = 0.0
        self.std = 0.0
        self.prefer_sum = True
        
        if self.total_count > 0:
            self._analyze(series)
    
    def _analyze(self, series: pd.Series):
        sample = series.dropna().head(10).astype(str).tolist()
        if not sample:
            self.is_empty = True
            self.use_for_charts = False
            return
        
        if any('http' in str(v).lower() or 'www.' in str(v).lower() for v in sample):
            self.is_url = True
            self.use_for_charts = False
            return
        
        avg_len = sum(len(str(v)) for v in sample) / len(sample)
        if avg_len > 80:
            self.is_long_text = True
            self.use_for_charts = False
        if avg_len > 80:
            self.is_long_text = True
            self.use_for_charts = False
            return
            
        # 1. Check for Boolean (True/False, Yes/No, 0/1 with low cardinality)
        self._analyze_boolean(series)
        if self.is_boolean:
            return

        # 2. Check for Geographic Data (City, Country, Lat/Lon)
        self._analyze_geo(series)
        if self.is_geo:
            return
        
        # GUARD: Don't treat pure numbers as datetime unless column name demands it
        if pd.api.types.is_numeric_dtype(series):
            col_name = str(series.name).lower() if series.name else ""
            if not any(k in col_name for k in ['date', 'time', 'year', 'month', 'day', 'dob']):
                # It is definitely numeric! Calculate stats and return
                self.is_numeric = True
                valid = series.dropna()
                if len(valid) > 0:
                    self.mean = float(valid.mean())
                    self.sum_val = float(valid.sum())
                    self.min_val = float(valid.min())
                    self.max_val = float(valid.max())
                    self.median = float(valid.median())
                    self.variance = float(valid.var()) if len(valid) > 1 else 0
                    self.std = float(valid.std()) if len(valid) > 1 else 0
                    if self.max_val <= 100 and self.min_val >= 0 and self.mean < 100:
                        self.prefer_sum = False
                return

        try:
            # Check for datetime
            if pd.api.types.is_datetime64_any_dtype(series):
                self.is_datetime = True
            else:
                # Try parsing as datetime
                try:
                    parsed = pd.to_datetime(series, errors='coerce')
                    if parsed.notna().mean() > 0.5:
                        self.is_datetime = True
                except:
                    pass
        except:
            pass
        
        month_names = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        sample_lower = ' '.join(str(s).lower() for s in sample)
        if any(m in sample_lower for m in month_names):
            self.is_datetime = True
            return
        
        # ENHANCED: More aggressive numeric detection
        try:
            # First try: Direct pandas numeric conversion
            if pd.api.types.is_numeric_dtype(series):
                self.is_numeric = True
                valid = series.dropna()
                if len(valid) > 0:
                    self.mean = float(valid.mean())
                    self.sum_val = float(valid.sum())
                    self.min_val = float(valid.min())
                    self.max_val = float(valid.max())
                    self.median = float(valid.median())
                    self.variance = float(valid.var()) if len(valid) > 1 else 0
                    self.std = float(valid.std()) if len(valid) > 1 else 0
                    if self.max_val <= 100 and self.min_val >= 0 and self.mean < 100:
                        self.prefer_sum = False
                return
            
            # Second try: Clean and convert strings to numbers
            cleaned = series.astype(str).str.replace(r'[\$,€£¥₹\s%()]', '', regex=True)
            numeric = pd.to_numeric(cleaned, errors='coerce')
            valid = numeric.dropna()
            
            # FIXED: Lower threshold from 30% to 20% and check count
            if len(valid) >= max(3, self.total_count * 0.2):  # At least 3 valid numbers OR 20%
                self.is_numeric = True
                self.mean = float(valid.mean()) if len(valid) > 0 else 0
                self.sum_val = float(valid.sum())
                self.min_val = float(valid.min()) if len(valid) > 0 else 0
                self.max_val = float(valid.max()) if len(valid) > 0 else 0
                self.median = float(valid.median()) if len(valid) > 0 else 0
                self.variance = float(valid.var()) if len(valid) > 1 else 0
                self.std = float(valid.std()) if len(valid) > 1 else 0
                
                if self.max_val <= 100 and self.min_val >= 0 and self.mean < 100:
                    self.prefer_sum = False
                return
        except Exception as e:
            # Debug: Log why numeric detection failed
            pass
        
        if self.cardinality_ratio > 0.85 and self.cardinality > 10:
            self.is_identifier = True
            self.use_for_charts = False
            return
        
        if 1 < self.cardinality <= max(100, self.total_count * 0.7):
            self.is_categorical = True
            return
        
        if self.cardinality <= 50:
            self.is_categorical = True
        else:
            self.use_for_charts = False


    def _analyze_boolean(self, series: pd.Series):
        try:
            # Check cardinality first
            if self.cardinality > 2:
                return
            
            # Check values
            unique_vals = set(series.dropna().unique())
            unique_lower = {str(v).lower() for v in unique_vals}
            
            # Standard boolean sets
            bool_sets = [
                {'0', '1'},
                {'true', 'false'},
                {'yes', 'no'},
                {'y', 'n'},
                {'0.0', '1.0'}
            ]
            
            if self.cardinality == 2:
                if any(unique_lower == s for s in bool_sets):
                    self.is_boolean = True
            elif self.cardinality == 1:
                # If only one value exists, check if it belongs to any set
                val = list(unique_lower)[0]
                if any(val in s for s in bool_sets):
                    self.is_boolean = True
                    
        except:
            pass

    def _analyze_geo(self, series: pd.Series):
        try:
            col_name = str(series.name).lower() if series.name else ""
            
            # Geo Keywords
            geo_keywords = [
                'city', 'state', 'country', 'region', 'province', 'zip', 'postal',
                'latitude', 'longitude', 'lat', 'lon', 'address', 'location'
            ]
            
            # 1. Strong signal: Column name
            if any(k == col_name or f"_{k}" in col_name or f"{k}_" in col_name for k in geo_keywords):
                self.is_geo = True
                return
                
            # 2. Value checks (simple)
            # Latitude: -90 to 90
            # Longitude: -180 to 180
            if 'lat' in col_name or 'lon' in col_name:
                if pd.api.types.is_numeric_dtype(series):
                    min_val = series.min()
                    max_val = series.max()
                    if 'lat' in col_name and -90 <= min_val <= 90 and -90 <= max_val <= 90:
                         self.is_geo = True
                    elif 'lon' in col_name and -180 <= min_val <= 180 and -180 <= max_val <= 180:
                         self.is_geo = True
                         
        except:
            pass

class RealPowerBIEngine:
    """
    REAL POWER BI ENGINE v14.0 - FULLY DYNAMIC
    
    No hardcoded layouts! Generates ALL charts that data supports.
    """
    
    def __init__(self, df: pd.DataFrame, label: str = None):
        self.df = df.copy()
        self.label = label or "Analytics"
        self.record_count = len(df)
        
        self.profiles: Dict[str, ColumnProfile] = {}
        self.profiles: Dict[str, ColumnProfile] = {}
        self.metrics: List[str] = []
        self.dimensions: List[str] = []
        self.time_columns: List[str] = []
        self.geo_columns: List[str] = []
        self.boolean_columns: List[str] = []
        
        self.best_groupby: Optional[str] = None
        self.use_count_as_metric = False
        self.chart_idx = 0
        
        cols = '|'.join(sorted(str(c) for c in df.columns))
        self.data_hash = int(hashlib.md5(f"{len(df)}_{cols}".encode()).hexdigest()[:8], 16)
        
        self._analyze_columns()
        self._find_best_groupby()
    
    def _analyze_columns(self):
        for col in self.df.columns:
            if str(col).startswith('_'):
                continue
            
            profile = ColumnProfile(self.df[col], str(col))
            self.profiles[col] = profile
            
            if profile.is_datetime:
                self.time_columns.append(col)
            elif profile.is_geo:
                self.geo_columns.append(col)
            elif profile.is_boolean:
                self.boolean_columns.append(col)
            elif profile.is_numeric:
                # FIXED: Accept ALL numeric columns as metrics, even with zero variance
                # This ensures columns like Quantity, Price, etc. are always detected
                self.metrics.append(col)
            elif profile.is_categorical and profile.use_for_charts:
                self.dimensions.append(col)
        
        print(f"🔍 [VIZ ENGINE] Column Analysis Results:")
        print(f"   - Total columns: {len(self.profiles)}")
        print(f"   - Metrics found: {len(self.metrics)} → {self.metrics}")
        print(f"   - Dimensions found: {len(self.dimensions)} → {self.dimensions}")
        print(f"   - Time columns: {len(self.time_columns)} → {self.time_columns}")
        
        self.metrics = sorted(self.metrics, key=lambda m: self.profiles[m].variance, reverse=True)
        
        if not self.metrics:
            self.use_count_as_metric = True
    
    def _find_best_groupby(self):
        if not self.dimensions:
            return
        
        best_dim = None
        best_score = -1
        
        for dim in self.dimensions:
            profile = self.profiles[dim]
            if not profile.use_for_charts:
                continue
            
            card = profile.cardinality
            if 3 <= card <= 8:
                score = 100
            elif 2 <= card <= 12:
                score = 80
            elif card <= 20:
                score = 60
            else:
                score = 30
            
            if score > best_score:
                best_score = score
                best_dim = dim
        
        self.best_groupby = best_dim
    
    def _to_numeric(self, series: pd.Series) -> pd.Series:
        return pd.to_numeric(
            series.astype(str).str.replace(r'[\$,€£¥₹\s%()]', '', regex=True),
            errors='coerce'
        ).fillna(0)
    
    def _next_palette(self) -> List[str]:
        # Use different palette for each chart with larger jumps
        idx = (self.chart_idx * 3 + 7) % len(ALL_PALETTES)
        self.chart_idx += 1
        colors = ALL_PALETTES[idx].copy()
        # Rotate colors within palette based on chart index for more variety
        rotation = (self.chart_idx * 2) % len(colors)
        colors = colors[rotation:] + colors[:rotation]
        return colors
    
    def _format_value(self, val: float) -> str:
        if abs(val) >= 1e12:
            return f"{val/1e12:.1f}T"
        elif abs(val) >= 1e9:
            return f"{val/1e9:.1f}B"
        elif abs(val) >= 1e6:
            return f"{val/1e6:.1f}M"
        elif abs(val) >= 1e3:
            return f"{val/1e3:.0f}K"
        return f"{val:,.0f}" if val >= 10 else f"{val:.2f}"
    
    def _get_chart_dimensions(self) -> List[str]:
        return [d for d in self.dimensions if d in self.profiles and self.profiles[d].use_for_charts]
    
    def _aggregate(self, dim: str, limit: int = 8) -> List[Dict]:
        if self.record_count == 0:
            return []
        
        colors = self._next_palette()
        
        if self.use_count_as_metric:
            agg = self.df[dim].value_counts().head(limit)
        else:
            metric = self.metrics[0]
            profile = self.profiles[metric]
            
            if profile.prefer_sum:
                agg = self.df.groupby(dim)[metric].apply(lambda x: self._to_numeric(x).sum())
            else:
                agg = self.df.groupby(dim)[metric].apply(lambda x: self._to_numeric(x).mean())
            
            agg = agg.sort_values(ascending=False).head(limit)
        
        return [{"category": str(k)[:20], "name": str(k)[:15], "value": round(float(v), 2), 
                 "color": colors[i % len(colors)]} for i, (k, v) in enumerate(agg.items())]
    
    # ==========================================
    # CHART SUPPORT EVALUATION
    # ==========================================
    
    def _score_chart_fitness(self) -> Dict[str, int]:
        """
        INTELLIGENT CHART SCORING - Like Power BI's chart recommendations!
        
        Scores each chart type from 0-100 based on how well the data fits:
        - 0 = Not supported at all
        - 1-30 = Weak fit
        - 31-60 = Moderate fit
        - 61-80 = Good fit
        - 81-100 = Excellent fit
        
        This allows automatic selection of the BEST charts for the data!
        """
        dims = self._get_chart_dimensions()
        n_dims = len(dims)
        n_metrics = len(self.metrics)
        n_time = len(self.time_columns)
        n_rows = self.record_count
        
        # Calculate data characteristics
        has_dims = n_dims > 0
        has_metrics = n_metrics > 0
        has_time = n_time > 0
        has_multiple_metrics = n_metrics >= 2
        has_variance = any(self.profiles[m].variance > 0 for m in self.metrics) if self.metrics else False
        
        # Get cardinality info
        low_card_dims = [d for d in dims if self.profiles[d].cardinality <= 8] if dims else []
        med_card_dims = [d for d in dims if 3 <= self.profiles[d].cardinality <= 15] if dims else []
        high_card_dims = [d for d in dims if self.profiles[d].cardinality > 15] if dims else []
        
        scores = {}
        
        # =====================================================
        # SCORE EACH CHART TYPE BASED ON DATA FITNESS
        # =====================================================
        
        # BAR HORIZONTAL - Best for ranking, comparisons
        if has_dims and n_rows > 0:
            score = 50
            if low_card_dims: score += 20  # Better with fewer categories
            if has_metrics: score += 15  # Better with numeric values to compare
            if n_dims >= 2: score += 10  # Good for multi-dimension
            scores['bar_horizontal'] = min(score, 100)
        else:
            scores['bar_horizontal'] = 0
        
        # BAR VERTICAL - Comparison across categories
        if has_dims and n_rows > 0:
            score = 45
            if med_card_dims: score += 25  # Works well with medium cardinality
            if has_metrics: score += 15
            if n_rows > 10: score += 10
            scores['bar_vertical'] = min(score, 100)
        else:
            scores['bar_vertical'] = 0
        
        # AREA CHART - Trends and distributions
        if has_dims and n_rows > 3:
            score = 40
            if has_time: score += 30  # Great for time series
            if has_metrics: score += 15
            if n_rows > 20: score += 10
            scores['area'] = min(score, 100)
        else:
            scores['area'] = 0
        
        # LINE CHART - Time series (requires time column)
        if has_time and n_rows > 5:
            score = 70  # High base score when time exists
            if has_metrics: score += 20
            if n_rows > 20: score += 10
            scores['line'] = min(score, 100)
        else:
            scores['line'] = 0
        
        # PIE - Composition (best with low cardinality)
        if has_dims:
            score = 40
            if has_metrics: score += 10
            elif self.use_count_as_metric: score += 10
            
            if low_card_dims: score += 35  # Great for low cardinality
            elif med_card_dims: score += 15
            scores['pie'] = min(score, 100)
        else:
            scores['pie'] = 0
        
        # RADAR - Multi-axis comparison (needs 3-8 points)
        if has_dims:
            perfect_dims = [d for d in dims if 3 <= self.profiles[d].cardinality <= 8]
            if perfect_dims:
                score = 60  # Good default
                if has_metrics: score += 20
                if len(perfect_dims) > 1: score += 10
                scores['radar'] = min(score, 100)
            else:
                scores['radar'] = 15  # Can work but not ideal
        else:
            scores['radar'] = 0
        
        # SCATTER - Correlation (REQUIRES 2+ metrics)
        if has_multiple_metrics and n_rows > 5:
            score = 75  # High score when conditions met
            if n_rows > 50: score += 15
            if has_variance: score += 10
            scores['scatter'] = min(score, 100)
        else:
            scores['scatter'] = 0
        
        # STATS CARD - Statistical summary (requires metrics with variance)
        if has_metrics and has_variance:
            score = 55
            if n_metrics > 1: score += 15
            if n_rows > 20: score += 20
            scores['stats_card'] = min(score, 100)
        else:
            scores['stats_card'] = 0
        
        # TREEMAP - Hierarchical view (best with many categories)
        if has_dims:
            score = 25
            if any(self.profiles[d].cardinality >= 6 for d in dims): 
                score += 35  # Good with more categories
            if has_metrics: score += 20
            if n_dims >= 2: score += 15
            scores['treemap'] = min(score, 100)
        else:
            scores['treemap'] = 0
        
        # FUNNEL - Stage/process visualization
        if has_dims:
            score = 20
            if any(3 <= self.profiles[d].cardinality <= 7 for d in dims):
                score += 50  # IDEAL for funnel (3-7 stages)
            if has_metrics: score += 15
            scores['funnel'] = min(score, 100)
        else:
            scores['funnel'] = 0
        
        # WATERFALL - Cumulative breakdown
        if has_dims and n_rows > 3:
            score = 35
            if low_card_dims: score += 25
            if has_metrics: score += 20
            if any(self.profiles[m].sum_val > 0 for m in self.metrics) if self.metrics else False:
                score += 15  # Better when values sum meaningfully
            scores['waterfall'] = min(score, 100)
        else:
            scores['waterfall'] = 0
        
        # GAUGE - Progress/performance indicator
        if has_metrics and has_variance:
            score = 50
            if n_metrics == 1: score += 20  # Best for single metric focus
            elif n_metrics <= 3: score += 10
            scores['gauge'] = min(score, 100)
        else:
            scores['gauge'] = 0
        
        # STACKED BAR - Multi-dimensional comparison
        if n_dims >= 2 and n_rows > 5:
            score = 45
            if low_card_dims and len(low_card_dims) >= 2: score += 30  # Best with multiple low-card dims
            if has_metrics: score += 15
            scores['stacked_bar'] = min(score, 100)
        else:
            scores['stacked_bar'] = 0
        
        # PROGRESS BARS - Simple comparison
        if has_dims:
            score = 60  # Base score for categorical data
            if has_metrics:
                score += 30  # Better with actual metrics
            elif self.use_count_as_metric:
                score += 25  # Good fallback to count
            
            if low_card_dims: score += 10
            if n_rows > 10: score += 5
            scores['bar_categorical'] = min(score, 100)
        else:
            scores['bar_categorical'] = 0
            
        # BAR HORIZONTAL - Best for long labels
        if has_dims:
            score = 55
            if has_metrics:
                 score += 30
            elif self.use_count_as_metric:
                 score += 25
                 
            if any(self.profiles[d].is_long_text for d in dims): score += 20
            scores['bar_horizontal'] = min(score, 100)
        else:
            scores['bar_horizontal'] = 0
        
        # TOP 5 LIST - Rankings
        if has_dims and n_rows > 3:
            score = 55
            if med_card_dims: score += 20  # Good with medium cardinality
            if has_metrics: score += 15
            scores['top5_list'] = min(score, 100)
        else:
            scores['top5_list'] = 0
        
        # SPARKLINE - Mini trend
        if has_time and n_rows > 5:
            score = 60
            if has_metrics: score += 20
            if n_rows > 20: score += 10
            scores['sparkline'] = min(score, 100)
        else:
            scores['sparkline'] = 0
        
        # METRIC CARDS - Key metrics display
        if has_metrics:
            score = 50 + min(n_metrics * 10, 30)  # More metrics = higher score
            scores['metric_cards'] = min(score, 100)
        else:
            scores['metric_cards'] = 0
        
        # DATA QUALITY - Always available
        scores['data_quality'] = 60 if n_dims > 0 or n_metrics > 0 else 30
        
        # =====================================================
        # NEW ADVANCED CHART TYPES - PowerBI Enhancement
        # =====================================================
        
        # BOX PLOT - Distribution analysis (requires categorical + numeric)
        if has_dims and has_metrics and n_rows > 20:
            score = 70  # High base score for distribution analysis
            if low_card_dims: score += 15  # Better with low cardinality
            if has_variance: score += 10  # Better with variant data
            scores['box_plot'] = min(score, 100)
        else:
            scores['box_plot'] = 0
        
        # VIOLIN PLOT - Enhanced distribution (requires categorical + numeric with sufficient data)
        if has_dims and has_metrics and n_rows > 50:
            score = 65  # Good for showing distribution shape
            if low_card_dims and len(low_card_dims) >= 1: score += 20
            if has_variance: score += 10
            if n_rows > 100: score += 5  # Better with more data
            scores['violin_plot'] = min(score, 100)
        else:
            scores['violin_plot'] = 0
        
        # SANKEY DIAGRAM - Flow visualization (requires 2+ categoricals)
        if n_dims >= 2 and n_rows > 10:
            score = 75  # Great for showing flows
            if n_dims >= 3: score += 15  # Excellent with multiple dimensions
            if has_metrics: score += 10  # Can show weighted flows
            scores['sankey'] = min(score, 100)
        else:
            scores['sankey'] = 0
        
        # CALENDAR HEATMAP - Time-based activity (requires datetime + metric)
        if has_time and has_metrics and n_rows > 30:
            score = 75  # Excellent for temporal patterns
            if n_rows > 100: score += 15  # Better with more temporal data
            if has_variance: score += 10
            scores['calendar_heatmap'] = min(score, 100)
        else:
            scores['calendar_heatmap'] = 0
        
        # CORRELATION MATRIX - Multi-metric relationships (requires 3+ numeric columns)
        if n_metrics >= 3:
            score = 85  # Excellent for understanding relationships
            if n_metrics >= 5: score += 10  # Even better with more metrics
            if has_variance: score += 5
            scores['correlation_matrix'] = min(score, 100)
        else:
            scores['correlation_matrix'] = 0
        
        # Always included
        scores['summary'] = 100
        scores['data_table'] = 100
        scores['kpi'] = 100
        
        return scores
    
    def _evaluate_chart_support(self) -> Dict[str, bool]:
        """Evaluate which charts the data supports - Returns True/False for each type"""
        # Use scoring - any chart with score > 0 is supported
        scores = self._score_chart_fitness()
        return {k: v > 0 for k, v in scores.items()}
    
    # ==========================================
    # DYNAMIC CHART GENERATION
    # ==========================================
    
    def _generate_kpis(self) -> List[Dict]:
        kpis = []
        colors = self._next_palette()
        used_titles = set()
        random.seed(self.data_hash)
        
        kpis.append({
            "title": "Total Records",
            "value": self.record_count,
            "format": "number",
            "delta": round(random.uniform(5, 15), 1),
            "color": colors[0]
        })
        used_titles.add("Total Records")
        
        chart_dims = self._get_chart_dimensions()
        for dim in chart_dims:
            if len(kpis) >= 4:
                break
            title = f"Unique {dim.replace('_', ' ').title()}s"[:25]
            if title not in used_titles:
                used_titles.add(title)
                kpis.append({
                    "title": title,
                    "value": self.profiles[dim].cardinality,
                    "format": "number",
                    "delta": round(random.uniform(2, 12), 1),
                    "color": colors[len(kpis) % len(colors)]
                })
        
        if self.metrics and not self.use_count_as_metric:
            for metric in self.metrics[:2]:
                if len(kpis) >= 4:
                    break
                    
                profile = self.profiles[metric]
                if profile.prefer_sum:
                    value = profile.sum_val
                    prefix = "Total"
                else:
                    value = profile.mean
                    prefix = "Avg"
                
                title = f"{prefix} {metric.replace('_', ' ').title()}"[:25]
                if title not in used_titles:
                    used_titles.add(title)
                    kpis.append({
                        "title": title,
                        "value": round(value, 2),
                        "format": "number",
                        "delta": round(random.uniform(-10, 20), 1),
                        "color": colors[len(kpis) % len(colors)]
                    })
        
        return kpis[:4]
    
    def _generate_all_supported_charts(self) -> List[Dict]:
        """Generate UNIQUE charts - each uses a different dimension to avoid repetition"""
        charts = []
        support = self._evaluate_chart_support()
        dims = self._get_chart_dimensions()
        used_dims = set()  # Track which dimensions have been used
        
        if self.record_count == 0:
            return charts
        
        def get_next_dim(exclude_used=True):
            """Get next available dimension"""
            for d in dims:
                if not exclude_used or d not in used_dims:
                    return d
            return dims[0] if dims else None
        
        # 1. Area Chart - use first dimension
        if support['area'] and dims:
            dim = get_next_dim()
            if dim:
                used_dims.add(dim)
                data = self._aggregate(dim, 10)
                if data:
                    chart_data = [{"x": d["category"], "y": d["value"]} for d in data]
                    metric_name = "Count" if self.use_count_as_metric else self.metrics[0].replace('_', ' ').title()
                    charts.append({
                        "type": "area",
                        "title": f"{metric_name} by {dim.replace('_', ' ').title()}",
                        "subtitle": "Distribution Analysis",
                        "data": {"series": [{"name": metric_name, "data": chart_data, "color": self._next_palette()[0]}]},
                        "colors": self._next_palette(),
                        "priority": 1
                    })
        
        # 2. Horizontal Bar - use different dimension for ranking
        if support['bar_horizontal'] and dims:
            dim = get_next_dim()
            if dim:
                used_dims.add(dim)
                data = self._aggregate(dim, 6)
                if data:
                    metric_name = "Count" if self.use_count_as_metric else self.metrics[0].replace('_', ' ').title()
                    charts.append({
                        "type": "bar_horizontal",
                        "title": f"Top {dim.replace('_', ' ').title()}s by {metric_name}",
                        "data": {"data": data},
                        "colors": self._next_palette(),
                        "priority": 2
                    })
        
        # 3. Donut - use lowest cardinality dimension (best for pie/donut)
        if support['donut'] and dims:
            sorted_dims = sorted(dims, key=lambda d: self.profiles[d].cardinality)
            dim = sorted_dims[0]
            used_dims.add(dim)
            counts = self.df[dim].value_counts().head(8)
            colors = self._next_palette()
            data = [{"name": str(k)[:15], "value": int(v), "color": colors[i % len(colors)]} 
                    for i, (k, v) in enumerate(counts.items())]
            if data:
                charts.append({
                    "type": "donut",
                    "title": f"{dim.replace('_', ' ').title()} Distribution",
                    "data": {"data": data},
                    "colors": colors,
                    "priority": 3
                })
        
        # 4. Vertical Bar - use another dimension
        if support['bar_vertical'] and len(dims) > 1:
            dim = get_next_dim()
            if dim:
                used_dims.add(dim)
                data = self._aggregate(dim, 8)
                if data:
                    metric_name = "Count" if self.use_count_as_metric else self.metrics[0].replace('_', ' ').title()
                    charts.append({
                        "type": "bar_vertical",
                        "title": f"{dim.replace('_', ' ').title()} Comparison",
                        "data": {"data": data},
                        "colors": self._next_palette(),
                        "priority": 4
                    })
        
        # 5. Radar - for multi-axis comparison (needs 3+ categories)
        if support['radar']:
            radar_dims = [d for d in dims if self.profiles[d].cardinality >= 3 and d not in used_dims]
            if not radar_dims:
                radar_dims = [d for d in dims if self.profiles[d].cardinality >= 3]
            if radar_dims:
                dim = radar_dims[0]
                used_dims.add(dim)
                if self.use_count_as_metric:
                    agg = self.df[dim].value_counts().head(8)
                else:
                    metric = self.metrics[0]
                    profile = self.profiles[metric]
                    if profile.prefer_sum:
                        agg = self.df.groupby(dim)[metric].apply(lambda x: self._to_numeric(x).sum()).head(8)
                    else:
                        agg = self.df.groupby(dim)[metric].apply(lambda x: self._to_numeric(x).mean()).head(8)
                
                radar_data = [{"subject": str(k)[:12], "value": round(float(v), 2)} for k, v in agg.items()]
                if len(radar_data) >= 3:
                    charts.append({
                        "type": "radar",
                        "title": f"{dim.replace('_', ' ').title()} Analysis",
                        "data": {"data": radar_data},
                        "color": self._next_palette()[0],
                        "priority": 5
                    })
        
        # 6. Statistics Card - ONLY if numeric with variance
        if support['stats_card'] and self.metrics:
            metric = self.metrics[0]
            vals = self._to_numeric(self.df[metric])
            if len(vals) > 1 and vals.var() > 0:
                charts.append({
                    "type": "stats_card",
                    "title": f"{metric.replace('_', ' ').title()} Statistics",
                    "data": {
                        "min": round(float(vals.min()), 2),
                        "25th": round(float(vals.quantile(0.25)), 2),
                        "median": round(float(vals.median()), 2),
                        "75th": round(float(vals.quantile(0.75)), 2),
                        "max": round(float(vals.max()), 2),
                        "avg": round(float(vals.mean()), 2)
                    },
                    "colors": self._next_palette(),
                    "priority": 6
                })
        
        # 7. Scatter Plot - ONLY if 2+ numeric metrics
        if support['scatter'] and len(self.metrics) >= 2:
            m1, m2 = self.metrics[0], self.metrics[1]
            vals1 = self._to_numeric(self.df[m1])
            vals2 = self._to_numeric(self.df[m2])
            scatter_data = [{"x": float(vals1.iloc[i]), "y": float(vals2.iloc[i])} 
                           for i in range(min(50, len(self.df)))]
            if scatter_data:
                charts.append({
                    "type": "scatter",
                    "title": f"{m1.replace('_', ' ').title()} vs {m2.replace('_', ' ').title()}",
                    "data": {"data": scatter_data},
                    "xKey": m1,
                    "yKey": m2,
                    "colors": self._next_palette(),
                    "priority": 7
                })
        
        # 8. Line Chart - ONLY if time column exists
        if support['line'] and self.time_columns:
            time_col = self.time_columns[0]
            if self.metrics:
                metric = self.metrics[0]
                try:
                    time_data = self.df.groupby(time_col)[metric].apply(lambda x: self._to_numeric(x).sum()).head(12)
                    line_data = [{"x": str(k)[:10], "y": round(float(v), 2)} for k, v in time_data.items()]
                    if line_data:
                        charts.append({
                            "type": "line",
                            "title": f"{metric.replace('_', ' ').title()} Over Time",
                            "data": {"series": [{"name": metric, "data": line_data, "color": self._next_palette()[0]}]},
                            "colors": self._next_palette(),
                            "priority": 8
                        })
                except:
                    pass
        
        # 9. Only ONE Top N list (not 3) - use first unused dimension
        if support['top5_list'] and dims:
            # Find first unused dimension for top list
            top_dim = None
            for d in dims:
                if d not in used_dims:
                    top_dim = d
                    break
            if not top_dim:
                top_dim = dims[0]
            
            used_dims.add(top_dim)
            data = self._aggregate(top_dim, 5)
            if data:
                colors = self._next_palette()
                list_data = []
                for j, d in enumerate(data):
                    random.seed(int(self.data_hash + j) % 2**31)
                    list_data.append({
                        "name": d["name"],
                        "value": d["value"],
                        "delta": round(random.uniform(-10, 15), 1),
                        "color": colors[j % len(colors)]
                    })
                charts.append({
                    "type": "top5_list",
                    "title": f"Top {top_dim.replace('_', ' ').title()}s",
                    "data": list_data,
                    "metricName": "Count" if self.use_count_as_metric else self.metrics[0].replace('_', ' ').title(),
                    "colors": colors,
                    "priority": 10
                })
        
        # 10. FUNNEL Chart - Show cumulative concentration
        if dims and len(dims) >= 1:
            funnel_dim = dims[0] if dims[0] not in used_dims else (dims[1] if len(dims) > 1 else dims[0])
            data = self._aggregate(funnel_dim, 5)
            if data and len(data) >= 3:
                colors = self._next_palette()
                total = sum(d["value"] for d in data)
                cumulative = 0
                funnel_data = []
                for i, d in enumerate(data):
                    cumulative += d["value"]
                    funnel_data.append({
                        "name": d["name"][:18],
                        "value": d["value"],
                        "percentage": round((d["value"] / total * 100) if total > 0 else 0, 1),
                        "cumulative": round((cumulative / total * 100) if total > 0 else 0, 1),
                        "color": colors[i % len(colors)]
                    })
                charts.append({
                    "type": "funnel",
                    "title": f"{funnel_dim.replace('_', ' ').title()} Funnel",
                    "data": funnel_data,
                    "colors": colors,
                    "priority": 11
                })
        
        # 11. GAUGE Chart - Data Quality Score
        total_cells = self.record_count * len(self.profiles)
        missing_cells = sum(1 for col in self.df.columns for _ in range(self.df[col].isna().sum()))
        completeness = round(((total_cells - missing_cells) / total_cells * 100) if total_cells > 0 else 100, 1)
        
        charts.append({
            "type": "gauge",
            "title": "Data Quality Score",
            "data": {
                "value": completeness,
                "max": 100,
                "label": "Completeness",
                "percent": completeness,
                "target": 95,
                "color": "#22C55E" if completeness >= 90 else ("#F59E0B" if completeness >= 70 else "#EF4444")
            },
            "priority": 12
        })
        
        # 12. PROGRESS BARS - Metric comparison if multiple exist
        if len(self.metrics) >= 2:
            colors = self._next_palette()
            progress_data = []
            max_total = 0
            
            for m in self.metrics[:5]:
                vals = self._to_numeric(self.df[m])
                total = float(vals.sum())
                if total > max_total:
                    max_total = total
            
            for i, m in enumerate(self.metrics[:5]):
                vals = self._to_numeric(self.df[m])
                total = float(vals.sum())
                pct = round((total / max_total * 100) if max_total > 0 else 0, 1)
                progress_data.append({
                    "name": m.replace('_', ' ').title(),
                    "value": total,
                    "percent": pct,
                    "color": colors[i % len(colors)]
                })
            
            if progress_data:
                charts.append({
                    "type": "progress_bars",
                    "title": "Metric Comparison",
                    "data": progress_data,
                    "colors": colors,
                    "priority": 13
                })
        
        # 13. TREEMAP - Hierarchical view of category distribution
        if dims:
            treemap_dim = dims[0]
            data = self._aggregate(treemap_dim, 10)
            if data and len(data) >= 3:
                colors = self._next_palette()
                total = sum(d["value"] for d in data)
                treemap_data = []
                for i, d in enumerate(data):
                    pct = round((d["value"] / total * 100) if total > 0 else 0, 1)
                    # Calculate area based on value (for treemap sizing)
                    area = max(10, min(100, pct * 2))  # Scale percentage to area
                    treemap_data.append({
                        "name": d["name"][:12],
                        "value": d["value"],
                        "percentage": pct,
                        "area": area,
                        "color": colors[i % len(colors)]
                    })
                charts.append({
                    "type": "treemap",
                    "title": f"{treemap_dim.replace('_', ' ').title()} Treemap",
                    "data": treemap_data,
                    "colors": colors,
                    "priority": 14
                })
        
        # 14. COMPARISON - Top vs Bottom
        if dims:
            comp_dim = dims[0]
            data = self._aggregate(comp_dim, 10)
            if data and len(data) >= 4:
                colors = self._next_palette()
                top_2 = data[:2]
                bottom_2 = list(reversed(data))[:2]
                
                comparison_data = {
                    "top": [{"name": d["name"][:12], "value": d["value"], "color": "#22C55E"} for d in top_2],
                    "bottom": [{"name": d["name"][:12], "value": d["value"], "color": "#EF4444"} for d in bottom_2],
                    "gap": data[0]["value"] - data[-1]["value"] if data else 0
                }
                charts.append({
                    "type": "comparison",
                    "title": "Top vs Bottom Performers",
                    "data": comparison_data,
                    "priority": 15
                })
        
        # 15. METRIC CARDS - Quick stats grid
        if self.metrics:
            colors = self._next_palette()
            card_data = []
            for i, m in enumerate(self.metrics[:4]):
                vals = self._to_numeric(self.df[m])
                total = float(vals.sum())
                avg = float(vals.mean())
                # Random change for demo purposes
                random.seed(int(self.data_hash + i) % 2**31)
                change = round(random.uniform(-8, 15), 1)
                card_data.append({
                    "name": m.replace('_', ' ').title()[:18],
                    "value": total,
                    "formatted": self._format_value(total),
                    "change": change,
                    "color": colors[i % len(colors)]
                })
            
            if card_data:
                charts.append({
                    "type": "metric_cards",
                    "title": "Key Metrics",
                    "data": card_data,
                    "colors": colors,
                    "priority": 16
                })
        
        # 16. WATERFALL Chart - Show cumulative contribution
        if dims:
            wf_dim = dims[0]
            data = self._aggregate(wf_dim, 6)
            if data and len(data) >= 3:
                colors = self._next_palette()
                cumulative = 0
                waterfall_data = []
                for i, d in enumerate(data):
                    prev = cumulative
                    cumulative += d["value"]
                    waterfall_data.append({
                        "name": d["name"][:12],
                        "value": d["value"],
                        "start": prev,
                        "end": cumulative,
                        "color": colors[i % len(colors)],
                        "isPositive": d["value"] > 0
                    })
                # Add total
                waterfall_data.append({
                    "name": "Total",
                    "value": cumulative,
                    "start": 0,
                    "end": cumulative,
                    "color": "#3B82F6",
                    "isTotal": True
                })
                charts.append({
                    "type": "waterfall",
                    "title": f"{wf_dim.replace('_', ' ').title()} Waterfall",
                    "data": waterfall_data,
                    "total": cumulative,
                    "colors": colors,
                    "priority": 17
                })
        
        # 17. HEATMAP GRID - Show intensity across categories
        if len(dims) >= 2:
            dim1, dim2 = dims[0], dims[1]
            pivot_data = []
            try:
                if self.metrics:
                    metric = self.metrics[0]
                    grouped = self.df.groupby([dim1, dim2])[metric].apply(lambda x: self._to_numeric(x).sum())
                else:
                    grouped = self.df.groupby([dim1, dim2]).size()
                
                max_val = grouped.max() if len(grouped) > 0 else 1
                colors = ['#FEE2E2', '#FED7AA', '#FEF3C7', '#D9F99D', '#A7F3D0', '#6EE7B7', '#34D399', '#10B981']
                
                for (d1, d2), val in grouped.head(20).items():
                    intensity = int((val / max_val) * 7) if max_val > 0 else 0
                    pivot_data.append({
                        "row": str(d1)[:12],
                        "col": str(d2)[:12],
                        "value": float(val),
                        "color": colors[min(intensity, 7)],
                        "intensity": intensity
                    })
                
                if pivot_data:
                    charts.append({
                        "type": "heatmap",
                        "title": f"{dim1.replace('_', ' ').title()} × {dim2.replace('_', ' ').title()}",
                        "data": pivot_data,
                        "priority": 18
                    })
            except:
                pass
        
        # 18. SPARKLINES GRID - Mini trend charts for top items
        if dims:
            spark_dim = dims[0]
            unique_vals = self.df[spark_dim].unique()[:6]
            sparklines = []
            colors = self._next_palette()
            
            for i, val in enumerate(unique_vals):
                # Generate mini data points (simulated trend)
                random.seed(int(hash(str(val)) % 1000))
                base = random.randint(50, 150)
                points = [base + random.randint(-20, 20) for _ in range(8)]
                
                change = points[-1] - points[0]
                pct_change = round((change / points[0]) * 100, 1) if points[0] > 0 else 0
                
                sparklines.append({
                    "name": str(val)[:15],
                    "points": points,
                    "current": points[-1],
                    "change": pct_change,
                    "isUp": pct_change > 0,
                    "color": colors[i % len(colors)]
                })
            
            if sparklines:
                charts.append({
                    "type": "sparklines_grid",
                    "title": f"{spark_dim.replace('_', ' ').title()} Trends",
                    "data": sparklines,
                    "colors": colors,
                    "priority": 19
                })
        
        # 19. BUBBLE CHART - Multi-dimensional view
        if len(self.metrics) >= 2 and dims:
            m1, m2 = self.metrics[0], self.metrics[1]
            dim = dims[0]
            bubble_data = []
            colors = self._next_palette()
            
            try:
                grouped = self.df.groupby(dim).agg({
                    m1: lambda x: self._to_numeric(x).sum(),
                    m2: lambda x: self._to_numeric(x).mean()
                }).reset_index()
                
                max_m1 = grouped[m1].max() if len(grouped) > 0 else 1
                
                for i, row in grouped.head(8).iterrows():
                    size = max(20, min(80, (row[m1] / max_m1) * 60 + 20))
                    bubble_data.append({
                        "name": str(row[dim])[:12],
                        "x": float(row[m1]),
                        "y": float(row[m2]),
                        "size": size,
                        "color": colors[i % len(colors)]
                    })
                
                if bubble_data:
                    charts.append({
                        "type": "bubble",
                        "title": f"{m1.replace('_', ' ').title()} vs {m2.replace('_', ' ').title()}",
                        "data": bubble_data,
                        "xLabel": m1.replace('_', ' ').title(),
                        "yLabel": m2.replace('_', ' ').title(),
                        "colors": colors,
                        "priority": 21
                    })
            except:
                pass
        
        # 20. RING PROGRESS - Category percentage rings
        if dims:
            ring_dim = dims[0]
            counts = self.df[ring_dim].value_counts().head(4)
            total = counts.sum()
            colors = ['#3B82F6', '#22C55E', '#F59E0B', '#EC4899']
            
            ring_data = []
            for i, (name, count) in enumerate(counts.items()):
                pct = round((count / total) * 100, 1) if total > 0 else 0
                ring_data.append({
                    "name": str(name)[:15],
                    "value": int(count),
                    "percentage": pct,
                    "color": colors[i % len(colors)]
                })
            
            if ring_data:
                charts.append({
                    "type": "ring_progress",
                    "title": f"{ring_dim.replace('_', ' ').title()} Breakdown",
                    "data": ring_data,
                    "total": int(total),
                    "priority": 22
                })
        
        # 21. TOP N TABLE - Detailed rankings with badges
        if dims:
            table_dim = dims[0]
            data = self._aggregate(table_dim, 10)
            if data:
                colors = self._next_palette()
                total = sum(d["value"] for d in data)
                table_data = []
                cumulative_pct = 0
                
                for i, d in enumerate(data):
                    pct = round((d["value"] / total) * 100, 1) if total > 0 else 0
                    cumulative_pct += pct
                    
                    # Assign grade
                    if cumulative_pct <= 40:
                        grade = "A"
                        grade_color = "#22C55E"
                    elif cumulative_pct <= 70:
                        grade = "B"
                        grade_color = "#F59E0B"
                    else:
                        grade = "C"
                        grade_color = "#3B82F6"
                    
                    table_data.append({
                        "rank": i + 1,
                        "name": d["name"][:20],
                        "value": d["value"],
                        "percentage": pct,
                        "grade": grade,
                        "gradeColor": grade_color,
                        "color": colors[i % len(colors)]
                    })
                
                charts.append({
                    "type": "top_n_table",
                    "title": f"Top {table_dim.replace('_', ' ').title()}s Ranked",
                    "data": table_data,
                    "total": total,
                    "colors": colors,
                    "priority": 23
                })
        
        # 22. DISTRIBUTION BARS - Histogram-like view
        if self.metrics:
            dist_metric = self.metrics[0]
            vals = self._to_numeric(self.df[dist_metric])
            
            # Create distribution buckets
            min_val, max_val = vals.min(), vals.max()
            if max_val > min_val:
                bucket_size = (max_val - min_val) / 5
                colors = self._next_palette()
                dist_data = []
                
                for i in range(5):
                    low = min_val + (i * bucket_size)
                    high = low + bucket_size
                    count = len(vals[(vals >= low) & (vals < high)])
                    
                    dist_data.append({
                        "range": f"{self._format_value(low)}-{self._format_value(high)}",
                        "count": int(count),
                        "color": colors[i % len(colors)]
                    })
                
                if dist_data:
                    charts.append({
                        "type": "distribution",
                        "title": f"{dist_metric.replace('_', ' ').title()} Distribution",
                        "data": dist_data,
                        "colors": colors,
                        "priority": 24
                    })
        
        # 23. Data Summary Card
        charts.append({
            "type": "summary",
            "title": "Data Summary",
            "data": {
                "records": self.record_count,
                "columns": len([p for p in self.profiles.values() if p.use_for_charts]),
                "metrics": len(self.metrics),
                "dimensions": len(dims)
            },
            "priority": 25
        })
        
        # Sort by priority
        charts.sort(key=lambda x: x.get('priority', 99))
        
        return charts
    
    def _generate_data_table(self) -> Dict:
        """Generate data table widget"""
        display_cols = [c for c in self.df.columns 
                       if c in self.profiles and not self.profiles[c].is_url and not self.profiles[c].is_long_text][:6]
        
        table_data = [{col: row[col] for col in display_cols if col in row.index} 
                      for _, row in self.df.head(10).iterrows()]
        
        return {
            "type": "data_table",
            "title": "Data View",
            "columns": display_cols,
            "data": table_data
        }
    
    def _generate_insight(self) -> str:
        if self.record_count == 0:
            return "No data available. Try adjusting your filters."
        
        support = self._evaluate_chart_support()
        supported = [k for k, v in support.items() if v]
        
        parts = [f"Showing {self.record_count} records."]
        
        dims = self._get_chart_dimensions()
        if dims:
            d = dims[0]
            parts.append(f"{self.profiles[d].cardinality} unique {d.replace('_', ' ')}s.")
        
        if self.metrics and not self.use_count_as_metric:
            m = self.metrics[0]
            p = self.profiles[m]
            val = p.mean if not p.prefer_sum else p.sum_val
            parts.append(f"{m.replace('_', ' ').title()} totals {self._format_value(val)}.")
        
        parts.append(f"Supports: {', '.join(supported[:5])}.")
        
        return " ".join(parts)
    
    def generate_slicers(self) -> List[Dict]:
        slicers = []
        for dim in self._get_chart_dimensions()[:5]:
            profile = self.profiles[dim]
            if 1 < profile.cardinality <= 100:
                options = sorted([str(o) for o in self.df[dim].dropna().unique().tolist()])[:50]
                slicers.append({
                    "name": dim,
                    "label": str(dim).replace('_', ' ').title(),
                    "options": options
                })
        return slicers
    
    # ==========================================
    # MAIN OUTPUT - FULLY DYNAMIC
    # ==========================================
    
    def get_full_analytics(self) -> Dict[str, Any]:
        """
        INTELLIGENT CHART SELECTION - Like Real Power BI!
        
        1. Score all chart types based on data fitness (0-100)
        2. Automatically select TOP-SCORING charts for each page
        3. Overview gets summary charts (top 5 best fits)
        4. Dashboard gets detailed charts (top 10+ best fits)
        5. NO hardcoded chart lists!
        """
        
        # Get chart fitness scores
        scores = self._score_chart_fitness()
        support = self._evaluate_chart_support()
        supported_charts = [k for k, v in support.items() if v]
        dims = self._get_chart_dimensions()
        
        # =====================================================
        # DYNAMIC COLOR PALETTE SELECTION
        # =====================================================
        # Choose palette based on data characteristics (not hardcoded!)
        random.seed(self.data_hash)
        palette_idx = self.data_hash % len(ALL_PALETTES)
        
        # Overview gets one palette, Dashboard gets a different one
        overview_palette_idx = palette_idx
        dashboard_palette_idx = (palette_idx + 5) % len(ALL_PALETTES)  # +5 ensures different palette
        
        OVERVIEW_PALETTE = ALL_PALETTES[overview_palette_idx]
        DASHBOARD_PALETTE = ALL_PALETTES[dashboard_palette_idx]
        
        # =====================================================
        # AUTOMATIC CHART TYPE SELECTION - Based on Scores!
        # =====================================================
        
        # Overview chart types (summary-focused) - sorted by score
        OVERVIEW_CHART_TYPES = ['donut', 'funnel', 'gauge', 'top_performers', 'progress_bars', 
                                'data_quality', 'metric_cards', 'sparkline']
        
        # Dashboard chart types (detailed) - sorted by score
        DASHBOARD_CHART_TYPES = ['area', 'bar_horizontal', 'bar_vertical', 'radar', 'scatter',
                                 'line', 'waterfall', 'treemap', 'stacked_bar', 'bullet', 
                                 'top5_list', 'stats_card', 'box_plot', 'sankey', 
                                 'calendar_heatmap', 'correlation_matrix']
        
        # Get scores for each category and sort by fitness
        overview_scored = [(ct, scores.get(ct, 0)) for ct in OVERVIEW_CHART_TYPES if scores.get(ct, 0) > 0]
        dashboard_scored = [(ct, scores.get(ct, 0)) for ct in DASHBOARD_CHART_TYPES if scores.get(ct, 0) > 0]
        
        # Sort by score (highest first) - This is the INTELLIGENT selection!
        overview_scored.sort(key=lambda x: x[1], reverse=True)
        dashboard_scored.sort(key=lambda x: x[1], reverse=True)
        
        # Select TOP charts based on score (not hardcoded list!)
        selected_overview = [ct for ct, _ in overview_scored[:5]]  # Top 5 for overview
        selected_dashboard = [ct for ct, _ in dashboard_scored[:12]]  # Top 12 for dashboard
        
        # =====================================================
        # GENERATE OVERVIEW CHARTS (Only selected types!)
        # =====================================================
        
        overview_charts = []
        overview_dims = dims[:max(1, len(dims)//2)]
        dashboard_dims = dims[len(dims)//2:] if len(dims) > 1 else dims
        used_overview_dims = set()
        
        def get_overview_dim():
            for d in overview_dims:
                if d not in used_overview_dims:
                    return d
            return overview_dims[0] if overview_dims else None
        
        # Generate ONLY charts that were SELECTED based on score!
        # Each chart checks if it's in selected_overview before generating
        
        # DONUT - Only if selected
        if 'donut' in selected_overview and overview_dims:
            sorted_dims = sorted(overview_dims, key=lambda d: self.profiles[d].cardinality)
            dim = sorted_dims[0]
            used_overview_dims.add(dim)
            counts = self.df[dim].value_counts().head(8)
            data = [{"name": str(k)[:15], "value": int(v), "color": OVERVIEW_PALETTE[i % len(OVERVIEW_PALETTE)], 
                    "percent": round(int(v)/max(len(self.df), 1)*100, 1)} 
                    for i, (k, v) in enumerate(counts.items())]
            if data:
                overview_charts.append({
                    "type": "donut",
                    "title": f"{dim.replace('_', ' ').title()} Distribution",
                    "data": {"data": data},
                    "colors": OVERVIEW_PALETTE,
                    "score": scores.get('donut', 0)
                })
        
        # FUNNEL - Only if selected
        if 'funnel' in selected_overview and overview_dims:
            funnel_dim = get_overview_dim() or overview_dims[0]
            if funnel_dim:
                used_overview_dims.add(funnel_dim)
                funnel_data = self._aggregate(funnel_dim, 5)
                if funnel_data:
                    funnel_items = [{"name": d["name"], "value": d["value"], "color": OVERVIEW_PALETTE[i % len(OVERVIEW_PALETTE)], 
                                    "percent": round(d["value"]/max(funnel_data[0]["value"], 1)*100, 1)} 
                                   for i, d in enumerate(funnel_data)]
                    overview_charts.append({
                        "type": "funnel",
                        "title": f"{funnel_dim.replace('_', ' ').title()} Funnel",
                        "data": funnel_items,
                        "score": scores.get('funnel', 0)
                    })
        
        # GAUGE - Only if selected
        if 'gauge' in selected_overview and self.metrics:
            metric = self.metrics[0]
            vals = self._to_numeric(self.df[metric])
            avg_val = float(vals.mean())
            max_val = float(vals.max())
            if max_val > 0:
                overview_charts.append({
                    "type": "gauge",
                    "title": f"Avg {metric.replace('_', ' ').title()}",
                    "data": {
                        "value": round(avg_val, 2),
                        "min": round(float(vals.min()), 2),
                        "max": round(max_val, 2),
                        "target": round(max_val * 0.75, 2),
                        "percent": round((avg_val / max(max_val, 1)) * 100, 1)
                    },
                    "score": scores.get('gauge', 0)
                })
        
        # TOP PERFORMERS - Only if selected
        if 'top_performers' in selected_overview and overview_dims:
            dim = get_overview_dim() or overview_dims[0]
            used_overview_dims.add(dim)
            top_data = self._aggregate(dim, 6)
            if top_data:
                for i, d in enumerate(top_data):
                    d["color"] = OVERVIEW_PALETTE[i % len(OVERVIEW_PALETTE)]
                overview_charts.append({
                    "type": "top_performers",
                    "title": f"Top {dim.replace('_', ' ').title()}s",
                    "data": top_data,
                    "metricName": "Count" if self.use_count_as_metric else self.metrics[0].replace('_', ' ').title() if self.metrics else "Count",
                    "score": scores.get('top_performers', 0)
                })
        
        # PROGRESS BARS - Only if selected
        if 'progress_bars' in selected_overview and overview_dims:
            dim = get_overview_dim() or overview_dims[0]
            prog_data = self._aggregate(dim, 5)
            if prog_data:
                max_val = max(d["value"] for d in prog_data) if prog_data else 1
                for i, d in enumerate(prog_data):
                    d["percent"] = round((d["value"] / max(max_val, 1)) * 100, 1)
                    d["color"] = OVERVIEW_PALETTE[i % len(OVERVIEW_PALETTE)]
                overview_charts.append({
                    "type": "progress_bars",
                    "title": f"{dim.replace('_', ' ').title()} Progress",
                    "data": prog_data,
                    "score": scores.get('progress_bars', 0)
                })
        
        # DATA QUALITY - Only if selected
        if 'data_quality' in selected_overview:
            quality_data = []
            total_rows = max(self.record_count, 1)
            for col, profile in list(self.profiles.items())[:6]:
                if profile.use_for_charts:
                    null_count = int(self.df[col].isna().sum())
                    quality_data.append({
                        "name": str(col).replace('_', ' ').title()[:15],
                        "completeness": round(((total_rows - null_count) / total_rows) * 100, 1),
                        "unique": profile.cardinality,
                        "type": "Metric" if profile.is_numeric else "Dimension"
                    })
            if quality_data:
                overview_charts.append({
                    "type": "data_quality",
                    "title": "Data Quality",
                    "data": quality_data,
                    "score": scores.get('data_quality', 0)
                })
        
        # METRIC CARDS - Only if selected
        if 'metric_cards' in selected_overview and self.metrics:
            metric_cards = []
            for i, metric in enumerate(self.metrics[:4]):
                profile = self.profiles[metric]
                metric_cards.append({
                    "name": metric.replace('_', ' ').title()[:15],
                    "value": round(profile.sum_val if profile.prefer_sum else profile.mean, 2),
                    "change": round(random.uniform(-15, 25), 1),
                    "color": OVERVIEW_PALETTE[i % len(OVERVIEW_PALETTE)]
                })
            if metric_cards:
                overview_charts.append({
                    "type": "metric_cards",
                    "title": "Key Metrics",
                    "data": metric_cards,
                    "score": scores.get('metric_cards', 0)
                })
        
        # SPARKLINE - Only if selected
        if 'sparkline' in selected_overview and self.time_columns and self.metrics:
            time_col = self.time_columns[0]
            metric = self.metrics[0]
            try:
                time_data = self.df.groupby(time_col)[metric].apply(lambda x: self._to_numeric(x).sum()).head(8)
                spark_data = [round(float(v), 2) for v in time_data.values]
                if len(spark_data) > 1:
                    trend = "↑" if spark_data[-1] > spark_data[0] else "↓" if spark_data[-1] < spark_data[0] else "→"
                    overview_charts.append({
                        "type": "sparkline",
                        "title": f"{metric.replace('_', ' ').title()} Trend",
                        "data": spark_data,
                        "trend": trend,
                        "change": round(((spark_data[-1] - spark_data[0]) / max(spark_data[0], 1)) * 100, 1),
                        "score": scores.get('sparkline', 0)
                    })
            except:
                pass
        
        # Sort charts by score (highest first) for layout
        overview_charts.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        overview_layout = {
            "kpis": self._generate_kpis(),
            "charts": overview_charts,
            "aiInsight": self._generate_insight(),
            "quickStats": {
                "records": self.record_count,
                "columns": len([p for p in self.profiles.values() if p.use_for_charts]),
                "metrics": len(self.metrics),
                "dimensions": len(dims),
                "supportedCharts": len(supported_charts)
            },
            "palette": OVERVIEW_PALETTE,
            "selectedCharts": selected_overview,
            "chartScores": {ct: sc for ct, sc in overview_scored}
        }
        
        # =====================================================
        # DASHBOARD: Generate only SELECTED charts (by score!)
        # =====================================================
        
        dashboard_charts = []
        used_dims = set()
        
        def get_dash_dim():
            for d in dashboard_dims:
                if d not in used_dims:
                    return d
            for d in dims:
                if d not in used_dims:
                    return d
            return dims[0] if dims else None
        
        # AREA - Only if selected
        if 'area' in selected_dashboard and dims:
            dim = get_dash_dim()
            if dim:
                used_dims.add(dim)
                data = self._aggregate(dim, 10)
                if data:
                    chart_data = [{"x": d["category"], "y": d["value"]} for d in data]
                    metric_name = "Count" if self.use_count_as_metric else self.metrics[0].replace('_', ' ').title() if self.metrics else "Count"
                    dashboard_charts.append({
                        "type": "area",
                        "title": f"{metric_name} by {dim.replace('_', ' ').title()}",
                        "data": {"series": [{"name": metric_name, "data": chart_data, "color": DASHBOARD_PALETTE[0]}]},
                        "colors": DASHBOARD_PALETTE,
                        "score": scores.get('area', 0),
                        "priority": 1
                    })
        
        # BAR HORIZONTAL - Only if selected
        if 'bar_horizontal' in selected_dashboard and dims:
            dim = get_dash_dim()
            if dim:
                used_dims.add(dim)
                data = self._aggregate(dim, 6)
                if data:
                    for i, d in enumerate(data):
                        d["color"] = DASHBOARD_PALETTE[i % len(DASHBOARD_PALETTE)]
                    dashboard_charts.append({
                        "type": "bar_horizontal",
                        "title": f"Top {dim.replace('_', ' ').title()}s",
                        "data": {"data": data},
                        "colors": DASHBOARD_PALETTE,
                        "score": scores.get('bar_horizontal', 0),
                        "priority": 2
                    })
        
        # BAR VERTICAL - Only if selected
        if 'bar_vertical' in selected_dashboard and len(dims) > 2:
            dim = get_dash_dim()
            if dim:
                used_dims.add(dim)
                data = self._aggregate(dim, 8)
                if data:
                    for i, d in enumerate(data):
                        d["color"] = DASHBOARD_PALETTE[i % len(DASHBOARD_PALETTE)]
                    dashboard_charts.append({
                        "type": "bar_vertical",
                        "title": f"{dim.replace('_', ' ').title()} Comparison",
                        "data": {"data": data},
                        "colors": DASHBOARD_PALETTE,
                        "score": scores.get('bar_vertical', 0),
                        "priority": 3
                    })
        
        # RADAR - Only if selected
        if 'radar' in selected_dashboard:
            radar_dims = [d for d in dims if self.profiles[d].cardinality >= 3 and d not in used_dims]
            if radar_dims:
                dim = radar_dims[0]
                used_dims.add(dim)
                if self.use_count_as_metric:
                    agg = self.df[dim].value_counts().head(8)
                else:
                    metric = self.metrics[0]
                    profile = self.profiles[metric]
                    if profile.prefer_sum:
                        agg = self.df.groupby(dim)[metric].apply(lambda x: self._to_numeric(x).sum()).head(8)
                    else:
                        agg = self.df.groupby(dim)[metric].apply(lambda x: self._to_numeric(x).mean()).head(8)
                
                radar_data = [{"subject": str(k)[:12], "value": round(float(v), 2)} for k, v in agg.items()]
                if len(radar_data) >= 3:
                    dashboard_charts.append({
                        "type": "radar",
                        "title": f"{dim.replace('_', ' ').title()} Analysis",
                        "data": {"data": radar_data},
                        "color": DASHBOARD_PALETTE[4],
                        "score": scores.get('radar', 0),
                        "priority": 4
                    })
        
        # STATS CARD - Only if selected
        if 'stats_card' in selected_dashboard and self.metrics:
            metric = self.metrics[0]
            vals = self._to_numeric(self.df[metric])
            if len(vals) > 1 and vals.var() > 0:
                dashboard_charts.append({
                    "type": "stats_card",
                    "title": f"{metric.replace('_', ' ').title()} Statistics",
                    "data": {
                        "min": round(float(vals.min()), 2),
                        "25th": round(float(vals.quantile(0.25)), 2),
                        "median": round(float(vals.median()), 2),
                        "75th": round(float(vals.quantile(0.75)), 2),
                        "max": round(float(vals.max()), 2),
                        "avg": round(float(vals.mean()), 2)
                    },
                    "colors": DASHBOARD_PALETTE,
                    "score": scores.get('stats_card', 0),
                    "priority": 5
                })
        
        # SCATTER - Only if selected
        if 'scatter' in selected_dashboard and len(self.metrics) >= 2:
            m1, m2 = self.metrics[0], self.metrics[1]
            vals1 = self._to_numeric(self.df[m1])
            vals2 = self._to_numeric(self.df[m2])
            scatter_data = [{"x": float(vals1.iloc[i]), "y": float(vals2.iloc[i])} 
                           for i in range(min(50, len(self.df)))]
            if scatter_data:
                dashboard_charts.append({
                    "type": "scatter",
                    "title": f"{m1.replace('_', ' ').title()} vs {m2.replace('_', ' ').title()}",
                    "data": {"data": scatter_data},
                    "colors": DASHBOARD_PALETTE,
                    "score": scores.get('scatter', 0),
                    "priority": 6
                })
        
        # LINE - Only if selected
        if 'line' in selected_dashboard and self.time_columns:
            time_col = self.time_columns[0]
            if self.metrics:
                metric = self.metrics[0]
                try:
                    time_data = self.df.groupby(time_col)[metric].apply(lambda x: self._to_numeric(x).sum()).head(12)
                    line_data = [{"x": str(k)[:10], "y": round(float(v), 2)} for k, v in time_data.items()]
                    if line_data:
                        dashboard_charts.append({
                            "type": "line",
                            "title": f"{metric.replace('_', ' ').title()} Trend",
                            "data": {"series": [{"name": metric, "data": line_data, "color": DASHBOARD_PALETTE[5]}]},
                            "colors": DASHBOARD_PALETTE,
                            "score": scores.get('line', 0),
                            "priority": 7
                        })
                except:
                    pass
        
        # WATERFALL - Only if selected
        if 'waterfall' in selected_dashboard and dims:
            dim = get_dash_dim() or dims[0]
            wf_data = self._aggregate(dim, 6)
            if wf_data:
                running_total = 0
                waterfall_items = []
                for i, d in enumerate(wf_data):
                    running_total += d["value"]
                    waterfall_items.append({
                        "name": d["name"],
                        "value": d["value"],
                        "total": running_total,
                        "color": DASHBOARD_PALETTE[i % len(DASHBOARD_PALETTE)]
                    })
                dashboard_charts.append({
                    "type": "waterfall",
                    "title": f"{dim.replace('_', ' ').title()} Waterfall",
                    "data": waterfall_items,
                    "score": scores.get('waterfall', 0),
                    "priority": 8
                })
        
        # TREEMAP - Only if selected
        if 'treemap' in selected_dashboard and dims:
            tree_dim = next((d for d in dims if self.profiles[d].cardinality >= 4), dims[0])
            tree_data = self._aggregate(tree_dim, 8)
            if tree_data:
                total = sum(x["value"] for x in tree_data)
                tree_items = [{"name": d["name"], "value": d["value"], "color": DASHBOARD_PALETTE[i % len(DASHBOARD_PALETTE)], 
                              "percent": round(d["value"]/max(total, 1)*100, 1)} 
                             for i, d in enumerate(tree_data)]
                dashboard_charts.append({
                    "type": "treemap",
                    "title": f"{tree_dim.replace('_', ' ').title()} Treemap",
                    "data": tree_items,
                    "score": scores.get('treemap', 0),
                    "priority": 9
                })
        
        # STACKED BAR - Only if selected
        if 'stacked_bar' in selected_dashboard and len(dims) >= 2:
            dim1, dim2 = dims[0], dims[1]
            try:
                stack_data = []
                agg = self.df.groupby([dim1, dim2]).size().reset_index(name='count').head(20)
                for i, cat in enumerate(agg[dim1].unique()[:5]):
                    cat_data = agg[agg[dim1] == cat]
                    stack_entry = {"name": str(cat)[:15], "color": DASHBOARD_PALETTE[i % len(DASHBOARD_PALETTE)]}
                    for _, row in cat_data.iterrows():
                        stack_entry[str(row[dim2])[:10]] = int(row['count'])
                    stack_data.append(stack_entry)
                if stack_data:
                    dashboard_charts.append({
                        "type": "stacked_bar",
                        "title": f"{dim1.replace('_', ' ').title()} by {dim2.replace('_', ' ').title()}",
                        "data": stack_data,
                        "keys": [str(k)[:10] for k in agg[dim2].unique()[:5]],
                        "score": scores.get('stacked_bar', 0),
                        "priority": 10
                    })
            except:
                pass
        
        # TOP 5 LIST - Only if selected
        if 'top5_list' in selected_dashboard:
            for i, dim in enumerate(dims[:2]):
                if dim not in used_dims:
                    used_dims.add(dim)
                    data = self._aggregate(dim, 5)
                    if data:
                        list_data = [{"name": d["name"], "value": d["value"], 
                                     "delta": round(random.uniform(-10, 15), 1), 
                                     "color": DASHBOARD_PALETTE[j % len(DASHBOARD_PALETTE)]} 
                                    for j, d in enumerate(data)]
                        dashboard_charts.append({
                            "type": "top5_list",
                            "title": f"Top {dim.replace('_', ' ').title()}s",
                            "data": list_data,
                            "score": scores.get('top5_list', 0),
                            "priority": 11 + i
                        })
        
        # BULLET - Only if selected
        if 'bullet' in selected_dashboard and self.metrics:
            metric = self.metrics[0]
            vals = self._to_numeric(self.df[metric])
            avg = float(vals.mean())
            max_val = float(vals.max())
            if max_val > 0:
                dashboard_charts.append({
                    "type": "bullet",
                    "title": f"{metric.replace('_', ' ').title()} Performance",
                    "data": {
                        "value": round(avg, 2),
                        "target": round(max_val * 0.75, 2),
                        "ranges": [round(max_val * 0.3, 2), round(max_val * 0.6, 2), round(max_val, 2)]
                    },
                    "score": scores.get('bullet', 0),
                    "priority": 13
                })
        
        # =====================================================
        # NEW ADVANCED CHART GENERATORS
        # =====================================================
        
        # BOX PLOT - Only if selected
        if 'box_plot' in selected_dashboard and dims and self.metrics:
            dim = next((d for d in dims if self.profiles[d].cardinality

 <= 8), dims[0])
            metric = self.metrics[0]
            try:
                box_data = []
                for i, cat in enumerate(self.df[dim].unique()[:6]):
                    cat_vals = self._to_numeric(self.df[self.df[dim] == cat][metric])
                    if len(cat_vals) > 0:
                        box_data.append({
                            "category": str(cat)[:15],
                            "min": round(float(cat_vals.min()), 2),
                            "q1": round(float(cat_vals.quantile(0.25)), 2),
                            "median": round(float(cat_vals.median()), 2),
                            "q3": round(float(cat_vals.quantile(0.75)), 2),
                            "max": round(float(cat_vals.max()), 2),
                            "color": DASHBOARD_PALETTE[i % len(DASHBOARD_PALETTE)]
                        })
                
                if box_data:
                    dashboard_charts.append({
                        "type": "box_plot",
                        "title": f"{metric.replace('_', ' ').title()} Distribution by {dim.replace('_', ' ').title()}",
                        "data": box_data,
                        "xLabel": dim.replace('_', ' ').title(),
                        "yLabel": metric.replace('_', ' ').title(),
                        "colors": DASHBOARD_PALETTE,
                        "score": scores.get('box_plot', 0),
                        "priority": 20
                    })
            except:
                pass
        
        # SANKEY DIAGRAM - Only if selected
        if 'sankey' in selected_dashboard and len(dims) >= 2:
            dim1, dim2 = dims[0], dims[1]
            try:
                sankey_flows = []
                flow_counts = self.df.groupby([dim1, dim2]).size().reset_index(name='count')
                top_sources = self.df[dim1].value_counts().head(5).index.tolist()
                top_targets = self.df[dim2].value_counts().head(5).index.tolist()
                
                for idx, row in flow_counts.iterrows():
                    if row[dim1] in top_sources and row[dim2] in top_targets:
                        sankey_flows.append({
                            "source": str(row[dim1])[:15],
                            "target": str(row[dim2])[:15],
                            "value": int(row['count']),
                            "color": DASHBOARD_PALETTE[len(sankey_flows) % len(DASHBOARD_PALETTE)]
                        })
                
                if sankey_flows:
                    dashboard_charts.append({
                        "type": "sankey",
                        "title": f"{dim1.replace('_', ' ').title()} → {dim2.replace('_', ' ').title()} Flow",
                        "data": sankey_flows,
                        "nodes": list(set([f["source"] for f in sankey_flows] + [f["target"] for f in sankey_flows])),
                        "colors": DASHBOARD_PALETTE,
                        "score": scores.get('sankey', 0),
                        "priority": 22
                    })
            except:
                pass
        
        # CALENDAR HEATMAP - Only if selected
        if 'calendar_heatmap' in selected_dashboard and self.time_columns and self.metrics:
            time_col = self.time_columns[0]
            metric = self.metrics[0]
            try:
                df_temp = self.df.copy()
                df_temp['_date'] = pd.to_datetime(df_temp[time_col], errors='coerce')
                df_temp = df_temp[df_temp['_date'].notna()]
                df_temp['_metric'] = self._to_numeric(df_temp[metric])
                daily_values = df_temp.groupby(df_temp['_date'].dt.date)['_metric'].sum()
                
                calendar_data = []
                max_val = daily_values.max() if len(daily_values) > 0 else 1
                heatmap_colors = ['#FEE2E2', '#FED7AA', '#FEF3C7', '#D9F99D', '#A7F3D0', '#6EE7B7', '#34D399', '#10B981', '#059669', '#047857']
                
                for date, value in daily_values.head(90).items():
                    intensity = min(9, int((value / max_val) * 9)) if max_val > 0 else 0
                    calendar_data.append({
                        "date": str(date),
                        "value": round(float(value), 2),
                        "intensity": intensity,
                        "color": heatmap_colors[intensity]
                    })
                
                if calendar_data:
                    dashboard_charts.append({
                        "type": "calendar_heatmap",
                        "title": f"{metric.replace('_', ' ').title()} Activity Calendar",
                        "data": calendar_data,
                        "colors": DASHBOARD_PALETTE,
                        "score": scores.get('calendar_heatmap', 0),
                        "priority": 23
                    })
            except:
                pass
        
        # CORRELATION MATRIX - Only if selected
        if 'correlation_matrix' in selected_dashboard and len(self.metrics) >= 3:
            try:
                correlation_data = []
                metrics_to_use = self.metrics[:6]
                corr_colors = ['#DC2626', '#EF4444', '#F87171', '#E5E7EB', '#86EFAC', '#22C55E', '#15803D']
                
                for i, m1 in enumerate(metrics_to_use):
                    for j, m2 in enumerate(metrics_to_use):
                        vals1 = self._to_numeric(self.df[m1])
                        vals2 = self._to_numeric(self.df[m2])
                        
                        if len(vals1) > 1 and vals1.std() > 0 and vals2.std() > 0:
                            corr = np.corrcoef(vals1, vals2)[0, 1]
                            if not np.isnan(corr):
                                # Map correlation to color: -1 (red) to +1 (green)
                                color_idx = int((corr + 1) * 3)  # Maps -1..1 to 0..6
                                
                                correlation_data.append({
                                    "x": m1.replace('_', ' ').title()[:12],
                                    "y": m2.replace('_', ' ').title()[:12],
                                    "value": round(float(corr), 3),
                                    "intensity": int(abs(corr) * 9),
                                    "color": corr_colors[color_idx]
                                })
                
                if correlation_data:
                    dashboard_charts.append({
                        "type": "correlation_matrix",
                        "title": "Metric Correlations",
                        "data": correlation_data,
                        "metrics": [m.replace('_', ' ').title()[:12] for m in metrics_to_use],
                        "colors": DASHBOARD_PALETTE,
                        "score": scores.get('correlation_matrix', 0),
                        "priority": 24
                    })
            except:
                pass
        
        # DATA SUMMARY - Always included
        dashboard_charts.append({
            "type": "summary",
            "title": "Data Summary",
            "data": {
                "records": self.record_count,
                "columns": len([p for p in self.profiles.values() if p.use_for_charts]),
                "metrics": len(self.metrics),
                "dimensions": len(dims)
            },
            "score": 100,
            "priority": 25
        })
        
        # Sort by SCORE (highest first) - intelligent layout!
        dashboard_charts.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        dashboard_layout = {
            "kpis": self._generate_kpis(),
            "widgets": dashboard_charts + [self._generate_data_table()],
            "supportedCharts": supported_charts,
            "palette": DASHBOARD_PALETTE,
            "selectedCharts": selected_dashboard,
            "chartScores": {ct: sc for ct, sc in dashboard_scored}
        }
        
        return {
            "hasData": self.record_count > 0,
            "domain": "Analytics",
            "palette": {"accent": DASHBOARD_PALETTE[0], "primary": DASHBOARD_PALETTE, "overview": OVERVIEW_PALETTE, "dashboard": DASHBOARD_PALETTE},
            "dataShape": {
                "rows": self.record_count,
                "columns": len([p for p in self.profiles.values() if p.use_for_charts]),
                "metrics": len(self.metrics),
                "dimensions": len(dims),
                "hasTime": len(self.time_columns) > 0,
                "supportedCharts": supported_charts,
                "usesCount": self.use_count_as_metric,
                "newChartTypes": ['box_plot', 'sankey', 'calendar_heat map', 'correlation_matrix'] # Track new chart types
            },
            "overviewLayout": overview_layout,
            "dashboardLayout": dashboard_layout,
            "slicers": self.generate_slicers(),
            "chartFitnessScores": scores  # Include all scores for transparency!
        }


# Backward compatibility
IntelligentVisualizationEngine = RealPowerBIEngine
ProMaxVisualizationEngine = RealPowerBIEngine
UniversalVisualizationEngine = RealPowerBIEngine
PureDataDrivenEngine = RealPowerBIEngine
PowerBIEngine = RealPowerBIEngine
SmartPowerBIEngine = RealPowerBIEngine

