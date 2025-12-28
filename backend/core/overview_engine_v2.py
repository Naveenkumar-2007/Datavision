"""
Overview Engine V2 - VISUAL INTELLIGENCE COMPILER
==============================================
Data Signals -> Visual Forces -> Visual Grammar -> Rendering.
NO predefined chart templates.

CRITICAL: Overview and Dashboard generate COMPLETELY DIFFERENT visualizations.
- Overview: Executive summary charts (KPIs, trends, distributions)
- Dashboard: Detailed exploration charts (correlations, comparisons, breakdowns)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
import random

from core.advanced_pattern_detector import AdvancedPatternDetector
from core.data_behavior_scorer import DataBehaviorScorer
from core.color_derivation_engine import ColorDerivationEngine
from core.layout_synthesizer import LayoutSynthesizer

# Compiler Components
from core.data_signal_processor import DataSignalProcessor
from core.visual_force_engine import VisualForceEngine
from core.visual_grammar_resolver import VisualGrammarResolver


class OverviewEngineV2:
    """
    AUTONOMOUS Visual Intelligence Engine.
    
    Key: Overview and Dashboard produce COMPLETELY DIFFERENT charts.
    Not "Dashboard = Overview + More" but truly different perspectives.
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
    
    def generate(self, df: pd.DataFrame, mode: str = 'overview') -> Dict[str, Any]:
        """
        Generate visualizations using Visual Intelligence Compiler.
        
        Overview Mode: Executive summary - trends, key metrics, high-level distribution
        Dashboard Mode: Deep exploration - correlations, comparisons, detailed breakdowns
        """
        print(f"\n🧠 [VISUAL COMPILER] Compiling {mode.upper()} visualizations...")
        
        # 1. Analyze data structure
        col_info = self._analyze_columns(df)
        print(f"   📊 Columns: {len(col_info['numeric'])} numeric, {len(col_info['datetime'])} temporal, {len(col_info['categorical'])} categorical")
        
        # 2. Compute Data Signals
        signals = self.signal_processor.process_signals(df)
        print(f"   📡 Signals: Temporal={signals['temporal_strength']:.2f}, Entropy={signals['entropy']:.2f}")

        # 3. Compute Visual Forces
        forces = self.force_engine.compute_forces(signals)
        print(f"   ⚛️  Forces: Flow={forces.flow:.2f}, Frag={forces.fragmentation:.2f}")

        # 4. Resolve Visual Grammar
        grammar = self.grammar_resolver.resolve(forces, col_info, len(df))
        print(f"   📐 Strategy: {grammar['strategy']}")
        
        # 5. Generate Content
        analysis = self.pattern_detector.analyze(df)
        insights = analysis['insights']
        
        # 6. Compile to Frontend Primitives - DIFFERENT FOR EACH MODE
        if mode == 'overview':
            visual_primitives = self._compile_overview_charts(df, col_info, insights, grammar)
        else:
            visual_primitives = self._compile_dashboard_charts(df, col_info, insights, grammar)
        
        # 7. Layout and Colors
        behavior = self.scorer.score(df) 
        color_palette = self.color_engine.derive_palette(df, behavior)
        layout = self.layout_synthesizer.synthesize(df, behavior, mode=mode)
        
        narrative = self._create_narrative(grammar['strategy'], mode)

        return {
            "layout_spec": layout.to_dict(),
            "visual_primitives": visual_primitives,
            "color_palette": color_palette.to_dict(),
            "narrative_elements": narrative,
            "behavior_scores": behavior.to_dict(),
            "mode": mode,
            "compiler_metadata": {
                "signals": signals,
                "forces": forces.to_dict(),
                "grammar": grammar
            }
        }
    
    def _analyze_columns(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """Analyze and categorize columns."""
        datetime_cols = self.signal_processor._detect_datetime_cols(df)
        numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns.tolist() 
                       if 'id' not in c.lower()]
        categorical_cols = [c for c in df.select_dtypes(include=['object', 'category']).columns.tolist()
                           if c not in datetime_cols]
        
        return {
            "datetime": datetime_cols,
            "numeric": numeric_cols,
            "categorical": categorical_cols
        }
    
    def _compile_overview_charts(self, df, col_info, insights, grammar) -> List[Dict]:
        """
        OVERVIEW MODE: Executive summary perspective.
        
        Focus on:
        - Primary KPI (the most important metric)
        - Time trend (how things are changing)
        - Top-level category distribution
        - Key insight highlight
        
        Uses: Area chart, Pie chart, Single bar comparison
        """
        print(f"\n   📋 [OVERVIEW] Generating executive summary charts...")
        primitives = []
        
        # Find the PRIMARY financial metric
        primary_metric = self._find_primary_metric(df, col_info['numeric'])
        
        # 1. HERO KPI - The single most important number
        if primary_metric:
            primitives.append({
                "primitive": "metric_display",
                "title": primary_metric['name'],
                "description": "Primary business metric",
                "priority": 10,
                "data_binding": {"metric": primary_metric['col'], "value": primary_metric['value']},
                "visual_properties": {
                    "chart_type": "kpi",
                    "emphasis": 1.0,
                    "formatted_value": primary_metric['formatted']
                }
            })
        
        # 2. TIME TREND - Area chart showing primary metric over time
        if col_info['datetime'] and primary_metric:
            primitives.append({
                "primitive": "trend_carrier",
                "title": f"{primary_metric['name']} Trend Over Time",
                "description": self._get_trend_description(df, col_info['datetime'][0], primary_metric['col']),
                "priority": 9,
                "data_binding": {
                    "x": col_info['datetime'][0],
                    "y": primary_metric['col']
                },
                "visual_properties": {
                    "chart_type": "area",
                    "emphasis": 0.9
                }
            })
        
        # 3. PIE CHART - Distribution by primary category
        if col_info['categorical'] and col_info['numeric']:
            # Find the best category for overview (fewer unique values is better for pie)
            best_cat = self._find_best_category_for_pie(df, col_info['categorical'])
            value_col = primary_metric['col'] if primary_metric else col_info['numeric'][0]
            
            primitives.append({
                "primitive": "partition_field",
                "title": f"{value_col.replace('_', ' ').title()} Distribution",
                "description": f"Breakdown across {best_cat}",
                "priority": 8,
                "data_binding": {
                    "x": best_cat,
                    "y": value_col,
                    "group": best_cat
                },
                "visual_properties": {
                    "chart_type": "pie",
                    "emphasis": 0.8
                }
            })
        
        # 4. TOP PERFORMERS - Horizontal bar chart
        if col_info['categorical'] and col_info['numeric']:
            # Use a different category than the pie chart
            other_cats = [c for c in col_info['categorical'] if c != best_cat]
            comp_cat = other_cats[0] if other_cats else col_info['categorical'][0]
            value_col = col_info['numeric'][1] if len(col_info['numeric']) > 1 else col_info['numeric'][0]
            
            primitives.append({
                "primitive": "comparison_field",
                "title": f"Top {comp_cat.replace('_', ' ').title()}s",
                "description": f"Ranked by {value_col.replace('_', ' ')}",
                "priority": 7,
                "data_binding": {
                    "x": comp_cat,
                    "y": value_col
                },
                "visual_properties": {
                    "chart_type": "bar",
                    "emphasis": 0.7
                }
            })
        
        print(f"   ✅ Generated {len(primitives)} overview visualizations")
        return primitives

    def _compile_dashboard_charts(self, df, col_info, insights, grammar) -> List[Dict]:
        """
        DASHBOARD MODE: Detailed exploration perspective.
        
        Focus on:
        - Multiple KPIs (all important metrics)
        - Correlations between metrics
        - Category comparisons (bar charts)
        - Segment breakdowns
        - Scatter plots for relationships
        
        Uses: Bar charts, Scatter plots, Multiple bar comparisons, Detailed breakdowns
        NO Area charts or Pie charts (those are for Overview)
        """
        print(f"\n   📊 [DASHBOARD] Generating detailed exploration charts...")
        primitives = []
        
        # 1. MULTIPLE KPIs - All key metrics
        all_metrics = self._find_all_metrics(df, col_info['numeric'])
        for i, metric in enumerate(all_metrics[:4]):  # Up to 4 KPIs
            primitives.append({
                "primitive": "metric_display",
                "title": metric['name'],
                "description": f"Key Metric #{i+1}",
                "priority": 10 - i,
                "data_binding": {"metric": metric['col'], "value": metric['value']},
                "visual_properties": {
                    "chart_type": "kpi",
                    "emphasis": 1.0 - (i * 0.05),
                    "formatted_value": metric['formatted']
                }
            })
        
        used_combinations = set()
        
        # 2. CATEGORY COMPARISONS - Multiple bar charts for each category
        for cat_col in col_info['categorical'][:4]:  # Up to 4 categories
            for num_col in col_info['numeric'][:2]:  # Compare with top 2 metrics
                combo = f"{cat_col}_{num_col}"
                if combo in used_combinations:
                    continue
                used_combinations.add(combo)
                
                primitives.append({
                    "primitive": "comparison_field",
                    "title": f"{num_col.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}",
                    "description": f"Comparison across {cat_col}",
                    "priority": 7,
                    "data_binding": {
                        "x": cat_col,
                        "y": num_col
                    },
                    "visual_properties": {
                        "chart_type": "bar",
                        "emphasis": 0.7
                    }
                })
                
                if len(primitives) >= 8:  # Limit bar charts
                    break
            if len(primitives) >= 8:
                break
        
        # 3. SCATTER PLOTS - Correlations between numeric columns
        if len(col_info['numeric']) >= 2:
            numeric_pairs = []
            for i, col1 in enumerate(col_info['numeric'][:4]):
                for col2 in col_info['numeric'][i+1:4]:
                    numeric_pairs.append((col1, col2))
            
            for col1, col2 in numeric_pairs[:2]:  # Up to 2 scatter plots
                primitives.append({
                    "primitive": "relationship_mapper",
                    "title": f"{col1.replace('_', ' ').title()} vs {col2.replace('_', ' ').title()}",
                    "description": "Correlation analysis",
                    "priority": 6,
                    "data_binding": {
                        "x": col1,
                        "y": col2
                    },
                    "visual_properties": {
                        "chart_type": "scatter",
                        "emphasis": 0.6
                    }
                })
        
        # 4. TREEMAP - Hierarchical view (different from pie)
        if col_info['categorical'] and col_info['numeric']:
            cat_col = col_info['categorical'][0]
            num_col = col_info['numeric'][0]
            
            primitives.append({
                "primitive": "partition_field",
                "title": f"{num_col.replace('_', ' ').title()} Breakdown",
                "description": f"Hierarchical view by {cat_col}",
                "priority": 5,
                "data_binding": {
                    "x": cat_col,
                    "y": num_col,
                    "group": cat_col
                },
                "visual_properties": {
                    "chart_type": "treemap",
                    "emphasis": 0.5
                }
            })
        
        print(f"   ✅ Generated {len(primitives)} dashboard visualizations")
        return primitives

    def _find_primary_metric(self, df, numeric_cols) -> Dict:
        """Find the single most important metric for Overview."""
        priority_keywords = ['total', 'amount', 'revenue', 'sales', 'profit']
        
        for keyword in priority_keywords:
            for col in numeric_cols:
                if keyword in col.lower():
                    val = df[col].sum()
                    return {
                        "name": col.replace('_', ' ').title(),
                        "col": col,
                        "value": val,
                        "formatted": self._format_number(val)
                    }
        
        # Fallback to first numeric column
        if numeric_cols:
            col = numeric_cols[0]
            val = df[col].sum()
            return {
                "name": col.replace('_', ' ').title(),
                "col": col,
                "value": val,
                "formatted": self._format_number(val)
            }
        
        return None

    def _find_all_metrics(self, df, numeric_cols) -> List[Dict]:
        """Find all metrics for Dashboard KPIs."""
        metrics = []
        
        for col in numeric_cols:
            if 'id' in col.lower():
                continue
                
            val = df[col].sum()
            if val > 0:
                metrics.append({
                    "name": col.replace('_', ' ').title(),
                    "col": col,
                    "value": val,
                    "formatted": self._format_number(val)
                })
        
        # Sort by value descending
        metrics.sort(key=lambda x: x['value'], reverse=True)
        return metrics

    def _find_best_category_for_pie(self, df, categorical_cols) -> str:
        """Find best category for pie chart (3-8 unique values ideal)."""
        best_col = categorical_cols[0]
        best_score = 0
        
        for col in categorical_cols:
            unique_count = df[col].nunique()
            # Score: 5-7 unique values is ideal for pie chart
            if 3 <= unique_count <= 8:
                score = 10 - abs(6 - unique_count)
                if score > best_score:
                    best_score = score
                    best_col = col
        
        return best_col

    def _get_trend_description(self, df, date_col, value_col) -> str:
        """Generate description for trend chart."""
        try:
            df_sorted = df.sort_values(date_col)
            first_half = df_sorted[value_col].iloc[:len(df)//2].mean()
            second_half = df_sorted[value_col].iloc[len(df)//2:].mean()
            
            if second_half > first_half * 1.1:
                return f"{value_col.replace('_', ' ')} showing upward trend"
            elif second_half < first_half * 0.9:
                return f"{value_col.replace('_', ' ')} showing decline"
            else:
                return f"{value_col.replace('_', ' ')} relatively stable"
        except:
            return f"{value_col.replace('_', ' ')} over time"

    def _format_number(self, value: float) -> str:
        """Format numbers for display."""
        if value >= 1_000_000:
            return f"${value/1_000_000:.1f}M"
        if value >= 1_000:
            return f"${value/1_000:.1f}K"
        return f"${value:.0f}"

    def _create_narrative(self, strategy, mode):
        """Create narrative elements based on mode."""
        mode_title = "Executive Summary" if mode == "overview" else "Detailed Dashboard"
        
        return [
            {
                "type": "headline",
                "content": f"Visual Strategy: {strategy.replace('_', ' ').title()}",
                "emphasis": "high"
            },
            {
                "type": "text",
                "content": f"Mode: {mode_title}. Layout derived autonomously from data behavior signals.",
                "emphasis": "low"
            }
        ]
