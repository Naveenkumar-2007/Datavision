# Enterprise Agent Router v3.0 - Simple & Clean
"""
Simple routing system for business analytics queries.
Supports 5 modes: analyst, deep, vision, predict, agent

NO DEPENDENCIES on deleted files!
"""

from typing import Tuple


# ============================================================================
# KEYWORD-BASED ROUTING (Simple & Reliable)
# ============================================================================

RAG_KEYWORDS = [
    "what is", "what are", "show me", "tell me",
    "list all", "display", "from file", "from document",
    "total", "number of", "how many", "summarize"
]

GRAPH_KEYWORDS = [
    "why", "how did", "what caused", "trend", "pattern",
    "correlation", "relationship", "connection", "insight",
    "best", "worst", "top", "bottom", "customer", "product"
]

PREDICT_KEYWORDS = [
    "predict", "forecast", "future", "next month", "next year",
    "projection", "estimate", "what if", "scenario", "expect"
]

VISION_KEYWORDS = [
    "image", "picture", "photo", "chart", "graph",
    "diagram", "invoice", "receipt", "screenshot", "ocr", "scan"
]

AGENT_KEYWORDS = [
    "search", "find online", "web", "latest", "news",
    "industry", "benchmark", "competitor", "market", "external"
]


def route_question(
    question: str, 
    has_image: bool = False, 
    mode: str = "auto"
) -> str:
    """
    Simple routing for business analytics queries.
    
    Args:
        question: User's business question
        has_image: Whether query includes image/file
        mode: Force specific mode ("auto" or mode name)
        
    Returns:
        Route name: "analyst", "deep", "vision", "predict", "agent", 
                    or legacy modes: "rag", "graph", "hybrid"
    """
    
    # New 5 modes - pass through directly
    NEW_MODES = ["analyst", "deep", "vision", "predict", "agent"]
    if mode in NEW_MODES:
        print(f"🚀 New mode selected: {mode.upper()}")
        return mode
    
    # Legacy modes - pass through
    LEGACY_MODES = ["rag", "graph", "hybrid", "graphrag", "prediction", "agentic", "multirag"]
    if mode in LEGACY_MODES:
        print(f"🔷 Legacy mode selected: {mode.upper()}")
        return mode
    
    # AI Model modes - pass through directly
    AI_MODEL_MODES = ["deepseek-chat", "mistral-7b", "llama-70b"]
    if mode in AI_MODEL_MODES:
        print(f"🤖 AI Model mode selected: {mode}")
        return mode
    
    # Vision mode priority
    if has_image:
        print(f"🟩 Routed to VISION mode (Image detected)")
        return "vision"
    
    # Auto-routing based on keywords
    q_lower = question.lower()
    
    # Check each category
    if any(kw in q_lower for kw in VISION_KEYWORDS):
        print(f"🟩 Routed to VISION mode (Image keywords)")
        return "vision"
    
    if any(kw in q_lower for kw in PREDICT_KEYWORDS):
        print(f"🔮 Routed to PREDICT mode (Forecast keywords)")
        return "predict"
    
    if any(kw in q_lower for kw in AGENT_KEYWORDS):
        print(f"🤖 Routed to AGENT mode (Web/external keywords)")
        return "agent"
    
    # Score graph vs rag
    graph_score = sum(1 for kw in GRAPH_KEYWORDS if kw in q_lower)
    rag_score = sum(1 for kw in RAG_KEYWORDS if kw in q_lower)
    
    if graph_score > rag_score:
        print(f"🟧 Routed to GRAPH mode (Relationship analysis)")
        return "graph"
    elif rag_score > 0:
        print(f"🟦 Routed to RAG mode (Document search)")
        return "rag"
    else:
        # Default to analyst mode for new 5-mode system
        print(f"📊 Routed to ANALYST mode (Default)")
        return "analyst"


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
