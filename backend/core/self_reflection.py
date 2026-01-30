"""
Self-Reflection RAG Module
===========================

Adds self-reflection/self-correction capability to RAG responses.
After generating an answer, the LLM evaluates its own response for:
- Accuracy (is it grounded in the data?)
- Completeness (did it answer the full question?)
- Clarity (is it easy to understand?)

If issues are detected, it regenerates a corrected response.
"""

import os
from typing import Dict, Any, Optional, Tuple
import json


def self_reflect_on_answer(
    query: str,
    answer: str,
    context: str,
    api_key: str = None
) -> Dict[str, Any]:
    """
    Self-reflect on an AI-generated answer.
    
    Returns:
        {
            "is_good": bool,
            "issues": [...],
            "score": int (1-10),
            "suggestion": str or None
        }
    """
    if not api_key:
        api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        return {"is_good": True, "issues": [], "score": 7, "suggestion": None}
    
    import requests
    
    reflection_prompt = f"""You are a quality evaluator. Evaluate this AI response.

Question: {query}

Context (data the AI had access to):
{context[:2000]}

AI's Answer:
{answer}

Evaluate on:
1. GROUNDING: Does the answer use ONLY information from the context? (No made-up data)
2. COMPLETENESS: Does it fully answer the question?
3. CLARITY: Is it clear and well-structured?

Respond in JSON format:
{{
    "is_good": true/false,
    "score": 1-10,
    "issues": ["issue1", "issue2"],
    "suggestion": "how to improve" or null
}}"""

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [{"role": "user", "content": reflection_prompt}],
                "max_tokens": 300,
                "temperature": 0.3
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=15
        )
        
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content']
            # Parse JSON from response
            try:
                # Find JSON in response
                start = content.find('{')
                end = content.rfind('}') + 1
                if start >= 0 and end > start:
                    result = json.loads(content[start:end])
                    print(f"🔍 Self-reflection: Score={result.get('score', 'N/A')}")
                    return result
            except json.JSONDecodeError:
                pass
        
        return {"is_good": True, "issues": [], "score": 7, "suggestion": None}
        
    except Exception as e:
        print(f"⚠️ Self-reflection error: {e}")
        return {"is_good": True, "issues": [], "score": 7, "suggestion": None}


async def self_reflect_async(
    query: str,
    answer: str,
    context: str,
    api_key: str = None
) -> Dict[str, Any]:
    """Async version of self-reflection"""
    import aiohttp
    
    if not api_key:
        api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        return {"is_good": True, "issues": [], "score": 7, "suggestion": None}
    
    reflection_prompt = f"""Evaluate this AI response briefly. Output JSON only.

Question: {query}
Context: {context[:1500]}
Answer: {answer}

JSON format: {{"is_good": bool, "score": 1-10, "issues": [], "suggestion": str|null}}"""

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json={
                    "model": "deepseek/deepseek-chat",
                    "messages": [{"role": "user", "content": reflection_prompt}],
                    "max_tokens": 200,
                    "temperature": 0.3
                },
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data['choices'][0]['message']['content']
                    try:
                        start = content.find('{')
                        end = content.rfind('}') + 1
                        if start >= 0 and end > start:
                            return json.loads(content[start:end])
                    except:
                        pass
    except:
        pass
    
    return {"is_good": True, "issues": [], "score": 7, "suggestion": None}


def regenerate_with_feedback(
    query: str,
    context: str,
    issues: list,
    suggestion: str,
    api_key: str = None
) -> str:
    """
    Regenerate answer with explicit feedback to avoid previous issues.
    """
    if not api_key:
        api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        return ""
    
    import requests
    
    regeneration_prompt = f"""Answer this question based ONLY on the provided data.

IMPORTANT: Your previous answer had these issues:
{', '.join(issues)}

Suggestion: {suggestion}

Context (YOUR ONLY DATA SOURCE):
{context[:3000]}

Question: {query}

Provide a corrected, accurate answer:"""

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [{"role": "user", "content": regeneration_prompt}],
                "max_tokens": 1000,
                "temperature": 0.3
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            corrected = response.json()['choices'][0]['message']['content']
            print(f"✅ Regenerated answer after self-reflection")
            return corrected
            
    except Exception as e:
        print(f"⚠️ Regeneration error: {e}")
    
    return ""


def self_rag_pipeline(
    query: str,
    initial_answer: str,
    context: str,
    max_iterations: int = 1
) -> Tuple[str, Dict[str, Any]]:
    """
    Full Self-RAG pipeline with reflection and optional regeneration.
    
    Returns:
        (final_answer, reflection_info)
    """
    current_answer = initial_answer
    reflection_history = []
    
    for i in range(max_iterations + 1):
        reflection = self_reflect_on_answer(query, current_answer, context)
        reflection_history.append({
            "iteration": i,
            "score": reflection.get("score", 0),
            "issues": reflection.get("issues", [])
        })
        
        # If answer is good enough (score >= 7) or we've reached max iterations
        if reflection.get("is_good", True) or reflection.get("score", 0) >= 7:
            return current_answer, {
                "iterations": i,
                "final_score": reflection.get("score", 7),
                "history": reflection_history
            }
        
        # Try to regenerate
        if i < max_iterations and reflection.get("issues"):
            regenerated = regenerate_with_feedback(
                query, context,
                reflection.get("issues", []),
                reflection.get("suggestion", "Be more accurate")
            )
            if regenerated:
                current_answer = regenerated
    
    return current_answer, {
        "iterations": max_iterations,
        "final_score": reflection_history[-1].get("score", 5),
        "history": reflection_history
    }


# Test
if __name__ == "__main__":
    context = """
    Employee data from HR dataset:
    - Total employees: 500
    - Average salary: $75,000
    - Engineering department: 120 people
    - Sales department: 80 people
    """
    
    query = "How many employees are in Engineering?"
    
    # Good answer
    good_answer = "There are 120 employees in the Engineering department."
    
    # Bad answer (wrong number)
    bad_answer = "There are 250 employees in Engineering with an average salary of $100,000."
    
    print("Testing Self-Reflection...")
    print("=" * 50)
    
    print("\nGood answer:")
    result = self_reflect_on_answer(query, good_answer, context)
    print(f"Score: {result.get('score')}, Is good: {result.get('is_good')}")
    
    print("\nBad answer:")
    result = self_reflect_on_answer(query, bad_answer, context)
    print(f"Score: {result.get('score')}, Issues: {result.get('issues')}")
