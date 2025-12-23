# Enterprise Agent Router v2.0 - Intelligent Query Routing
"""
Advanced routing system for business analytics queries.

Features:
- LLM-powered query classification
- Confidence-based routing
- Multi-mode support: RAG, GraphRAG, Hybrid, Vision
- Automatic mode selection
"""

from typing import Tuple
from agents.query_classifier import (
    classify_query, 
    QueryType, 
    QueryAnalysis,
    EnterpriseQueryClassifier
)


# ============================================================================
# ENTERPRISE ROUTING CONFIGURATION
# ============================================================================

# Confidence thresholds for routing decisions
CONFIDENCE_THRESHOLDS = {
    "high": 0.75,
    "medium": 0.5,
    "low": 0.25
}

# Mode mapping from query types
QUERY_TYPE_TO_MODE = {
    QueryType.FACTUAL: "rag",
    QueryType.AGGREGATION: "rag",
    QueryType.COMPARISON: "hybrid",
    QueryType.TREND: "hybrid",
    QueryType.CAUSAL: "graph",
    QueryType.RELATIONAL: "graph",
    QueryType.PREDICTIVE: "graph",
    QueryType.EXPLORATORY: "hybrid",
    QueryType.VISUAL: "vision"
}


def route_question(
    question: str, 
    has_image: bool = False, 
    mode: str = "auto"
) -> str:
    """
    Enterprise-grade routing for business analytics queries.
    
    Uses LLM-powered query classification with rule-based fallback.
    
    Args:
        question: User's business question
        has_image: Whether query includes image/file
        mode: Force specific mode ("auto", "rag", "graph", "hybrid", "vision", or AI model)
        
    Returns:
        Route name: "rag", "graph", "hybrid", "vision", or AI model id
    """
    
    # AI Model modes - pass through directly
    AI_MODEL_MODES = ["deepseek-chat", "mistral-7b", "llama-70b"]
    if mode in AI_MODEL_MODES:
        print(f"🤖 AI Model mode selected: {mode}")
        return mode
    
    # Manual mode override for RAG modes
    if mode != "auto" and mode in ["rag", "graph", "hybrid", "vision", "graphrag", "prediction"]:
        actual_mode = mode if mode != "graphrag" else "graph"
        print(f"🎯 Manual mode selected: {actual_mode.upper()}")
        return actual_mode
    
    # Vision mode priority
    if has_image:
        print(f"🟩 Routed to VISION mode (Image detected)")
        return "vision"
    
    # Use enterprise query classifier
    analysis = classify_query(question, has_image=has_image)
    
    # Log classification details
    print(f"📊 Query Classification:")
    print(f"   Type: {analysis.query_type.value}")
    print(f"   Confidence: {analysis.confidence:.2f}")
    print(f"   Reasoning Depth: {analysis.reasoning_depth.value}")
    print(f"   Entities: {analysis.entities_mentioned}")
    
    # Get recommended route from classifier
    route = analysis.recommended_route
    
    # Validate route
    if route not in ["rag", "graph", "hybrid", "vision"]:
        route = QUERY_TYPE_TO_MODE.get(analysis.query_type, "hybrid")
    
    # Adjust based on confidence
    if analysis.confidence < CONFIDENCE_THRESHOLDS["medium"]:
        # Low confidence - use hybrid for safety
        if route in ["rag", "graph"]:
            print(f"⚠️ Low confidence ({analysis.confidence:.2f}) - upgrading to HYBRID")
            route = "hybrid"
    
    # Log final decision
    mode_icons = {
        "rag": "🟦",
        "graph": "🟧", 
        "hybrid": "🟪",
        "vision": "🟩"
    }
    print(f"{mode_icons.get(route, '🔷')} Routed to {route.upper()} mode")
    print(f"   Reason: {analysis.explanation}")
    
    return route


def get_query_analysis(question: str, has_image: bool = False) -> QueryAnalysis:
    """
    Get full query analysis without routing.
    
    Useful for debugging or detailed logging.
    
    Args:
        question: User's query
        has_image: Whether image is attached
        
    Returns:
        Complete QueryAnalysis object
    """
    return classify_query(question, has_image=has_image)


