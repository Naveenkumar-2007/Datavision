# Enterprise Agent Router - Graph-First Architecture
"""
Intelligent routing system for business analytics queries
Supports 4 modes: RAG, GraphRAG, Hybrid, Vision

Architecture: GRAPH-FIRST
- Default to graph mode (knowledge graph reasoning)
- Use RAG only for simple factual lookups
- Hybrid for complex queries
- Vision for images
"""
from core.llm import chat

# ============================================================================
# ENTERPRISE ROUTING KEYWORDS - Carefully Curated
# ============================================================================

# RAG Mode - ONLY for simple factual, document-based queries
RAG_KEYWORDS = [
    "what is", "what are",
    "show me", "tell me",
    "list all", "display",
    "from file", "from document",
    "total", "number of", "how many",
    "summarize file", "extract from"
]

# GraphRAG Mode - PRIMARY MODE (Graph-First Architecture)
# Patterns, Trends, Reasoning, Insights
GRAPH_KEYWORDS = [
    "why", "how did", "what caused",
    "trend", "pattern", "correlation",
    "increase", "decrease", "drop", "fell", "rose",
    "growth", "decline", "change",
    "compared to", "versus", "vs",
    "relationship", "connection", "link",
    "behavior", "activity", "performance",
    "insight", "analysis", "reasoning",
    "explain", "understand", "predict",
    "best", "worst", "top", "bottom",
    "customer", "product", "revenue", "sales"
]

# Hybrid Mode - Complex, Multi-faceted queries
HYBRID_KEYWORDS = [
    "compare and analyze", "comprehensive",
    "both", "combined", "overall",
    "deep analysis", "detailed breakdown",
    "show trends and data", "explain with facts",
    "across", "between", "over time"
]

# Vision Mode - Image, Chart, Visual analysis
VISION_KEYWORDS = [
    "image", "picture", "photo",
    "chart", "graph", "diagram",
    "invoice", "receipt", "screenshot",
    "extract from image", "read image",
    "analyze visual", "what's in this",
    "ocr", "scan"
]


def route_question(question: str, has_image: bool = False, mode: str = "auto") -> str:
    """
    Enterprise-grade routing for business analytics queries
    
    GRAPH-FIRST ARCHITECTURE:
    - Default to graph mode for business intelligence
    - RAG only for explicit document lookups
    - Hybrid for complex multi-source queries
    
    Args:
        question: User's business question
        has_image: Whether query includes image/file
        mode: Force specific mode ("auto", "rag", "graph", "hybrid", "vision")
        
    Returns:
        Route name: "rag", "graph", "hybrid", or "vision"
    """
    
    # Manual mode override
    if mode != "auto" and mode in ["rag", "graph", "hybrid", "vision"]:
        print(f"🎯 Manual mode selected: {mode.upper()}")
        return mode
    
    q_lower = question.lower()
    
    # 🟩 VISION MODE - Highest priority if image detected
    if has_image or any(kw in q_lower for kw in VISION_KEYWORDS):
        print(f"🟩 Routed to VISION mode (Image/Visual analysis)")
        return "vision"
    
    # Try Adaptive RAG routing first (if available)
    try:
        from agents.adaptive_rag import get_query_analysis
        analysis = get_query_analysis(question)
        
        if analysis.confidence > 0.6:
            route = analysis.recommended_route
            print(f"🎯 Adaptive routing: {route.upper()} (type={analysis.query_type.value}, conf={analysis.confidence:.2f})")
            return route
    except ImportError:
        pass
    except Exception as e:
        print(f"⚠️ Adaptive routing unavailable: {e}")
    
    # Calculate confidence scores
    rag_score = sum(1 for kw in RAG_KEYWORDS if kw in q_lower)
    graph_score = sum(1 for kw in GRAPH_KEYWORDS if kw in q_lower)
    hybrid_score = sum(1 for kw in HYBRID_KEYWORDS if kw in q_lower)
    
    # 🟪 HYBRID MODE - Complex multi-dimensional queries
    if hybrid_score > 0:
        print(f"🟪 Routed to HYBRID mode (RAG+GraphRAG combined)")
        return "hybrid"
    
    # Compare vs questions are always hybrid
    if any(word in q_lower for word in ["compare", "vs", "versus", "difference between"]):
        print(f"🟪 Routed to HYBRID mode (Comparison query)")
        return "hybrid"
    
    # 🟧 GRAPHRAG MODE - PRIMARY (Graph-First Architecture)
    # Graph handles most business intelligence queries
    graph_triggers = [
        "why", "trend", "pattern", "drop", "increase", "decrease", 
        "correlation", "segmentation", "analysis", "insight",
        "customer", "product", "revenue", "sales", "performance",
        "best", "worst", "top", "predict", "forecast"
    ]
    
    if any(kw in q_lower for kw in graph_triggers):
        print(f"🟧 Routed to GRAPHRAG mode (Pattern/Trend/Business analysis)")
        return "graph"
    
    if graph_score > rag_score:
        print(f"🟧 Routed to GRAPHRAG mode (Score: {graph_score} vs RAG: {rag_score})")
        return "graph"
    
    # 🟦 RAG MODE - Only for explicit document lookups
    rag_explicit = ["what is", "show me the file", "from document", "extract from", "summarize file"]
    if any(kw in q_lower for kw in rag_explicit):
        print(f"🟦 Routed to RAG mode (Explicit document lookup)")
        return "rag"
    
    if rag_score > graph_score + 2:  # High threshold for RAG
        print(f"🟦 Routed to RAG mode (Score: {rag_score} vs Graph: {graph_score})")
        return "rag"
    
    # 🟧 DEFAULT: GRAPH MODE (Graph-First Architecture)
    # Business queries benefit from knowledge graph reasoning
    print(f"🟧 Default routing: GRAPHRAG mode (Graph-First Architecture)")
    return "graph"

