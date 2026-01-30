"""
Strict Data Grounding - ONLY User Data, NO Outside Information
================================================================

This is CRITICAL for DataVision:
- AI must ONLY use information from uploaded data
- NEVER use general knowledge
- NEVER make up numbers
- REFUSE to answer if data doesn't have the answer

This prevents hallucination and ensures trust.
"""

import logging
from typing import Dict, List, Optional, Tuple
from core.llm import chat

logger = logging.getLogger(__name__)


def build_grounded_system_prompt(
    columns: List[str],
    data_sample: str,
    currency_symbol: str = "$",
    user_name: Optional[str] = None
) -> str:
    """
    Build a system prompt that STRICTLY grounds the AI in user data.
    """
    
    prompt = f"""You are DataVision, a data analysis AI.

⚠️ CRITICAL RULES - FOLLOW EXACTLY:

1. **ONLY USE THE DATA PROVIDED** - You can ONLY answer questions using the data below.
2. **NEVER USE OUTSIDE KNOWLEDGE** - Do not use any information not in the user's data.
3. **NEVER MAKE UP NUMBERS** - Every number must come from the actual data.
4. **IF DATA DOESN'T EXIST, SAY SO** - Example: "I don't see [X] in your data."
5. **CITE YOUR SOURCE** - When giving answers, mention which column/data you used.

📊 USER'S DATA:
Columns: {columns}

Sample Data:
{data_sample[:2000]}

Currency: {currency_symbol}
{f"User: {user_name}" if user_name else ""}

🚫 FORBIDDEN:
- Do NOT answer questions about topics not in the data
- Do NOT use general knowledge about industries, markets, etc.
- Do NOT guess or estimate if data is missing
- Do NOT say "typically" or "usually" - only use actual data

✅ CORRECT BEHAVIOR:
- "Your data shows X is {currency_symbol}Y"
- "Based on the [column] column, the total is..."
- "I don't have data about [topic] in your files"
- "The data doesn't include [field], so I can't answer that"

Remember: You are a DATA ANALYST, not a general AI. Stay in your lane!"""

    return prompt


def validate_response_grounding(
    response: str,
    data_context: str,
    columns: List[str]
) -> Tuple[bool, str]:
    """
    Validate that a response is grounded in the actual data.
    Returns (is_valid, cleaned_response)
    """
    
    # Check for hallucination indicators
    hallucination_phrases = [
        "typically",
        "usually",
        "in general",
        "generally speaking",
        "most companies",
        "industry standard",
        "common practice",
        "on average in the industry",
        "according to research",
        "studies show",
        "it's common to",
        "best practices suggest",
    ]
    
    response_lower = response.lower()
    
    for phrase in hallucination_phrases:
        if phrase in response_lower:
            logger.warning(f"[GROUNDING] Hallucination detected: '{phrase}'")
            # Remove the hallucinating sentence or add disclaimer
            return False, response + "\n\n⚠️ *Note: This response may contain general information. Please verify against your actual data.*"
    
    return True, response


def create_grounded_query_prompt(
    query: str,
    columns: List[str],
    data_context: str,
    previous_response: Optional[str] = None
) -> str:
    """
    Create a query prompt that enforces data grounding.
    """
    
    prompt = f"""Answer this question using ONLY the data provided below.

❓ QUESTION: {query}

📊 AVAILABLE DATA:
Columns: {columns}

Data Context:
{data_context[:2500]}

{f"Previous Response (for follow-up context): {previous_response[:500]}" if previous_response else ""}

⚠️ STRICT RULES:
1. Use ONLY numbers and facts from the data above
2. If the data doesn't contain the answer, say "I don't have data for that"
3. Do NOT use general knowledge or make assumptions
4. Cite which column/data you're using

📝 YOUR ANSWER (based strictly on the data above):"""

    return prompt


def refuse_off_topic(query: str, columns: List[str]) -> Optional[str]:
    """
    Check if query is off-topic and generate refusal if needed.
    Uses LLM to determine this intelligently.
    """
    try:
        prompt = f"""Can this question be answered using ONLY the data columns listed?

QUESTION: "{query}"
AVAILABLE COLUMNS: {columns}

If the question is about something NOT in these columns, respond with a polite refusal.
If it CAN be answered with this data, respond with "ANSWERABLE".

Response:"""

        result = chat(prompt, temperature=0.1, max_tokens=150)
        
        if "ANSWERABLE" in result.upper():
            return None  # Can be answered
        else:
            return result.strip()  # Return the refusal message
    except:
        return None


def add_data_citation(response: str, columns: List[str]) -> str:
    """
    Ensure response cites which data columns were used.
    """
    # Check if response already has citation
    if "based on" in response.lower() or "from the" in response.lower():
        return response
    
    # Add subtle citation
    used_columns = []
    response_lower = response.lower()
    
    for col in columns:
        if col.lower() in response_lower or col.replace('_', ' ').lower() in response_lower:
            used_columns.append(col)
    
    if used_columns and len(used_columns) <= 3:
        citation = f"\n\n📊 *Data source: {', '.join(used_columns)}*"
        return response + citation
    
    return response


def ground_response(
    response: str,
    query: str,
    columns: List[str],
    data_context: str
) -> str:
    """
    Post-process response to ensure it's grounded.
    """
    # Validate grounding
    is_valid, processed = validate_response_grounding(response, data_context, columns)
    
    # Add citation
    final = add_data_citation(processed, columns)
    
    return final


def get_answerable_topics(columns: List[str]) -> str:
    """
    Generate a description of what CAN be answered with this data.
    """
    try:
        prompt = f"""Based on these data columns, what types of questions can be answered?

COLUMNS: {columns}

List 3-5 example questions that could be answered with this data.
Format as bullet points.

Examples:"""

        result = chat(prompt, temperature=0.5, max_tokens=150)
        return result.strip()
    except:
        return f"Questions about: {', '.join(columns[:5])}"
