# Mode Intelligence - Smart AI Mode Selection
"""
$5M Enterprise Feature: Intelligent mode selection and response depth.

Each mode (RAG, GraphRAG, Hybrid, Vision) has different strengths.
This module uses LLM to:
1. Suggest the best mode for each query
2. Explain why that mode is better
3. Adjust response depth based on mode

NO HARDCODING - LLM figures out optimal mode from query understanding.
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class AnalysisMode(Enum):
    RAG = "rag"
    GRAPHRAG = "graphrag"
    HYBRID = "hybrid"
    VISION = "vision"
    PREDICTION = "prediction"


@dataclass
class ModeRecommendation:
    """LLM-generated mode recommendation"""
    recommended_mode: AnalysisMode
    confidence: float  # 0-1
    reason: str  # Why this mode
    expected_depth: str  # "shallow", "medium", "deep"
    alternative_mode: Optional[AnalysisMode] = None
    

def get_mode_recommendation(
    query: str,
    available_data: Optional[Dict] = None,
    current_mode: str = "rag"
) -> ModeRecommendation:
    """
    Use LLM to recommend the best mode for a query.
    
    NO HARDCODING - LLM analyzes query and recommends mode.
    
    Mode capabilities:
    - RAG: Fast document search, simple facts, basic aggregations
    - GraphRAG: Relationships, multi-hop reasoning, "which customers buy what"
    - Hybrid: Complex queries needing both document + relationship analysis
    - Vision: Image/chart analysis
    - Prediction: Forecasting, what-if scenarios
    
    Args:
        query: User's question
        available_data: What data is available
        current_mode: Currently selected mode
        
    Returns:
        ModeRecommendation with best mode and explanation
    """
    try:
        from core.llm import chat
    except ImportError:
        return ModeRecommendation(
            recommended_mode=AnalysisMode.RAG,
            confidence=0.5,
            reason="Default mode",
            expected_depth="medium"
        )
    
    system_prompt = """You are an AI mode selector for a Business Intelligence system.

Analyze the query and recommend the BEST mode.

MODES:
1. RAG - Best for: Simple facts, totals, single-entity lookups, basic questions
   Examples: "What is total revenue?", "List all products", "Average order value"
   
2. GRAPHRAG - Best for: Relationships, comparisons, multi-entity analysis, "which X does Y"
   Examples: "Which customers buy Product A?", "Compare customer segments", "Who are connected to..."
   
3. HYBRID - Best for: Complex analysis needing both documents AND relationships
   Examples: "Why did sales drop and which customers were affected?", "Deep dive on revenue by customer and product"
   
4. PREDICTION - Best for: Forecasting, trends, what-if scenarios
   Examples: "Forecast next 3 months", "What if we increase prices?", "Predict growth"

RESPOND WITH JSON ONLY:
{
    "mode": "rag|graphrag|hybrid|prediction",
    "confidence": 0.0-1.0,
    "reason": "Brief explanation why this mode",
    "depth": "shallow|medium|deep",
    "alternative": "another mode if close second, or null"
}"""

    user_prompt = f"""Query: "{query}"
Current mode: {current_mode}

Recommend the best mode (JSON only):"""

    try:
        import json
        import re
        
        response = chat(
            messages=[{"role": "user", "content": user_prompt}],
            system=system_prompt,
            temperature=0.1,
            max_tokens=200
        )
        
        # Parse JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            data = json.loads(json_match.group())
            
            mode_map = {
                "rag": AnalysisMode.RAG,
                "graphrag": AnalysisMode.GRAPHRAG,
                "hybrid": AnalysisMode.HYBRID,
                "prediction": AnalysisMode.PREDICTION,
                "vision": AnalysisMode.VISION,
            }
            
            return ModeRecommendation(
                recommended_mode=mode_map.get(data.get("mode", "rag"), AnalysisMode.RAG),
                confidence=float(data.get("confidence", 0.7)),
                reason=data.get("reason", "Best match for this query"),
                expected_depth=data.get("depth", "medium"),
                alternative_mode=mode_map.get(data.get("alternative")) if data.get("alternative") else None
            )
    except Exception as e:
        print(f"[MODE] Recommendation failed: {e}")
    
    # Default fallback
    return ModeRecommendation(
        recommended_mode=AnalysisMode.RAG,
        confidence=0.5,
        reason="Default mode for general queries",
        expected_depth="medium"
    )


def get_mode_system_prompt(
    mode: AnalysisMode,
    query_type: str = "general"
) -> str:
    """
    Generate mode-specific system prompt for optimal responses.
    
    Each mode should respond differently:
    - RAG: Quick, direct answers
    - GraphRAG: Relationship-aware, explain connections
    - Hybrid: Comprehensive, multi-perspective
    - Prediction: Include confidence levels, assumptions
    
    Args:
        mode: Selected analysis mode
        query_type: Type of query
        
    Returns:
        System prompt tailored for the mode
    """
    base_prompt = """You are a $5M Enterprise AI Business Analyst.
    
