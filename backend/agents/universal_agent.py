"""
🤖 UNIVERSAL DATA AGENT - DataVision Intelligent Query Handler
==============================================================

The brain that understands ANY query and routes it intelligently:
- Natural language understanding
- Multi-step query decomposition  
- Context-aware follow-ups
- Self-correction with confidence

Integrates: Reasoning Engine + Autonomous Brain + MCPs
"""

import json
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import pandas as pd

from core.llm import chat

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Detected query intents"""
    ANALYZE = "analyze"          # General data analysis
    PREDICT = "predict"          # Forecasting/prediction
    COMPARE = "compare"          # Comparison between segments
    EXPLAIN = "explain"          # Root cause / why questions
    SUMMARIZE = "summarize"      # Data summary
    VISUALIZE = "visualize"      # Chart/graph request
    SEGMENT = "segment"          # Customer/data segmentation
    TREND = "trend"              # Trend analysis
    ANOMALY = "anomaly"          # Anomaly detection
    FILTER = "filter"            # Data filtering
    AGGREGATE = "aggregate"      # Aggregations (sum, avg, etc.)
    CONVERSATIONAL = "chat"      # General conversation
    ACTION = "action"            # Take an action (export, alert, etc.)


@dataclass 
class QueryContext:
    """Context for query processing"""
    user_id: str
    query: str
    intent: QueryIntent
    entities: Dict[str, List[str]]  # columns, values, dates, etc.
    confidence: float
    requires_data: bool
    suggested_mcps: List[str]
    follow_up_context: Optional[str] = None


@dataclass
class AgentResponse:
    """Response from the universal agent"""
    answer: str
    confidence: float
    reasoning_steps: List[Dict[str, str]]
    visualizations: List[Dict[str, Any]]
    follow_up_suggestions: List[str]
    mcps_used: List[str]
    processing_time_ms: int
    data_summary: Optional[Dict] = None


class UniversalDataAgent:
    """
    🤖 Universal Data Agent
    
    Understands any query and orchestrates:
    - Reasoning Engine for complex analysis
    - Autonomous Brain for data profiling
    - MCPs for specific operations
    - Visualization generation
    """
    
    def __init__(self):
        self.conversation_history: Dict[str, List[Dict]] = {}
        self.max_history = 10
        
        # Intent patterns for fast classification
        self.intent_patterns = {
            QueryIntent.PREDICT: ['predict', 'forecast', 'future', 'next month', 'next year', 'projection'],
            QueryIntent.COMPARE: ['compare', 'versus', 'vs', 'difference', 'between'],
            QueryIntent.EXPLAIN: ['why', 'how come', 'reason', 'cause', 'explain'],
            QueryIntent.SUMMARIZE: ['summarize', 'summary', 'overview', 'brief'],
            QueryIntent.VISUALIZE: ['chart', 'graph', 'plot', 'visualize', 'show me', 'display'],
            QueryIntent.SEGMENT: ['segment', 'cluster', 'group', 'categorize', 'types of'],
            QueryIntent.TREND: ['trend', 'pattern', 'over time', 'monthly', 'yearly'],
            QueryIntent.ANOMALY: ['anomaly', 'outlier', 'unusual', 'abnormal', 'spike'],
            QueryIntent.FILTER: ['filter', 'where', 'only', 'with', 'having'],
            QueryIntent.AGGREGATE: ['total', 'sum', 'average', 'count', 'max', 'min'],
            QueryIntent.ACTION: ['export', 'send', 'email', 'alert', 'save', 'download'],
        }
    
    async def process_query(
        self,
        query: str,
        user_id: str,
        df: Optional[pd.DataFrame] = None,
        data_schema: Optional[Dict] = None
    ) -> AgentResponse:
        """
        Main entry point - Process any user query
        
        Args:
            query: User's natural language query
            user_id: User identifier
            df: Optional DataFrame if data is available
            data_schema: Optional schema of available data
            
        Returns:
            Complete agent response with answer, visualizations, etc.
        """
        start_time = datetime.now()
        
        logger.info(f"🤖 Agent processing: {query[:50]}...")
        
        # 1. Understand the query
        context = await self._understand_query(query, user_id, data_schema)
        
        # 2. Add conversation history
        history = self._get_conversation_history(user_id)
        
        # 3. Route to appropriate handler
        if context.intent == QueryIntent.PREDICT and df is not None:
            answer, visualizations = await self._handle_prediction(query, df, context)
        elif context.intent == QueryIntent.EXPLAIN and df is not None:
            answer, visualizations = await self._handle_explanation(query, df, context)
        elif context.intent == QueryIntent.SEGMENT and df is not None:
            answer, visualizations = await self._handle_segmentation(query, df, context)
        elif context.intent == QueryIntent.TREND and df is not None:
            answer, visualizations = await self._handle_trend(query, df, context)
        elif context.intent == QueryIntent.VISUALIZE and df is not None:
            answer, visualizations = await self._handle_visualization(query, df, context)
        elif context.intent == QueryIntent.SUMMARIZE and df is not None:
            answer, visualizations = await self._handle_summary(query, df, context)
        else:
            # Use reasoning engine for general queries
            answer, visualizations = await self._handle_general(query, df, context, history)
        
        # 4. Generate follow-up suggestions
        follow_ups = self._generate_follow_ups(context, answer)
        
        # 5. Update conversation history
        self._add_to_history(user_id, query, answer)
        
        # Calculate processing time
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return AgentResponse(
            answer=answer,
            confidence=context.confidence,
            reasoning_steps=[],
            visualizations=visualizations,
            follow_up_suggestions=follow_ups,
            mcps_used=context.suggested_mcps,
            processing_time_ms=processing_time,
            data_summary=self._get_data_summary(df) if df is not None else None
        )
    
    async def _understand_query(
        self,
        query: str,
        user_id: str,
        data_schema: Optional[Dict]
    ) -> QueryContext:
        """Understand the user's query intent and entities"""
        query_lower = query.lower()
        
        # Fast pattern matching for intent
        detected_intent = QueryIntent.ANALYZE
        highest_score = 0
        
        for intent, patterns in self.intent_patterns.items():
            score = sum(1 for p in patterns if p in query_lower)
            if score > highest_score:
                highest_score = score
                detected_intent = intent
        
        # If no strong pattern match, use LLM for understanding
        confidence = min(0.9, 0.5 + highest_score * 0.2)
        
        if highest_score == 0:
            detected_intent, confidence = await self._llm_intent_classification(query)
        
        # Extract entities (columns, values, dates)
        entities = self._extract_entities(query, data_schema)
        
        # Determine required MCPs
        suggested_mcps = self._suggest_mcps(detected_intent, entities)
        
        # Check if data is required
        requires_data = detected_intent not in [QueryIntent.CONVERSATIONAL]
        
        return QueryContext(
            user_id=user_id,
            query=query,
            intent=detected_intent,
            entities=entities,
            confidence=confidence,
            requires_data=requires_data,
            suggested_mcps=suggested_mcps
        )
    
    async def _llm_intent_classification(self, query: str) -> Tuple[QueryIntent, float]:
        """Use LLM for intent classification when patterns don't match"""
        prompt = f"""Classify this user query into one of these intents:
- ANALYZE: General data analysis
- PREDICT: Forecasting/prediction
- COMPARE: Comparison
- EXPLAIN: Why/root cause questions
- SUMMARIZE: Summary request
- VISUALIZE: Chart/visualization request
- SEGMENT: Grouping/clustering
- TREND: Trend analysis
- CHAT: General conversation

Query: "{query}"

Respond with just the intent name and confidence (0-1):
INTENT: [intent]
CONFIDENCE: [0.0-1.0]"""

        try:
            response = chat(messages=prompt, temperature=0.1, max_tokens=50)
            
            # Parse response
            intent_match = re.search(r'INTENT:\s*(\w+)', response, re.IGNORECASE)
            conf_match = re.search(r'CONFIDENCE:\s*([\d.]+)', response, re.IGNORECASE)
            
            if intent_match:
                intent_str = intent_match.group(1).upper()
                intent_map = {
                    'ANALYZE': QueryIntent.ANALYZE,
                    'PREDICT': QueryIntent.PREDICT,
                    'COMPARE': QueryIntent.COMPARE,
                    'EXPLAIN': QueryIntent.EXPLAIN,
                    'SUMMARIZE': QueryIntent.SUMMARIZE,
                    'VISUALIZE': QueryIntent.VISUALIZE,
                    'SEGMENT': QueryIntent.SEGMENT,
                    'TREND': QueryIntent.TREND,
                    'CHAT': QueryIntent.CONVERSATIONAL,
                }
                intent = intent_map.get(intent_str, QueryIntent.ANALYZE)
                confidence = float(conf_match.group(1)) if conf_match else 0.7
                return intent, confidence
        except Exception as e:
            logger.warning(f"LLM intent classification failed: {e}")
        
        return QueryIntent.ANALYZE, 0.6
    
    def _extract_entities(
        self, 
        query: str, 
        data_schema: Optional[Dict]
    ) -> Dict[str, List[str]]:
        """Extract entities from query"""
        entities = {
            "columns": [],
            "values": [],
            "dates": [],
            "numbers": []
        }
        
        # Extract column references if schema available
        if data_schema and "columns" in data_schema:
            for col in data_schema["columns"]:
                col_name = col.get("name", "") if isinstance(col, dict) else col
                if col_name.lower() in query.lower():
                    entities["columns"].append(col_name)
        
        # Extract date patterns
        date_patterns = [
            r'\b\d{4}-\d{2}-\d{2}\b',
            r'\b\d{2}/\d{2}/\d{4}\b',
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}\b',
            r'\b(q1|q2|q3|q4)\s*\d{4}\b',
            r'\blast\s+(week|month|year|quarter)\b',
        ]
        for pattern in date_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            entities["dates"].extend(matches)
        
        # Extract numbers
        numbers = re.findall(r'\b\d+\.?\d*\b', query)
        entities["numbers"] = numbers[:5]
        
        return entities
    
    def _suggest_mcps(
        self, 
        intent: QueryIntent, 
        entities: Dict
    ) -> List[str]:
        """Suggest MCPs based on intent"""
        mcp_map = {
            QueryIntent.PREDICT: ["forecast_engine", "prediction_engine"],
            QueryIntent.EXPLAIN: ["root_cause_analyzer", "insight_engine"],
            QueryIntent.SEGMENT: ["segmentation_engine", "clustering"],
            QueryIntent.TREND: ["trend_detector", "time_series"],
            QueryIntent.ANOMALY: ["anomaly_detector", "isolation_forest"],
            QueryIntent.VISUALIZE: ["chart_generator", "visual_intelligence"],
            QueryIntent.SUMMARIZE: ["insight_engine", "data_profiler"],
        }
        return mcp_map.get(intent, ["insight_engine"])
    
    async def _handle_prediction(
        self,
        query: str,
        df: pd.DataFrame,
        context: QueryContext
    ) -> Tuple[str, List[Dict]]:
        """Handle prediction/forecast queries"""
        try:
            from mcp.forecast_engine import forecast_from_dataframe
            
            # Find numeric column to predict
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            target_col = context.entities.get("columns", [None])[0] or (numeric_cols[0] if numeric_cols else None)
            
            if not target_col:
                return "I need a numeric column to make predictions. Please specify which metric you want to forecast.", []
            
            # Generate forecast
            result = forecast_from_dataframe(df, target_col)
            
            answer = f"""📊 **Prediction for {target_col}:**

{result.get('summary', 'Forecast generated successfully.')}

**Key Predictions:**
• Next period: {result.get('next_value', 'N/A')}
• Trend: {result.get('trend', 'N/A')}
• Confidence: {result.get('confidence', 0.8)*100:.0f}%
"""
            
            visualizations = [{
                "type": "line",
                "title": f"{target_col} Forecast",
                "data": result.get("forecast_data", [])
            }]
            
            return answer, visualizations
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return await self._handle_general(query, df, context, [])
    
    async def _handle_explanation(
        self,
        query: str,
        df: pd.DataFrame,
        context: QueryContext
    ) -> Tuple[str, List[Dict]]:
        """Handle 'why' and explanation queries"""
        try:
            from mcp.advanced_mcps import analyze_root_cause
            
            # Find target column from query or schema
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            target_col = context.entities.get("columns", [None])[0] or (numeric_cols[0] if numeric_cols else None)
            
            if not target_col:
                return await self._handle_general(query, df, context, [])
            
            result = await analyze_root_cause(df, target_col, query)
            
            return result.get("summary", "Analysis complete."), []
            
        except Exception as e:
            logger.error(f"Explanation error: {e}")
            return await self._handle_general(query, df, context, [])
    
    async def _handle_segmentation(
        self,
        query: str,
        df: pd.DataFrame,
        context: QueryContext
    ) -> Tuple[str, List[Dict]]:
        """Handle segmentation queries"""
        try:
            from mcp.advanced_mcps import segment_data
            
            result = await segment_data(df)
            
            return result.get("summary", "Segmentation complete."), []
            
        except Exception as e:
            logger.error(f"Segmentation error: {e}")
            return await self._handle_general(query, df, context, [])
    
    async def _handle_trend(
        self,
        query: str,
        df: pd.DataFrame,
        context: QueryContext
    ) -> Tuple[str, List[Dict]]:
        """Handle trend analysis queries"""
        try:
            from mcp.advanced_mcps import detect_trends
            
            result = await detect_trends(df)
            
            return result.get("summary", "Trend analysis complete."), []
            
        except Exception as e:
            logger.error(f"Trend error: {e}")
            return await self._handle_general(query, df, context, [])
    
    async def _handle_visualization(
        self,
        query: str,
        df: pd.DataFrame,
        context: QueryContext
    ) -> Tuple[str, List[Dict]]:
        """Handle visualization requests"""
        try:
            from core.autonomous_brain import get_brain
            
            brain = get_brain()
            analysis = await brain.analyze(df, "query_data", generate_insights=False)
            result = brain.to_dict(analysis)
            
            suggested_charts = result.get("suggested_charts", [])
            
            answer = f"📊 Here are the recommended visualizations for your data:\n\n"
            for i, chart in enumerate(suggested_charts[:5], 1):
                answer += f"{i}. **{chart.get('title', 'Chart')}** ({chart.get('type', 'chart')})\n"
            
            return answer, suggested_charts[:5]
            
        except Exception as e:
            logger.error(f"Visualization error: {e}")
            return "I can help you visualize this data. What specific chart would you like to see?", []
    
    async def _handle_summary(
        self,
        query: str,
        df: pd.DataFrame,
        context: QueryContext
    ) -> Tuple[str, List[Dict]]:
        """Handle summary/overview requests"""
        try:
            from core.autonomous_brain import get_brain
            
            brain = get_brain()
            analysis = await brain.analyze(df, "summary", generate_insights=True)
            result = brain.to_dict(analysis)
            
            return result.get("summary", "Data analysis complete."), []
            
        except Exception as e:
            logger.error(f"Summary error: {e}")
            return await self._handle_general(query, df, context, [])
    
    async def _handle_general(
        self,
        query: str,
        df: Optional[pd.DataFrame],
        context: QueryContext,
        history: List[Dict]
    ) -> Tuple[str, List[Dict]]:
        """Handle general queries with reasoning engine"""
        try:
            from core.reasoning_engine import reason, ReasoningMode
            
            # Build data context
            data_context = ""
            if df is not None:
                data_context = f"""
Data Overview: {len(df)} rows, {len(df.columns)} columns
Columns: {', '.join(df.columns[:15])}
Sample: {df.head(3).to_string()}
"""
            
            # Add conversation history
            history_context = ""
            if history:
                history_context = "\n\nPrevious conversation:\n"
                for h in history[-3:]:
                    history_context += f"User: {h['query']}\nAssistant: {h['answer'][:200]}...\n"
            
            full_context = data_context + history_context
            
            result = await reason(
                query=query,
                context=full_context,
                mode=ReasoningMode.CHAIN_OF_THOUGHT
            )
            
            return result.final_answer, []
            
        except Exception as e:
            logger.error(f"General query error: {e}")
            
            # Fallback to basic LLM
            response = chat(
                messages=query,
                system="You are DataVision, an intelligent data analysis assistant. Be helpful and concise.",
                temperature=0.7
            )
            return response, []
    
    def _generate_follow_ups(
        self, 
        context: QueryContext, 
        answer: str
    ) -> List[str]:
        """Generate follow-up suggestions"""
        suggestions = []
        
        intent_followups = {
            QueryIntent.PREDICT: [
                "What factors influence this prediction?",
                "Show me the prediction confidence intervals",
                "Compare with last year's trend"
            ],
            QueryIntent.EXPLAIN: [
                "What actions can I take to improve this?",
                "Show me similar patterns in the past",
                "Which segment is most affected?"
            ],
            QueryIntent.SEGMENT: [
                "Show characteristics of each segment",
                "Which segment has the highest value?",
                "How did segments change over time?"
            ],
            QueryIntent.TREND: [
                "Predict the next month",
                "Find anomalies in this trend",
                "Compare with industry benchmarks"
            ],
            QueryIntent.ANALYZE: [
                "Summarize the key insights",
                "Show me a visualization",
                "What should I focus on?"
            ]
        }
        
        suggestions = intent_followups.get(context.intent, [
            "Tell me more",
            "Show me a chart",
            "What are the key insights?"
        ])
        
        return suggestions[:3]
    
    def _get_conversation_history(self, user_id: str) -> List[Dict]:
        """Get conversation history for user"""
        return self.conversation_history.get(user_id, [])
    
    def _add_to_history(self, user_id: str, query: str, answer: str):
        """Add to conversation history"""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        self.conversation_history[user_id].append({
            "query": query,
            "answer": answer[:500],
            "timestamp": datetime.now().isoformat()
        })
        
        # Limit history
        if len(self.conversation_history[user_id]) > self.max_history:
            self.conversation_history[user_id] = self.conversation_history[user_id][-self.max_history:]
    
    def _get_data_summary(self, df: pd.DataFrame) -> Dict:
        """Get quick data summary"""
        return {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns[:10]),
            "numeric_columns": df.select_dtypes(include=['number']).columns.tolist()[:5]
        }


# Global instance
_agent_instance: Optional[UniversalDataAgent] = None


def get_agent() -> UniversalDataAgent:
    """Get or create the global agent instance"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = UniversalDataAgent()
    return _agent_instance


async def process_query(
    query: str,
    user_id: str,
    df: Optional[pd.DataFrame] = None,
    data_schema: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Quick function to process a query
    
    Usage:
        result = await process_query("Why did sales drop?", "user123", df)
    """
    agent = get_agent()
    response = await agent.process_query(query, user_id, df, data_schema)
    
    return {
        "answer": response.answer,
        "confidence": response.confidence,
        "visualizations": response.visualizations,
        "follow_ups": response.follow_up_suggestions,
        "mcps_used": response.mcps_used,
        "processing_time_ms": response.processing_time_ms
    }
