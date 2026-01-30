"""
🧠 INTELLIGENT QUERY PROCESSOR - Claude-Style Understanding
===========================================================

Uses LLM to understand ANY user query and generate appropriate responses.
No hardcoded patterns - fully dynamic interpretation.

Features:
- 🧠 LLM understands natural language queries
- 📊 Dynamic chart generation when requested
- 📈 Data analysis based on user's actual data
- 🌐 General knowledge for non-data queries
- 🔄 Works across ALL modes
"""

import logging
import json
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Try to import LLM
try:
    from core.llm import chat as llm_chat
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logger.warning("LLM not available for query processor")


class IntelligentQueryProcessor:
    """
    🧠 INTELLIGENT QUERY PROCESSOR
    
    Uses AI to understand ANY query and generate appropriate responses.
    This is Claude-style: understand intent, not match patterns.
    """
    
    def __init__(self, user_id: str = None, mode: str = "analyst"):
        self.user_id = user_id
        self.mode = mode
    
    def process(self, query: str, df: pd.DataFrame = None, context: str = "") -> Dict[str, Any]:
        """
        Process ANY query intelligently with Claude-style MCP tools.
        
        Args:
            query: User's natural language query
            df: Optional DataFrame with user's data
            context: Optional context
            
        Returns:
            Dict with answer, chart (if requested), tool_executions, and metadata
        """
        result = {
            "answer": "",
            "chart": None,
            "visualization": None,
            "confidence": 0.85,
            "sources": [],
            "tool_executions": []
        }
        
        if not LLM_AVAILABLE:
            result["answer"] = "LLM not available. Please configure your API key."
            return result
        
        # First, run Claude-style MCPs if applicable
        mcp_result = None
        try:
            from core.claude_mcp import mcp_process
            mcp_result = mcp_process(query, df, self.user_id)
            result["tool_uses"] = mcp_result.get("tool_uses", [])
            result["tool_results"] = mcp_result.get("tool_results", [])
        except ImportError:
            pass  # Claude MCP not available
        except Exception as e:
            logger.warning(f"Claude MCP failed: {e}")
        
        # Get data summary if available
        data_summary = self._get_data_summary(df) if df is not None and not df.empty else None
        
        # Determine what the user wants
        intent = self._understand_intent(query, data_summary)
        
        # Route to appropriate handler
        if intent["wants_chart"]:
            result = self._handle_chart_request(query, df, intent)
        elif intent["is_data_query"] and data_summary:
            result = self._handle_data_query(query, df, data_summary, intent)
        else:
            result = self._handle_general_query(query, context, intent)
        
        # Append MCP results to response if tools were executed
        if mcp_result and mcp_result.get("tool_uses"):
            # Use the answer from MCP if it has content
            if mcp_result.get("answer"):
                result["answer"] = mcp_result["answer"]
            
            result["tool_uses"] = mcp_result.get("tool_uses", [])
            result["tool_results"] = mcp_result.get("tool_results", [])
            
            # Add any charts from MCPs
            for chart_content in mcp_result.get("charts", []):
                if chart_content and "plotly_chart" in str(chart_content):
                    if "plotly_chart" not in result["answer"]:
                        result["answer"] += f"\n\n{chart_content}"
        
        return result
    
    def _understand_intent(self, query: str, data_summary: str = None) -> Dict[str, Any]:
        """Use LLM to understand what the user wants."""
        
        prompt = f"""Analyze this user query and determine their intent.

QUERY: "{query}"

{f'USER HAS DATA: {data_summary[:500]}' if data_summary else 'USER HAS NO DATA'}

Respond with ONLY a JSON object:
{{
    "wants_chart": true/false (does user want a visualization?),
    "chart_type": "bar/line/pie/radar/scatter/heatmap/treemap/sunburst/etc" or null,
    "color_preference": "color name" or null,
    "is_data_query": true/false (is this about the user's data?),
    "data_columns": ["column names mentioned"] or [],
    "aggregation": "sum/mean/count/max/min" or null,
    "group_by": "column name" or null,
    "is_comparison": true/false,
    "is_trend": true/false,
    "summary": "brief description of what user wants"
}}"""

        try:
            response = llm_chat(prompt, temperature=0.1, max_tokens=300)
            
            # Parse JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                intent = json.loads(json_match.group())
                return intent
        except Exception as e:
            logger.warning(f"Intent parsing failed: {e}")
        
        # Fallback intent detection
        q_lower = query.lower()
        return {
            "wants_chart": any(t in q_lower for t in ['chart', 'graph', 'visualize', 'plot', 'show']),
            "chart_type": None,
            "color_preference": None,
            "is_data_query": any(t in q_lower for t in ['my data', 'the data', 'average', 'total', 'count']),
            "data_columns": [],
            "aggregation": None,
            "group_by": None,
            "is_comparison": 'compare' in q_lower,
            "is_trend": 'trend' in q_lower,
            "summary": "General query"
        }
    
    def _handle_chart_request(self, query: str, df: pd.DataFrame, intent: Dict) -> Dict[str, Any]:
        """Handle chart generation requests."""
        result = {
            "answer": "",
            "chart": None,
            "visualization": None,
            "confidence": 0.9,
            "sources": ["Chart Generator"]
        }
        
        if df is None or df.empty:
            result["answer"] = "📊 I'd love to create a chart, but I need data first. Please upload a file."
            return result
        
        try:
            from core.llm_visualizer import llm_visualize
            
            viz_result = llm_visualize(df, query, self.user_id)
            
            if viz_result.get("success") and viz_result.get("chart"):
                chart = viz_result.get("chart")
                chart_type = viz_result.get("chart_type", "chart")
                
                # Generate explanation
                explanation = self._generate_chart_explanation(query, chart_type, df, intent)
                
                # Embed chart in response
                if isinstance(chart, dict) and 'data' in chart and 'layout' in chart:
                    chart_json = json.dumps(chart, default=str)
                    result["answer"] = f"{explanation}\n\n```plotly_chart\n{chart_json}\n```"
                    result["chart"] = chart
                    result["visualization"] = chart
                else:
                    result["answer"] = explanation
            else:
                result["answer"] = "I couldn't generate the requested chart. Please try a different visualization type."
                
        except Exception as e:
            logger.error(f"Chart generation failed: {e}")
            result["answer"] = f"Chart generation encountered an issue. Please try again."
        
        return result
    
    def _generate_chart_explanation(self, query: str, chart_type: str, df: pd.DataFrame, intent: Dict) -> str:
        """Generate explanation for the chart."""
        
        prompt = f"""Generate a brief, helpful response for a user who asked for a chart.

USER QUERY: "{query}"
CHART TYPE: {chart_type}
DATA: {len(df)} rows, columns: {list(df.columns)[:10]}

Write 2-3 sentences explaining what the chart shows. Be specific about the data.
Start with "📊" emoji. Be concise and informative."""

        try:
            return llm_chat(prompt, temperature=0.5, max_tokens=150)
        except:
            return f"📊 Here's your {chart_type} visualization based on your data."
    
    def _handle_data_query(self, query: str, df: pd.DataFrame, data_summary: str, intent: Dict) -> Dict[str, Any]:
        """Handle queries about user's data."""
        result = {
            "answer": "",
            "chart": None,
            "visualization": None,
            "confidence": 0.9,
            "sources": ["Data Analysis"]
        }
        
        # Calculate relevant statistics
        stats = self._calculate_stats(df, intent)
        
        prompt = f"""You are a helpful data analyst. Answer the user's question about their data.

USER QUESTION: "{query}"

DATA SUMMARY:
{data_summary}

CALCULATED STATISTICS:
{json.dumps(stats, default=str, indent=2)}

INSTRUCTIONS:
- Answer the specific question directly
- Use actual numbers from the data
- Be concise but complete
- If the question can't be answered with this data, say so

Provide a clear, helpful response."""

        try:
            response = llm_chat(prompt, temperature=0.3, max_tokens=500)
            result["answer"] = response
        except Exception as e:
            logger.error(f"Data query failed: {e}")
            result["answer"] = f"📊 Based on your data:\n\n{data_summary}"
        
        return result
    
    def _handle_general_query(self, query: str, context: str, intent: Dict) -> Dict[str, Any]:
        """Handle general knowledge queries."""
        result = {
            "answer": "",
            "chart": None,
            "visualization": None,
            "confidence": 0.85,
            "sources": ["AI Knowledge"]
        }
        
        mode_context = {
            "analyst": "You are a Business Analyst AI assistant.",
            "agent": "You are an AI Agent with autonomous capabilities.",
            "deepthink": "You are a Deep Thinking AI that provides thorough analysis.",
            "predict": "You are an ML/AI prediction assistant.",
            "vision": "You are a Vision AI assistant."
        }
        
        prompt = f"""{mode_context.get(self.mode, "You are a helpful AI assistant.")}

USER QUESTION: "{query}"

{f'CONTEXT: {context[:500]}' if context else ''}

Provide a helpful, accurate, and informative response. Be concise but complete."""

        try:
            response = llm_chat(prompt, temperature=0.7, max_tokens=600)
            result["answer"] = f"## 🌐 AI Knowledge\n\n{response}"
        except Exception as e:
            logger.error(f"General query failed: {e}")
            result["answer"] = "I'm having trouble processing your request. Please try again."
        
        return result
    
    def _get_data_summary(self, df: pd.DataFrame) -> str:
        """Get compact data summary."""
        if df is None or df.empty:
            return ""
        
        summary = f"Dataset: {len(df)} rows, {len(df.columns)} columns\n\n"
        
        for col in df.columns[:15]:  # Limit columns
            if pd.api.types.is_numeric_dtype(df[col]):
                summary += f"• {col} (numeric): min={df[col].min():.2f}, max={df[col].max():.2f}, mean={df[col].mean():.2f}\n"
            else:
                unique = df[col].nunique()
                top_val = df[col].value_counts().head(1)
                top_str = f", top: {top_val.index[0]} ({top_val.values[0]})" if len(top_val) > 0 else ""
                summary += f"• {col} (categorical): {unique} unique{top_str}\n"
        
        return summary
    
    def _calculate_stats(self, df: pd.DataFrame, intent: Dict) -> Dict[str, Any]:
        """Calculate statistics based on intent."""
        stats = {}
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Basic stats for all numeric columns
        for col in numeric_cols[:8]:
            stats[col] = {
                "mean": float(df[col].mean()),
                "sum": float(df[col].sum()),
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "count": int(df[col].count())
            }
        
        # Unique counts for categorical
        for col in categorical_cols[:5]:
            stats[f"{col}_unique"] = int(df[col].nunique())
            stats[f"{col}_top"] = df[col].value_counts().head(3).to_dict()
        
        # Row count
        stats["total_rows"] = len(df)
        stats["total_columns"] = len(df.columns)
        
        return stats


def intelligent_process(user_id: str, query: str, df: pd.DataFrame = None, 
                       context: str = "", mode: str = "analyst") -> Dict[str, Any]:
    """Quick function for intelligent query processing."""
    processor = IntelligentQueryProcessor(user_id, mode)
    return processor.process(query, df, context)


__all__ = ['IntelligentQueryProcessor', 'intelligent_process']
