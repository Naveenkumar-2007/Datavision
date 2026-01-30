"""
Smart Suggestions Generator - Competition-Winning Feature
============================================================

Generates dynamic, context-aware follow-up suggestions after each AI response.
NOT hardcoded - uses LLM to create relevant, actionable suggestions.
"""

import logging
from typing import List, Optional

from core.llm import chat

logger = logging.getLogger(__name__)


def generate_smart_suggestions(
    query: str,
    response: str,
    columns: List[str] = None,
    max_suggestions: int = 3
) -> List[str]:
    """
    Generate smart follow-up suggestions based on the conversation.
    
    Args:
        query: The user's original query
        response: The AI's response
        columns: Available data columns
        max_suggestions: Maximum number of suggestions
        
    Returns:
        List of follow-up question strings
    """
    try:
        prompt = f"""Based on this data analysis conversation, suggest {max_suggestions} natural follow-up questions.

USER QUERY: {query}
AI RESPONSE: {response[:500]}
AVAILABLE COLUMNS: {columns or "Unknown"}

Generate exactly {max_suggestions} short, specific follow-up questions that:
1. Would logically follow from the current response
2. Are valuable for deeper data analysis
3. Are concise (under 10 words each)

Format: Return ONLY the questions, one per line, no numbering:"""

        result = chat(prompt, temperature=0.7, max_tokens=150)
        
        # Parse questions
        lines = result.strip().split('\n')
        suggestions = []
        
        for line in lines:
            line = line.strip()
            # Remove numbering if present
            if line and len(line) > 5:
                # Remove common prefixes
                for prefix in ['1.', '2.', '3.', '-', '•', '*']:
                    if line.startswith(prefix):
                        line = line[len(prefix):].strip()
                
                if line and len(line) > 5:
                    suggestions.append(line)
        
        return suggestions[:max_suggestions]
        
    except Exception as e:
        logger.warning(f"Suggestion generation failed: {e}")
        return []


def calculate_confidence(
    response: str,
    data_context: str,
    columns: List[str] = None
) -> float:
    """
    Calculate confidence score for a response based on data grounding.
    
    Returns:
        Float between 0.0 and 1.0
    """
    # Base confidence
    confidence = 0.7
    
    # Check if response mentions actual data
    if columns:
        columns_mentioned = sum(1 for col in columns if col.lower() in response.lower())
        if columns_mentioned > 0:
            confidence += 0.1
        if columns_mentioned > 2:
            confidence += 0.1
    
    # Check for weak language (lower confidence)
    weak_phrases = ['might', 'could be', 'possibly', 'perhaps', 'i think', "i don't have"]
    if any(phrase in response.lower() for phrase in weak_phrases):
        confidence -= 0.2
    
    # Check for strong data-based language
    strong_phrases = ['the data shows', 'based on your data', 'from the', 'total of', 'according to']
    if any(phrase in response.lower() for phrase in strong_phrases):
        confidence += 0.15
    
    # Check for numbers (indicates actual data usage)
    import re
    numbers = re.findall(r'\b\d+(?:,\d+)*(?:\.\d+)?\b', response)
    if len(numbers) > 2:
        confidence += 0.1
    
    # Clamp between 0 and 1
    return max(0.1, min(1.0, confidence))


def generate_quick_actions(query_type: str, response: str) -> List[str]:
    """
    Generate quick action buttons based on query type.
    """
    actions = []
    
    query_lower = query_type.lower()
    
    if 'chart' in response.lower() or 'graph' in response.lower():
        actions.append("📊 Show as table")
    
    if any(w in query_lower for w in ['total', 'sum', 'count']):
        actions.append("📈 Show trend")
        actions.append("📊 Add to dashboard")
    
    if 'compare' in query_lower:
        actions.append("📊 Side-by-side chart")
    
    return actions[:3]
