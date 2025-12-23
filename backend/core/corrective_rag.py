"""
Corrective RAG - Self-correction with web fallback
===================================================

When the retrieved context is insufficient or confidence is low,
corrective RAG will:
1. Detect low-quality retrieval
2. Attempt query reformulation
3. Fallback to web search if needed
4. Combine results for better answers
"""

import os
from typing import Dict, List, Any, Optional, Tuple


def assess_retrieval_quality(
    query: str,
    retrieved_docs: List[Dict[str, Any]],
    min_relevance_score: float = 0.5
) -> Dict[str, Any]:
    """
    Assess the quality of retrieved documents.
    
    Returns:
        {
            "quality": "good" | "medium" | "poor",
            "confidence": float 0-1,
            "needs_correction": bool,
            "reason": str
        }
    """
    if not retrieved_docs:
        return {
            "quality": "poor",
            "confidence": 0.0,
            "needs_correction": True,
            "reason": "No documents retrieved"
        }
    
    # Check average relevance score
    scores = []
    for doc in retrieved_docs:
        score = doc.get('score', 0) or doc.get('rerank_score', 0) or 0.5
        scores.append(float(score))
    
    avg_score = sum(scores) / len(scores) if scores else 0
    
    # Check content overlap with query
    query_terms = set(query.lower().split())
    doc_coverage = 0
    
    for doc in retrieved_docs:
        text = doc.get('text', '') or doc.get('content', '')
        doc_terms = set(text.lower().split())
        overlap = len(query_terms & doc_terms) / len(query_terms) if query_terms else 0
        doc_coverage = max(doc_coverage, overlap)
    
    # Determine quality
    if avg_score >= 0.7 and doc_coverage >= 0.5:
        quality = "good"
        needs_correction = False
    elif avg_score >= 0.4 and doc_coverage >= 0.3:
        quality = "medium"
        needs_correction = False
    else:
        quality = "poor"
        needs_correction = True
    
    confidence = (avg_score * 0.6) + (doc_coverage * 0.4)
    
    return {
        "quality": quality,
        "confidence": round(confidence, 2),
        "needs_correction": needs_correction,
        "reason": f"Avg score: {avg_score:.2f}, Query coverage: {doc_coverage:.2f}"
    }


def reformulate_query(query: str, context_hint: str = "") -> List[str]:
    """
    Generate alternative query formulations.
    
    Returns list of reformulated queries to try.
    """
    query_lower = query.lower()
    alternatives = [query]  # Always include original
    
    # Expand abbreviations
    expansions = {
        'avg': 'average',
        'max': 'maximum',
        'min': 'minimum',
        'qty': 'quantity',
        'amt': 'amount',
        'dept': 'department',
        'emp': 'employee',
        'yr': 'year',
        'mo': 'month',
    }
    
    expanded = query_lower
    for abbr, full in expansions.items():
        if abbr in expanded:
            expanded = expanded.replace(abbr, full)
    
    if expanded != query_lower:
        alternatives.append(expanded)
    
    # Add domain context if provided
    if context_hint:
        alternatives.append(f"{query} in {context_hint}")
    
    # Try removing question words for keyword search
    for word in ['what is', 'what are', 'how many', 'show me', 'list']:
        if query_lower.startswith(word):
            keyword_query = query_lower[len(word):].strip()
            if len(keyword_query) > 3:
                alternatives.append(keyword_query)
            break
    
    return alternatives[:3]  # Max 3 alternatives


async def web_search_fallback(
    query: str,
    max_results: int = 3
) -> List[Dict[str, Any]]:
    """
    Fallback to web search when local retrieval fails.
    Uses a simple web search API (if configured).
    
    Returns list of web results as documents.
    """
    # Check if web search is configured
    search_api_key = os.getenv("SERPER_API_KEY") or os.getenv("TAVILY_API_KEY")
    
    if not search_api_key:
        print("⚠️ Web search not configured (no SERPER_API_KEY or TAVILY_API_KEY)")
        return []
    
    try:
        import aiohttp
        
        # Try Serper first (Google Search API)
        if os.getenv("SERPER_API_KEY"):
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://google.serper.dev/search",
                    json={"q": query, "num": max_results},
                    headers={"X-API-KEY": os.getenv("SERPER_API_KEY")},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        for item in data.get('organic', [])[:max_results]:
                            results.append({
                                "text": f"{item.get('title', '')}: {item.get('snippet', '')}",
                                "source": item.get('link', 'Web'),
                                "metadata": {"type": "web_result"}
                            })
                        print(f"🌐 Web search returned {len(results)} results")
                        return results
        
        # Try Tavily
        if os.getenv("TAVILY_API_KEY"):
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": os.getenv("TAVILY_API_KEY"),
                        "query": query,
                        "max_results": max_results
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        for item in data.get('results', [])[:max_results]:
                            results.append({
                                "text": item.get('content', ''),
                                "source": item.get('url', 'Web'),
                                "metadata": {"type": "web_result"}
                            })
                        print(f"🌐 Tavily search returned {len(results)} results")
                        return results
                        
    except Exception as e:
        print(f"⚠️ Web search error: {e}")
    
    return []


def correctiverag_pipeline(
    query: str,
    retrieved_docs: List[Dict[str, Any]],
    retrieval_fn,  # Function to call for re-retrieval
    context_hint: str = ""
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Full corrective RAG pipeline.
    
    Args:
        query: Original query
        retrieved_docs: Initially retrieved documents
        retrieval_fn: Function to call for retrieval (takes query, returns docs)
        context_hint: Domain hint
        
    Returns:
        (corrected_docs, correction_info)
    """
    # Assess initial retrieval
    assessment = assess_retrieval_quality(query, retrieved_docs)
    
    if not assessment["needs_correction"]:
        return retrieved_docs, {
            "corrected": False,
            "method": "none",
            "assessment": assessment
        }
    
    print(f"🔄 Corrective RAG: Quality={assessment['quality']}, attempting correction...")
    
    # Try reformulated queries
    alternatives = reformulate_query(query, context_hint)
    best_docs = retrieved_docs
    best_assessment = assessment
    
    for alt_query in alternatives[1:]:  # Skip original
        try:
            new_docs = retrieval_fn(alt_query)
            new_assessment = assess_retrieval_quality(alt_query, new_docs)
            
            if new_assessment["confidence"] > best_assessment["confidence"]:
                best_docs = new_docs
                best_assessment = new_assessment
                print(f"✅ Better results with reformulation: '{alt_query[:50]}...'")
        except Exception as e:
            print(f"⚠️ Reformulation retrieval error: {e}")
    
    return best_docs, {
        "corrected": True,
        "method": "reformulation",
        "assessment": best_assessment,
        "alternatives_tried": len(alternatives) - 1
    }


# Test
if __name__ == "__main__":
    # Test assessment
    test_docs = [
        {"text": "Total salary is $3,750,000", "score": 0.85},
        {"text": "Engineering department has 50 employees", "score": 0.72},
    ]
    
    query = "What is the total salary?"
    assessment = assess_retrieval_quality(query, test_docs)
    print(f"Assessment: {assessment}")
    
    # Test reformulation
    alternatives = reformulate_query("what is the avg emp salary in dept?")
    print(f"Reformulations: {alternatives}")
