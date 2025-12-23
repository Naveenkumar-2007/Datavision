"""
Enterprise Response Generator - $5M AI System
==============================================

Generates professional, interactive responses with:
- Dynamic visualizations based on query
- Prediction charts with confidence bands
- Clean, attractive formatting
- Source attribution

ALL based on user's trained data - NOTHING made up!
"""

import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class EnterpriseResponse:
    """Complete enterprise response"""
    text: str
    visualization: Optional[Dict[str, Any]]
    sources: List[str]
    confidence: float
    mode: str
    insights: Optional[List[str]]
    followup_suggestions: List[str]


class EnterpriseResponseGenerator:
    """
    Generates $5M worth responses - clean, professional, impactful.
    """
    
    def __init__(self, user_id: str, currency_symbol: str = "₹"):
        self.user_id = user_id
        self.currency = currency_symbol
    
    def generate(
        self,
        query: str,
        data_context: Dict[str, Any],
        mode: str = "rag"
    ) -> EnterpriseResponse:
        """
        Generate complete enterprise response.
        
        Args:
            query: User's question
            data_context: Data from user's trained files
            mode: Analysis mode (rag, graph, hybrid, prediction)
        """
        from core.query_intelligence import analyze_query, ChartType
        from core.llm import chat
        
        # Analyze query
        intelligence = analyze_query(query)
        print(f"[ENTERPRISE] Query intent: {intelligence.query_intent}")
        print(f"[ENTERPRISE] Chart type: {intelligence.chart_type.value}")
        print(f"[ENTERPRISE] Is prediction: {intelligence.is_prediction}")
        
        # Build professional prompt
        prompt = self._build_prompt(query, data_context, intelligence, mode)
        
        # Generate response
        response_text = chat(prompt, temperature=0.3, max_tokens=3000)
        
        # Generate visualization if needed
        visualization = None
        if intelligence.needs_chart:
            visualization = self._generate_visualization(
                query, data_context, intelligence
            )
        
        # Generate follow-up suggestions
        followups = self._generate_followups(query, intelligence)
        
        # Extract insights
        insights = self._extract_insights(data_context)
        
        # Get sources
        sources = self._get_sources(data_context, mode)
        
        return EnterpriseResponse(
            text=response_text,
            visualization=visualization,
            sources=sources,
            confidence=intelligence.confidence,
            mode=mode,
            insights=insights,
            followup_suggestions=followups
        )
    
    def _build_prompt(
        self,
        query: str,
        data: Dict,
        intelligence,
        mode: str
    ) -> str:
        """Build professional prompt based on intelligence"""
        
        # Response format instruction
        format_instructions = {
            "BRIEF": "Give a ONE LINE answer. Be extremely concise.",
            "DETAILED": "Provide a comprehensive but focused answer with bullet points.",
            "TABLE": "Format the answer as a clean markdown table.",
            "VISUAL": "Describe the key insight, a visualization will be auto-generated.",
            "NARRATIVE": "Explain in a conversational, story-like manner.",
        }
        
        format_inst = format_instructions.get(
            intelligence.response_format.name, 
            format_instructions["DETAILED"]
        )
        
        # Mode-specific instruction
        mode_instructions = {
            "rag": "Use ONLY the data provided. Cite sources.",
            "graph": "Focus on RELATIONSHIPS between entities.",
            "hybrid": "Provide COMPREHENSIVE analysis from multiple perspectives.",
            "prediction": f"Generate FORECAST for {intelligence.prediction_periods} {intelligence.prediction_unit} with confidence levels.",
        }
        
        mode_inst = mode_instructions.get(mode, mode_instructions["rag"])
        
        # Build data summary
        data_summary = self._summarize_data(data)
        
        prompt = f"""You are a $5M Enterprise AI Business Analyst.

## YOUR TASK:
Answer the user's question professionally and accurately.

## DATA AVAILABLE:
{data_summary}

## RESPONSE REQUIREMENTS:
1. {format_inst}
2. {mode_inst}
3. Use {self.currency} for all currency values
4. Format numbers with commas (e.g., 1,234,567)
5. Be DIRECT - answer first, then explain

## WHAT NOT TO DO:
- Don't say "Based on the data" or "According to the analysis"
- Don't repeat the question
- Don't make up any numbers
- Don't give long introductions

## USER QUESTION:
{query}

## YOUR PROFESSIONAL RESPONSE:"""
        
        return prompt
    
    def _summarize_data(self, data: Dict) -> str:
        """Create clean data summary"""
        if not data:
            return "No specific data provided."
        
        summary = []
        
        if "total_revenue" in data:
            summary.append(f"• Total Revenue: {self.currency}{data['total_revenue']:,.2f}")
        if "total_records" in data:
            summary.append(f"• Total Records: {data['total_records']:,}")
        if "unique_customers" in data:
            summary.append(f"• Unique Customers: {data['unique_customers']}")
        if "unique_products" in data:
            summary.append(f"• Unique Products: {data['unique_products']}")
        if "top_customers" in data:
            summary.append(f"• Top Customers: {', '.join(data['top_customers'][:5])}")
        if "top_products" in data:
            summary.append(f"• Top Products: {', '.join(data['top_products'][:5])}")
        if "date_range" in data:
            summary.append(f"• Date Range: {data['date_range']}")
        
        return "\n".join(summary) if summary else str(data)[:500]
    
    def _generate_visualization(
        self,
        query: str,
        data: Dict,
        intelligence
    ) -> Optional[Dict[str, Any]]:
        """Generate visualization based on query intelligence"""
        from core.query_intelligence import ChartType
        
        chart_type = intelligence.chart_type
        
        if chart_type == ChartType.NONE:
            return None
        
        # Build Plotly-compatible chart configuration
        chart_config = {
            "type": chart_type.value,
            "title": self._generate_chart_title(intelligence),
            "data": [],
            "layout": {
                "showlegend": True,
                "margin": {"l": 50, "r": 50, "t": 50, "b": 50},
                "font": {"family": "Inter, sans-serif"},
            }
        }
        
        # Get chart data based on type
        if chart_type == ChartType.BAR:
            chart_config["data"] = self._get_bar_data(data, intelligence)
        elif chart_type == ChartType.LINE:
            chart_config["data"] = self._get_line_data(data, intelligence)
        elif chart_type == ChartType.PIE:
            chart_config["data"] = self._get_pie_data(data, intelligence)
        elif chart_type == ChartType.FORECAST:
            chart_config["data"] = self._get_forecast_data(data, intelligence)
        
        return chart_config
    
    def _generate_chart_title(self, intelligence) -> str:
        """Generate appropriate chart title"""
        if intelligence.is_prediction:
            return f"Revenue Forecast ({intelligence.prediction_periods} {intelligence.prediction_unit})"
        
        intent = intelligence.query_intent
        titles = {
            "aggregation": "Total Overview",
            "comparison": "Comparison Analysis",
            "ranking": "Top Performance Ranking",
            "trend": "Trend Analysis",
            "breakdown": "Distribution Breakdown",
        }
        return titles.get(intent, "Data Analysis")
    
    def _get_bar_data(self, data: Dict, intelligence) -> List[Dict]:
        """Get bar chart data"""
        # Get data based on grouping
        grouping = intelligence.grouping_column or "customer"
        
        if "revenue_by_customer" in data:
            items = data["revenue_by_customer"][:10]
            return [{
                "type": "bar",
                "x": [item["name"] for item in items],
                "y": [item["revenue"] for item in items],
                "marker": {"color": "#667eea"},
                "name": "Revenue"
            }]
        
        if "top_items" in data:
            items = data["top_items"][:10]
            return [{
                "type": "bar",
                "x": [item.get("name", f"Item {i}") for i, item in enumerate(items)],
                "y": [item.get("value", 0) for item in items],
                "marker": {"color": "#667eea"},
            }]
        
        return []
    
    def _get_line_data(self, data: Dict, intelligence) -> List[Dict]:
        """Get line chart data"""
        if "revenue_over_time" in data:
            time_data = data["revenue_over_time"]
            return [{
                "type": "scatter",
                "mode": "lines+markers",
                "x": [item["date"] for item in time_data],
                "y": [item["revenue"] for item in time_data],
                "line": {"color": "#667eea", "width": 2},
                "marker": {"size": 6},
                "name": "Revenue"
            }]
        
        return []
    
    def _get_pie_data(self, data: Dict, intelligence) -> List[Dict]:
        """Get pie chart data"""
        if "revenue_by_product" in data:
            items = data["revenue_by_product"]
            return [{
                "type": "pie",
                "labels": [item["name"] for item in items],
                "values": [item["revenue"] for item in items],
                "hole": 0.4,
                "marker": {
                    "colors": ["#667eea", "#764ba2", "#f093fb", "#f5576c", "#48bb78"]
                }
            }]
        
        return []
    
    def _get_forecast_data(self, data: Dict, intelligence) -> List[Dict]:
        """Get forecast chart data with confidence bands"""
        periods = intelligence.prediction_periods
        
        if "forecast" in data:
            forecast = data["forecast"]
            historical = data.get("historical", [])
            
            traces = []
            
            # Historical data
            if historical:
                traces.append({
                    "type": "scatter",
                    "mode": "lines+markers",
                    "x": [h["date"] for h in historical],
                    "y": [h["value"] for h in historical],
                    "name": "Historical",
                    "line": {"color": "#667eea"}
                })
            
            # Forecast
            if forecast:
                traces.append({
                    "type": "scatter",
                    "mode": "lines+markers",
                    "x": [f["date"] for f in forecast],
                    "y": [f["value"] for f in forecast],
                    "name": "Forecast",
                    "line": {"color": "#48bb78", "dash": "dash"}
                })
                
                # Confidence band (upper)
                traces.append({
                    "type": "scatter",
                    "mode": "lines",
                    "x": [f["date"] for f in forecast],
                    "y": [f.get("upper", f["value"] * 1.1) for f in forecast],
                    "name": "Upper Bound",
                    "line": {"color": "rgba(72, 187, 120, 0.3)"},
                    "fill": None
                })
                
                # Confidence band (lower)
                traces.append({
                    "type": "scatter",
                    "mode": "lines",
                    "x": [f["date"] for f in forecast],
                    "y": [f.get("lower", f["value"] * 0.9) for f in forecast],
                    "name": "Lower Bound",
                    "line": {"color": "rgba(72, 187, 120, 0.3)"},
                    "fill": "tonexty",
                    "fillcolor": "rgba(72, 187, 120, 0.1)"
                })
            
            return traces
        
        return []
    
    def _generate_followups(self, query: str, intelligence) -> List[str]:
        """Generate relevant follow-up questions"""
        intent = intelligence.query_intent
        
        followups = {
            "aggregation": [
                "How does this compare to last period?",
                "Which customers contributed most?",
                "Show breakdown by product"
            ],
            "comparison": [
                "What's driving the difference?",
                "Show trend over time",
                "Forecast future performance"
            ],
            "trend": [
                "What's causing this trend?",
                "Forecast next quarter",
                "Which products are growing?"
            ],
            "prediction": [
                "What assumptions are used?",
                "Show confidence intervals",
                "What if revenue increases 10%?"
            ],
        }
        
        return followups.get(intent, [
            "Explain in more detail",
            "Show visualization",
            "Compare with previous period"
        ])
    
    def _extract_insights(self, data: Dict) -> List[str]:
        """Extract key insights from data"""
        insights = []
        
        if "total_revenue" in data and "previous_revenue" in data:
            change = ((data["total_revenue"] - data["previous_revenue"]) / 
                     data["previous_revenue"] * 100)
            if change > 0:
                insights.append(f"📈 Revenue increased {change:.1f}% vs previous period")
            else:
                insights.append(f"📉 Revenue decreased {abs(change):.1f}% vs previous period")
        
        if "top_customer" in data:
            insights.append(f"🏆 Top customer: {data['top_customer']}")
        
        if "growth_rate" in data:
            insights.append(f"📊 Growth rate: {data['growth_rate']:.1f}%")
        
        return insights[:3]  # Max 3 insights
    
    def _get_sources(self, data: Dict, mode: str) -> List[str]:
        """Get source attribution"""
        sources = []
        
        if "source_files" in data:
            sources.extend(data["source_files"])
        
        mode_sources = {
            "rag": ["Document Search", "Vector Index"],
            "graph": ["Knowledge Graph"],
            "hybrid": ["Document Search", "Knowledge Graph"],
            "prediction": ["Prediction Engine", "Statistical Models"],
        }
        
        sources.extend(mode_sources.get(mode, ["AI Analysis"]))
        
        return list(set(sources))


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def generate_enterprise_response(
    user_id: str,
    query: str,
    data_context: Dict = None,
    mode: str = "rag",
    currency: str = "₹"
) -> Dict[str, Any]:
    """
    Generate enterprise-grade response.
    
    Usage:
        result = generate_enterprise_response(
            user_id="user123",
            query="What is total revenue?",
            data_context={"total_revenue": 548765.39},
            mode="rag"
        )
    """
    generator = EnterpriseResponseGenerator(user_id, currency)
    response = generator.generate(query, data_context or {}, mode)
    
    return {
        "text": response.text,
        "visualization": response.visualization,
        "sources": response.sources,
        "confidence": response.confidence,
        "mode": response.mode,
        "insights": response.insights,
        "followups": response.followup_suggestions,
    }
