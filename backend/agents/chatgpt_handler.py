# ChatGPT-Style Query Handler
"""
$5M Enterprise Feature: LLM-Driven Query Understanding and Response

This module makes the AI Business Analyst work EXACTLY like ChatGPT:
1. NO HARDCODED PATTERNS - LLM decides everything
2. Dynamic response generation based on query understanding
3. Mode-specific quality differences
4. Natural, conversational tone

The key insight: ChatGPT doesn't have if/else patterns for query types.
It uses LLM understanding for everything. We do the same here.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json


@dataclass
class QueryUnderstanding:
    """What the LLM understood from the query"""
    intent: str              # What user wants (view, compare, predict, explain...)
    entities: List[str]      # What entities mentioned (customers, products, dates...)
    metrics: List[str]       # What metrics (revenue, orders, growth...)
    time_range: Optional[str] # Time context if any
    chart_request: Optional[str]  # If user wants a specific chart
    response_style: str      # How to respond (brief, detailed, table, list...)
    confidence: float        # How confident we are


def understand_query_with_llm(
    query: str,
    available_columns: List[str],
    sample_data: Optional[str] = None
) -> QueryUnderstanding:
    """
    Use LLM to understand the query - NO PATTERN MATCHING.
    
    This is the core difference from traditional chatbots.
    We ask the LLM to understand the query and tell us what the user wants.
    """
    try:
        from core.llm import chat
    except ImportError:
        # Fallback if LLM not available
        return QueryUnderstanding(
            intent="general",
            entities=[],
            metrics=[],
            time_range=None,
            chart_request=None,
            response_style="detailed",
            confidence=0.5
        )
    
    system_prompt = """You are a query analyzer for a Business Intelligence system.

Analyze the user's query and extract understanding in JSON format.

RESPOND WITH ONLY JSON, no explanation:
{
    "intent": "view|compare|trend|rank|breakdown|predict|explain|aggregate",
    "entities": ["list", "of", "entities", "mentioned"],
    "metrics": ["revenue", "orders", "or", "other", "metrics"],
    "time_range": "if mentioned, e.g., 'last month', 'Q3', or null",
    "chart_request": "pie|bar|line|area|scatter|null if not specified",
    "response_style": "brief|detailed|table|list|one_line",
    "confidence": 0.0-1.0
}"""

    columns_context = f"Available data columns: {', '.join(available_columns[:20])}" if available_columns else ""
    
    user_prompt = f"""Query: "{query}"
{columns_context}

Analyze and respond with JSON only:"""

    try:
        import re
        
        response = chat(
            messages=[{"role": "user", "content": user_prompt}],
            system=system_prompt,
            temperature=0.1,
            max_tokens=300
        )
        
        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            data = json.loads(json_match.group())
            return QueryUnderstanding(
                intent=data.get("intent", "general"),
                entities=data.get("entities", []),
                metrics=data.get("metrics", []),
                time_range=data.get("time_range"),
                chart_request=data.get("chart_request"),
                response_style=data.get("response_style", "detailed"),
                confidence=float(data.get("confidence", 0.7))
            )
    except Exception as e:
        print(f"[QUERY] LLM understanding failed: {e}")
    
    return QueryUnderstanding(
        intent="general",
        entities=[],
        metrics=[],
        time_range=None,
        chart_request=None,
        response_style="detailed",
        confidence=0.5
    )


def generate_chatgpt_prompt(
    query: str,
    understanding: QueryUnderstanding,
    context: str,
    mode: str = "rag",
    currency_symbol: str = "₹"
) -> str:
    """
    Generate a ChatGPT-quality system prompt based on understanding.
    
    This prompt is dynamically generated - no template matching.
    """
    try:
        from core.llm import chat
    except ImportError:
        return _get_fallback_prompt(mode, currency_symbol)
    
    system_prompt = """You are an AI prompt engineer creating system prompts.

Based on the query understanding, generate a system prompt that will make the AI respond naturally like ChatGPT.

The prompt should:
1. Be specific to the user's intent
2. Use the exact entities and metrics mentioned
3. Specify the response format clearly
4. Sound natural, not robotic
5. Be concise (max 150 words)

Respond with JUST the system prompt text, no quotes or meta-text."""

    intent_context = f"""
Query: "{query}"
Intent: {understanding.intent}
Entities: {', '.join(understanding.entities) or 'general data'}
Metrics: {', '.join(understanding.metrics) or 'various'}
Response style: {understanding.response_style}
Mode: {mode}
Currency: {currency_symbol}
"""

    try:
        generated_prompt = chat(
            messages=[{"role": "user", "content": intent_context}],
            system=system_prompt,
            temperature=0.3,
            max_tokens=300
        )
        
        if generated_prompt and len(generated_prompt) > 50:
            # Add essential rules
            return f"""{generated_prompt.strip()}

