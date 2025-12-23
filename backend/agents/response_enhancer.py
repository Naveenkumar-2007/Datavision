# Response Enhancer - ChatGPT-Quality AI Responses
"""
$5M Enterprise Feature: Makes AI responses feel intelligent and helpful.

NO HARDCODING - Uses LLM to dynamically generate:
1. Proactive Insights - "💡 I noticed..."
2. Follow-up Suggestions - "You might also want to know..."
3. Natural Tone - Conversational, not robotic
4. Helpful Error Recovery - Suggest what to do next

This is what separates a $5M product from a $5K product.
"""

from typing import Dict, List, Optional, Any
import json
import re


def generate_proactive_insight(
    query: str,
    response: str,
    data_summary: Optional[Dict] = None,
    currency_symbol: str = "₹"
) -> Optional[str]:
    """
    Use LLM to generate a proactive insight about the data.
    
    NO HARDCODING - LLM analyzes the data and finds interesting patterns.
    
    Examples of insights it might generate:
    - "💡 I noticed Customer_33 contributes 5.4% of revenue - significant dependency"
    - "💡 Your June peak was 76% higher than April's low - strong seasonality"
    - "💡 Digital Products drive 77% of revenue - consider expanding this line"
    
    Args:
        query: User's original question
        response: The answer we generated
        data_summary: Optional summary of data (top items, totals, etc.)
        currency_symbol: Currency symbol for formatting
        
    Returns:
        Insight string or None if no interesting pattern found
    """
    try:
        from core.llm import chat
    except ImportError:
        return None
    
    # Build context for LLM
    data_context = ""
    if data_summary:
        data_context = f"""
Data Summary:
- Total: {currency_symbol}{data_summary.get('total', 0):,.2f}
- Top Item: {data_summary.get('top_name', 'N/A')} = {currency_symbol}{data_summary.get('top_value', 0):,.2f}
- Bottom Item: {data_summary.get('bottom_name', 'N/A')} = {currency_symbol}{data_summary.get('bottom_value', 0):,.2f}
- Item Count: {data_summary.get('count', 0)}
"""
        if data_summary.get('top_value') and data_summary.get('total'):
            top_pct = (data_summary['top_value'] / data_summary['total']) * 100
            data_context += f"- Top Item Contributes: {top_pct:.1f}%\n"
    
    system_prompt = """You are an expert business analyst generating proactive insights.

Based on the query and response, identify ONE interesting business insight.

RULES:
1. Start with "💡 I noticed" or similar
2. Be SPECIFIC with numbers/percentages
3. Provide actionable context
4. Keep it to ONE sentence (max 30 words)
5. If nothing interesting, respond with just "NONE"

Examples:
- "💡 I noticed your top customer contributes 12% of revenue - that's significant concentration risk."
- "💡 June outperformed April by 76% - you may have seasonal patterns worth exploring."
- "💡 Digital Products at 77% of revenue suggests a strong product-market fit there."

RESPOND WITH JUST THE INSIGHT OR "NONE". Nothing else."""

    user_prompt = f"""Query: "{query}"

Response: {response[:500]}

{data_context}

Generate ONE proactive insight (or NONE if nothing interesting):"""

    try:
        insight = chat(
            messages=[{"role": "user", "content": user_prompt}],
            system=system_prompt,
            temperature=0.3,
            max_tokens=100
        )
        
        insight = insight.strip()
        
        if insight.upper() == "NONE" or len(insight) < 10:
            return None
        
        # Ensure it starts with emoji
        if not insight.startswith("💡"):
            insight = "💡 " + insight
        
        return insight
        
    except Exception as e:
        print(f"[INSIGHT] Generation failed: {e}")
        return None


