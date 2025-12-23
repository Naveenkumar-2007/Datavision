# Enterprise Query Dispatcher - LLM-Powered Intelligent Query Understanding
"""
$5M Enterprise Product Quality - Query Understanding System

This module is the BRAIN of the AI Business Analyst. It uses LLM to understand
user queries exactly like how ChatGPT understands natural language:

1. INTENT DETECTION - What does the user want? (answer, chart, prediction)
2. FORMAT DETERMINATION - How should we respond? (brief, detailed, table)
3. ENTITY EXTRACTION - What business entities are mentioned?
4. MODE SELECTION - Which AI mode is best for this query?
5. VISUALIZATION DECISION - Should we generate a chart?

Key Principle: NO HARDCODED PATTERNS for query understanding.
The LLM figures out intent from natural language, just like ChatGPT.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
import json
import re

from core.llm import chat


class QueryIntent(Enum):
    """What the user wants to accomplish"""
    FACTUAL = "factual"           # "What is total revenue?"
    AGGREGATION = "aggregation"   # "Sum of sales by region"
    COMPARISON = "comparison"     # "Compare customer A vs B"
    TREND = "trend"               # "Show me sales trends"
    RANKING = "ranking"           # "Top 5 customers"
    BREAKDOWN = "breakdown"       # "Revenue by category"
    PREDICTION = "prediction"     # "Forecast next quarter"
    ANOMALY = "anomaly"           # "Find unusual patterns"
    SUMMARY = "summary"           # "Summarize my data"
    EXPLANATION = "explanation"   # "Explain this chart"
    GENERAL = "general"           # General business question
    GREETING = "greeting"         # "Hello", "Hi"
    PERSONAL = "personal"         # "My name is..."


class ResponseFormat(Enum):
    """How the user wants the answer formatted"""
    ONE_LINE = "one_line"         # Single sentence
    BRIEF = "brief"               # 2-3 sentences
    DETAILED = "detailed"         # Full analysis with tables
    TABLE = "table"               # Tabular format preferred
    BULLET = "bullet"             # Bullet points
    NARRATIVE = "narrative"       # Story-like explanation
    AUTO = "auto"                 # Let system decide


class VisualizationType(Enum):
    """What type of visualization (if any)"""
    BAR = "bar"
    PIE = "pie"
    LINE = "line"
    AREA = "area"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    FUNNEL = "funnel"
    NONE = "none"
    AUTO = "auto"                 # Let system decide based on data


@dataclass
class QueryDispatch:
    """
    Complete analysis of a user query.
    
    This is passed to the processing nodes to guide their behavior.
    """
    original_query: str
    normalized_query: str          # Cleaned/expanded version
    
    # Intent Analysis
    intent: QueryIntent
    intent_confidence: float       # 0.0 - 1.0
    
    # Response Formatting
    response_format: ResponseFormat
    max_length: Optional[int]      # If user specified (e.g., "in 50 words")
    
    # Visualization
    needs_visualization: bool
    visualization_type: VisualizationType
    chart_title: Optional[str]
    
    # Entities Extracted
    entities: List[str]            # Customer names, products, etc.
    metrics: List[str]             # Revenue, sales, orders, etc.
    time_references: List[str]     # "last month", "2024", etc.
    
    # Aggregations
    aggregation_type: Optional[str]  # sum, avg, count, max, min
    group_by: Optional[str]          # Entity to group by
    limit: Optional[int]             # "top 5" -> limit=5
    
    # Mode Recommendation
    recommended_mode: str          # "rag", "graphrag", "hybrid"
    mode_reason: str               # Why this mode was chosen
    
    # Follow-up Detection
    is_followup: bool
    followup_type: Optional[str]   # "clarification", "refinement", "conversion"
    references_previous: bool      # Uses "that", "this", "above"
    
    # Metadata
    complexity_score: int          # 1-10 query complexity
    requires_calculation: bool     # Needs math beyond simple lookup
    requires_prediction: bool      # Needs forecasting model


class LLMQueryDispatcher:
    """
    Enterprise LLM-Powered Query Dispatcher.
    
    Uses LLM to understand queries like ChatGPT does - through natural
    language understanding, not pattern matching.
    """
    
    def __init__(self, use_llm: bool = True):
        """
        Args:
            use_llm: If False, uses fast pattern matching only (for testing)
        """
        self.use_llm = use_llm
    
    def dispatch(self, query: str, conversation_history: str = "") -> QueryDispatch:
        """
        Main entry point - analyze a query and return dispatch instructions.
        
        Args:
            query: User's natural language query
            conversation_history: Recent conversation for context
            
        Returns:
            QueryDispatch with complete analysis
        """
        # Step 1: Quick pattern pre-processing (for greetings, simple cases)
        quick_dispatch = self._quick_pattern_check(query)
        if quick_dispatch:
            return quick_dispatch
        
        # Step 2: LLM-based deep analysis
        if self.use_llm:
            try:
                llm_analysis = self._llm_analyze(query, conversation_history)
                return self._build_dispatch(query, llm_analysis)
            except Exception as e:
                print(f"[DISPATCHER] LLM analysis failed: {e}, falling back to patterns")
        
        # Step 3: Fallback to pattern-based analysis
        return self._pattern_analyze(query)
    
    def _quick_pattern_check(self, query: str) -> Optional[QueryDispatch]:
        """Quick check for simple queries that don't need LLM."""
        q_lower = query.lower().strip()
        
        # Greetings
        greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
        if q_lower in greetings or q_lower.startswith(('hi ', 'hello ', 'hey ')):
            return QueryDispatch(
                original_query=query,
                normalized_query=query,
                intent=QueryIntent.GREETING,
                intent_confidence=1.0,
                response_format=ResponseFormat.BRIEF,
                max_length=None,
                needs_visualization=False,
                visualization_type=VisualizationType.NONE,
                chart_title=None,
                entities=[],
                metrics=[],
                time_references=[],
                aggregation_type=None,
                group_by=None,
                limit=None,
                recommended_mode="rag",
                mode_reason="Simple greeting",
                is_followup=False,
                followup_type=None,
                references_previous=False,
                complexity_score=1,
                requires_calculation=False,
                requires_prediction=False
            )
        
        return None
    
    def _llm_analyze(self, query: str, conversation_history: str) -> Dict[str, Any]:
        """
        Use LLM to deeply understand the query.
        
        This is the CORE of ChatGPT-like understanding.
        """
        system_prompt = """You are an expert query analyzer for a Business Intelligence system.
        
Analyze the user's query and return a JSON object with the following structure:
{
    "intent": "factual|aggregation|comparison|trend|ranking|breakdown|prediction|anomaly|summary|explanation|general",
    "intent_confidence": 0.0-1.0,
    "response_format": "one_line|brief|detailed|table|bullet|narrative|auto",
    "needs_chart": true|false,
    "chart_type": "bar|pie|line|area|scatter|none|auto",
    "chart_title": "Suggested title or null",
    "entities": ["list of business entities mentioned"],
    "metrics": ["revenue", "sales", "orders", etc.],
    "time_references": ["last month", "2024", etc.],
    "aggregation": {"type": "sum|avg|count|max|min|null", "group_by": "entity or null"},
    "limit": number or null (e.g., "top 5" -> 5),
    "is_followup": true|false,
    "followup_type": "clarification|refinement|conversion|null",
    "references_previous": true|false,
    "complexity": 1-10,
    "requires_calculation": true|false,
    "requires_prediction": true|false,
    "recommended_mode": "rag|graphrag|hybrid",
    "mode_reason": "brief explanation"
}

Guidelines:
- "factual": Simple fact lookup (What is X?)
- "aggregation": Needs summing/averaging (Total revenue)
- "comparison": Comparing entities (A vs B)
- "trend": Time-based analysis (growth over time)
- "ranking": Ordering entities (top/bottom N)
- "breakdown": Distribution analysis (by category)
- "prediction": Future forecasting (next quarter)
- "anomaly": Finding unusual patterns
- "summary": Overview request
- "explanation": Ask about previous response/chart

For response_format:
- "one_line": User asked for brief answer
- "brief": Normal conversational response
- "detailed": User wants thorough analysis
- "table": Tabular data works best
- "auto": Let system decide

For recommended_mode:
- "rag": Simple factual queries, document lookups
- "graphrag": Relationship queries, entity comparisons
- "hybrid": Complex queries needing both

ONLY respond with valid JSON. No explanation text."""

        user_prompt = f"""Query: "{query}"

Conversation History:
{conversation_history if conversation_history else "No previous conversation"}

Analyze this query and return the JSON analysis."""

        try:
            response = chat(
                messages=[{"role": "user", "content": user_prompt}],
                system=system_prompt,
                temperature=0.1,  # Low temperature for consistent analysis
                max_tokens=1000
            )
            
            # Parse JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            print(f"[DISPATCHER] LLM parse error: {e}")
            raise
    
    def _build_dispatch(self, query: str, analysis: Dict[str, Any]) -> QueryDispatch:
        """Build QueryDispatch from LLM analysis."""
        
        # Map string values to enums
        intent_map = {
            "factual": QueryIntent.FACTUAL,
            "aggregation": QueryIntent.AGGREGATION,
            "comparison": QueryIntent.COMPARISON,
            "trend": QueryIntent.TREND,
            "ranking": QueryIntent.RANKING,
            "breakdown": QueryIntent.BREAKDOWN,
            "prediction": QueryIntent.PREDICTION,
            "anomaly": QueryIntent.ANOMALY,
            "summary": QueryIntent.SUMMARY,
            "explanation": QueryIntent.EXPLANATION,
            "general": QueryIntent.GENERAL,
        }
        
        format_map = {
            "one_line": ResponseFormat.ONE_LINE,
            "brief": ResponseFormat.BRIEF,
            "detailed": ResponseFormat.DETAILED,
            "table": ResponseFormat.TABLE,
            "bullet": ResponseFormat.BULLET,
            "narrative": ResponseFormat.NARRATIVE,
            "auto": ResponseFormat.AUTO,
        }
        
        viz_map = {
            "bar": VisualizationType.BAR,
            "pie": VisualizationType.PIE,
            "line": VisualizationType.LINE,
            "area": VisualizationType.AREA,
            "scatter": VisualizationType.SCATTER,
            "heatmap": VisualizationType.HEATMAP,
            "funnel": VisualizationType.FUNNEL,
            "none": VisualizationType.NONE,
            "auto": VisualizationType.AUTO,
        }
        
        aggregation = analysis.get("aggregation", {}) or {}
        
        return QueryDispatch(
            original_query=query,
            normalized_query=query,  # Could enhance with query expansion
            intent=intent_map.get(analysis.get("intent", "general"), QueryIntent.GENERAL),
            intent_confidence=float(analysis.get("intent_confidence", 0.8)),
            response_format=format_map.get(analysis.get("response_format", "auto"), ResponseFormat.AUTO),
            max_length=analysis.get("max_length"),
            needs_visualization=analysis.get("needs_chart", False),
            visualization_type=viz_map.get(analysis.get("chart_type", "auto"), VisualizationType.AUTO),
            chart_title=analysis.get("chart_title"),
            entities=analysis.get("entities", []),
            metrics=analysis.get("metrics", []),
            time_references=analysis.get("time_references", []),
            aggregation_type=aggregation.get("type"),
            group_by=aggregation.get("group_by"),
            limit=analysis.get("limit"),
            recommended_mode=analysis.get("recommended_mode", "rag"),
            mode_reason=analysis.get("mode_reason", "Default selection"),
            is_followup=analysis.get("is_followup", False),
            followup_type=analysis.get("followup_type"),
            references_previous=analysis.get("references_previous", False),
            complexity_score=int(analysis.get("complexity", 5)),
            requires_calculation=analysis.get("requires_calculation", False),
            requires_prediction=analysis.get("requires_prediction", False)
        )
    
    def _pattern_analyze(self, query: str) -> QueryDispatch:
        """
        Fallback pattern-based analysis.
        
        Used when LLM is unavailable or fails.
        """
        q_lower = query.lower()
        
        # Intent detection
        intent = QueryIntent.GENERAL
        if any(kw in q_lower for kw in ['top', 'best', 'highest', 'lowest', 'worst', 'bottom']):
            intent = QueryIntent.RANKING
        elif any(kw in q_lower for kw in ['compare', 'vs', 'versus', 'difference between']):
            intent = QueryIntent.COMPARISON
        elif any(kw in q_lower for kw in ['trend', 'over time', 'monthly', 'growth', 'change']):
            intent = QueryIntent.TREND
        elif any(kw in q_lower for kw in ['breakdown', 'by category', 'by region', 'distribution']):
            intent = QueryIntent.BREAKDOWN
        elif any(kw in q_lower for kw in ['predict', 'forecast', 'future', 'next month', 'next year']):
            intent = QueryIntent.PREDICTION
        elif any(kw in q_lower for kw in ['total', 'sum', 'average', 'count', 'how many', 'how much']):
            intent = QueryIntent.AGGREGATION
        elif any(kw in q_lower for kw in ['what is', 'who is', 'show me', 'tell me']):
            intent = QueryIntent.FACTUAL
        
        # Response format detection
        response_format = ResponseFormat.AUTO
        if any(kw in q_lower for kw in ['one line', '1 line', 'briefly', 'short']):
            response_format = ResponseFormat.BRIEF
        elif any(kw in q_lower for kw in ['detailed', 'comprehensive', 'full analysis']):
            response_format = ResponseFormat.DETAILED
        
        # Visualization detection
        needs_viz = any(kw in q_lower for kw in ['chart', 'graph', 'plot', 'visualize', 'show'])
        viz_type = VisualizationType.AUTO
        if 'pie' in q_lower:
            viz_type = VisualizationType.PIE
        elif 'bar' in q_lower:
            viz_type = VisualizationType.BAR
        elif 'line' in q_lower:
            viz_type = VisualizationType.LINE
        
        # Extract limit (top N)
        limit_match = re.search(r'(?:top|bottom|best|worst)\s+(\d+)', q_lower)
        limit = int(limit_match.group(1)) if limit_match else None
        
        # Determine mode
        mode = "rag"
        if intent in [QueryIntent.COMPARISON, QueryIntent.RANKING]:
            mode = "graphrag"
        elif intent in [QueryIntent.TREND, QueryIntent.PREDICTION]:
            mode = "hybrid"
        
        return QueryDispatch(
            original_query=query,
            normalized_query=query,
            intent=intent,
            intent_confidence=0.7,
            response_format=response_format,
            max_length=None,
            needs_visualization=needs_viz,
            visualization_type=viz_type,
            chart_title=None,
            entities=[],
            metrics=[],
            time_references=[],
            aggregation_type=None,
            group_by=None,
            limit=limit,
            recommended_mode=mode,
            mode_reason="Pattern-based selection",
            is_followup=False,
            followup_type=None,
            references_previous=any(kw in q_lower for kw in ['that', 'this', 'above', 'it']),
            complexity_score=5,
            requires_calculation=intent in [QueryIntent.AGGREGATION, QueryIntent.COMPARISON],
            requires_prediction=intent == QueryIntent.PREDICTION
        )