CRITICAL RULES:
- Use ONLY data from the context provided - never make up numbers
- Format currency as {currency_symbol}X,XXX.XX
- Be confident and direct, no "As an AI..." phrases"""
    
    except Exception as e:
        print(f"[PROMPT] Generation failed: {e}")
    
    return _get_fallback_prompt(mode, currency_symbol)


def _get_fallback_prompt(mode: str, currency_symbol: str) -> str:
    """Fallback prompt if LLM generation fails"""
    mode_prompts = {
        "rag": f"""You are a precise Business Analyst. Answer questions using only the provided document context.
Be direct, use {currency_symbol} for currency. If data isn't available, say so clearly.""",
        
        "graphrag": f"""You are a Relationship Analyst exploring connections in business data.
Focus on how entities relate (customers-products, trends-causes). Use {currency_symbol} for currency.
Explain connections naturally, like telling a story about the business.""",
        
        "hybrid": f"""You are a Comprehensive Business Analyst using both document search and relationship analysis.
Provide deep insights by combining factual data with relationship patterns.
Use {currency_symbol} for currency. Be thorough but structured.""",
        
        "prediction": f"""You are a Forecasting Analyst predicting future business outcomes.
Base predictions on historical patterns in the data. Include confidence levels.
Use {currency_symbol} for currency. Clearly state assumptions.""",
    }
    
    return mode_prompts.get(mode, mode_prompts["rag"])


def should_generate_chart(
    query: str,
    understanding: QueryUnderstanding
) -> Tuple[bool, Optional[str]]:
    """
    Use LLM to decide if a chart should be generated.
    
    Returns: (should_generate, chart_type)
    """
    # If user explicitly requested a chart type, use it
    if understanding.chart_request:
        return True, understanding.chart_request
    
    try:
        from core.llm import chat
    except ImportError:
        return False, None
    
    system_prompt = """Decide if this query needs a chart visualization.

Respond with ONLY JSON:
{
    "needs_chart": true/false,
    "chart_type": "bar|line|pie|area|scatter|null",
    "reason": "brief explanation"
}

Chart guidelines:
- Comparisons/rankings → bar
- Trends over time → line
- Proportions/breakdown → pie
- Correlations → scatter
- Simple facts → no chart needed"""

    try:
        import re
        
        response = chat(
            messages=[{"role": "user", "content": f'Query: "{query}"\nIntent: {understanding.intent}'}],
            system=system_prompt,
            temperature=0.1,
            max_tokens=100
        )
        
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            data = json.loads(json_match.group())
            return data.get("needs_chart", False), data.get("chart_type")
    
    except Exception as e:
        print(f"[CHART] Decision failed: {e}")
    
    return False, None


def get_mode_quality_settings(mode: str) -> Dict[str, Any]:
    """
    Get quality settings for each mode.
    
    Each mode has different:
    - Max tokens (response length)
    - Temperature (creativity)
    - Detail level
    """
    settings = {
        "rag": {
            "max_tokens": 800,
            "temperature": 0.2,
            "detail_level": "concise",
            "includes_reasoning": False,
            "description": "Fast, direct answers from documents"
        },
        "graphrag": {
            "max_tokens": 1200,
            "temperature": 0.3,
            "detail_level": "medium",
            "includes_reasoning": True,
            "description": "Relationship-aware analysis with explanations"
        },
        "hybrid": {
            "max_tokens": 1500,
            "temperature": 0.3,
            "detail_level": "comprehensive",
            "includes_reasoning": True,
            "description": "Deep analysis combining multiple sources"
        },
        "prediction": {
            "max_tokens": 1200,
            "temperature": 0.4,
            "detail_level": "detailed",
            "includes_reasoning": True,
            "description": "Forward-looking analysis with confidence levels"
        },
        "vision": {
            "max_tokens": 1000,
            "temperature": 0.2,
            "detail_level": "medium",
            "includes_reasoning": False,
            "description": "Image and chart analysis"
        }
    }
    
    return settings.get(mode, settings["rag"])


def enhance_response_like_chatgpt(
    response: str,
    query: str,
    mode: str,
    add_insights: bool = True,
    add_suggestions: bool = True
) -> str:
    """
    Enhance response to feel like ChatGPT.
    
    Uses LLM to:
    1. Add natural transitions
    2. Include relevant insights
    3. Suggest follow-ups
    4. Maintain conversational tone
    """
    try:
        from core.llm import chat
    except ImportError:
        return response
    
    if not add_insights and not add_suggestions:
        return response
    
    system_prompt = """Enhance this business analysis response to be more like ChatGPT.

ADD to the end (after the main content):
1. One brief insight (if interesting pattern exists)
2. 2-3 follow-up question suggestions

Format:
💡 [Optional insight - only if genuinely interesting]

---
💭 **You might also want to know:**
- [Relevant follow-up 1]
- [Relevant follow-up 2]

DO NOT change the main response. Only ADD to the end.
If nothing interesting to add, just return the original response."""

    try:
        enhanced = chat(
            messages=[{"role": "user", "content": f"Query: {query}\n\nResponse to enhance:\n{response}"}],
            system=system_prompt,
            temperature=0.4,
            max_tokens=len(response) + 300
        )
        
        if enhanced and len(enhanced) > len(response):
            return enhanced.strip()
    
    except Exception as e:
        print(f"[ENHANCE] Failed: {e}")
    
    return response