def generate_followup_suggestions(
    query: str,
    query_type: str = "general",
    entities: Optional[List[str]] = None
) -> Optional[str]:
    """
    Use LLM to suggest relevant follow-up analyses.
    
    NO HARDCODING - LLM generates context-aware suggestions.
    
    Examples:
    - After "top 5 customers": "Who has the highest growth rate?"
    - After "revenue trend": "What's driving the peak in June?"
    - After "breakdown by product": "Which product has best margin?"
    
    Args:
        query: User's original question
        query_type: Type of query (ranking, trend, breakdown, etc.)
        entities: Entities mentioned (customers, products, etc.)
        
    Returns:
        Formatted suggestions or None
    """
    try:
        from core.llm import chat
    except ImportError:
        return None
    
    entities_str = ", ".join(entities[:5]) if entities else "general business data"
    
    system_prompt = """You are a business analyst suggesting follow-up analyses.

Based on what the user just asked, suggest 2-3 natural follow-up questions.

RULES:
1. Questions should be RELEVANT to what was just asked
2. Use the same entities/context
3. Progress from simple to deeper analysis
4. Keep each question SHORT (under 10 words)
5. Output EXACTLY in this format with dashes:

- First follow-up question here
- Second follow-up question here
- Third follow-up question here

RESPOND WITH JUST THE BULLET POINTS STARTING WITH DASH. No other text."""

    user_prompt = f"""User just asked: "{query}"
Query type: {query_type}
Entities involved: {entities_str}

Suggest 2-3 relevant follow-up questions (use dash bullets):"""

    try:
        suggestions = chat(
            messages=[{"role": "user", "content": user_prompt}],
            system=system_prompt,
            temperature=0.4,
            max_tokens=150
        )
        
        suggestions = suggestions.strip()
        
        if not suggestions or len(suggestions) < 10:
            return None
        
        # Clean up the suggestions - ensure proper formatting
        lines = []
        for line in suggestions.split('\n'):
            line = line.strip()
            if not line:
                continue
            # Ensure it starts with a dash
            if line.startswith('•'):
                line = '- ' + line[1:].strip()
            elif not line.startswith('-'):
                line = '- ' + line
            lines.append(line)
        
        if not lines:
            return None
        
        formatted_suggestions = '\n'.join(lines)
        
        # Format with header - clean markdown
        formatted = f"\n\n---\n💭 **You might also want to know:**\n\n{formatted_suggestions}"
        
        return formatted
        
    except Exception as e:
        print(f"[SUGGESTIONS] Generation failed: {e}")
        return None


def enhance_response_tone(
    response: str,
    query_type: str = "general"
) -> str:
    """
    Use LLM to make the response more natural and conversational.
    
    NO HARDCODING - LLM rewrites robotic phrases naturally.
    
    Changes:
    - "Your revenue breakdown by product is:" → "Here's how your revenue breaks down:"
    - "The top 5 customers are listed below." → "Here are your top 5 customers:"
    
    Args:
        response: Original response
        query_type: Type of query for context
        
    Returns:
        Enhanced response with natural tone
    """
    try:
        from core.llm import chat
    except ImportError:
        return response
    
    # Only enhance if response seems robotic
    robotic_patterns = [
        r'^Your .+ is:?\s*$',
        r'^The .+ are listed below\.?$',
        r'^Here is the .+:$',
        r'^I have found .+:$',
    ]
    
    first_line = response.split('\n')[0] if response else ""
    is_robotic = any(re.match(pattern, first_line, re.IGNORECASE) for pattern in robotic_patterns)
    
    if not is_robotic:
        return response  # Already natural enough
    
    system_prompt = """Rewrite ONLY the first line of this response to be more natural and conversational.

RULES:
1. Keep the same meaning
2. Make it friendly but professional
3. Don't change any data or numbers
4. Only rewrite the FIRST LINE
5. Return the FULL response with just the first line changed

Example rewrites:
- "Your revenue breakdown by product is:" → "Here's how your revenue breaks down by product:"
- "The top 5 customers are listed below." → "Here are your top 5 customers:"
- "Your total revenue is ₹548,765.39" → "Your total revenue comes to ₹548,765.39" (minimal change OK)"""

    try:
        enhanced = chat(
            messages=[{"role": "user", "content": response}],
            system=system_prompt,
            temperature=0.2,
            max_tokens=len(response) + 100
        )
        
        return enhanced.strip() if enhanced else response
        
    except Exception as e:
        print(f"[TONE] Enhancement failed: {e}")
        return response


