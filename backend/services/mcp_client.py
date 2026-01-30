"""
MCP Client - Wrapper for MCP tool integrations
Provides unified interface to RAG, GraphRAG, and Prediction MCPs
"""

import logging
from typing import Dict, Any, List
from core.llm import chat
from vector.retriever import retrieve
from graph.query import query_graph
from api.v1.endpoints.charts import get_user_data
from mcp.forecast_engine import forecast_from_dataframe
from mcp.insight_engine import generate_insights

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for interacting with MCP tools"""
    
    @staticmethod
    async def detect_insights(workspace_id: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect insights using RAG + GraphRAG + ML
        Returns list of insights with title, body, severity, score, chart_payload
        """
        insights = []
        
        try:
            # Get workspace data - use get_user_data to preserve original columns
            df = get_user_data(workspace_id)
            
            if df is None or df.empty:
                logger.warning(f"No data available for workspace {workspace_id}")
                return []
            
            # Calculate metrics for insight generation
            amount_col = 'amount' if 'amount' in df.columns else 'total_amount'
            total_revenue = df[amount_col].sum()
            total_customers = df['customer'].nunique() if 'customer' in df.columns else 0
            total_orders = len(df)
            
            # Generate automated insights using Insight Engine
            insight_result = generate_insights(
                revenue=total_revenue,
                revenue_previous=total_revenue * 0.9,  # Assume 10% growth
                customers=total_customers,
                orders=total_orders,
                churn_rate=0.05,
                inventory_levels={},
                recent_campaigns_data={}
            )
            
            # Convert insight engine output to standard format
            for insight_data in insight_result.get('insights', []):
                insights.append({
                    'title': insight_data.get('title', 'Business Insight'),
                    'body': insight_data.get('description', ''),
                    'severity': insight_data.get('severity', 'medium'),
                    'score': insight_data.get('impact_score', 0),
                    'metadata': {
                        'category': insight_data.get('category', 'general'),
                        'metrics': insight_data.get('metrics', {})
                    },
                    'chart_payload': None
                })
            
            # Add RAG-based insights
            rag_insights = await MCPClient._generate_rag_insights(workspace_id)
            insights.extend(rag_insights)
            
            # Add Graph-based insights
            graph_insights = await MCPClient._generate_graph_insights(workspace_id)
            insights.extend(graph_insights)
            
            logger.info(f"Generated {len(insights)} insights for workspace {workspace_id}")
            return insights
            
        except Exception as e:
            logger.error(f"Error detecting insights: {e}", exc_info=True)
            return []
    
    @staticmethod
    async def _generate_rag_insights(workspace_id: str) -> List[Dict[str, Any]]:
        """Generate insights using RAG (document analysis)"""
        insights = []
        
        try:
            # Retrieve recent documents
            docs = retrieve("revenue anomalies and risks", k=5, user_id=workspace_id)
            
            if not docs:
                return []
            
            # Build context from documents
            context = "\n\n".join([doc.get('text', '')[:500] for doc in docs[:3]])
            
            # Use LLM to generate insight
            prompt = f"""Analyze this business data and identify ONE critical insight:

Context:
{context}

Generate a JSON response with:
{{
    "title": "Brief insight title",
    "body": "Detailed explanation (2-3 sentences)",
    "severity": "low|medium|high",
    "score": 0-100
}}"""
            
            response = chat(prompt, max_tokens=300)
            
            # Parse LLM response (simplified - add proper JSON parsing)
            if "high" in response.lower():
                insights.append({
                    'title': "Document Anomaly Detected",
                    'body': response[:200],
                    'severity': 'high',
                    'score': 85,
                    'metadata': {'source': 'RAG'},
                    'chart_payload': None
                })
            
        except Exception as e:
            logger.error(f"RAG insight generation error: {e}")
        
        return insights
    
    @staticmethod
    async def _generate_graph_insights(workspace_id: str) -> List[Dict[str, Any]]:
        """Generate insights using GraphRAG (relationship analysis)"""
        insights = []
        
        try:
            # Query graph for anomalies
            graph_result = query_graph("find revenue anomalies", workspace_id)
            
            if graph_result and 'anomalies' in str(graph_result):
                insights.append({
                    'title': "Customer Relationship Anomaly",
                    'body': "Detected unusual patterns in customer-product relationships.",
                    'severity': 'medium',
                    'score': 70,
                    'metadata': {'source': 'GraphRAG'},
                    'chart_payload': None
                })
            
        except Exception as e:
            logger.error(f"GraphRAG insight generation error: {e}")
        
        return insights
    
    @staticmethod
    async def run_forecast(workspace_id: str, periods: int = 3) -> Dict[str, Any]:
        """
        Run revenue forecast using Prediction MCP
        Returns forecast with points, upper/lower bounds, metrics
        """
        try:
            # Use get_user_data to preserve original columns
            df = get_user_data(workspace_id)
            
            if df is None or df.empty:
                return {}
            
            # Run forecast using forecast engine
            forecast_result = forecast_from_dataframe(df, periods=periods)
            
            return forecast_result
            
        except Exception as e:
            logger.error(f"Forecast error: {e}", exc_info=True)
            return {}


# Singleton instance
mcp_client = MCPClient()
