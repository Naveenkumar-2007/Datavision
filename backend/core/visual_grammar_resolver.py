"""
Visual Grammar Resolver
=======================
The 'Compiler' phase.
Maps abstract Visual Forces into concrete Geometric Primitives.

Concepts:
- Flow > 0.7 -> Sequential Traces (Lines, Areas)
- Fragmentation > 0.7 -> Small Multiples / Part-to-whole (Treemap, Voronoi)
- Cohesion > 0.7 -> Relational Constellations (Nodes, Links)
- Contrast > 0.7 -> Comparative Fields (Bars, Spikes)

Output: A list of abstract primitive specifications.
"""

from typing import Dict, List, Any
from core.visual_force_engine import VisualForces

class VisualGrammarResolver:
    def resolve(self, forces: VisualForces, column_info: Dict[str, List[str]], row_count: int) -> List[Dict[str, Any]]:
        """
        Compile forces into geometric specs.
        """
        primitives = []
        
        # 1. Determine Major Layout Strategy
        layout_strategy = self._determine_strategy(forces)
        
        # 2. High Flow -> Sequential Generation
        if forces.flow > 0.5 and column_info['datetime']:
            primitives.append({
                "type": "sequential_trace",
                "subtype": "smooth" if forces.contrast < 0.5 else "step",
                "weight": forces.dominance,
                "encoding": {
                    "x": "temporal",
                    "y": "quantitative",
                    "color": "nominal" if forces.fragmentation > 0.4 else "gradient"
                }
            })
            
        # 3. High Fragmentation -> Partitioning
        if forces.fragmentation > 0.5:
            primitives.append({
                "type": "partition_field",
                "subtype": "voronoi" if forces.cohesion < 0.3 else "rect", # Voronoi for loose, Rect for ordered
                "weight": forces.dominance,
                "encoding": {
                    "size": "quantitative",
                    "group": "nominal"
                }
            })

        # 4. High Cohesion -> Constellation
        if forces.cohesion > 0.6 and len(column_info['numeric']) >= 2:
            primitives.append({
                "type": "relational_constellation",
                "subtype": "force_directed",
                "weight": forces.dominance * 0.8,
                "encoding": {
                    "x": "quantitative_1",
                    "y": "quantitative_2",
                    "size": "quantitative_3" if len(column_info['numeric']) > 2 else None
                }
            })

        # 5. Default/Fallback: Comparative Field (Standard Comparison)
        # If nothing else is dominant, or contrast is high
        if not primitives or forces.contrast > 0.4:
            primitives.append({
                "type": "comparative_field",
                "subtype": "column" if forces.flow < 0.3 else "bar",
                "weight": forces.dominance,
                "encoding": {
                    "major": "nominal",
                    "minor": "quantitative"
                }
            })
            
        # 6. Apply Decorators based on forces
        for p in primitives:
            p['style'] = {
                'opacity': 0.6 + (forces.dominance * 0.4),
                'stroke_width': 1 + (forces.contrast * 3),
                'corner_radius': 0 if forces.contrast > 0.8 else 10
            }

        return {
            "strategy": layout_strategy,
            "primitives": primitives,
            "forces_snapshot": forces.to_dict()
        }

    def _determine_strategy(self, forces: VisualForces) -> str:
        if forces.flow > 0.8: return "continuous_stream"
        if forces.fragmentation > 0.8: return "molecular_cloud"
        if forces.cohesion > 0.8: return "central_gravity"
        if forces.contrast > 0.8: return "hierarchical_grid"
        return "organic_balance"
