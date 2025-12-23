"""
HyDE (Hypothetical Document Embeddings)
========================================

Improves RAG retrieval by generating a hypothetical answer first,
then using that to search for similar documents.

Flow:
1. User query → LLM generates hypothetical answer
2. Embed the hypothetical answer (not the query)
3. Search for similar real documents
4. Return results that match the hypothetical answer

This helps when queries are vague or use different terminology than documents.
"""

import os
from typing import List, Dict, Any, Optional


# Lazy load LLM
_llm_available = False
_openrouter_key = None


def _get_openrouter_key():
    """Get OpenRouter API key from environment"""
    global _openrouter_key
    if _openrouter_key is None:
        _openrouter_key = os.getenv("OPENROUTER_API_KEY")
    return _openrouter_key


async def generate_hypothetical_document(
    query: str,
    context_hint: str = "",
    model: str = "deepseek/deepseek-chat"
) -> str:
    """
    Generate a hypothetical document that would answer the query.
    
    Args:
        query: The user's question
        context_hint: Optional hint about the data domain
        model: LLM model to use
        
    Returns:
        A hypothetical document/answer
    """
    import aiohttp
    
    api_key = _get_openrouter_key()
    if not api_key:
        print("⚠️ HyDE: No API key, returning original query")
        return query
    
    prompt = f"""Generate a short, factual paragraph that would directly answer this question.
Write as if you're writing a document excerpt that contains the answer.
Be specific with numbers and details (you can make them up).
Keep it under 100 words.

Question: {query}
{f'Context: This is about {context_hint}' if context_hint else ''}

Hypothetical document excerpt:"""

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200,
        "temperature": 0.7  # Slightly creative for generation
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    hypothetical = data['choices'][0]['message']['content']
                    print(f"📄 HyDE generated: {hypothetical[:100]}...")
                    return hypothetical
                else:
                    print(f"⚠️ HyDE API error: {response.status}")
                    return query
    except Exception as e:
        print(f"⚠️ HyDE error: {e}")
        return query


def generate_hypothetical_document_sync(
    query: str,
    context_hint: str = "",
    model: str = "deepseek/deepseek-chat"
) -> str:
    """
    Synchronous version of generate_hypothetical_document.
    Uses requests instead of aiohttp.
    """
    import requests
    
    api_key = _get_openrouter_key()
    if not api_key:
        print("⚠️ HyDE: No API key, returning original query")
        return query
    
    prompt = f"""Generate a short, factual paragraph that would directly answer this question.
Write as if you're writing a document excerpt that contains the answer.
Be specific with numbers and details (you can make them up).
Keep it under 100 words.

Question: {query}
{f'Context: This is about {context_hint}' if context_hint else ''}

Hypothetical document excerpt:"""

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 200,
                "temperature": 0.7
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=15
        )
        
        if response.status_code == 200:
            hypothetical = response.json()['choices'][0]['message']['content']
            print(f"📄 HyDE generated: {hypothetical[:100]}...")
            return hypothetical
        else:
            print(f"⚠️ HyDE API error: {response.status_code}")
            return query
    except Exception as e:
        print(f"⚠️ HyDE error: {e}")
        return query


def should_use_hyde(query: str) -> bool:
    """
    Determine if HyDE would benefit this query.
    
    HyDE helps when:
    - Query is vague or abstract
    - Query uses different terminology than documents
    - Query is a "how to" or exploratory question
    
    HyDE is not needed when:
    - Query contains specific entity names
    - Query is a direct lookup
    - Query has quoted exact terms
    """
    query_lower = query.lower()
    
    # Skip HyDE for simple lookups
    skip_patterns = [
        'what is the total',
        'how many',
        'list all',
        'show me',
        '"',  # Quoted terms
        'exact',
    ]
    if any(p in query_lower for p in skip_patterns):
        return False
    
    # Use HyDE for exploratory/abstract queries
    hyde_patterns = [
        'why',
        'how does',
        'explain',
        'what would happen',
        'best way to',
        'recommend',
        'should i',
        'help me understand',
        'what are the',
        'trends',
        'patterns',
    ]
    if any(p in query_lower for p in hyde_patterns):
        return True
    
    # Default: don't use HyDE (it's slower)
    return False


# Test
if __name__ == "__main__":
    import asyncio
    
    test_queries = [
        "What are the key trends in our sales data?",
        "What is the total revenue?",  # Should skip HyDE
        "Why has Engineering department salary increased?",
        "How many employees do we have?",  # Should skip HyDE
    ]
    
    print("HyDE Query Analysis")
    print("=" * 50)
    
    for q in test_queries:
        use_hyde = should_use_hyde(q)
        print(f"\nQuery: {q}")
        print(f"Use HyDE: {use_hyde}")
        
        if use_hyde:
            # Test sync version
            hypothetical = generate_hypothetical_document_sync(q, "HR and employee data")
            print(f"Hypothetical: {hypothetical[:150]}...")