def explain_routing(question: str) -> str:
    """
    Generate human-readable explanation of routing decision.
    
    Args:
        question: User's query
        
    Returns:
        Explanation string
    """
    analysis = classify_query(question)
    route = route_question(question, mode="auto")
    
    explanation = f"""
## Query Routing Analysis

**Question:** {question}

**Classification:**
- Type: {analysis.query_type.value}
- Confidence: {analysis.confidence:.2f}
- Reasoning Depth: {analysis.reasoning_depth.value}

**Entities Detected:** {', '.join(analysis.entities_mentioned) or 'None'}

**Routing Decision:** {route.upper()}

**Reasoning:** {analysis.explanation}

---
**Mode Descriptions:**
- 🟦 **RAG**: Document search for factual lookups
- 🟧 **GraphRAG**: Knowledge graph for relationship analysis
- 🟪 **Hybrid**: Combined analysis for best results
- 🟩 **Vision**: Image and chart analysis
"""
    return explanation


# ============================================================================
# LEGACY KEYWORD-BASED ROUTING (Fallback)
# ============================================================================

RAG_KEYWORDS = [
    "what is", "what are", "show me", "tell me",
    "list all", "display", "from file", "from document",
    "total", "number of", "how many", "summarize file"
]

GRAPH_KEYWORDS = [
    "why", "how did", "what caused", "trend", "pattern",
    "correlation", "increase", "decrease", "growth",
    "relationship", "connection", "insight", "analysis",
    "best", "worst", "top", "bottom", "customer", "product",
    "currency", "currencies", "money", "breakdown", "revenue"
]

HYBRID_KEYWORDS = [
    "compare and analyze", "comprehensive", "both",
    "combined", "overall", "deep analysis", "detailed",
    "across", "between", "over time"
]

VISION_KEYWORDS = [
    "image", "picture", "photo", "chart", "graph",
    "diagram", "invoice", "receipt", "screenshot",
    "extract from image", "read image", "ocr", "scan"
]


def legacy_route_question(question: str, has_image: bool = False) -> str:
    """
    Legacy keyword-based routing (fallback).
    
    Used when LLM-based classification is unavailable.
    """
    q_lower = question.lower()
    
    if has_image or any(kw in q_lower for kw in VISION_KEYWORDS):
        return "vision"
    
    # Score each mode
    rag_score = sum(1 for kw in RAG_KEYWORDS if kw in q_lower)
    graph_score = sum(1 for kw in GRAPH_KEYWORDS if kw in q_lower)
    hybrid_score = sum(1 for kw in HYBRID_KEYWORDS if kw in q_lower)
    
    if hybrid_score > 0:
        return "hybrid"
    elif graph_score > rag_score:
        return "graph"
    elif rag_score > 0:
        return "rag"
    else:
        return "graph"  # Default to graph for business queries


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def is_business_query(question: str) -> bool:
    """Check if query is about business data (not personal/greeting)"""
    business_indicators = [
        'product', 'customer', 'revenue', 'sales', 'invoice', 'amount',
        'total', 'lowest', 'highest', 'top', 'bottom', 'best', 'worst',
        'performance', 'trend', 'analysis', 'data', 'report', 'show',
        'list', 'which', 'what is the', 'how much', 'how many', 'compare'
    ]
    
    q_lower = question.lower()
    return any(kw in q_lower for kw in business_indicators)


def is_greeting(question: str) -> bool:
    """Check if query is a greeting/personal message"""
    greetings = [
        'hello', 'hi', 'hey', 'howdy', 'how are you',
        'thank you', 'thanks', 'bye', 'goodbye',
        'good morning', 'good evening', 'good night',
        'who are you', 'what are you', 'your name'
    ]
    
    q_lower = question.lower().strip()
    words = q_lower.split()
    
    # Short messages with greeting words
    if len(words) <= 5:
        return any(g in q_lower for g in greetings)
    
    return False