def generate_helpful_error_recovery(
    error_type: str,
    context: str,
    available_data: Optional[List[str]] = None
) -> str:
    """
    Use LLM to generate helpful error messages with recovery suggestions.
    
    NO HARDCODING - LLM generates context-aware help.
    
    Changes:
    - "Data not found" → "I don't see that data yet. Try uploading a file with customer info."
    - "Comparison not possible" → "I need context for comparison. Ask 'show top products' first."
    
    Args:
        error_type: Type of error (no_data, comparison_failed, etc.)
        context: What the user was trying to do
        available_data: What data IS available
        
    Returns:
        Helpful error message with suggestions
    """
    try:
        from core.llm import chat
    except ImportError:
        return f"I couldn't complete that request. Please try rephrasing your question."
    
    available_str = ", ".join(available_data[:5]) if available_data else "unknown"
    
    system_prompt = """You are a helpful AI assistant explaining why something didn't work.

Generate a friendly, helpful error message that:
1. Explains what went wrong simply
2. Suggests what the user can do instead
3. Is encouraging, not frustrating
4. Stays under 40 words

Example:
- Input: "comparison_failed, user wanted to compare products, available: customers, revenue"
- Output: "I don't have product data in context yet. Try asking 'show me revenue by product' first, then I can compare them for you!"

RESPOND WITH JUST THE ERROR MESSAGE. No quotes or formatting."""

    user_prompt = f"""Error type: {error_type}
User was trying to: {context}
Available data: {available_str}

Generate a helpful error message:"""

    try:
        helpful_error = chat(
            messages=[{"role": "user", "content": user_prompt}],
            system=system_prompt,
            temperature=0.3,
            max_tokens=80
        )
        
        return helpful_error.strip() if helpful_error else "I couldn't complete that request. Please try a different question."
        
    except Exception as e:
        print(f"[ERROR] Recovery generation failed: {e}")
        return "I couldn't complete that request. Please try rephrasing your question."


def enhance_full_response(
    query: str,
    response: str,
    query_type: str = "general",
    data_summary: Optional[Dict] = None,
    entities: Optional[List[str]] = None,
    add_insight: bool = True,
    add_suggestions: bool = False,  # DISABLED: User data speaks for itself
    enhance_tone: bool = True,
    currency_symbol: str = "₹"
) -> str:
    """
    Full response enhancement pipeline.
    
    Applies all enhancements in order:
    1. Natural tone (if needed)
    2. Proactive insight  
    3. Follow-up suggestions
    
    Args:
        query: User's original question
        response: Generated response
        query_type: Type of query
        data_summary: Data summary for insights
        entities: Entities for suggestions
        add_insight: Whether to add proactive insight
        add_suggestions: Whether to add follow-up suggestions
        enhance_tone: Whether to enhance response tone
        currency_symbol: Currency symbol
        
    Returns:
        Fully enhanced response
    """
    enhanced = response
    
    # Step 1: Enhance tone (if needed)
    if enhance_tone:
        enhanced = enhance_response_tone(enhanced, query_type)
    
    # Step 2: Add proactive insight
    if add_insight and data_summary:
        insight = generate_proactive_insight(query, enhanced, data_summary, currency_symbol)
        if insight:
            # Insert after main response, before any charts
            if "```plotly_chart" in enhanced:
                parts = enhanced.split("```plotly_chart")
                enhanced = parts[0].rstrip() + f"\n\n{insight}\n\n```plotly_chart" + "```plotly_chart".join(parts[1:])
            else:
                enhanced = enhanced.rstrip() + f"\n\n{insight}"
    
    # Step 3: Add follow-up suggestions
    if add_suggestions:
        suggestions = generate_followup_suggestions(query, query_type, entities)
        if suggestions:
            # Add at the very end
            enhanced = enhanced.rstrip() + suggestions
    
    return enhanced


# ============================================================================
# DATA SUMMARY BUILDER - Extract summary from response for insights
# ============================================================================

def extract_data_summary_from_response(response: str, currency_symbol: str = "₹") -> Optional[Dict]:
    """
    Extract data summary from a response for insight generation.
    
    Uses pattern matching to find:
    - Total values
    - Top/bottom items
    - Percentages
    
    Returns dict with summary or None
    """
    summary = {}
    
    # Find currency values
    currency_pattern = rf'{re.escape(currency_symbol)}?\s*([\d,]+\.?\d*)'
    values = re.findall(currency_pattern, response)
    
    if values:
        parsed_values = []
        for v in values:
            try:
                parsed_values.append(float(v.replace(',', '')))
            except:
                pass
        
        if parsed_values:
            summary['total'] = max(parsed_values)  # Assume largest is total
            summary['values'] = parsed_values
    
    # Find percentages
    pct_pattern = r'(\d+\.?\d*)\s*%'
    percentages = re.findall(pct_pattern, response)
    if percentages:
        summary['percentages'] = [float(p) for p in percentages]
    
    # Find entity names (Customer_X, Product X, etc.)
    entity_pattern = r'([A-Z][a-z]*_?\d+|[A-Z][a-z]+ [A-Z][a-z]+)'
    entities = re.findall(entity_pattern, response)
    if entities:
        summary['entities'] = list(set(entities))[:5]
        if len(entities) >= 2:
            summary['top_name'] = entities[0]
            summary['bottom_name'] = entities[-1]
    
    return summary if summary else None
