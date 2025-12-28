"""
Overview Engine - Understanding, Hierarchy, Narrative
=====================================================
Generates understanding-focused visual intelligence.

Characteristics:
- LOW DENSITY: 3-6 visuals maximum
- HIGH NARRATIVE: Text insights, KPIs, summary metrics
- HIERARCHICAL: Clear primary → secondary → tertiary structure
- SIMPLIFIED PRIMITIVES: Trend carriers, single comparisons

Output is structurally DIFFERENT from dashboard even for same data.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from core.data_behavior_scorer import DataBehaviorScorer, BehaviorScores
from core.color_derivation_engine import ColorDerivationEngine, ColorPalette
from core.layout_synthesizer import LayoutSynthesizer, LayoutSpec
from core.visual_primitive_resolver import VisualPrimitiveResolver, VisualPrimitive


class OverviewEngine:
    """
    Overview generator - understanding and narrative focus.
    
    Example:
        engine = OverviewEngine()
        overview = engine.generate(df, behavior_scores)
    """
    
    def __init__(self):
        self.scorer = DataBehaviorScorer()
        self.color_engine = ColorDerivationEngine()
        self.layout_synthesizer = LayoutSynthesizer()
        self.primitive_resolver = VisualPrimitiveResolver()
    
    def generate(self, df: pd.DataFrame, behavior: BehaviorScores = None) -> Dict[str, Any]:
        """
        Generate overview visual intelligence.
        
        Args:
            df: Dataset
            behavior: Optional pre-computed behavior scores
            
        Returns:
            Complete overview specification
        """
        # 1. Score behavior if not provided
        if behavior is None:
            behavior = self.scorer.score(df)
        
        # 2. Derive color palette
        color_palette = self.color_engine.derive_palette(df, behavior)
        
        # 3. Synthesize layout with mode='overview' (zone-based, low density)
        overview_layout = self.layout_synthesizer.synthesize(df, behavior, mode='overview')
        
        # 4. Resolve visual primitives with mode='overview' for autonomous differentiation
        overview_primitives = self.primitive_resolver.resolve(
            df, behavior, overview_layout.visual_count, mode='overview'
        )
        
        # 5. Generate narrative elements
        narrative_elements = self._generate_narrative_elements(df, behavior, overview_primitives)
        
        return {
            "layout_spec": overview_layout.to_dict(),
            "visual_primitives": [p.to_dict() for p in overview_primitives],
            "color_palette": color_palette.to_dict(),
            "narrative_elements": narrative_elements,
            "behavior_scores": behavior.to_dict(),
            "mode": "overview"
        }
    
    def _determine_overview_visual_count(self, behavior: BehaviorScores) -> int:
        """
        Determine visual count for overview (LOW DENSITY).
        
        Range: 3-6 visuals
        """
        # Override: overview has fewer visuals than dashboard
        if behavior.complexity > 0.7:
            return 6
        elif behavior.complexity > 0.5:
            return 5
        elif behavior.complexity > 0.3:
            return 4
        else:
            return 3
    
    def _adapt_layout_for_overview(self, base_layout: LayoutSpec, 
                                   visual_count: int) -> LayoutSpec:
        """
        Adapt layout for overview constraints.
        
        - Force hierarchical structure
        - Increase spacing
        - Simplify spatial flow
        """
        # Override visual count
        base_layout.visual_count = visual_count
        
        # Force higher hierarchy depth (overview is more hierarchical)
        if base_layout.hierarchy_depth < 2:
            base_layout.hierarchy_depth = 2
        
        # Increase spacing (overview is less dense)
        base_layout.spacing_density = max(base_layout.spacing_density * 0.7, 0.4)
        
        # Simplify spatial flow (overview avoids complex layouts)
        if base_layout.spatial_flow in ["radial", "cascade"]:
            base_layout.spatial_flow = "grid"
        
        # Adjust groupings
        base_layout.grouping = [[i] for i in range(visual_count)]  # Individual groups
        
        # Ensure primary focus on first 2 visuals
        base_layout.primary_focus = [0, 1] if visual_count >= 2 else [0]
        
        return base_layout
    
    def _generate_narrative_elements(self, df: pd.DataFrame, behavior: BehaviorScores,
                                     primitives: List[VisualPrimitive]) -> List[Dict[str, Any]]:
        """
        Generate narrative elements (text insights, summaries).
        
        Overview is HIGH NARRATIVE.
        """
        narrative = []
        
        # 1. Dataset summary
        narrative.append({
            "type": "summary",
            "title": "Dataset Overview",
            "text": f"Analyzing {len(df):,} records across {len(df.columns)} dimensions. "
                   f"Data exhibits {'high' if behavior.complexity > 0.6 else 'moderate'} complexity "
                   f"with {'strong' if behavior.temporal > 0.7 else 'weak'} temporal patterns.",
            "priority": 10
        })
        
        # 2. Key insights from behavior
        insights = []
        
        if behavior.volatility > 0.6:
            insights.append(f"High volatility detected (score: {behavior.volatility:.2f}). "
                          "Data shows significant variance and noise.")
        
        if behavior.temporal > 0.7:
            insights.append(f"Strong temporal patterns (score: {behavior.temporal:.2f}). "
                          "Time-series analysis recommended.")
        
        if behavior.sparsity > 0.4:
            insights.append(f"Data sparsity noted (score: {behavior.sparsity:.2f}). "
                          f"{int(behavior.sparsity * 100)}% of values are missing or duplicate.")
        
        if insights:
            narrative.append({
                "type": "insights",
                "title": "Key Observations",
                "items": insights,
                "priority": 9
            })
        
        # 3. Metric summaries (from metric_display primitives)
        metric_primitives = [p for p in primitives if p.primitive == "metric_display"]
        if metric_primitives:
            metrics = []
            for mp in metric_primitives[:3]:
                col = mp.data_binding.get("value")
                if col and col in df.columns:
                    col_data = df[col].dropna()
                    total = col_data.sum()
                    mean = col_data.mean()
                    
                    metrics.append({
                        "label": mp.title,
                        "value": total,
                        "average": mean,
                        "format": mp.data_binding.get("format", "number")
                    })
            
            if metrics:
                narrative.append({
                    "type": "metrics",
                    "title": "Key Metrics",
                    "data": metrics,
                    "priority": 8
                })
        
        return narrative


# Example usage
if __name__ == "__main__":
    # Test with sample data
    test_data = pd.DataFrame({
        'date': pd.date_range('2023-01-01', periods=100),
        'revenue': np.random.normal(10000, 2000, 100),
        'profit': np.random.normal(2000, 500, 100),
        'customers': np.random.poisson(50, 100),
    })
    
    # Generate overview
    engine = OverviewEngine()
    overview = engine.generate(test_data)
    
    print("Generated Overview:")
    print(f"  Mode: {overview['mode']}")
    print(f"  Visual Count: {overview['layout_spec']['visual_count']}")
    print(f"  Spatial Flow: {overview['layout_spec']['spatial_flow']}")
    print(f"  Narrative Elements: {len(overview['narrative_elements'])}")
    print(f"  Color Base Hue: {overview['color_palette']['metadata']['base_hue']:.0f}°")
    print(f"\nPrimitives:")
    for i, prim in enumerate(overview['visual_primitives']):
        print(f"  {i+1}. {prim['primitive']}: {prim['title']}")
