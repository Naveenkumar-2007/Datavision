"""
Intelligent Chart Selection System
====================================
Scores each chart type for each insight and picks best matches.

NO hardcoded rules - uses scoring matrix based on:
- Data type compatibility
- Insight type matching
- Cardin

ality appropriateness
- Complexity handling
"""

import numpy as np
from typing import Dict, List, Any, Tuple


class ChartSelector:
    """
    Intelligently selects chart types for insights.
    Uses scoring system (not hardcoded rules).
    
    NEW: Also detects user intent from natural language queries.
    """
    
    # 30+ Chart Types Available
    CHART_TYPES = [
        # Basic (7)
        "line", "bar", "area", "scatter", "pie", "donut", "table",
        
        # Advanced (10)
        "stacked_bar", "grouped_bar", "bubble", "radar", "heatmap",
        "box_plot", "violin", "histogram", "density", "funnel",
        
        # Premium (8)
        "sankey", "sunburst", "treemap", "network", "waterfall",
        "gantt", "timeline", "parallel",
        
        # Statistical (5)
        "ridge", "stream", "hexbin", "voronoi", "chord"
    ]
    
    # Chart Intent Detection from User Query
    CHART_INTENT_MAP = {
        # Explicit chart mentions
        "pie chart": ["pie"],
        "pie": ["pie"],
        "donut": ["donut"],
        "bar chart": ["bar"],
        "bar graph": ["bar"],
        "line chart": ["line"],
        "line graph": ["line"],
        "scatter": ["scatter"],
        "scatter plot": ["scatter"],
        "bubble": ["bubble"],
        "heatmap": ["heatmap"],
        "heat map": ["heatmap"],
        "treemap": ["treemap"],
        "tree map": ["treemap"],
        "sunburst": ["sunburst"],
        "histogram": ["histogram"],
        "box plot": ["box_plot"],
        "violin": ["violin"],
        "funnel": ["funnel"],
        "waterfall": ["waterfall"],
        "sankey": ["sankey"],
        "radar": ["radar"],
        "area chart": ["area"],
        
        # Semantic intents
        "trend": ["line", "area"],
        "trends": ["line", "area"],
        "over time": ["line", "area"],
        "time series": ["line", "area"],
        "growth": ["line", "area"],
        "compare": ["bar", "grouped_bar"],
        "comparison": ["bar", "grouped_bar"],
        "vs": ["bar", "grouped_bar"],
        "versus": ["bar", "grouped_bar"],
        "breakdown": ["pie", "donut", "treemap", "sunburst"],
        "distribution": ["histogram", "box_plot", "violin"],
        "spread": ["histogram", "box_plot"],
        "outliers": ["box_plot", "scatter"],
        "anomalies": ["box_plot", "scatter"],
        "relationship": ["scatter", "bubble", "heatmap"],
        "correlation": ["scatter", "heatmap"],
        "flow": ["sankey"],
        "hierarchy": ["treemap", "sunburst"],
        "composition": ["pie", "donut", "stacked_bar"],
        "proportion": ["pie", "donut"],
        "percentage": ["pie", "donut"],
        "geographic": ["choropleth"],
        "map": ["choropleth"],
        "location": ["choropleth"],
        "top": ["bar", "horizontal_bar"],
        "bottom": ["bar", "horizontal_bar"],
        "ranking": ["bar", "horizontal_bar"],
    }
    
    # Dynamic Color Palettes for Variety
    COLOR_PALETTES = [
        # Teal/Cyan (Default)
        ['#14b8a6', '#0d9488', '#0f766e', '#06b6d4', '#0891b2', '#22d3ee'],
        # Purple/Violet
        ['#8b5cf6', '#7c3aed', '#6d28d9', '#a855f7', '#9333ea', '#c084fc'],
        # Orange/Amber
        ['#f97316', '#ea580c', '#fb923c', '#f59e0b', '#fbbf24', '#fcd34d'],
        # Pink/Rose
        ['#ec4899', '#db2777', '#f472b6', '#f43f5e', '#fb7185', '#fda4af'],
        # Blue/Indigo
        ['#3b82f6', '#2563eb', '#1d4ed8', '#6366f1', '#4f46e5', '#818cf8'],
        # Green/Emerald
        ['#10b981', '#059669', '#047857', '#22c55e', '#16a34a', '#4ade80'],
    ]
    
    def __init__(self):
        self._color_index = 0  # Rotate colors
    
    def detect_chart_intent(self, query: str) -> list:
        """
        Detect what chart type(s) the user wants from their query.
        
        Args:
            query: Natural language query from user
            
        Returns:
            List of chart types (empty if no specific intent detected)
        """
        query_lower = query.lower()
        detected_charts = []
        
        # Check each intent pattern
        for pattern, charts in self.CHART_INTENT_MAP.items():
            if pattern in query_lower:
                for chart in charts:
                    if chart not in detected_charts:
                        detected_charts.append(chart)
        
        return detected_charts
    
    def get_dynamic_colors(self, seed: str = None) -> list:
        """
        Get a color palette. Rotates automatically for variety.
        If seed provided, uses deterministic selection based on seed.
        """
        if seed:
            # Deterministic based on seed (e.g., query hash)
            idx = hash(seed) % len(self.COLOR_PALETTES)
        else:
            # Rotate through palettes
            idx = self._color_index
            self._color_index = (self._color_index + 1) % len(self.COLOR_PALETTES)
        
        return self.COLOR_PALETTES[idx]
    
    def select_charts(self, insights: List[Dict], column_info: Dict, target_count: int) -> List[Dict]:
        """
        Select best chart types for insights.
        
        Args:
            insights: List of discovered patterns
            column_info: Column type information
            target_count: How many charts to generate
        
        Returns:
            List of chart specifications
        """
        print(f"\n📊 Selecting charts for {len(insights)} insights...")
        
        chart_candidates = []
        
        # Score each chart type for each insight
        for insight in insights[:min(len(insights), target_count * 2)]:
            scores = self._score_charts_for_insight(insight, column_info)
            
            # Get top 3 scored charts for this insight
            top_charts = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
            
            for chart_type, score in top_charts:
                if score > 0.3:  # Minimum threshold
                    chart_candidates.append({
                        "insight": insight,
                        "chart_type": chart_type,
                        "score": score,
                        "priority": insight['confidence'] * score
                    })
        
        # Sort by priority and select top N
        chart_candidates.sort(key=lambda x: x['priority'], reverse=True)
        
        # Ensure diversity - don't use same chart type too many times
        selected = []
        chart_type_counts = {}
        
        for candidate in chart_candidates:
            if len(selected) >= target_count:
                break
            
            chart_type = candidate['chart_type']
            count = chart_type_counts.get(chart_type, 0)
            
            # Allow max 3 of same type (unless target_count > 20)
            max_same = 3 if target_count <= 20 else 5
            
            if count < max_same:
                selected.append(self._create_chart_spec(candidate))
                chart_type_counts[chart_type] = count + 1
        
        print(f"   ✅ Selected {len(selected)} charts")
        for i, chart in enumerate(selected[:5]):
            print(f"      {i+1}. {chart['chart_type']}: {chart['title']}")
        
        return selected
    
    def _score_charts_for_insight(self, insight: Dict, column_info: Dict) -> Dict[str, float]:
        """
        Score each chart type for an insight.
        Returns: {chart_type: score}
        """
        scores = {}
        
        insight_type = insight.get('type', '')
        subtype = insight.get('subtype', '')
        columns = insight.get('columns', [insight.get('column')])
        confidence = insight.get('confidence', 0.5)
        
        for chart_type in self.CHART_TYPES:
            score = 0.0
            
            # === COMPATIBILITY CHECKS ===
            # These are hard requirements, not preferences
            
            if not self._is_compatible(chart_type, columns, column_info):
                scores[chart_type] = 0.0
                continue
            
            # === INSIGHT TYPE MATCHING ===
            
            if insight_type == 'trend':
                if chart_type in ['line', 'area', 'stream']:
                    score += 0.6
                elif chart_type in ['bar', 'waterfall']:
                    score += 0.3
            
            elif insight_type == 'seasonality':
                if chart_type in ['line', 'area', 'ridge']:
                    score += 0.6
                elif chart_type == 'heatmap':
                    score += 0.4
            
            elif insight_type == 'correlation':
                if chart_type in ['scatter', 'bubble', 'hexbin']:
                    score += 0.7
                elif chart_type in ['heatmap', 'parallel']:
                    score += 0.4
            
            elif insight_type == 'outlier':
                if chart_type in ['box_plot', 'violin', 'scatter']:
                    score += 0.7
                elif chart_type in ['histogram', 'density']:
                    score += 0.3
            
            elif insight_type == 'pareto' or insight_type == 'concentration':
                if chart_type in ['bar', 'waterfall']:
                    score += 0.7
                elif chart_type in ['pie', 'donut', 'treemap']:
                    score += 0.5
            
            elif insight_type == 'clustering':
                if chart_type in ['scatter', 'bubble', 'network']:
                    score += 0.7
                elif chart_type in ['treemap', 'sunburst']:
                    score += 0.4
            
            elif insight_type == 'distribution':
                if chart_type in ['histogram', 'density', 'violin']:
                    score += 0.7
                elif chart_type in ['box_plot', 'ridge']:
                    score += 0.4
            
            # === CARDINALITY BONUS ===
            
            if isinstance(columns, list) and len(columns) > 0:
                col = columns[0]
                if col in column_info.get('categorical', []):
                    cardinality = self._estimate_cardinality(col, column_info)
                    
                    if cardinality <= 6:
                        if chart_type in ['pie', 'donut', 'radar']:
                            score += 0.3
                    elif cardinality <= 12:
                        if chart_type in ['bar', 'grouped_bar']:
                            score += 0.3
                    else:
                        if chart_type in ['heatmap', 'treemap', 'table']:
                            score += 0.3
            
            # === COMPLEXITY BONUS ===
            
            if confidence > 0.8:  # High confidence insight
                if chart_type in ['sankey', 'network', 'sunburst']:
                    score += 0.2
            
            # === TEMPORAL BONUS ===
            
            if isinstance(columns, list):
                has_temporal = any(col in column_info.get('datetime', []) for col in columns)
                if has_temporal:
                    if chart_type in ['line', 'area', 'gantt', 'timeline']:
                        score += 0.3
            
            scores[chart_type] = min(score, 1.0)
        
        return scores
    
    def _is_compatible(self, chart_type: str, columns: List[str], column_info: Dict) -> bool:
        """
        Check if chart type is compatible with data types.
        Hard requirement - returns False if incompatible.
        """
        if not columns:
            return False
        
        numeric_cols = column_info.get('numeric', [])
        categorical_cols = column_info.get('categorical', [])
        datetime_cols = column_info.get('datetime', [])
        
        # Scatter/bubble need 2 numeric
        if chart_type in ['scatter', 'bubble', 'hexbin']:
            numeric_count = sum(1 for c in columns if c in numeric_cols)
            return numeric_count >= 2
        
        # Heatmap needs 2 dimensions
        if chart_type == 'heatmap':
            return len(columns) >= 2
        
        # Pie/donut need 1 categorical or numeric
        if chart_type in ['pie', 'donut']:
            return len(columns) >= 1
        
        # Most charts can work with any data
        return True
    
    def _estimate_cardinality(self, col: str, column_info: Dict) -> int:
        """Estimate unique value count (rough approximation)."""
        # TODO: Pass actual cardinality from data profiler
        return 10  # Default estimate
    
    def _create_chart_spec(self, candidate: Dict) -> Dict:
        """Create full chart specification."""
        insight = candidate['insight']
        chart_type = candidate['chart_type']
        
        # Extract data bindings from insight
        columns = insight.get('columns', [insight.get('column')])
        if not isinstance(columns, list):
            columns = [columns]
        
        return {
            "chart_type": chart_type,
            "title": insight['description'],
            "data_binding": {
                "columns": columns,
                "insight_type": insight['type']
            },
            "visual_properties": {
                "priority": candidate['priority'],
                "confidence": insight['confidence']
            },
            "metadata": insight.get('metadata', {})
        }