CRITICAL RULES:
1. Use ONLY data from the context provided
2. Never make up numbers or facts
3. Be confident and direct
4. No "As an AI..." phrases
5. Use the user's currency format

"""
    
    mode_specifics = {
        AnalysisMode.RAG: """
MODE: RAG (Document Search)
RESPONSE STYLE:
- Quick, direct answers
- Focus on the specific question asked
- Include relevant data points
- Keep explanations concise
- Best for: facts, totals, simple lookups
""",
        
        AnalysisMode.GRAPHRAG: """
MODE: GRAPHRAG (Relationship Analysis)
RESPONSE STYLE:
- Explain connections and relationships
- Show how entities are linked
- Highlight patterns across relationships
- Use "connected to", "related through" language
- Best for: customer-product relationships, comparisons
""",
        
        AnalysisMode.HYBRID: """
MODE: HYBRID (Comprehensive Analysis)
RESPONSE STYLE:
- Provide multi-perspective analysis
- Combine document facts with relationship insights
- Show both the "what" and the "why"
- Include supporting evidence
- Best for: complex queries, deep analysis
""",
        
        AnalysisMode.PREDICTION: """
MODE: PREDICTION (Forecasting)
RESPONSE STYLE:
- State predictions clearly with confidence levels
- List key assumptions
- Show historical basis for forecast
- Include uncertainty ranges if applicable
- Best for: future projections, what-if scenarios
""",
        
        AnalysisMode.VISION: """
MODE: VISION (Image Analysis)
RESPONSE STYLE:
- Describe what you see in images/charts
- Extract data points from visuals
- Explain trends shown in charts
- Best for: chart interpretation, image data
""",
    }
    
    return base_prompt + mode_specifics.get(mode, mode_specifics[AnalysisMode.RAG])


def format_mode_suggestion(recommendation: ModeRecommendation, current_mode: str) -> Optional[str]:
    """
    Format a mode suggestion if a better mode is available.
    
    Only shows suggestion if confidence is high enough and different from current.
    
    Returns:
        Formatted suggestion string or None
    """
    if recommendation.recommended_mode.value == current_mode.lower():
        return None  # Already using best mode
    
    if recommendation.confidence < 0.7:
        return None  # Not confident enough
    
    return f"\n\n💡 **Tip:** For this type of query, try **{recommendation.recommended_mode.value.upper()}** mode - {recommendation.reason}"


def explain_mode_capabilities() -> str:
    """
    Generate explanation of what each mode does best.
    
    Used when user asks "what mode should I use?" or similar.
    """
    try:
        from core.llm import chat
    except ImportError:
        return """
**AI Modes:**

🔵 **RAG** - Fast answers for simple questions
   Best for: "What is total revenue?", "List top customers"

🟧 **GraphRAG** - Relationship analysis
   Best for: "Which customers buy which products?", "Compare segments"

🟪 **Hybrid** - Comprehensive deep analysis
   Best for: "Why did sales drop?", "Full business review"

🔮 **Prediction** - Forecasting and scenarios
   Best for: "Forecast next quarter", "What if we raise prices?"
"""
    
    system_prompt = """Explain the 4 AI analysis modes in a concise, helpful way.

Make it practical - give 1-2 example queries for each mode.
Format with emojis and bold headers.
Keep under 150 words total."""

    try:
        explanation = chat(
            messages=[{"role": "user", "content": "Explain when to use each AI mode"}],
            system=system_prompt,
            temperature=0.3,
            max_tokens=300
        )
        return explanation.strip()
    except:
        return """
**Choose Your AI Mode:**

🔵 **RAG** - Quick facts and lookups
🟧 **GraphRAG** - Relationships and connections  
🟪 **Hybrid** - Deep comprehensive analysis
🔮 **Prediction** - Forecasting and what-ifs
"""
