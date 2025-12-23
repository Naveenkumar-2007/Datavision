# MCP Router - Smart Query-Based MCP Selection
"""
Intelligently routes queries to the appropriate MCP servers.
Only calls MCPs when data/computation is actually required.

Principles:
1. MCPs are for DATA operations, not pure reasoning
2. Skip MCP for summaries, definitions, greetings
3. Fallback gracefully on MCP failures
4. Optimize for speed - minimize unnecessary calls
"""

from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass


class QueryIntent(Enum):
    """Types of query intents"""
    GREETING = "greeting"           # Hello, thanks, etc.
    DEFINITION = "definition"       # What is X?
    SUMMARY = "summary"             # Summarize, explain
    FACTUAL = "factual"             # Get specific data
    AGGREGATION = "aggregation"     # Total, average, sum
    COMPARISON = "comparison"       # Compare A vs B
    TREND = "trend"                 # Over time, growth
    PREDICTION = "prediction"       # Forecast future
    SIMULATION = "simulation"       # What if scenarios
    VISUALIZATION = "visualization" # Show chart, graph
    ANALYSIS = "analysis"           # Analyze, insights


# ============================================================================
# MCP ROUTING RULES
# ============================================================================

# Which MCPs are needed for each intent
INTENT_TO_MCP: Dict[QueryIntent, List[str]] = {
    # No MCP needed - pure LLM reasoning
    QueryIntent.GREETING: [],
    QueryIntent.DEFINITION: [],
    QueryIntent.SUMMARY: [],
    
    # Data retrieval - need SQL/Graph
    QueryIntent.FACTUAL: ["sql_executor", "graph_builder"],
    QueryIntent.AGGREGATION: ["sql_executor"],
    QueryIntent.COMPARISON: ["sql_executor", "graph_builder"],
    
    # Time-series - need forecast
    QueryIntent.TREND: ["sql_executor", "forecast_engine"],
    QueryIntent.PREDICTION: ["forecast_engine", "prediction_engine"],
    
    # Advanced analysis
    QueryIntent.SIMULATION: ["simulation_engine"],
    QueryIntent.VISUALIZATION: ["chart_generator"],
    QueryIntent.ANALYSIS: ["insight_engine", "sql_executor"],
}

# Keywords to detect intent
INTENT_KEYWORDS = {
    QueryIntent.GREETING: ["hello", "hi", "hey", "thanks", "thank you", "bye", "goodbye"],
    QueryIntent.DEFINITION: ["what is", "what are", "define", "meaning of", "explain what"],
    QueryIntent.SUMMARY: ["summarize", "summary", "overview", "brief", "explain"],
    QueryIntent.FACTUAL: ["how much", "how many", "what was", "show me", "list", "get"],
    QueryIntent.AGGREGATION: ["total", "sum", "average", "count", "minimum", "maximum"],
    QueryIntent.COMPARISON: ["compare", "versus", "vs", "difference", "between"],
    QueryIntent.TREND: ["trend", "over time", "monthly", "weekly", "growth", "decline"],
    QueryIntent.PREDICTION: ["predict", "forecast", "future", "next month", "next quarter"],
    QueryIntent.SIMULATION: ["what if", "simulate", "scenario", "if we", "impact of"],
    QueryIntent.VISUALIZATION: ["chart", "graph", "visualize", "plot", "show"],
    QueryIntent.ANALYSIS: ["analyze", "insight", "why", "reason", "cause"],
}


@dataclass
class MCPRoutingDecision:
    """Decision on which MCPs to call"""
    required_mcps: List[str]
    optional_mcps: List[str]
    skip_reason: Optional[str]
    intent: QueryIntent
    confidence: float


def detect_intent(query: str) -> Tuple[QueryIntent, float]:
    """
    Detect the intent of a query.
    
    Returns:
        Tuple[QueryIntent, float]: (detected intent, confidence 0-1)
    """
    query_lower = query.lower().strip()
    
    # Score each intent
    intent_scores: Dict[QueryIntent, int] = {}
    
    for intent, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > 0:
            intent_scores[intent] = score
    
    if not intent_scores:
        # Default to analysis if no clear match
        return QueryIntent.ANALYSIS, 0.3
    
    # Get highest scoring intent
    best_intent = max(intent_scores, key=intent_scores.get)
    max_score = intent_scores[best_intent]
    
    # Calculate confidence
    confidence = min(1.0, max_score / 3)  # 3+ matches = 100% confidence
    
    return best_intent, confidence


