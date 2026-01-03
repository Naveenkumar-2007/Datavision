"""
ANALYST ENGINE - Smart Data Analysis (Universal)
==================================================

YOU ONLY USE THE USER'S PERSONAL DATA - NEVER OUTSIDE INFORMATION!

Power: Fast, intelligent data analysis with auto RAG routing.

Features:
- RAG Router: Auto-selects best retrieval strategy
- Smart Charts: Always generates relevant visualizations
- Schema Intelligence: Understands any data structure
- Quick Insights: Optimized for speed

This is the DEFAULT mode - best for everyday data questions.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from core.llm import chat
from core.rag_router import route_query, RAGStrategy

logger = logging.getLogger(__name__)


class AnalystEngine:
    """
    The Analyst Engine - Your Smart Data Analyst
    
    💡 UNIQUE STRENGTH: 
    - Fastest analysis mode
    - Auto-selects best RAG strategy
    - Smart chart generation
    
    ⚠️ STRICT RULE: Uses ONLY user's uploaded data!
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
    
    async def process(
        self,
        query: str,
        context: str = "",
        df = None,
        generate_chart: bool = True
    ) -> Dict[str, Any]:
        """
        Process a query with the Enhanced Analyst engine.
        
        Features:
        1. Query Intent Detection - understands what user wants
        2. Smart RAG Strategy - picks optimal retrieval
        3. Auto-visualization - generates relevant charts
        4. Data-driven response - no hallucination
        """
        
        start_time = datetime.now()
        logger.info(f"📊 ANALYST ENGINE (Enhanced): Processing '{query[:50]}...'")
        
        # Step 1: Detect query intent
        query_intent = self._detect_query_intent(query)
        logger.info(f"🎯 Query intent: {query_intent}")
        
        # Step 2: Route to best RAG strategy
        routing = route_query(query, context_available=bool(context))
        strategy = routing.strategy.value
        logger.info(f"📊 RAG Strategy: {strategy}")
        
        # Step 3: Build analysis prompt with STRICT DATA GROUNDING
        prompt = f"""You are DataVision Analyst - an elite data analyst.

⚠️ CRITICAL - STRICT DATA GROUNDING:
1. ONLY use data provided below - NEVER use outside knowledge
2. NEVER make up numbers or use industry averages
3. If data doesn't exist, say "Your data doesn't include this"
4. Every number must come from the ACTUAL DATA below

📊 USER'S PERSONAL DATA:
{context[:4000] if context else "No data available. Ask user to upload files."}

❓ USER'S QUESTION: {query}
🎯 DETECTED INTENT: {query_intent['type']} ({query_intent['action']})

📝 RESPONSE FORMAT:
1. **Direct Answer** (first line - answer the question immediately)
2. **Key Numbers** (cite specific data values)
3. **Quick Insight** (1-2 sentence pattern or trend)

DO NOT:
- Make up statistics
- Use vague language like "approximately" without data
- Write long explanations

YOUR DATA-DRIVEN ANALYSIS:"""

        # Step 4: Generate response
        try:
            response = chat(prompt, temperature=0.3, max_tokens=1500)
        except Exception as e:
            logger.error(f"Analyst LLM error: {e}")
            response = f"Error analyzing data: {str(e)}"
        
        # Step 5: Auto-generate chart based on intent
        chart = None
        ml_charts = []
        
        if generate_chart and df is not None:
            chart, ml_charts = await self._auto_visualize(query, df, query_intent)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        result = {
            "answer": response,
            "mode": "analyst",
            "strategy": strategy,
            "chart": chart,
            "query_intent": query_intent,
            "execution_time": f"{execution_time:.2f}s",
            "features_used": ["Query Intent Detection", "RAG Router", "Auto-Visualization", "Data Grounding"],
            "sources": []
        }
        
        if ml_charts:
            result["ml_charts"] = ml_charts
        
        return result
    
    def _detect_query_intent(self, query: str) -> Dict[str, str]:
        """Detect user's intent from query text"""
        query_lower = query.lower()
        
        # Intent patterns
        intents = {
            "trend": ["trend", "over time", "growth", "change", "history", "timeline", "monthly", "yearly"],
            "comparison": ["compare", "versus", "vs", "difference", "between", "against"],
            "distribution": ["distribution", "breakdown", "split", "percentage", "share", "proportion"],
            "ranking": ["top", "best", "worst", "highest", "lowest", "most", "least", "ranking"],
            "correlation": ["relationship", "correlation", "affect", "impact", "influence", "relate"],
            "aggregation": ["total", "sum", "average", "mean", "count", "how many", "how much"],
            "prediction": ["predict", "forecast", "future", "will", "expect", "estimate"],
        }
        
        for intent_type, keywords in intents.items():
            if any(kw in query_lower for kw in keywords):
                return {
                    "type": intent_type,
                    "action": f"analyze_{intent_type}",
                    "chart_suggestion": self._suggest_chart_for_intent(intent_type)
                }
        
        return {
            "type": "general",
            "action": "general_analysis",
            "chart_suggestion": "bar"
        }
    
    def _suggest_chart_for_intent(self, intent: str) -> str:
        """Suggest chart type based on intent"""
        chart_map = {
            "trend": "line",
            "comparison": "grouped_bar",
            "distribution": "pie",
            "ranking": "bar",
            "correlation": "scatter",
            "aggregation": "bar",
            "prediction": "line"
        }
        return chart_map.get(intent, "bar")
    
    async def _auto_visualize(self, query: str, df, intent: Dict) -> tuple:
        """Automatically generate the most relevant visualization"""
        import pandas as pd
        import numpy as np
        
        chart = None
        ml_charts = []
        
        try:
            # Try smart_chart first
            from agents.smart_chart import smart_chart
            chart = smart_chart(query, df)
        except Exception as e:
            logger.warning(f"Smart chart error: {e}")
        
        # Generate ML visualizations for complex intents
        if intent['type'] in ['correlation', 'distribution', 'prediction']:
            try:
                from core.ml_visualizer import MLVisualizer
                viz = MLVisualizer()
                
                if intent['type'] == 'correlation':
                    corr_chart = viz.create_correlation_heatmap(df, "Data Correlations")
                    if corr_chart.get('image'):
                        ml_charts.append(corr_chart)
                
                elif intent['type'] == 'distribution':
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    if len(numeric_cols) > 0:
                        dist_chart = viz.create_distribution_plot(
                            df[numeric_cols[0]].dropna().tolist(),
                            column_name=numeric_cols[0]
                        )
                        if dist_chart.get('image'):
                            ml_charts.append(dist_chart)
                            
            except Exception as e:
                logger.warning(f"ML visualization error: {e}")
        
        return chart, ml_charts


async def analyst_response(
    user_id: str,
    query: str,
    context: str = "",
    df = None
) -> Dict[str, Any]:
    """Quick function to get analyst response"""
    engine = AnalystEngine(user_id)
    return await engine.process(query, context, df)


# Sync version for compatibility
def analyst_response_sync(
    user_id: str,
    query: str,
    context: str = ""
) -> str:
    """Synchronous analyst response for existing code"""
    
    try:
        # Route query
        routing = route_query(query, context_available=bool(context))
        
        prompt = f"""You are DataVision Analyst.

⚠️ CRITICAL: Use ONLY the data below. NEVER use outside knowledge!

📊 USER'S DATA:
{context[:4000] if context else "No data uploaded. Ask user to upload files."}

❓ QUESTION: {query}

Give a DIRECT, DATA-DRIVEN answer using ONLY the data above.
If data doesn't exist, say "I don't have this in your data."

YOUR ANSWER:"""

        return chat(prompt, temperature=0.3)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Analysis error: {str(e)} - check console logs for details"