# Singleton instance
_dispatcher: Optional[LLMQueryDispatcher] = None


def get_query_dispatcher() -> LLMQueryDispatcher:
    """Get or create singleton dispatcher."""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = LLMQueryDispatcher(use_llm=True)
    return _dispatcher


def dispatch_query(query: str, conversation_history: str = "") -> QueryDispatch:
    """
    Convenience function for query dispatch.
    
    Args:
        query: User's natural language query
        conversation_history: Recent conversation context
        
    Returns:
        QueryDispatch with complete analysis
    """
    dispatcher = get_query_dispatcher()
    return dispatcher.dispatch(query, conversation_history)


# Quick test
if __name__ == "__main__":
    # Test queries
    test_queries = [
        "What is my total revenue?",
        "Show me top 5 customers in a bar chart",
        "Compare Product A vs Product B",
        "Predict next quarter revenue",
        "Give me a brief summary",
        "Explain that in one line",
    ]
    
    dispatcher = LLMQueryDispatcher(use_llm=False)  # Use patterns for testing
    
    for q in test_queries:
        result = dispatcher.dispatch(q)
        print(f"\nQuery: {q}")
        print(f"  Intent: {result.intent.value}")
        print(f"  Format: {result.response_format.value}")
        print(f"  Needs Chart: {result.needs_visualization}")
        print(f"  Mode: {result.recommended_mode}")