def get_required_mcps(
    query: str,
    enabled_mcps: Optional[Dict[str, bool]] = None
) -> MCPRoutingDecision:
    """
    Determine which MCPs are required for a query.
    
    Args:
        query: The user's query
        enabled_mcps: Dict of MCP names to enabled status (from frontend)
        
    Returns:
        MCPRoutingDecision with required and optional MCPs
    """
    intent, confidence = detect_intent(query)
    required_mcps = INTENT_TO_MCP.get(intent, [])
    
    # Filter by enabled MCPs if provided
    if enabled_mcps:
        required_mcps = [mcp for mcp in required_mcps if enabled_mcps.get(mcp, True)]
    
    # Determine skip reason for no-MCP queries
    skip_reason = None
    if not required_mcps:
        if intent == QueryIntent.GREETING:
            skip_reason = "Greeting - no data needed"
        elif intent == QueryIntent.DEFINITION:
            skip_reason = "Definition - pure reasoning"
        elif intent == QueryIntent.SUMMARY:
            skip_reason = "Summary - no new data fetch needed"
    
    return MCPRoutingDecision(
        required_mcps=required_mcps,
        optional_mcps=[],  # Could add context-dependent optional MCPs
        skip_reason=skip_reason,
        intent=intent,
        confidence=confidence,
    )


def should_call_mcp(query: str, mcp_name: str) -> bool:
    """
    Quick check: should we call this specific MCP for this query?
    """
    decision = get_required_mcps(query)
    return mcp_name in decision.required_mcps


# ============================================================================
# GRACEFUL FALLBACK
# ============================================================================

@dataclass
class MCPResult:
    """Result from MCP call with fallback support"""
    success: bool
    data: any
    error: Optional[str] = None
    fallback_used: bool = False
    fallback_message: Optional[str] = None


def execute_mcp_with_fallback(
    mcp_name: str,
    handler_func,
    fallback_response: str = None,
    **kwargs
) -> MCPResult:
    """
    Execute MCP with graceful fallback on failure.
    
    Args:
        mcp_name: Name of the MCP tool
        handler_func: The MCP handler function to call
        fallback_response: Optional fallback response on failure
        **kwargs: Arguments to pass to handler
        
    Returns:
        MCPResult with data or fallback
    """
    try:
        result = handler_func(**kwargs)
        return MCPResult(
            success=True,
            data=result,
        )
    except Exception as e:
        # Log error but don't crash
        print(f"⚠️ MCP {mcp_name} failed: {e}")
        
        # Use fallback
        fallback_msg = fallback_response or f"Unable to execute {mcp_name} operation"
        
        return MCPResult(
            success=False,
            data=None,
            error=str(e),
            fallback_used=True,
            fallback_message=fallback_msg,
        )


# ============================================================================
# MCP OPTIMIZATION
# ============================================================================

def get_mcp_priority(mcp_name: str) -> int:
    """
    Get execution priority for MCP (lower = higher priority).
    Used to order MCP calls for speed.
    """
    priorities = {
        "sql_executor": 1,      # Fast, try first
        "graph_builder": 2,    # Fast
        "vectorizer": 3,       # Medium
        "insight_engine": 4,   # Medium
        "forecast_engine": 5,  # Slower
        "prediction_engine": 6, # Slower
        "simulation_engine": 7, # Slow
        "vision_ocr": 8,       # Varies
        "data_cleaner": 9,     # Batch operation
        "chart_generator": 10, # Last (needs data first)
    }
    return priorities.get(mcp_name, 99)


def order_mcps_by_priority(mcp_list: List[str]) -> List[str]:
    """Order MCPs by execution priority for speed optimization"""
    return sorted(mcp_list, key=get_mcp_priority)
