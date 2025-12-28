"""
Visual Primitive Resolver - Primitive Detection
================================================
Resolves VISUAL PRIMITIVES, not chart types.

NO HARDCODED CHART MAPPINGS.

Primitives:
- trend_carrier: shows change over ordered dimension
- comparison_field: shows relative magnitudes
- distribution_surface: shows value spread  
- relationship_mapper: shows correlations
- anomaly_indicator: shows outliers
- composition_view: shows part-to-whole
- metric_display: shows single values

Chart library mapping is implementation detail only.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from core.data_behavior_scorer import BehaviorScores


@dataclass
class VisualPrimitive:
    """A visual primitive representation"""
    primitive: str                      # trend_carrier, comparison_field, etc.
    data_binding: Dict[str, Any]       # x, y, encoding, etc.
    visual_properties: Dict[str, Any]  # interpolation, emphasis, etc.
    priority: int                       # 1-10: rendering priority
    title: str                          # Dynamic title
    description: str                    # What this shows
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "primitive": self.primitive,
            "data_binding": self.data_binding,
            "visual_properties": self.visual_properties,
            "priority": self.priority,
            "title": self.title,
            "description": self.description
        }


class VisualPrimitiveResolver:
    """
    Resolves data to visual primitives - NOT chart types.
    
    Example:
        resolver = VisualPrimitiveResolver()
        primitives = resolver.resolve(df, behavior_scores, visual_count=8)
        # Returns: List[VisualPrimitive]
    """
    
    def resolve(self, df: pd.DataFrame, behavior: BehaviorScores, 
                visual_count: int, mode: str = 'overview') -> List[VisualPrimitive]:
        """
        Resolve visual primitives for the dataset.
        
        Args:
            df: The dataset
            behavior: BehaviorScores object
            visual_count: Number of primitives to generate
            mode: 'overview' or 'dashboard' - influences primitive distribution
            
        Returns:
            List of VisualPrimitive objects
        """
        primitives = []
        
        # Detect column types
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        datetime_cols = self._detect_datetime_cols(df)
        categorical_cols = [c for c in df.columns 
                          if c not in numeric_cols and c not in datetime_cols]
        
        # Priority queue for primitives
        priority_counter = 10
        
        # AUTONOMOUS PRIMITIVE DISTRIBUTION - 100% Behavior-Driven
        # NO hardcoded limits, counts calculated from data characteristics
        
        # 1. METRIC DISPLAYS (KPIs) - Count based on data richness and mode
        metric_primitives_list = []
        for i, metric_col in enumerate(numeric_cols):  # All numeric columns considered
            col_data = df[metric_col].dropna()
            
            # Determine format based on data range
            max_val = col_data.max()
            if max_val > 1000:
                format_type = "number"
            elif max_val <= 1.0:
                format_type = "percentage"
            else:
                format_type = "decimal"
            
            # Check if looks like currency
            if any(term in metric_col.lower() for term in ['revenue', 'profit', 'cost', 'price', 'amount']):
                format_type = "currency"
            
            primitive = VisualPrimitive(
                primitive="metric_display",
                data_binding={
                    "value": metric_col,
                    "aggregation": "sum",
                    "format": format_type
                },
                visual_properties={
                    "show_sparkline": behavior.temporal > 0.5,
                    "show_delta": behavior.temporal > 0.5,
                    "size": "large" if i == 0 else "medium"
                },
                priority=priority_counter - i,
                title=metric_col.replace('_', ' ').title(),
               description=f"Total {metric_col}"
            )
            metric_primitives_list.append(primitive)
        
        # Calculate KPI count: purely from behavior + mode influence
        if mode == 'overview':
            # Overview: Fewer KPIs (20-40% of visuals)
            kpi_weight = 0.2 + (behavior.density * 0.2)  # 0.2-0.4 range
        else:  # dashboard
            # Dashboard: More KPIs (30-50% of visuals)
            kpi_weight = 0.3 + (behavior.complexity * 0.2)  # 0.3-0.5 range
        
        metric_count = max(1, int(visual_count * kpi_weight))  # At least 1, no max
        primitives.extend(metric_primitives_list[:metric_count])
        priority_counter -= min(len(metric_primitives_list), metric_count)
        
        # 2. TREND CARRIERS - Count based on temporal behavior strength
        if len(datetime_cols) > 0 and len(numeric_cols) > 0:
            trend_primitives = self._resolve_trend_carriers(
                df, datetime_cols, numeric_cols, behavior, priority_counter
            )
            # Trend count: purely from temporal score and visual budget
            if mode == 'overview':
                # Overview: temporal strength determines trend emphasis
                trend_weight = behavior.temporal * 0.3  # 0-30% of visuals
            else:  # dashboard
                # Dashboard: higher temporal weight
                trend_weight = behavior.temporal * 0.4  # 0-40% of visuals
            
            trend_count = max(1, int(visual_count * trend_weight)) if behavior.temporal > 0.3 else 0
            primitives.extend(trend_primitives[:trend_count])
            priority_counter -= min(len(trend_primitives), trend_count)
        
        # 3. COMPARISON FIELDS - Count based on complexity and categorical richness
        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            comparison_primitives = self._resolve_comparison_fields(
                df, categorical_cols, numeric_cols, behavior, priority_counter
            )
            # Comparison count: complexity + categorical diversity
            categorical_richness = min(len(categorical_cols) / 5, 1.0)  # Normalize to 0-1
            if mode == 'overview':
                comparison_weight = (behavior.complexity * 0.2) + (categorical_richness * 0.1)  # 0-30%
            else:  # dashboard
                comparison_weight = (behavior.complexity * 0.3) + (categorical_richness * 0.2)  # 0-50%
            
            comparison_count = max(1, int(visual_count * comparison_weight)) if len(categorical_cols) > 0 else 0
            primitives.extend(comparison_primitives[:comparison_count])
            priority_counter -= min(len(comparison_primitives), comparison_count)
        
        # 4. DISTRIBUTION SURFACES - Based on density and volatility
        if len(numeric_cols) > 0:
            distribution_primitives = self._resolve_distribution_surfaces(
                df, numeric_cols, behavior, priority_counter
            )
            # Distribution weight: density + volatility indicate need for distribution views
            dist_weight = (behavior.density * 0.2 + behavior.volatility * 0.2) if mode == 'dashboard' else 0
            dist_count = int(visual_count * dist_weight)
            primitives.extend(distribution_primitives[:dist_count])
            priority_counter -= min(len(distribution_primitives), dist_count)
        
        # 5. RELATIONSHIP MAPPERS - High complexity data needs correlation views
        if len(numeric_cols) >= 2:
            relationship_primitives = self._resolve_relationship_mappers(
                df, numeric_cols, behavior, priority_counter
            )
            # Relationship weight: complexity drives need for correlation analysis
            rel_weight = (behavior.complexity * 0.15) if mode == 'dashboard' and behavior.complexity > 0.4 else 0
            rel_count = int(visual_count * rel_weight)
            primitives.extend(relationship_primitives[:rel_count])
            priority_counter -= min(len(relationship_primitives), rel_count)
        
        # 6. COMPOSITION VIEWS - Categorical richness drives pie/donut needs
        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            composition_primitives = self._resolve_composition_views(
                df, categorical_cols, numeric_cols, behavior, priority_counter
            )
            # Composition weight: more categorical columns = more composition views
            categorical_richness = min(len(categorical_cols) / 5, 1.0)
            comp_weight = categorical_richness * 0.15 if len(categorical_cols) >= 2 else 0
            if mode == 'dashboard':
                comp_weight *= 1.5  # Dashboard shows more compositions
            comp_count = int(visual_count * comp_weight)
            primitives.extend(composition_primitives[:comp_count])
            priority_counter -= min(len(composition_primitives), comp_count)
        
        # 7. ANOMALY INDICATORS - High volatility triggers anomaly detection
        if len(numeric_cols) > 0:
            anomaly_primitives = self._resolve_anomaly_indicators(
                df, numeric_cols, datetime_cols, behavior, priority_counter
            )
            # Anomaly weight: only show if volatility is significant
            anomaly_weight = (behavior.volatility - 0.5) * 0.1 if behavior.volatility > 0.6 and mode == 'dashboard' else 0
            anomaly_count = int(visual_count * anomaly_weight)
            primitives.extend(anomaly_primitives[:anomaly_count])
            priority_counter -= min(len(anomaly_primitives), anomaly_count)
        
        # Trim or expand to match visual_count
        if len(primitives) > visual_count:
            # Sort by priority and take top
            primitives.sort(key=lambda p: p.priority, reverse=True)
            primitives = primitives[:visual_count]
        elif len(primitives) < visual_count:
            # Duplicate lower priority primitives with variations
            while len(primitives) < visual_count:
                # Duplicate with slight variations
                base = primitives[len(primitives) % len(primitives)]
                duplicate = self._create_variation(base, len(primitives))
                primitives.append(duplicate)
        
        return primitives
    
    def _detect_datetime_cols(self, df: pd.DataFrame) -> List[str]:
        """Detect datetime columns"""
        datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        
        # Try parsing object columns
        for col in df.select_dtypes(include=['object']).columns:
            try:
                pd.to_datetime(df[col], errors='raise')
                datetime_cols.append(col)
                break  # Take first valid datetime
            except:
                pass
        
        return datetime_cols
    
    def _resolve_trend_carriers(self, df: pd.DataFrame, datetime_cols: List[str],
                                numeric_cols: List[str], behavior: BehaviorScores,
                                priority: int) -> List[VisualPrimitive]:
        """Resolve trend carrier primitives"""
        primitives = []
        
        time_col = datetime_cols[0]
        
        for i, metric_col in enumerate(numeric_cols[:2]):  # Max 2
            # Determine interpolation from volatility
            if behavior.volatility > 0.6:
                interpolation = "linear"
            else:
                interpolation = "smooth"
            
            # Emphasis from temporal score
            emphasis = "high" if behavior.temporal > 0.7 else "medium"
            
            primitive = VisualPrimitive(
                primitive="trend_carrier",
                data_binding={
                    "x": time_col,
                    "y": [metric_col],
                    "encoding": "continuous",
                    "aggregation": "none"
                },
                visual_properties={
                    "interpolation": interpolation,
                    "emphasis": emphasis,
                    "show_markers": behavior.sparsity > 0.3,
                    "area_fill": behavior.density > 0.6
                },
                priority=priority - i,
                title=f"{metric_col.replace('_', ' ').title()} Over Time",
                description=f"Trend of {metric_col} across time dimension"
            )
            primitives.append(primitive)
        
        return primitives
    
    def _resolve_comparison_fields(self, df: pd.DataFrame, categorical_cols: List[str],
                                   numeric_cols: List[str], behavior: BehaviorScores,
                                   priority: int) -> List[VisualPrimitive]:
        """Resolve comparison field primitives"""
        primitives = []
        
        cat_col = categorical_cols[0]
        
        for i, metric_col in enumerate(numeric_cols[:2]):
            # Determine encoding
            unique_cats = df[cat_col].nunique()
            if unique_cats > 10:
                encoding = "top_n"
                limit = 10
            else:
                encoding = "discrete"
                limit = None
            
            primitive = VisualPrimitive(
                primitive="comparison_field",
                data_binding={
                    "x": cat_col,
                    "y": [metric_col],
                    "encoding": encoding,
                    "aggregation": "sum",
                    "limit": limit
                },
                visual_properties={
                    "orientation": "vertical" if unique_cats <= 5 else "horizontal",
                    "show_values": unique_cats <= 8,
                    "sort_by": "value_desc"
                },
                priority=priority - i,
                title=f"{metric_col.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}",
                description=f"Comparison of {metric_col} across {cat_col}"
            )
            primitives.append(primitive)
        
        return primitives
    
    def _resolve_distribution_surfaces(self, df: pd.DataFrame, numeric_cols: List[str],
                                       behavior: BehaviorScores, priority: int) -> List[VisualPrimitive]:
        """Resolve distribution surface primitives"""
        primitives = []
        
        for i, metric_col in enumerate(numeric_cols[:2]):
            col_data = df[metric_col].dropna()
            
            # Determine bins from data range
            unique_vals = col_data.nunique()
            if unique_vals > 50:
                bins = 30
            elif unique_vals > 20:
                bins = 20
            else:
                bins = 10
            
            primitive = VisualPrimitive(
                primitive="distribution_surface",
                data_binding={
                    "value": metric_col,
                    "bins": bins,
                    "encoding": "histogram"
                },
                visual_properties={
                    "show_kde": behavior.volatility < 0.4,  # KDE for smooth data
                    "show_outliers": behavior.volatility > 0.6,
                    "bin_type": "auto"
                },
                priority=priority - i - 2,  # Lower priority
                title=f"{metric_col.replace('_', ' ').title()} Distribution",
                description=f"Value spread of {metric_col}"
            )
            primitives.append(primitive)
        
        return primitives
    
    def _resolve_relationship_mappers(self, df: pd.DataFrame, numeric_cols: List[str],
                                      behavior: BehaviorScores, priority: int) -> List[VisualPrimitive]:
        """Resolve relationship mapper primitives"""
        primitives = []
        
        # Find two most correlated columns
        if len(numeric_cols) >= 2:
            corr_matrix = df[numeric_cols].corr().abs()
            
            # Get strongest correlation (excluding diagonal)
            np.fill_diagonal(corr_matrix.values, 0)
            max_corr_idx = corr_matrix.values.argmax()
            row, col = np.unravel_index(max_corr_idx, corr_matrix.shape)
            
            x_col = numeric_cols[row]
            y_col = numeric_cols[col]
            
            primitive = VisualPrimitive(
                primitive="relationship_mapper",
                data_binding={
                    "x": x_col,
                    "y": y_col,
                    "encoding": "scatter"
                },
                visual_properties={
                    "show_trend_line": behavior.complexity > 0.5,
                    "point_size": "auto",
                    "opacity": 0.6
                },
                priority=priority - 3,
                title=f"{x_col.replace('_', ' ').title()} vs {y_col.replace('_', ' ').title()}",
                description=f"Relationship between {x_col} and {y_col}"
            )
            primitives.append(primitive)
        
        return primitives
    
    def _resolve_composition_views(self, df: pd.DataFrame, categorical_cols: List[str],
                                   numeric_cols: List[str], behavior: BehaviorScores,
                                   priority: int) -> List[VisualPrimitive]:
        """Resolve composition view primitives (part-to-whole)"""
        primitives = []
        
        cat_col = categorical_cols[0]
        metric_col = numeric_cols[0]
        
        unique_cats = df[cat_col].nunique()
        
        primitive = VisualPrimitive(
            primitive="composition_view",
            data_binding={
                "category": cat_col,
                "value": metric_col,
                "encoding": "pie" if unique_cats <= 6 else "donut",
                "aggregation": "sum"
            },
            visual_properties={
                "show_percentages": True,
                "show_labels": unique_cats <= 8,
                "inner_radius": 0.5 if unique_cats > 6 else 0
            },
            priority=priority - 4,
            title=f"{metric_col.replace('_', ' ').title()} Composition by {cat_col.replace('_', ' ').title()}",
            description=f"Breakdown of {metric_col} by {cat_col}"
        )
        primitives.append(primitive)
        
        return primitives
    
    def _resolve_anomaly_indicators(self, df: pd.DataFrame, numeric_cols: List[str],
                                    datetime_cols: List[str], behavior: BehaviorScores,
                                    priority: int) -> List[VisualPrimitive]:
        """Resolve anomaly indicator primitives"""
        primitives = []
        
        metric_col = numeric_cols[0]
        
        # Detect anomalies using IQR method
        col_data = df[metric_col].dropna()
        q1, q3 = col_data.quantile([0.25, 0.75])
        iqr = q3 - q1
        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)
        
        anomaly_count = ((col_data < lower_bound) | (col_data > upper_bound)).sum()
        
        if anomaly_count > 0:
            x_col = datetime_cols[0] if datetime_cols else metric_col
            
            primitive = VisualPrimitive(
                primitive="anomaly_indicator",
                data_binding={
                    "x": x_col,
                    "y": metric_col,
                    "encoding": "scatter",
                    "highlight": "outliers"
                },
                visual_properties={
                    "outlier_method": "iqr",
                    "highlight_color": "accent",
                    "show_bounds": True
                },
                priority=priority - 5,
                title=f"{metric_col.replace('_', ' ').title()} Anomalies",
                description=f"Outliers and unusual values in {metric_col}"
            )
            primitives.append(primitive)
        
        return primitives
    
    def _resolve_metric_displays(self, df: pd.DataFrame, numeric_cols: List[str],
                                 behavior: BehaviorScores, priority: int) -> List[VisualPrimitive]:
        """Resolve metric display primitives (KPIs)"""
        primitives = []
        
        for i, metric_col in enumerate(numeric_cols[:3]):
            col_data = df[metric_col].dropna()
            
            # Calculate key metric
            total = col_data.sum()
            mean = col_data.mean()
            
            # Determine format
            if col_data.max() > 1000:
                format_type = "number"
            elif col_data.max() <= 1.0:
                format_type = "percentage"
            else:
                format_type = "decimal"
            
            primitive = VisualPrimitive(
                primitive="metric_display",
                data_binding={
                    "value": metric_col,
                    "aggregation": "sum",
                    "format": format_type
                },
                visual_properties={
                    "show_sparkline": behavior.temporal > 0.5,
                    "show_delta": behavior.temporal > 0.5,
                    "size": "large" if i == 0 else "medium"
                },
                priority=priority - i - 6,
                title=metric_col.replace('_', ' ').title(),
                description=f"Total {metric_col}"
            )
            primitives.append(primitive)
        
        return primitives
    
    def _create_variation(self, base: VisualPrimitive, index: int) -> VisualPrimitive:
        """Create a variation of a primitive"""
        # Simple variation: duplicate with modified priority
        variation = VisualPrimitive(
            primitive=base.primitive,
            data_binding=base.data_binding.copy(),
            visual_properties=base.visual_properties.copy(),
            priority=base.priority - index,
            title=f"{base.title} (Variant)",
            description=base.description
        )
        return variation


# Example usage
if __name__ == "__main__":
    from data_behavior_scorer import DataBehaviorScorer
    
    # Test with sample data
    test_data = pd.DataFrame({
        'date': pd.date_range('2023-01-01', periods=100),
        'revenue': np.random.normal(10000, 2000, 100),
        'profit': np.random.normal(2000, 500, 100),
        'category': np.random.choice(['A', 'B', 'C', 'D'], 100),
        'region': np.random.choice(['North', 'South', 'East', 'West'], 100),
    })
    
    # Score behavior
    scorer = DataBehaviorScorer()
    behavior = scorer.score(test_data)
    
    # Resolve primitives
    resolver = VisualPrimitiveResolver()
    primitives = resolver.resolve(test_data, behavior, visual_count=8)
    
    print(f"Resolved {len(primitives)} Visual Primitives:")
    for i, prim in enumerate(primitives):
        print(f"\n{i+1}. {prim.primitive.upper()}")
        print(f"   Title: {prim.title}")
        print(f"   Priority: {prim.priority}")
        print(f"   Data Binding: {prim.data_binding}")
