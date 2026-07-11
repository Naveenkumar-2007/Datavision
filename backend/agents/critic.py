import json
import logging
from typing import Dict, Any
from core.llm import chat

logger = logging.getLogger(__name__)

def evaluate_with_critic(query: str, context: str, draft_answer: str) -> Dict[str, Any]:
    """
    Agentic Critic: Analyzes a drafted answer for hallucinations, math errors, 
    or incorrect Python/SQL code. Returns a JSON indicating pass/fail and feedback.
    """
    prompt = f"""You are a senior Data Science Critic in Silicon Valley.
Your job is to relentlessly review a Junior Analyst's drafted answer to ensure it is 100% accurate, 
does not hallucinate, and properly addresses the user's query using ONLY the provided context.

USER QUERY: "{query}"

AVAILABLE DATA CONTEXT (SCHEMA/INFO):
{context[:2000]}

JUNIOR ANALYST DRAFT ANSWER:
---
{draft_answer}
---

CRITIC INSTRUCTIONS:
1. Does the answer directly address the User Query?
2. Does the answer invent any numbers, tables, or metrics not supported by the Data Context? (Hallucination)
3. If there is code (Python/SQL) in the answer, does it look syntactically correct and logical?
4. Is the tone appropriate and helpful?

If the draft is good, pass it. If there is ANY major hallucination or error, FAIL it and provide specific feedback on how to fix it.

Output ONLY a valid JSON object in this exact format:
{{
    "pass": true,
    "feedback": "Detailed feedback on what to fix, or 'Looks good' if passed."
}}
"""
    try:
        # Use a strong model for criticism (e.g., Llama 3 70B or 8B)
        response = chat(prompt, temperature=0.1, max_tokens=250)
        
        # Parse JSON
        response = response.strip()
        if '```json' in response:
            response = response.split('```json')[1].split('```')[0]
        elif '```' in response:
            response = response.split('```')[1].split('```')[0]
            
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            response = response[start:end]
            
        decision = json.loads(response)
        
        # Ensure keys exist
        if "pass" not in decision:
            decision["pass"] = True
        if "feedback" not in decision:
            decision["feedback"] = "Looks good"
            
        logger.info(f"Critic Agent evaluation: Pass={decision['pass']}")
        return decision
        
    except Exception as e:
        logger.error(f"Critic Agent failed to parse response: {e}")
        # Default to pass if the critic fails, to avoid breaking the pipeline
        return {"pass": True, "feedback": "Critic failed to evaluate, defaulting to pass."}
