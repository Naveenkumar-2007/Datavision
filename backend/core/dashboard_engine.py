"""
Dashboard Engine - Exploration, Density, Interaction
====================================================
Generates exploration-focused visual intelligence.

Characteristics:
- HIGH DENSITY: 8-15 visuals
- DEEP INTERACTIONS: Filters, drill-downs, cross-filtering
- CLUSTERED LAYOUT: Relationship-based grouping
- COMPLEX PRIMITIVES: Multi-series, correlations, distributions

Output is structurally DIFFERENT from overview even for same data.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from core.data_behavior_scorer import DataBehaviorScorer, BehaviorScores
from core.color_derivation_engine import ColorDerivationEngine, ColorPalette
from core.layout_synthesizer import LayoutSynthesizer, LayoutSpec
from core.visual_primitive_resolver import VisualPrimitiveResolver, VisualPrimitive


class DashboardEngine:
    """
    Dashboard generator - exploration and density focus.
    
    Example:
        engine = DashboardEngine()
        dashboard = engine.generate(df, behavior_scores)
    """
    
    def __init__(self):
        self.scorer = DataBehaviorScorer()
        self.color_engine = ColorDerivationEngine()
        self.layout_synthesizer = LayoutSynthesizer()
        self.primitive_resolver = VisualPrimitiveResolver()
    
    def generate(self, df: pd.DataFrame, behavior: BehaviorScores = None) -> Dict[str, Any]:
        """
        Generate dashboard visual intelligence.
        
        Args:
            df: Dataset
            behavior: Optional pre-computed behavior scores
            
        Returns:
            Complete dashboard specification
        """
        # 1. Score behavior if not provided
        if behavior is None:
            behavior = self.scorer.score(df)
        
        # 2. Derive color palette (SAME as overview for same data)
        color_palette = self.color_engine.derive_palette(df, behavior)
        
        # 3. Synthesize layout with mode='dashboard' (zone-based, high density)
        dashboard_layout = self.layout_synthesizer.synthesize(df, behavior, mode='dashboard')
        
        # 4. Resolve visual primitives with mode='dashboard' for autonomous differentiation
        dashboard_primitives = self.primitive_resolver.resolve(
            df, behavior, dashboard_layout.visual_count, mode='dashboard'
        )
        
        # 5. Generate interaction configuration
        interaction_config = self._generate_interaction_config(df, dashboard_primitives)
        
        return {
            "layout_spec": dashboard_layout.to_dict(),
            "visual_primitives": [p.to_dict() for p in dashboard_primitives],
            "color_palette": color_palette.to_dict(),
            "interaction_config": interaction_config,
            "behavior_scores": behavior.to_dict(),
            "mode": "dashboard"
        }

    # Removed _determine_dashboard_visual_count and _adapt_layout_for_dashboard as they are now handled by LayoutSynthesizer
    
    def _enhance_primitives_for_dashboard(self, primitives: List[VisualPrimitive]) -> List[VisualPrimitive]:
        """
        Add interaction metadata to dashboard primitives.
        
        Note: Primitive selection is now fully autonomous via resolver mode.
        This function only adds interaction flags.
        """
        # Add interaction hints to visual properties
        for primitive in primitives:
            primitive.visual_properties["interactive"] = True
            primitive.visual_properties["clickable"] = True
            
            # Add drill-down capability to certain primitives
            if primitive.primitive in ["comparison_field", "composition_view"]:
                primitive.visual_properties["drill_down"] = True
        
        return primitives
    
    def _generate_interaction_config(self, df: pd.DataFrame, 
                                     primitives: List[VisualPrimitive]) -> Dict[str, Any]:
        """
        Generate interaction configuration (DEEP INTERACTIONS).
        
        Dashboard is highly interactive.
        """
        # Detect filterable columns
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        
        filters = []
        
        # Add categorical filters
        for col in categorical_cols[:3]:  # Max 3 category filters
            unique_values = df[col].unique().tolist()[:20]  # Max 20 options
            filters.append({
                "column": col,
                "type": "categorical",
                "options": unique_values,
                "default": "all"
            })
        
        # Add date range filter
        for col in datetime_cols[:1]:  # Max 1 date filter
            try:
                date_col = pd.to_datetime(df[col])
                min_date = date_col.min().isoformat()
                max_date = date_col.max().isoformat()
                
                filters.append({
                    "column": col,
                    "type": "date_range",
                    "min": min_date,
                    "max": max_date,
                    "default": [min_date, max_date]
                })
            except:
                pass
        
        # Cross-highlighting configuration
        cross_highlight = {
            "enabled": True,
            "mode": "hover",
            "linked_primitives": [i for i, p in enumerate(primitives) 
                                 if p.primitive in ["comparison_field", "trend_carrier"]]
        }
        
        # Drill-down paths
        drill_paths = []
        for i, primitive in enumerate(primitives):
            if primitive.visual_properties.get("drill_down"):
                drill_paths.append({
                    "primitive_index": i,
                    "drill_column": primitive.data_binding.get("category", 
                                   primitive.data_binding.get("x")),
                    "detail_level": "next"
                })
        
        return {
            "filters": filters,
            "cross_highlight": cross_highlight,
            "drill_paths": drill_paths,
            "export_enabled": True,
            "refresh_enabled": True
        }


# Example usage
if __name__ == "__main__":
    # Test with sample data
    test_data = pd.DataFrame({
        'date': pd.date_range('2023-01-01', periods=100),
        'revenue': np.random.normal(10000, 2000, 100),
        'profit': np.random.normal(2000, 500, 100),
        'customers': np.random.poisson(50, 100),
        'category': np.random.choice(['A', 'B', 'C'], 100),
        'region': np.random.choice(['North', 'South'], 100),
    })
    
    # Generate dashboard
    engine = DashboardEngine()
    dashboard = engine.generate(test_data)
    
    print("Generated Dashboard:")
    print(f"  Mode: {dashboard['mode']}")
    print(f"  Visual Count: {dashboard['layout_spec']['visual_count']}")
    print(f"  Spatial Flow: {dashboard['layout_spec']['spatial_flow']}")
    print(f"  Filters: {len(dashboard['interaction_config']['filters'])}")
    print(f"  Color Base Hue: {dashboard['color_palette']['metadata']['base_hue']:.0f}°")
    print(f"\nPrimitives:")
    for i, prim in enumerate(dashboard['visual_primitives'][:5]):
        print(f"  {i+1}. {prim['primitive']}: {prim['title']}")
