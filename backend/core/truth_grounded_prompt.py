# Truth-Grounded Business AI - Master System Prompt
"""
This module contains the CORE SYSTEM PROMPT that makes the AI behave like ChatGPT/Claude.

PRINCIPLES:
1. TRUTH OVER COMPLETENESS - Never guess or hallucinate
2. DATA GOVERNANCE - Every number must be traceable
3. CONTEXT MEMORY - Resolve "above", "that", "previous"
4. VISUALIZATION TRUTH - Charts from computed data only
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ConversationContext:
    """Stores what was discussed for follow-up resolution"""
    last_topic: Optional[str] = None           # "revenue", "customers", "products"
    last_result_type: Optional[str] = None     # "table", "chart", "number", "text"
    last_chart_type: Optional[str] = None      # "bar", "line", "pie"
    last_data_shown: Optional[Dict] = None     # The actual data displayed
    last_answer: Optional[str] = None          # The text response
    entities_mentioned: List[str] = field(default_factory=list)  # ["Microsoft", "June"]
    numbers_shown: Dict[str, float] = field(default_factory=dict)  # {"total_revenue": 13840000}
    timestamp: datetime = field(default_factory=datetime.now)


# Global context store per session
_context_store: Dict[str, ConversationContext] = {}


def get_context(session_id: str) -> ConversationContext:
    """Get or create context for a session"""
    if session_id not in _context_store:
        _context_store[session_id] = ConversationContext()
    return _context_store[session_id]


def update_context(
    session_id: str,
    topic: str = None,
    result_type: str = None,
    chart_type: str = None,
    data_shown: Dict = None,
    answer: str = None,
    entities: List[str] = None,
    numbers: Dict[str, float] = None
):
    """Update context after each response"""
    ctx = get_context(session_id)
    
    if topic:
        ctx.last_topic = topic
    if result_type:
        ctx.last_result_type = result_type
    if chart_type:
        ctx.last_chart_type = chart_type
    if data_shown:
        ctx.last_data_shown = data_shown
    if answer:
        ctx.last_answer = answer
    if entities:
        ctx.entities_mentioned = entities
    if numbers:
        ctx.numbers_shown.update(numbers)
    ctx.timestamp = datetime.now()


def resolve_above_reference(session_id: str, question: str) -> tuple:
    """
    Resolve references like "above", "that", "explain this".
    
    Returns: (resolved_question, resolution_context)
    """
    ctx = get_context(session_id)
    q_lower = question.lower().strip()
    
    resolution = {
        "had_reference": False,
        "reference_type": None,
        "resolved_to": None
    }
    
    # Check for "above" / "that" / "this" references
    above_triggers = [
        "above", "that", "this", "previous", "earlier",
        "explain it", "explain that", "what is this",
        "tell me more", "more details", "elaborate"
    ]
    
    is_followup = any(trigger in q_lower for trigger in above_triggers)
    
    if is_followup and ctx.last_topic:
        resolution["had_reference"] = True
        
        # Determine what "above" refers to
        if ctx.last_chart_type:
            resolution["reference_type"] = "chart"
            resolution["resolved_to"] = f"{ctx.last_chart_type} chart showing {ctx.last_topic}"
        elif ctx.last_result_type == "table":
            resolution["reference_type"] = "table"
            resolution["resolved_to"] = f"table showing {ctx.last_topic}"
        elif ctx.last_result_type == "number":
            resolution["reference_type"] = "number"
            resolution["resolved_to"] = f"the {ctx.last_topic} value"
        else:
            resolution["reference_type"] = "topic"
            resolution["resolved_to"] = ctx.last_topic
        
        # Build enhanced question with context
        if "explain" in q_lower:
            enhanced = f"Explain the {resolution['resolved_to']} that was just shown."
            if ctx.last_data_shown:
                enhanced += f" The data was: {ctx.last_data_shown}"
        elif "terminology" in q_lower:
            enhanced = f"Explain the terminology used in the {ctx.last_topic} analysis: {ctx.last_answer}"
        else:
            enhanced = f"{question} (Context: referring to {resolution['resolved_to']})"
        
        return enhanced, resolution
    
    return question, resolution


# =============================================================================
# MASTER SYSTEM PROMPT - Truth-Grounded AI
# =============================================================================

def get_truth_grounded_prompt(
    mode: str = "rag",
    currency_symbol: str = "$",
    has_data: bool = True,
    context: Optional[ConversationContext] = None
) -> str:
    """
    Generate the MASTER SYSTEM PROMPT for truth-grounded AI.
    
    This is the CORE of making the AI behave like ChatGPT/Claude.
    """
    
    context_section = ""
    if context and context.last_topic:
        context_section = f"""
CONVERSATION CONTEXT:
- Last topic discussed: {context.last_topic}
- Last result type: {context.last_result_type or 'text'}
- Last chart: {context.last_chart_type or 'none'}
- Numbers mentioned: {context.numbers_shown}

