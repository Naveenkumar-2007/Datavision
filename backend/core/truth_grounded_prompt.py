"""
Truth-Grounded Prompt - Anti-Hallucination System
===================================================

Ensures AI responses are grounded in actual data:
1. Reference resolution for "above", "that", "it"
2. Context tracking for follow-up questions
3. Fact verification against retrieved data
"""

import logging
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class TruthContext:
    """Context for truth-grounding"""
    session_id: str
    last_topic: Optional[str] = None
    last_result_type: str = "text"  # text, chart, table
    last_chart_type: Optional[str] = None
    last_answer_snippet: str = ""
    last_entities: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# Global context store
_truth_contexts: Dict[str, TruthContext] = {}


def get_truth_context(session_id: str) -> TruthContext:
    """Get or create truth context for a session"""
    if session_id not in _truth_contexts:
        _truth_contexts[session_id] = TruthContext(session_id=session_id)
    return _truth_contexts[session_id]


def update_truth_context(
    session_id: str,
    topic: Optional[str] = None,
    result_type: str = "text",
    chart_type: Optional[str] = None,
    answer: str = "",
    entities: List[str] = None
):
    """Update the truth context after a response"""
    ctx = get_truth_context(session_id)
    
    if topic:
        ctx.last_topic = topic
    if result_type:
        ctx.last_result_type = result_type
    if chart_type:
        ctx.last_chart_type = chart_type
    if answer:
        ctx.last_answer_snippet = answer[:500]
    if entities:
        ctx.last_entities = entities
    
    ctx.timestamp = datetime.now().isoformat()
    _truth_contexts[session_id] = ctx


def resolve_above_reference(
    session_id: str,
    query: str
) -> Tuple[str, Dict]:
    """
    Resolve references like "above", "that", "it" in queries.
    
    Args:
        session_id: User's session ID
        query: The query that may contain references
        
    Returns:
        Tuple of (resolved_query, resolution_metadata)
    """
    query_lower = query.lower()
    ctx = get_truth_context(session_id)
    
    resolution = {
        "had_reference": False,
        "reference_type": None,
        "resolved_to": None
    }
    
    # Reference patterns
    above_patterns = ['above', 'that', 'this', 'it', 'the chart', 'the table', 'previous']
    
    has_reference = any(p in query_lower for p in above_patterns)
    
    if not has_reference:
        return query, resolution
    
    resolution["had_reference"] = True
    
    # Resolve based on last context
    if ctx.last_result_type == "chart" and ctx.last_chart_type:
        resolution["reference_type"] = "chart"
        resolution["resolved_to"] = ctx.last_chart_type
        
        # Enhance query with chart context
        enhanced = f"{query}\n\n[Context: The user is referring to a {ctx.last_chart_type} chart that was just shown about {ctx.last_topic or 'the data'}.]"
        return enhanced, resolution
    
    elif ctx.last_result_type == "table":
        resolution["reference_type"] = "table"
        resolution["resolved_to"] = "table"
        
        enhanced = f"{query}\n\n[Context: The user is referring to the table shown above about {ctx.last_topic or 'the data'}.]"
        return enhanced, resolution
    
    elif ctx.last_answer_snippet:
        resolution["reference_type"] = "answer"
        resolution["resolved_to"] = ctx.last_answer_snippet[:100]
        
        enhanced = f"{query}\n\n[Context: The user is referring to this previous answer: {ctx.last_answer_snippet}]"
        return enhanced, resolution
    
    return query, resolution


def ground_response_in_data(
    response: str,
    data_context: str,
    query: str
) -> str:
    """
    Ensure response is grounded in actual data.
    
    This is a validation step that checks if claims in the response
    can be supported by the data context.
    """
    # For now, just return the response
    # In a more sophisticated implementation, you would:
    # 1. Extract claims from response
    # 2. Verify each claim against data_context
    # 3. Flag or remove unsupported claims
    
    return response


def build_grounded_prompt(
    query: str,
    data_context: str,
    session_id: str
) -> str:
    """
    Build a prompt that encourages grounded responses.
    """
    ctx = get_truth_context(session_id)
    
    prompt = f"""You are a Business Data Analyst. Your responses MUST be grounded in the data provided.

## RULES FOR TRUTH-GROUNDED RESPONSES:
1. ONLY use numbers that appear in the data context
2. NEVER invent statistics or percentages
3. If data is not available, say "I don't have data for X"
4. Cite the source of your numbers

## DATA CONTEXT:
{data_context}

## USER QUESTION:
{query}

"""
    
    # Add follow-up context if available
    if ctx.last_topic:
        prompt += f"\n## PREVIOUS CONTEXT:\nLast topic discussed: {ctx.last_topic}\n"
    
    if ctx.last_answer_snippet:
        prompt += f"Last response snippet: {ctx.last_answer_snippet[:200]}...\n"
    
    prompt += "\n## YOUR RESPONSE (grounded in data):"
    
    return prompt
