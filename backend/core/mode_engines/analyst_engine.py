"""
🎯 PRO ANALYST ENGINE v2.0 - DataVision Intelligence
=====================================================

A world-class intelligent data analyst that understands ANY data.

Features:
- 🧠 Smart Query Intent Detection
- 📊 Auto Statistics & Insights
- 🎯 Dynamic Chart Selection
- 📈 Trend & Anomaly Detection
- 🔗 Multi-RAG Strategy Selection
- 💡 Natural Language Insights

Built for DataVision - Not just business data, ANY data!

Author: DataVision Team
Version: 2.0.0
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import re
import json

logger = logging.getLogger(__name__)

# LLM for intelligent responses
try:
    from core.llm import chat as llm_chat
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

# RAG Router
try:
    from core.rag_router import route_query, RAGStrategy
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

# Universal Visualizer
try:
    from core.mode_engines.universal_visualizer import UniversalVisualizer
    VISUALIZER_AVAILABLE = True
except ImportError:
    VISUALIZER_AVAILABLE = False

# Smart Visualization MCP
try:
    from mcp.smart_visualization import smart_visualize, SmartVisualization
    SMART_VIZ_AVAILABLE = True
except ImportError:
    SMART_VIZ_AVAILABLE = False

# Advanced Hybrid Intelligence System
try:
    from core.knowledge_sources import (
        KnowledgeSource, SourceClassifier, HybridResponseCombiner,
        SOURCE_BADGES, classify_query, get_source_badge
    )
    HYBRID_KNOWLEDGE_AVAILABLE = True
except ImportError:
    HYBRID_KNOWLEDGE_AVAILABLE = False

try:
    from core.advanced_rag import AdaptiveRAG, RAGType
    ADVANCED_RAG_AVAILABLE = True
except ImportError:
    ADVANCED_RAG_AVAILABLE = False

try:
    from core.deep_agents import HybridAgent, deep_agent_query
    DEEP_AGENTS_AVAILABLE = True
except ImportError:
    DEEP_AGENTS_AVAILABLE = False

# Intelligent Visualizer (Knowledge Graphs, Mind Maps, 20+ Charts)
try:
    from core.intelligent_visualizer import (
        IntelligentVisualizer, VizType, smart_visualize,
        generate_knowledge_graph, generate_mind_map
    )
    INTELLIGENT_VIZ_AVAILABLE = True
except ImportError:
    INTELLIGENT_VIZ_AVAILABLE = False

# Intelligent Query Processor (Claude-style)
try:
    from core.intelligent_processor import IntelligentQueryProcessor, intelligent_process
    INTELLIGENT_PROCESSOR_AVAILABLE = True
except ImportError:
    INTELLIGENT_PROCESSOR_AVAILABLE = False


# =============================================================================
# QUERY INTENT DETECTION
# =============================================================================

class AnalystIntent(Enum):
    """Types of analysis queries"""
    SUMMARY = "summary"           # "Give me a summary"
    AGGREGATION = "aggregation"   # "Total sales", "Average price"
    COMPARISON = "comparison"     # "Compare A vs B"
    TREND = "trend"               # "Show trend over time"
    DISTRIBUTION = "distribution" # "Distribution of X"
    CORRELATION = "correlation"   # "Relationship between X and Y"
    RANKING = "ranking"           # "Top 10", "Best performing"
    FILTERING = "filtering"       # "Show where X > Y"
    OUTLIERS = "outliers"         # "Find anomalies"
    BREAKDOWN = "breakdown"       # "Sales by category"
    COUNT = "count"               # "How many"
    PERCENTAGE = "percentage"     # "What percent"
    GROWTH = "growth"             # "Growth rate"
    FORECAST = "forecast"         # "Predict next month"
    GENERAL = "general"           # General question


@dataclass
class QueryAnalysis:
    """Result of analyzing a user query"""
    intent: AnalystIntent
    confidence: float
    target_columns: List[str]
    group_by: Optional[str]
    time_column: Optional[str]
    aggregation: Optional[str]  # sum, mean, count, etc.
    filter_conditions: List[str]
    chart_suggestion: str
    wants_chart: bool = False    # User explicitly asked for chart
    wants_brief: bool = False    # User wants short answer


def detect_analyst_intent(query: str, df: pd.DataFrame = None) -> QueryAnalysis:
    """
    Intelligently detect what the user wants to analyze.
    Returns structured analysis of the query.
    """
    q = query.lower().strip()
    columns = list(df.columns) if df is not None else []
    columns_lower = [c.lower() for c in columns]
    
    # Intent patterns
    intent_patterns = {
        AnalystIntent.SUMMARY: [
            r'summar', r'overview', r'describe', r'tell me about',
            r'what.*data', r'explain.*data'
        ],
        AnalystIntent.AGGREGATION: [
            r'total', r'sum of', r'average', r'mean', r'median',
            r'minimum', r'maximum', r'count'
        ],
        AnalystIntent.COMPARISON: [
            r'compare', r'versus', r' vs ', r'difference between',
            r'higher than', r'lower than', r'better than'
        ],
        AnalystIntent.TREND: [
            r'trend', r'over time', r'by month', r'by year', r'by day',
            r'growth', r'decline', r'change over'
        ],
        AnalystIntent.DISTRIBUTION: [
            r'distribution', r'spread', r'histogram', r'frequency',
            r'how.*distributed'
        ],
        AnalystIntent.CORRELATION: [
            r'correlat', r'relationship', r'related', r'affect',
            r'impact on', r'depends on'
        ],
        AnalystIntent.RANKING: [
            r'top \d+', r'bottom \d+', r'best', r'worst', r'highest',
            r'lowest', r'rank', r'leading'
        ],
        AnalystIntent.FILTERING: [
            r'where', r'filter', r'only.*where', r'show.*where',
            r'greater than', r'less than'
        ],
        AnalystIntent.OUTLIERS: [
            r'outlier', r'anomal', r'unusual', r'extreme', r'abnormal'
        ],
        AnalystIntent.BREAKDOWN: [
            r'by category', r'by type', r'breakdown', r'per',
            r'group by', r'for each'
        ],
        AnalystIntent.COUNT: [
            r'how many', r'count of', r'number of', r'quantity'
        ],
        AnalystIntent.PERCENTAGE: [
            r'percent', r'proportion', r'share', r'ratio', r'%'
        ],
        AnalystIntent.GROWTH: [
            r'growth', r'increase', r'decrease', r'changed by'
        ],
        AnalystIntent.FORECAST: [
            r'predict', r'forecast', r'next month', r'future', r'estimate'
        ]
    }
    
    # Detect intent
    detected_intent = AnalystIntent.GENERAL
    max_confidence = 0.5
    
    for intent, patterns in intent_patterns.items():
        for pattern in patterns:
            if re.search(pattern, q):
                detected_intent = intent
                max_confidence = 0.85
                break
        if max_confidence > 0.8:
            break
    
    # Detect target columns
    target_columns = []
    for col in columns:
        if col.lower() in q or col.lower().replace('_', ' ') in q:
            target_columns.append(col)
    
    # Detect group by column
    group_by = None
    group_patterns = [r'by (\w+)', r'per (\w+)', r'for each (\w+)']
    for pattern in group_patterns:
        match = re.search(pattern, q)
        if match:
            potential_group = match.group(1)
            for col in columns:
                if potential_group in col.lower():
                    group_by = col
                    break
    
    # Detect time column
    time_column = None
    time_keywords = ['date', 'time', 'year', 'month', 'day', 'created', 'updated']
    for col in columns:
        if any(kw in col.lower() for kw in time_keywords):
            time_column = col
            break
    
    # Detect aggregation
    agg_map = {
        'total': 'sum', 'sum': 'sum', 'average': 'mean', 'mean': 'mean',
        'median': 'median', 'count': 'count', 'minimum': 'min',
        'maximum': 'max', 'min': 'min', 'max': 'max'
    }
    aggregation = None
    for word, agg in agg_map.items():
        if word in q:
            aggregation = agg
            break
    
    # Suggest chart type
    chart_map = {
        AnalystIntent.TREND: 'line',
        AnalystIntent.DISTRIBUTION: 'histogram',
        AnalystIntent.COMPARISON: 'bar',
        AnalystIntent.RANKING: 'bar',
        AnalystIntent.BREAKDOWN: 'pie',
        AnalystIntent.CORRELATION: 'scatter',
        AnalystIntent.PERCENTAGE: 'pie',
        AnalystIntent.COUNT: 'bar',
    }
    chart_suggestion = chart_map.get(detected_intent, 'bar')
    
    # Detect if user EXPLICITLY wants a chart
    chart_keywords = ['chart', 'graph', 'plot', 'visualize', 'visualization', 'show me', 'display', 'draw']
    wants_chart = any(kw in q for kw in chart_keywords)
    
    # Detect if user wants brief/short response
    brief_keywords = ['one word', 'brief', 'short', 'single word', 'just tell', 'only answer', 'yes or no', 'just say']
    wants_brief = any(kw in q for kw in brief_keywords)
    
    return QueryAnalysis(
        intent=detected_intent,
        confidence=max_confidence,
        target_columns=target_columns,
        group_by=group_by,
        time_column=time_column,
        aggregation=aggregation,
        filter_conditions=[],
        chart_suggestion=chart_suggestion,
        wants_chart=wants_chart,
        wants_brief=wants_brief
    )


# =============================================================================
# AUTO STATISTICS ENGINE
# =============================================================================

def calculate_auto_statistics(df: pd.DataFrame, analysis: QueryAnalysis) -> Dict[str, Any]:
    """
    Automatically calculate relevant statistics based on the query intent.
    """
    stats = {
        'dataset_info': {
            'rows': len(df),
            'columns': len(df.columns),
            'memory_mb': df.memory_usage(deep=True).sum() / 1024 / 1024
        },
        'computed_metrics': {}
    }
    
    # Get numeric and categorical columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Basic statistics for numeric columns
    if numeric_cols:
        stats['numeric_summary'] = {}
        for col in numeric_cols[:10]:  # Limit to 10 columns
            try:
                stats['numeric_summary'][col] = {
                    'mean': float(df[col].mean()),
                    'median': float(df[col].median()),
                    'std': float(df[col].std()),
                    'min': float(df[col].min()),
                    'max': float(df[col].max()),
                    'missing': int(df[col].isna().sum())
                }
            except:
                pass
    
    # Intent-specific calculations
    if analysis.intent == AnalystIntent.SUMMARY:
        # Full summary
        if numeric_cols:
            total_col = numeric_cols[0]
            stats['computed_metrics']['total'] = float(df[total_col].sum())
            stats['computed_metrics']['average'] = float(df[total_col].mean())
    
    elif analysis.intent == AnalystIntent.AGGREGATION:
        # Perform requested aggregation
        if analysis.target_columns and analysis.aggregation:
            for col in analysis.target_columns:
                if col in df.columns:
                    if analysis.aggregation == 'sum':
                        stats['computed_metrics'][f'total_{col}'] = float(df[col].sum())
                    elif analysis.aggregation == 'mean':
                        stats['computed_metrics'][f'average_{col}'] = float(df[col].mean())
                    elif analysis.aggregation == 'count':
                        stats['computed_metrics'][f'count_{col}'] = int(df[col].count())
    
    elif analysis.intent == AnalystIntent.CORRELATION:
        # Correlation matrix
        if len(numeric_cols) >= 2:
            corr = df[numeric_cols[:5]].corr()
            stats['correlation_matrix'] = corr.to_dict()
    
    elif analysis.intent == AnalystIntent.OUTLIERS:
        # Detect outliers using IQR
        stats['outliers'] = {}
        for col in numeric_cols[:5]:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outlier_count = len(df[(df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)])
            stats['outliers'][col] = {
                'count': int(outlier_count),
                'percentage': float(outlier_count / len(df) * 100)
            }
    
    elif analysis.intent == AnalystIntent.BREAKDOWN:
        # Group by analysis
        if analysis.group_by and analysis.group_by in df.columns:
            breakdown = df.groupby(analysis.group_by).size().to_dict()
            stats['breakdown'] = {str(k): int(v) for k, v in breakdown.items()}
    
    elif analysis.intent == AnalystIntent.RANKING:
        # Top/Bottom N
        if analysis.target_columns:
            col = analysis.target_columns[0]
            if col in df.columns:
                stats['top_10'] = df.nlargest(10, col)[[col]].to_dict()
    
    return stats


# =============================================================================
# CHART GENERATOR
# =============================================================================

def generate_analyst_chart(df: pd.DataFrame, analysis: QueryAnalysis, stats: Dict) -> Optional[Dict]:
    """
    Generate appropriate Plotly chart based on analysis.
    """
    try:
        chart_type = analysis.chart_suggestion
        
        if chart_type == 'bar' and analysis.group_by:
            # Grouped bar chart
            grouped = df.groupby(analysis.group_by).size().head(10)
            return {
                "data": [{
                    "type": "bar",
                    "x": [str(x) for x in grouped.index.tolist()],
                    "y": grouped.values.tolist(),
                    "marker": {"color": "#3b82f6"}
                }],
                "layout": {
                    "title": {"text": f"Count by {analysis.group_by}", "font": {"size": 16}},
                    "xaxis": {"title": analysis.group_by},
                    "yaxis": {"title": "Count"},
                    "paper_bgcolor": "#f8fafc"
                }
            }
        
        elif chart_type == 'histogram' and analysis.target_columns:
            # Histogram
            col = analysis.target_columns[0]
            if col in df.columns:
                return {
                    "data": [{
                        "type": "histogram",
                        "x": df[col].dropna().tolist()[:1000],
                        "marker": {"color": "#8b5cf6"}
                    }],
                    "layout": {
                        "title": {"text": f"Distribution of {col}", "font": {"size": 16}},
                        "xaxis": {"title": col},
                        "yaxis": {"title": "Frequency"},
                        "paper_bgcolor": "#f8fafc"
                    }
                }
        
        elif chart_type == 'line' and analysis.time_column:
            # Time series
            numeric_cols = df.select_dtypes(include=[np.number]).columns[:3]
            if len(numeric_cols) > 0:
                time_sorted = df.sort_values(analysis.time_column).head(100)
                return {
                    "data": [{
                        "type": "scatter",
                        "mode": "lines+markers",
                        "x": time_sorted[analysis.time_column].astype(str).tolist(),
                        "y": time_sorted[numeric_cols[0]].tolist(),
                        "name": numeric_cols[0],
                        "line": {"color": "#10b981"}
                    }],
                    "layout": {
                        "title": {"text": f"{numeric_cols[0]} Over Time", "font": {"size": 16}},
                        "xaxis": {"title": "Time"},
                        "yaxis": {"title": numeric_cols[0]},
                        "paper_bgcolor": "#f8fafc"
                    }
                }
        
        elif chart_type == 'pie' and analysis.group_by:
            # Pie chart
            grouped = df.groupby(analysis.group_by).size().head(8)
            return {
                "data": [{
                    "type": "pie",
                    "labels": [str(x) for x in grouped.index.tolist()],
                    "values": grouped.values.tolist(),
                    "hole": 0.4
                }],
                "layout": {
                    "title": {"text": f"Distribution by {analysis.group_by}", "font": {"size": 16}},
                    "paper_bgcolor": "#f8fafc"
                }
            }
        
        elif chart_type == 'scatter' and len(analysis.target_columns) >= 2:
            # Scatter plot
            col1, col2 = analysis.target_columns[:2]
            if col1 in df.columns and col2 in df.columns:
                sample = df[[col1, col2]].dropna().head(500)
                return {
                    "data": [{
                        "type": "scatter",
                        "mode": "markers",
                        "x": sample[col1].tolist(),
                        "y": sample[col2].tolist(),
                        "marker": {"color": "#ef4444", "opacity": 0.6}
                    }],
                    "layout": {
                        "title": {"text": f"{col1} vs {col2}", "font": {"size": 16}},
                        "xaxis": {"title": col1},
                        "yaxis": {"title": col2},
                        "paper_bgcolor": "#f8fafc"
                    }
                }
        
        # Default: Overview bar chart of numeric means
        numeric_cols = df.select_dtypes(include=[np.number]).columns[:8]
        if len(numeric_cols) > 0:
            means = df[numeric_cols].mean()
            return {
                "data": [{
                    "type": "bar",
                    "x": [str(c)[:15] for c in means.index.tolist()],
                    "y": means.values.tolist(),
                    "marker": {"color": "#6366f1"}
                }],
                "layout": {
                    "title": {"text": "Average Values by Column", "font": {"size": 16}},
                    "xaxis": {"tickangle": -45},
                    "yaxis": {"title": "Mean Value"},
                    "paper_bgcolor": "#f8fafc"
                }
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Chart generation error: {e}")
        return None


# =============================================================================
# PRO ANALYST ENGINE CLASS
# =============================================================================

class ProAnalystEngine:
    """
    🎯 PRO ANALYST ENGINE - DataVision Intelligence
    
    The smartest data analyst that understands ANY data type.
    
    💡 WHEN TO USE:
    - Quick data analysis questions
    - Statistics and aggregations
    - Data exploration
    - Simple visualizations
    
    Features:
    - Smart query intent detection
    - Auto statistics calculation
    - Dynamic chart generation
    - Natural language insights
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.analysis_history = []
    
    def process(
        self,
        query: str,
        context: str = "",
        df: pd.DataFrame = None,
        generate_chart: bool = True
    ) -> Dict[str, Any]:
        """
        Process a data analysis query with full intelligence.
        Uses DYNAMIC routing with visualizations for both data AND AI knowledge.
        """
        result = {
            "answer": "",
            "mode": "analyst",
            "confidence": 0.85,
            "sources": ["Analyst"],
            "chart": None,
            "insights": []
        }
        
        start_time = datetime.now()
        
        # =================================================================
        # 🔄 DYNAMIC ROUTING: Check if query relates to actual data
        # =================================================================
        q_lower = query.lower()
        
        # Get column names from data
        column_names = [col.lower() for col in df.columns] if df is not None and not df.empty else []
        column_names_spaced = [col.replace('_', ' ') for col in column_names]
        
        # Check if query mentions ANY column or data-related term
        data_terms = column_names + column_names_spaced + [
            'my data', 'my ', 'our ', 'the data', 'uploaded', 'dataset',
            'total', 'sum', 'average', 'count', 'column', 'row'
        ]
        
        query_is_about_data = any(term in q_lower for term in data_terms if term)
        
        # =================================================================
        # 🌐 AI KNOWLEDGE PATH - Query is NOT about user's data
        # =================================================================
        
        if not query_is_about_data and df is not None:
            logger.info("🌐 Analyst: Routing to AI KNOWLEDGE (query not about user data)")
            
            if LLM_AVAILABLE:
                try:
                    # Check if visualization requested for AI knowledge
                    wants_viz = any(term in q_lower for term in [
                        'chart', 'graph', 'diagram', 'visualize', 'show me', 'draw',
                        'compare', 'breakdown', 'distribution', 'pie', 'bar'
                    ])
                    
                    if wants_viz:
                        ai_prompt = f"""You are a helpful AI assistant.

Answer this question and provide data that could be visualized:

{query}

Format your response with:
1. A clear answer
2. If applicable, provide key points with numbers that could be charted

Example format for chartable data:
- Category A: 40%
- Category B: 30%
- Category C: 20%
- Category D: 10%"""
                    else:
                        ai_prompt = f"""You are a helpful AI assistant with broad knowledge.

Answer this question clearly and helpfully:

{query}

Provide a clear, accurate, and informative response. Use bullet points if helpful."""

                    llm_response = llm_chat(ai_prompt, temperature=0.7, max_tokens=600)
                    
                    result["answer"] = f"""## 🌐 AI Knowledge

{llm_response}

---
*💡 This is general AI knowledge. For analysis of YOUR data, ask about specific columns like {', '.join(column_names[:3]) if column_names else 'your metrics'}.*"""
                    
                    result["sources"] = ["AI Knowledge"]
                    result["confidence"] = 0.85
                    
                except Exception as e:
                    logger.error(f"AI Knowledge error: {e}")
                    result["answer"] = "🌐 I can help with that! Please ask your question again."
            else:
                result["answer"] = "🌐 AI Knowledge is not available. Please configure LLM."
            
            exec_time = (datetime.now() - start_time).total_seconds()
            result["execution_time"] = f"{exec_time:.2f}s"
            return result
        
        # =================================================================
        # 📊 DATA PATH - Query IS about user's data
        # =================================================================
        
        logger.info("📊 Analyst: Routing to DATA ANALYSIS")
        
        # Check if we have data
        if df is None or df.empty:
            result["answer"] = self._no_data_response(query)
            return result
        
        # Analyze the query
        analysis = detect_analyst_intent(query, df)
        logger.info(f"🎯 Analyst Intent: {analysis.intent.value} (conf: {analysis.confidence:.0%})")
        
        # Calculate statistics
        stats = calculate_auto_statistics(df, analysis)
        
        # Generate chart ONLY if user explicitly requested
        chart = None
        smart_viz_result = None
        if generate_chart and analysis.wants_chart:
            # Try LLM visualizer first (dynamic chart generation like Claude)
            try:
                from core.llm_visualizer import llm_visualize
                viz_result = llm_visualize(df, query, self.user_id)
                if viz_result.get("success") and viz_result.get("chart"):
                    chart = viz_result.get("chart")
                    smart_viz_result = viz_result
                    logger.info(f"📊 LLM Chart: {viz_result.get('chart_type')}")
            except Exception as e:
                logger.warning(f"LLM visualizer error: {e}")
            
            # Fallback to SmartVisualization
            if not chart and SMART_VIZ_AVAILABLE:
                try:
                    smart_viz_result = smart_visualize(self.user_id, query, df)
                    if smart_viz_result.get("success"):
                        chart = smart_viz_result.get("chart")
                        logger.info(f"📊 Smart Chart: {smart_viz_result.get('visualization_type')}")
                except Exception as e:
                    logger.warning(f"SmartViz error: {e}")
            
            # Final fallback to rule-based chart
            if not chart:
                chart = generate_analyst_chart(df, analysis, stats)
            
            logger.info(f"📊 Chart generated: {analysis.chart_suggestion}")
        
        # Generate intelligent response
        response = self._generate_response(query, df, analysis, stats, context)
        
        # Build final result
        result["answer"] = response
        result["confidence"] = analysis.confidence
        result["chart"] = chart
        result["query_analysis"] = {
            "intent": analysis.intent.value,
            "target_columns": analysis.target_columns,
            "group_by": analysis.group_by,
            "aggregation": analysis.aggregation
        }
        
        # Add visualization recommendations if available
        if smart_viz_result:
            result["viz_type"] = smart_viz_result.get("visualization_type")
            result["viz_recommendations"] = smart_viz_result.get("recommendations", [])
        
        # EMBED CHART IN RESPONSE TEXT - Critical for frontend rendering
        if chart and analysis.wants_chart:
            # Embed chart JSON in response so frontend can render it
            if isinstance(chart, dict) and 'data' in chart and 'layout' in chart:
                import json
                chart_json = json.dumps(chart, default=str)
                result["answer"] += f"\n\n```plotly_chart\n{chart_json}\n```"
            else:
                viz_type = smart_viz_result.get("visualization_type", "chart") if smart_viz_result else "chart"
                result["answer"] += f"\n\n*📊 {viz_type.replace('_', ' ').title()} visualization generated.*"
            result["visualization"] = chart
        
        # Execution time
        exec_time = (datetime.now() - start_time).total_seconds()
        result["execution_time"] = f"{exec_time:.2f}s"
        
        return result
    
    def _generate_response(
        self,
        query: str,
        df: pd.DataFrame,
        analysis: QueryAnalysis,
        stats: Dict,
        context: str
    ) -> str:
        """
        Generate data-focused response.
        Note: AI Knowledge routing is now handled in process() method.
        """
        
        # Build data summary for LLM
        data_summary = f"""
Dataset: {stats['dataset_info']['rows']} rows, {stats['dataset_info']['columns']} columns

"""
        
        # Add computed metrics
        if 'computed_metrics' in stats and stats['computed_metrics']:
            data_summary += "**Key Metrics:**\n"
            for key, value in stats['computed_metrics'].items():
                if isinstance(value, float):
                    data_summary += f"- {key.replace('_', ' ').title()}: {value:,.2f}\n"
                else:
                    data_summary += f"- {key.replace('_', ' ').title()}: {value}\n"
        
        # Add numeric summary
        if 'numeric_summary' in stats:
            data_summary += "\n**Column Statistics:**\n"
            for col, col_stats in list(stats['numeric_summary'].items())[:5]:
                data_summary += f"- **{col}**: mean={col_stats['mean']:,.2f}, "
                data_summary += f"min={col_stats['min']:,.2f}, max={col_stats['max']:,.2f}\n"
        
        # Add breakdown if available
        if 'breakdown' in stats:
            data_summary += "\n**Breakdown:**\n"
            for key, value in list(stats['breakdown'].items())[:5]:
                data_summary += f"- {key}: {value:,}\n"
        
        # Use LLM to generate data-based response
        if LLM_AVAILABLE:
            if analysis.wants_brief:
                prompt = f"""Answer based on ONLY this data. Be brief.

Question: {query}

Data: {data_summary}

Give a SHORT, direct answer."""
            else:
                prompt = f"""You are a data analyst. Answer based on the user's actual data.

Question: {query}

📊 USER'S DATA:
{data_summary}

{context if context else ''}

Provide insights from the data. Be specific with actual values."""

            try:
                max_tokens = 50 if analysis.wants_brief else 500
                llm_response = llm_chat(prompt, temperature=0.3, max_tokens=max_tokens)
                
                if analysis.wants_brief:
                    return llm_response.strip()
                
                return f"## 📊 Analysis\n\n📊 **From Your Data:**\n\n{llm_response}"
                
            except Exception as e:
                logger.error(f"LLM error: {e}")
        
        # Fallback response
        return f"## 📊 Analysis\n\n📊 **From Your Data:**\n\n{data_summary}"
    
    def _no_data_response(self, query: str) -> str:
        """Response when no data is available."""
        return """## 📊 Analyst

I need data to analyze! Please:

1. **Upload a file** in the Data Hub
2. **Use a file** from your uploads

Once you have data loaded, I can:
- 📈 Summarize your data
- 🔢 Calculate statistics
- 📊 Generate visualizations
- 🔍 Find patterns and insights

*Upload some data and ask me anything!*
"""


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def analyst_response(
    user_id: str,
    query: str,
    context: str = "",
    df: pd.DataFrame = None
) -> Dict[str, Any]:
    """Quick function for analyst response."""
    engine = ProAnalystEngine(user_id)
    return engine.process(query, context, df)


def analyst_response_sync(
    user_id: str,
    query: str,
    context: str = "",
    df: pd.DataFrame = None
) -> Dict[str, Any]:
    """Synchronous analyst response for compatibility."""
    return analyst_response(user_id, query, context, df)


# Alias for backwards compatibility
AnalystEngine = ProAnalystEngine

__all__ = ['ProAnalystEngine', 'AnalystEngine', 'analyst_response', 'analyst_response_sync']