If user says "above", "that", "this", "explain" - they refer to this context.
"""
    
    prompt = f"""═══════════════════════════════════════════════════════════════════════════════
                    TRUTH-GROUNDED BUSINESS AI SYSTEM
                    (ChatGPT/Claude Level Intelligence)
═══════════════════════════════════════════════════════════════════════════════

You are a PRODUCTION-GRADE Enterprise AI, engineered to the same principles as 
ChatGPT and Claude.

🚨 CORE PRINCIPLE: TRUTH OVER COMPLETENESS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Accuracy is MANDATORY
- Silence or clarification is ALWAYS better than a wrong answer
- Never guess, invent, approximate, or hallucinate

You must NEVER:
❌ Guess missing values
❌ Invent explanations
❌ Fake charts or data
❌ Simulate insights
❌ Generalize beyond available data
❌ Say "based on typical patterns" or "usually"

📊 DATA GOVERNANCE (STRICT)
━━━━━━━━━━━━━━━━━━━━━━━━━━━
All responses must be grounded in the data context provided.

Before answering:
1. Identify what data is available
2. Check if the question can be answered from this data
3. If NOT - say: "I don't have enough information to answer this accurately."

Currency: {currency_symbol}

{context_section}

📝 RESPONSE FORMAT
━━━━━━━━━━━━━━━━━━
- Be DIRECT and CONFIDENT (no "As an AI...")
- Use the exact numbers from the data
- If showing a calculation, show: "₹X × Y = ₹Z"
- Reference specific entities by name

🧠 QUERY UNDERSTANDING PIPELINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
For every query:
1. INTENT: What does the user actually want?
2. DATA CHECK: Do I have the data to answer?
3. COMPUTE: Calculate from the source data
4. VALIDATE: Cross-check the numbers
5. RESPOND: Clear, grounded, honest

🤖 FOLLOW-UP HANDLING
━━━━━━━━━━━━━━━━━━━━
When user says "explain above", "what is that", "tell me more":
- Refer to the MOST RECENT topic/chart/number discussed
- Don't start a new unrelated analysis
- Explain what was just shown

✅ SELF-CHECK (Before responding)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ask yourself:
- Is every claim supported by data from context?
- Can I point to where each number comes from?
- Am I answering the EXACT question asked?

If ANY answer is NO → Ask for clarification instead.

═══════════════════════════════════════════════════════════════════════════════
                    YOUR SUCCESS = USER TRUSTS YOU FOR REAL DECISIONS
═══════════════════════════════════════════════════════════════════════════════
"""
    
    return prompt


def get_followup_detection_prompt() -> str:
    """Prompt for detecting follow-up queries"""
    return """Analyze if this query is a follow-up to previous conversation.

Follow-up indicators:
- "above", "that", "this", "previous", "earlier"
- "explain it", "why?", "how?", "what about?"
- "tell me more", "elaborate", "details"
- Pronouns referring to previous topics: "it", "they", "them"

Return JSON:
{
    "is_followup": true/false,
    "reference_type": "chart" | "number" | "table" | "topic" | "none",
    "likely_refers_to": "description of what user is asking about"
}
"""


def validate_response_against_data(
    response: str,
    data_context: str,
    numbers_in_response: List[float]
) -> Dict[str, Any]:
    """
    Validate that response numbers exist in the data context.
    
    Returns validation result.
    """
    validation = {
        "is_valid": True,
        "issues": [],
        "numbers_verified": []
    }
    
    for num in numbers_in_response:
        # Check if number appears in context
        num_str = str(num)
        formatted_num = f"{num:,.2f}"
        
        if num_str in data_context or formatted_num in data_context:
            validation["numbers_verified"].append(num)
        else:
            # Try checking if it's a reasonable calculation
            # (e.g., sum of values in context)
            validation["issues"].append(f"Number {num} not found in source data")
            validation["is_valid"] = False
    
    return validation


# =============================================================================
# ERROR HANDLING - No Technical Errors to Users
# =============================================================================

def get_graceful_error_response(error_type: str, context: str = "") -> str:
    """
    Generate a helpful response instead of technical errors.
    
    NEVER show "PROCESSING ERROR" to users.
    """
    responses = {
        "no_data": "I don't have the data needed to answer this question. Could you upload a relevant file or clarify what data you'd like me to analyze?",
        
        "unclear_query": "I want to make sure I understand your question correctly. Could you please clarify what specific information you're looking for?",
        
        "missing_context": "I'm not sure what 'above' or 'that' refers to in your question. Could you specify what you'd like me to explain?",
        
        "calculation_error": "I encountered an issue calculating this. Let me try a different approach, or could you rephrase your question?",
        
        "chart_not_applicable": "A visualization wouldn't be meaningful for this data. Would you like me to present the information in a different format?",
        
        "default": "I couldn't process that request as expected. Could you try rephrasing your question?"
    }
    
    return responses.get(error_type, responses["default"])
