"""
Query Dispatcher - Routes queries to appropriate handlers
==========================================================

Dispatches queries to the right mode/engine based on:
1. User-selected mode
2. Query intent analysis
3. Data availability
"""

import logging
from typing import Dict, Optional, Tuple, Any
from enum import Enum

logger = logging.getLogger(__name__)


class DispatchMode(Enum):
    """Available dispatch modes"""
    RAG = "rag"
    GRAPH = "graph"
    HYBRID = "hybrid"
    PREDICTION = "prediction"
    AGENTIC = "agentic"
    VISION = "vision"
    ANALYST = "analyst"
    DEEP_THINK = "deep"
    AGENT = "agent"


def dispatch_query(
    query: str,
    user_mode: str,
    has_data: bool = True,
    has_image: bool = False
) -> Tuple[DispatchMode, Dict[str, Any]]:
    """
    Dispatch a query to the appropriate handler.
    
    Args:
        query: The user's query
        user_mode: Mode selected by user
        has_data: Whether user has uploaded data
        has_image: Whether query includes an image
        
    Returns:
        Tuple of (DispatchMode, context_dict)
    """
    query_lower = query.lower()
    context = {}
    
    # Handle image queries -> Vision mode
    if has_image:
        return DispatchMode.VISION, {"reason": "Image attached"}
    
    # Respect user's explicit mode selection
    mode_map = {
        "rag": DispatchMode.RAG,
        "graph": DispatchMode.GRAPH,
        "graphrag": DispatchMode.GRAPH,
        "hybrid": DispatchMode.HYBRID,
        "prediction": DispatchMode.PREDICTION,
        "agentic": DispatchMode.AGENTIC,
        "vision": DispatchMode.VISION,
        "analyst": DispatchMode.ANALYST,
        "deep": DispatchMode.DEEP_THINK,
        "predict": DispatchMode.PREDICTION,
        "agent": DispatchMode.AGENT,
    }
    
    if user_mode in mode_map:
        return mode_map[user_mode], {"reason": f"User selected {user_mode}"}
    
    # Auto-dispatch based on query analysis
    if any(w in query_lower for w in ['predict', 'forecast', 'will', 'next month']):
        return DispatchMode.PREDICTION, {"reason": "Prediction query detected"}
    
    if any(w in query_lower for w in ['relationship', 'connected', 'link', 'path']):
        return DispatchMode.GRAPH, {"reason": "Relationship query detected"}
    
    if any(w in query_lower for w in ['compare', 'vs', 'versus']):
        return DispatchMode.HYBRID, {"reason": "Comparison query detected"}
    
    if any(w in query_lower for w in ['send', 'email', 'schedule', 'create']):
        return DispatchMode.AGENTIC, {"reason": "Action query detected"}
    
    # Default to RAG
    return DispatchMode.RAG, {"reason": "Default RAG mode"}


def get_mode_description(mode: DispatchMode) -> str:
    """Get human-readable description of a mode"""
    descriptions = {
        DispatchMode.RAG: "Document-based retrieval and generation",
        DispatchMode.GRAPH: "Knowledge graph relationship analysis",
        DispatchMode.HYBRID: "Combined RAG and Graph analysis",
        DispatchMode.PREDICTION: "Forecasting and trend analysis",
        DispatchMode.AGENTIC: "AI agent with tool execution",
        DispatchMode.VISION: "Image and visual analysis",
        DispatchMode.ANALYST: "Smart data analysis with auto-routing",
        DispatchMode.DEEP_THINK: "Deep reasoning with chain of thought",
        DispatchMode.AGENT: "Autonomous multi-tool orchestration",
    }
    return descriptions.get(mode, "Unknown mode")
