"""
Query Decomposer - Break complex queries into sub-queries
==========================================================

Handles multi-part questions by:
1. Detecting if query is complex
2. Breaking into sub-queries
3. Merging results back together

Examples:
- "What is total revenue and who are top customers?" -> 2 sub-queries
- "Compare Q1 vs Q2 and show trends" -> 2 sub-queries
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SubQuery:
    """A decomposed sub-query"""
    query: str
    query_type: str  # factual, aggregation, comparison, etc.
    priority: int = 1
    depends_on: Optional[int] = None  # Index of query this depends on


@dataclass
class DecomposedQuery:
    """Result of query decomposition"""
    original: str
    is_complex: bool
    sub_queries: List[SubQuery]
    merge_strategy: str  # 'concat', 'compare', 'summarize'


def is_complex_query(query: str) -> bool:
    """
    Detect if a query needs decomposition.
    
    Complex queries contain:
    - Multiple questions (and, also, then)
    - Comparisons (vs, versus, compare)
    - Multi-step requests (first...then, after that)
    """
    query_lower = query.lower()
    
    # Multi-part indicators
    multi_part_patterns = [
        r'\band\b.*\?',  # "X and Y?"
        r'\balso\b',     # "also show"
        r'\bthen\b',     # "then compare"
        r'\bfirst\b.*\bthen\b',  # "first X then Y"
        r'\b(?:as well|additionally|moreover)\b',
    ]
    
    for pattern in multi_part_patterns:
        if re.search(pattern, query_lower):
            return True
    
    # Multiple question marks
    if query.count('?') > 1:
        return True
    
    # Long queries often need decomposition
    if len(query.split()) > 25:
        return True
    
    return False


def decompose_query(query: str) -> DecomposedQuery:
    """
    Decompose a complex query into simpler sub-queries.
    
    Args:
        query: The original user query
        
    Returns:
        DecomposedQuery with sub-queries and merge strategy
    """
    if not is_complex_query(query):
        return DecomposedQuery(
            original=query,
            is_complex=False,
            sub_queries=[SubQuery(query=query, query_type="simple")],
            merge_strategy="single"
        )
    
    sub_queries = []
    merge_strategy = "concat"
    
    # Split by common conjunctions
    query_lower = query.lower()
    
    # Handle "X and Y" patterns
    if ' and ' in query_lower:
        parts = re.split(r'\s+and\s+', query, flags=re.IGNORECASE)
        for i, part in enumerate(parts):
            part = part.strip().rstrip('?').strip()
            if len(part) > 5:  # Meaningful part
                query_type = _detect_query_type(part)
                sub_queries.append(SubQuery(
                    query=part + "?",
                    query_type=query_type,
                    priority=i + 1
                ))
    
    # Handle comparison patterns
    elif any(p in query_lower for p in ['compare', ' vs ', 'versus', 'difference between']):
        merge_strategy = "compare"
        
        # Extract entities to compare
        compare_match = re.search(
            r'(?:compare|difference between)\s+(.+?)\s+(?:and|vs|versus|with)\s+(.+?)(?:\?|$)',
            query, re.IGNORECASE
        )
        if compare_match:
            entity1 = compare_match.group(1).strip()
            entity2 = compare_match.group(2).strip()
            
            sub_queries.append(SubQuery(
                query=f"What are the details of {entity1}?",
                query_type="lookup",
                priority=1
            ))
            sub_queries.append(SubQuery(
                query=f"What are the details of {entity2}?",
                query_type="lookup",
                priority=1
            ))
            sub_queries.append(SubQuery(
                query=f"Compare {entity1} vs {entity2}",
                query_type="comparison",
                priority=2,
                depends_on=0  # Depends on first two
            ))

        # Handle "Compare X vs Y over time" (Trend Comparison)
        trend_match = re.search(r'(?:compare|how did)\s+(.+?)\s+(?:vs|versus|and)\s+(.+?)\s+(?:perform|change|grow|trend)\s+(?:over time|historically)', query_lower)
        if trend_match:
            entity1 = trend_match.group(1).strip()
            entity2 = trend_match.group(2).strip()
            sub_queries.append(SubQuery(
                query=f"Show trend for {entity1}",
                query_type="trend",
                priority=1
            ))
            sub_queries.append(SubQuery(
                query=f"Show trend for {entity2}",
                query_type="trend",
                priority=1
            ))
            sub_queries.append(SubQuery(
                query=f"Compare trends of {entity1} vs {entity2}",
                query_type="comparison_trend",
                priority=2
            ))
            merge_strategy = "compare"
    
    # Handle "first...then" patterns
    elif 'first' in query_lower and 'then' in query_lower:
        merge_strategy = "sequential"
        parts = re.split(r'\s*(?:,\s*)?then\s+', query, flags=re.IGNORECASE)
        for i, part in enumerate(parts):
            part = part.replace('first', '').strip()
            if len(part) > 5:
                sub_queries.append(SubQuery(
                    query=part,
                    query_type=_detect_query_type(part),
                    priority=i + 1,
                    depends_on=i - 1 if i > 0 else None
                ))
    
    # Fallback: treat as single query
    if not sub_queries:
        sub_queries.append(SubQuery(query=query, query_type="complex"))
    
    return DecomposedQuery(
        original=query,
        is_complex=True,
        sub_queries=sub_queries,
        merge_strategy=merge_strategy
    )


def _detect_query_type(query: str) -> str:
    """Detect the type of a sub-query"""
    query_lower = query.lower()
    
    if any(w in query_lower for w in ['total', 'sum', 'count', 'how many', 'how much']):
        return "aggregation"
    elif any(w in query_lower for w in ['top', 'best', 'highest', 'lowest', 'worst']):
        return "ranking"
    elif any(w in query_lower for w in ['trend', 'over time', 'growth', 'change']):
        return "trend"
    elif any(w in query_lower for w in ['compare', 'vs', 'versus', 'difference']):
        return "comparison"
    elif any(w in query_lower for w in ['why', 'reason', 'cause', 'explain']):
        return "analytical"
    elif any(w in query_lower for w in ['list', 'show', 'give me', 'what are']):
        return "listing"
    elif any(w in query_lower for w in ['predict', 'forecast', 'will', 'future']):
        return "prediction"
    else:
        return "factual"


def merge_results(results: List[str], strategy: str = "concat") -> str:
    """
    Merge results from multiple sub-queries.
    
    Args:
        results: List of answers from sub-queries
        strategy: How to merge ('concat', 'compare', 'summarize')
        
    Returns:
        Merged answer string
    """
    if not results:
        return "No results found."
    
    if len(results) == 1:
        return results[0]
    
    if strategy == "compare":
        # Format as comparison
        merged = "## Comparison\n\n"
        for i, result in enumerate(results):
            merged += f"**Option {i + 1}:**\n{result}\n\n"
        return merged
    
    elif strategy == "sequential":
        # Format as steps
        merged = ""
        for i, result in enumerate(results):
            merged += f"**Step {i + 1}:**\n{result}\n\n"
        return merged
    
    else:  # concat
        return "\n\n---\n\n".join(results)


def get_query_intent(query: str) -> Dict[str, any]:
    """
    Analyze query intent for routing decisions.
    
    Returns:
        Dict with intent, entities, and confidence
    """
    query_lower = query.lower()
    
    intent = {
        'type': 'unknown',
        'entities': [],
        'confidence': 0.5,
        'needs_data': True,
        'needs_chart': False
    }
    
    # Detect chart needs
    if any(w in query_lower for w in ['chart', 'graph', 'plot', 'visualize', 'show me']):
        intent['needs_chart'] = True
    
    # Detect intent type
    if any(w in query_lower for w in ['hi', 'hello', 'hey']):
        intent['type'] = 'greeting'
        intent['needs_data'] = False
        intent['confidence'] = 0.95
    elif any(w in query_lower for w in ['total', 'sum', 'how much', 'how many']):
        intent['type'] = 'aggregation'
        intent['confidence'] = 0.85
    elif any(w in query_lower for w in ['top', 'best', 'highest']):
        intent['type'] = 'ranking'
        intent['confidence'] = 0.85
    elif any(w in query_lower for w in ['compare', 'vs', 'difference']):
        intent['type'] = 'comparison'
        intent['confidence'] = 0.85
    elif any(w in query_lower for w in ['predict', 'forecast', 'future']):
        intent['type'] = 'prediction'
        intent['confidence'] = 0.8
    elif any(w in query_lower for w in ['list', 'show all', 'give me all']):
        intent['type'] = 'listing'
        intent['confidence'] = 0.8
    else:
        intent['type'] = 'general'
        intent['confidence'] = 0.6
    
    # Extract potential entities (capitalized words)
    entities = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', query)
    intent['entities'] = [e for e in entities if e.lower() not in 
                         ['what', 'who', 'when', 'where', 'how', 'why', 'show', 'list', 'give']]
    
    return intent
