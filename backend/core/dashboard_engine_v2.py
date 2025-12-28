"""
Dashboard Engine - VISUAL INTELLIGENCE COMPILER
===============================================
Data Signals -> Visual Forces -> Visual Grammar -> Rendering.
tuned for EXPLORATION (Higher Complexity, Relational Depth).
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List

from core.advanced_pattern_detector import AdvancedPatternDetector
from core.data_behavior_scorer import DataBehaviorScorer
from core.color_derivation_engine import ColorDerivationEngine
from core.layout_synthesizer import LayoutSynthesizer

# NEW COMPILER COMPONENTS
from core.data_signal_processor import DataSignalProcessor
from core.visual_force_engine import VisualForceEngine
from core.visual_grammar_resolver import VisualGrammarResolver

class DashboardEngineV2:
    """
    Dashboard: Exploratory visual intelligence.
    Uses the Signal->Force->Grammar pipeline but favors higher complexity/density.
    """
    
    def __init__(self):
        # Intelligence Core
        self.pattern_detector = AdvancedPatternDetector()
        self.scorer = DataBehaviorScorer()
        
        # Visual Compiler Core
        self.signal_processor = DataSignalProcessor()
        self.force_engine = VisualForceEngine()
        self.grammar_resolver = VisualGrammarResolver()
        
        # Rendering Helpers
        self.color_engine = ColorDerivationEngine()
        self.layout_synthesizer = LayoutSynthesizer()
    
    def generate(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate Dashboard using Visual Intelligence Compiler."""
        print(f"\n🧠 [VISUAL COMPILER] Compiling Dashboard...")
        
        # 1. Compute Data Signals
        signals = self.signal_processor.process_signals(df)
        
        # DASHBOARD TUNING: Artificial boost to relationship/entropy signals 
        # to encourage more complex visualizations (Scatter/Network/Treemap)
        signals['relationship_density'] = min(1.0, signals['relationship_density'] * 1.2)
        signals['entropy'] = min(1.0, signals['entropy'] * 1.1)

        # 2. Compute Visual Forces
        forces = self.force_engine.compute_forces(signals)
        
        # 3. Resolve Visual Grammar
        col_info = {
            "datetime": self.signal_processor._detect_datetime_cols(df),
            "numeric": df.select_dtypes(include=[np.number]).columns.tolist(),
            "categorical": df.select_dtypes(include=['object', 'category']).columns.tolist()
        }
        
        # Dashboard wants MORE items, so we might call resolve multiple times or use a generator
        # For now, we use the standard resolver which returns the dominant strategy
        grammar = self.grammar_resolver.resolve(forces, col_info, len(df))
        
        print(f"   📐 Grammar Strategy: {grammar['strategy']}")

        # 4. Generate Content (Insights & KPIs)
        analysis = self.pattern_detector.analyze(df)
        insights = analysis['insights']
        
        # 5. Compile to Frontend Primitives
        visual_primitives = self._compile_to_primitives(df, grammar, insights, col_info, forces)
        
        # 6. Colors & Layout
        behavior = self.scorer.score(df) 
        color_palette = self.color_engine.derive_palette(df, behavior)
        layout = self.layout_synthesizer.synthesize(df, behavior, mode='dashboard') # Gridier layout
        
        interaction_spec = self._create_interaction_spec()

        return {
            "layout_spec": layout.to_dict(),
            "visual_primitives": visual_primitives,
            "color_palette": color_palette.to_dict(),
            "narrative_elements": [], # No narrative in dashboard
            "behavior_scores": behavior.to_dict(),
            "interaction_spec": interaction_spec,
            "mode": "dashboard",
            "compiler_metadata": {
                "signals": signals,
                "forces": forces.to_dict(),
                "grammar": grammar
            }
        }

    def _compile_to_primitives(self, df, grammar, insights, col_info, forces) -> List[Dict]:
        """
        Map Abstract Grammar -> Concrete Frontend Primitives
        DASHBOARD VERSION: Generates MULTIPLE variations of the grammar.
        """
        primitives = []
        
        # 1. Add Multiple KPIs (Dashboard needs density)
        metrics = self._calculate_key_metrics(df, col_info)
        for i, metric in enumerate(metrics[:4]): # Top 4 metrics
            primitives.append({
                "primitive": "metric_display",
                "title": metric['name'],
                "description": "Exploration Metric",
                "priority": 10 - i,
                "data_binding": {"metric": metric['col'], "value": metric['value']},
                "visual_properties": {
                    "chart_type": "kpi", 
                    "emphasis": 1.0 - (i*0.1), 
                    "formatted_value": metric['formatted']
                }
            })

        # 2. Realize Grammar Primitives (Exploded)
        # We take the grammar rules and try to apply them to MULTIPLE variable combinations
        
        used_cols = set()
        
        for rule in grammar['primitives']:
            # Try to generate up to 3 charts per rule type
            for _ in range(3):
                binding = self._bind_data_to_rule_diverse(df, rule, col_info, used_cols)
                if not binding: break
                
                chart_type = self._map_grammar_to_chart(rule['type'], rule['subtype'])
                
                # Create Primitive
                primitives.append({
                    "primitive": self._map_chart_to_primitive(chart_type),
                    "title": f"{binding['y']} by {binding['x']}".title(),
                    "description": f"Analyzed via {rule['type']}",
                    "priority": int(rule['weight'] * 8),
                    "data_binding": binding,
                    "visual_properties": {
                        "chart_type": chart_type,
                        "emphasis": rule['weight']
                    }
                })
                
                if binding.get('x'): used_cols.add(binding['x'])
                if binding.get('y'): used_cols.add(binding['y'])

        return primitives
    
    def _bind_data_to_rule_diverse(self, df, rule, col_info, used_cols):
        """Find diverse columns that match the grammar rule."""
        binding = {}
        
        # X-Axis
        if rule['encoding'].get('x') == 'temporal':
            if not col_info['datetime']: return None
            binding['x'] = col_info['datetime'][0]
        elif rule['encoding'].get('major') == 'nominal':
            opts = [c for c in col_info['categorical'] if c not in used_cols]
            if not opts: opts = col_info['categorical'] # Reuse allowed if necessary
            if not opts: return None
            binding['x'] = opts[0]
        elif rule['encoding'].get('x') == 'quantitative_1':
             opts = [c for c in col_info['numeric'] if c not in used_cols]
             if not opts: opts = col_info['numeric']
             binding['x'] = opts[0] if opts else None

        # Y-Axis (Quantitative)
        num_opts = [c for c in col_info['numeric'] if 'id' not in c.lower()]
        unused = [c for c in num_opts if c not in used_cols]
        target_col = unused[0] if unused else (num_opts[0] if num_opts else None)
            
        binding['y'] = target_col
        
        # Size/Group
        if 'size' in rule['encoding']:
            binding['x'] = binding.get('x', 'Category')
            binding['y'] = target_col
            
        if not binding.get('y'): return None
        return binding

    def _map_grammar_to_chart(self, g_type, g_subtype):
        # Dashboard favors complexity
        if g_type == "sequential_trace":
            return "area"
        if g_type == "comparative_field":
            return "bar" 
        if g_type == "partition_field":
            return "sunburst" if g_subtype == "rect" else "treemap" # Swapped for variety
        if g_type == "relational_constellation":
            return "network"
        return "bar"

    def _map_chart_to_primitive(self, chart_type):
        mapping = {
            "area": "trend_carrier", "line": "trend_carrier",
            "bar": "comparison_field", "column": "comparison_field",
            "treemap": "treemap", "sunburst": "treemap",
            "network": "network", "scatter": "relationship_mapper"
        }
        return mapping.get(chart_type, "comparison_field")

    def _calculate_key_metrics(self, df, col_info):
        metrics = []
        for col in col_info['numeric']:
            if any(k in col.lower() for k in ['amount', 'revenue', 'sales', 'profit', 'cost', 'qty', 'quantity']):
                val = df[col].sum()
                metrics.append({
                    "name": col.replace('_', ' ').title(),
                    "col": col,
                    "value": val,
                    "formatted": self._format_number(val)
                })
        return metrics

    def _format_number(self, value: float) -> str:
        if value >= 1_000_000: return f"${value/1_000_000:.1f}M"
        if value >= 1_000: return f"${value/1_000:.1f}K"
        return f"${value:.0f}"

    def _create_interaction_spec(self):
        return {
            "cross_filter": True,
            "drill_down": True,
            "export": True,
            "insights_panel": {"enabled": True}
        }
