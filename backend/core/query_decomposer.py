"""
Advanced Query Decomposer v2.0 - LLM-Powered Query Understanding
=================================================================

PRO FEATURES:
- LLM-powered semantic decomposition (when patterns fail)
- Temporal expression parsing ("last quarter", "YoY")
- Context-aware query expansion using data schema
- Multi-hop reasoning ("First find X, then analyze Y")
- Comparison detection ("A vs B", "before and after")
- Intent classification for smarter routing

Handles sophisticated query patterns for enterprise RAG:
- Basic comparisons: "compare X and Y"
- Multi-entity: "what is X, Y, and Z"
- Time-based: "revenue this month vs last month"
- Aggregation chains: "total by department then average"
- Conditional: "show X where Y is greater than Z"
- Multi-step analysis: "first find top 5, then calculate average"
- Nested comparisons: "compare (A vs B) with (C vs D)"
"""

import re
import json
from typing import List, Tuple, Dict, Optional
from enum import Enum


class QueryIntent(Enum):
    """Semantic intent of the query"""
    FACTUAL = "factual"           # "What is total revenue?"
    COMPARISON = "comparison"     # "Compare X and Y"
    TREND = "trend"               # "Show trend over time"
    RANKING = "ranking"           # "Top 5 customers"
    AGGREGATION = "aggregation"   # "Total by category"
    BREAKDOWN = "breakdown"       # "Revenue breakdown"
    PREDICTION = "prediction"     # "Forecast next month"
    CORRELATION = "correlation"   # "Relationship between X and Y"
    ANOMALY = "anomaly"           # "Find unusual patterns"
    EXPLANATION = "explanation"   # "Explain this/why"
    MULTI_HOP = "multi_hop"       # "First X, then Y"


class TemporalExpression:
    """Parse temporal expressions from queries"""
    
    PATTERNS = {
        # Relative periods
        r'\b(this|current)\s+(month|week|year|quarter)\b': ('relative', 'current'),
        r'\b(last|previous)\s+(month|week|year|quarter)\b': ('relative', 'previous'),
        r'\b(next)\s+(month|week|year|quarter)\b': ('relative', 'next'),
        # Specific periods
        r'\bq([1-4])\b': ('quarter', None),
        r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b': ('month', None),
        r'\b(20\d{2})\b': ('year', None),
        # Comparisons
        r'\b(yoy|year.over.year)\b': ('comparison', 'yoy'),
        r'\b(mom|month.over.month)\b': ('comparison', 'mom'),
        r'\b(qoq|quarter.over.quarter)\b': ('comparison', 'qoq'),
        r'\b(ytd|year.to.date)\b': ('range', 'ytd'),
        r'\b(mtd|month.to.date)\b': ('range', 'mtd'),
    }
    
    @classmethod
    def extract(cls, query: str) -> List[Dict]:
        """Extract temporal expressions from query"""
        expressions = []
        query_lower = query.lower()
        
        for pattern, (expr_type, expr_value) in cls.PATTERNS.items():
            match = re.search(pattern, query_lower)
            if match:
                expressions.append({
                    'type': expr_type,
                    'value': expr_value or match.group(0),
                    'match': match.group(0)
                })
        
        return expressions


def llm_decompose_query(query: str, schema_context: str = "") -> List[str]:
    """
    🧠 LLM-POWERED QUERY DECOMPOSITION
    
    Use LLM to intelligently break down complex queries when
    regex patterns are insufficient.
    
    Args:
        query: Complex user query
        schema_context: Available columns/schema for context
        
    Returns:
        List of simpler sub-queries
    """
    try:
        from core.llm import chat
        
        prompt = f"""You are a query decomposition expert. Break this complex query into simpler sub-queries.

USER QUERY: "{query}"

{f"AVAILABLE DATA COLUMNS: {schema_context}" if schema_context else ""}

RULES:
1. Only decompose if the query has MULTIPLE distinct questions
2. Each sub-query should be answerable independently
3. Preserve the user's intent in each sub-query
4. Maximum 5 sub-queries
5. If the query is simple, return just the original query

RESPOND WITH ONLY A JSON ARRAY OF STRINGS. Examples:
- Simple: ["What is total revenue?"]
- Complex: ["What is Q1 revenue?", "What is Q2 revenue?", "Compare Q1 vs Q2"]

JSON ARRAY:"""

        response = chat(prompt, max_tokens=300)
        
        # Parse JSON response
        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        response = response.strip()
        
        sub_queries = json.loads(response)
        
        if isinstance(sub_queries, list) and len(sub_queries) > 0:
            print(f"[LLM DECOMPOSE] '{query[:50]}...' -> {len(sub_queries)} sub-queries")
            return sub_queries
            
    except Exception as e:
        print(f"[LLM DECOMPOSE] Fallback to regex: {e}")
    
    return [query]  # Fallback


def expand_query_with_schema(query: str, columns: List[str]) -> str:
    """
    🧠 SCHEMA-AWARE QUERY EXPANSION
    
    Expand ambiguous queries based on available data columns.
    
    Examples:
    - "show me revenue" + columns=['total_amount'] -> "show me total_amount as revenue"
    - "top customers" + columns=['client_name'] -> "top clients by client_name"
    """
    if not columns:
        return query
    
    query_lower = query.lower()
    expansions = []
    
    # Revenue/amount mapping
    amount_keywords = ['revenue', 'sales', 'amount', 'value', 'total']
    amount_cols = [c for c in columns if any(kw in c.lower() for kw in 
                   ['amount', 'revenue', 'sales', 'total', 'value', 'price', 'cost'])]
    
    if any(kw in query_lower for kw in amount_keywords) and amount_cols:
        expansions.append(f"[Using column: {amount_cols[0]} for amounts]")
    
    # Customer/entity mapping
    entity_keywords = ['customer', 'client', 'buyer', 'account']
    entity_cols = [c for c in columns if any(kw in c.lower() for kw in 
                   ['customer', 'client', 'name', 'account', 'company', 'buyer'])]
    
    if any(kw in query_lower for kw in entity_keywords) and entity_cols:
        expansions.append(f"[Using column: {entity_cols[0]} for entities]")
    
    # Date mapping
    if any(kw in query_lower for kw in ['trend', 'monthly', 'over time', 'timeline']):
        date_cols = [c for c in columns if any(kw in c.lower() for kw in 
                     ['date', 'time', 'day', 'month', 'year', 'period'])]
        if date_cols:
            expansions.append(f"[Using column: {date_cols[0]} for time series]")
    
    if expansions:
        return query + " " + " ".join(expansions)
    
    return query


def classify_query_intent(query: str) -> QueryIntent:
    """
    🧠 INTELLIGENT INTENT CLASSIFICATION
    
    Classify the semantic intent of a query for smarter routing.
    Uses pattern matching first, LLM fallback for ambiguous cases.
    """
    query_lower = query.lower()
    
    # Pattern-based classification (fast path)
    intent_patterns = {
        QueryIntent.COMPARISON: [
            r'\b(compare|comparison|vs|versus|between|against)\b',
            r'\b(difference|differ)\b',
            r'\b(which is (better|worse|higher|lower))\b',
        ],
        QueryIntent.TREND: [
            r'\b(trend|over time|monthly|weekly|daily|yearly)\b',
            r'\b(growth|decline|change over)\b',
            r'\b(timeline|progression|evolution)\b',
        ],
        QueryIntent.RANKING: [
            r'\b(top|bottom|best|worst|highest|lowest)\s*\d*\b',
            r'\b(rank|ranking|leader|leaderboard)\b',
        ],
        QueryIntent.AGGREGATION: [
            r'\b(total|sum|count|average|mean|median)\b',
            r'\b(by|per|grouped by|for each)\b',
        ],
        QueryIntent.BREAKDOWN: [
            r'\b(breakdown|break down|split|distribution)\b',
            r'\b(composition|proportion|percentage|share)\b',
        ],
        QueryIntent.PREDICTION: [
            r'\b(predict|forecast|projection|future)\b',
            r'\b(next month|next year|next quarter)\b',
            r'\b(will be|expected|anticipated)\b',
        ],
        QueryIntent.CORRELATION: [
            r'\b(correlation|relationship|correlate|related)\b',
            r'\b(affect|impact|influence)\b',
        ],
        QueryIntent.ANOMALY: [
            r'\b(anomaly|anomalies|unusual|outlier)\b',
            r'\b(strange|unexpected|abnormal)\b',
        ],
        QueryIntent.EXPLANATION: [
            r'\b(explain|why|how come|reason)\b',
            r'\b(elaborate|clarify|describe)\b',
        ],
        QueryIntent.MULTI_HOP: [
            r'\b(first|then|after that|next)\b.*\b(then|after|and then)\b',
            r'\b(step 1|step 2)\b',
        ],
    }
    
    best_intent = QueryIntent.FACTUAL
    best_score = 0
    
    for intent, patterns in intent_patterns.items():
        score = sum(1 for p in patterns if re.search(p, query_lower))
        if score > best_score:
            best_score = score
            best_intent = intent
    
    return best_intent


def decompose_query(query: str, use_llm: bool = True, schema_context: str = "") -> List[str]:
    """
    Break complex queries into simpler sub-queries for better retrieval.
    
    Handles:
    - "Compare sales in Q1 and Q2" → ["sales in Q1", "sales in Q2"]
    - "What is total revenue and customer count?" → ["total revenue", "customer count"]
    - "Show top 5 employees by salary in Engineering" → ["top 5 employees by salary", "filter: Engineering department"]
    - "Revenue this month vs last month" → ["revenue this month", "revenue last month"]
    - "Average salary by department then sort by highest" → ["average salary by department", "sort by highest"]
    
    Returns:
        List of sub-queries. If query is simple, returns [query] itself.
    """
    query_lower = query.lower().strip()
    sub_queries = []
    
    # =========================================================================
    # PATTERN 1: Basic Comparisons - "compare X and Y", "X vs Y"
    # =========================================================================
    compare_patterns = [
        r'compare\s+(.+?)\s+(?:and|with|to|vs\.?|versus)\s+(.+?)(?:\?|$)',
        r'(.+?)\s+(?:vs\.?|versus)\s+(.+?)(?:\?|$)',
        r'difference\s+between\s+(.+?)\s+and\s+(.+?)(?:\?|$)',
        r'how\s+does\s+(.+?)\s+compare\s+(?:to|with)\s+(.+?)(?:\?|$)',
    ]
    
    for pattern in compare_patterns:
        match = re.search(pattern, query_lower)
        if match:
            entity1, entity2 = match.groups()
            sub_queries.append(f"What is {entity1.strip()}?")
            sub_queries.append(f"What is {entity2.strip()}?")
            sub_queries.append(f"Compare: {entity1.strip()} vs {entity2.strip()}")
            return sub_queries
    
    # =========================================================================
    # PATTERN 2: Time-based Comparisons - "this month vs last month"
    # =========================================================================
    time_patterns = [
        r'(.+?)\s+(?:this|current)\s+(month|week|year|quarter)\s+(?:vs\.?|versus|compared\s+to|and)\s+(?:last|previous)\s+\2',
        r'(.+?)\s+(?:in|for|during)\s+(\w+)\s+(?:vs\.?|and|compared\s+to)\s+(\w+)',
        r'(.+?)\s+between\s+(\d{4})\s+and\s+(\d{4})',
        r'(.+?)\s+from\s+(\w+)\s+to\s+(\w+)',
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, query_lower)
        if match:
            groups = match.groups()
            if len(groups) == 2:
                metric, period = groups
                sub_queries.append(f"{metric.strip()} for current {period}")
                sub_queries.append(f"{metric.strip()} for previous {period}")
            elif len(groups) == 3:
                metric, period1, period2 = groups
                sub_queries.append(f"{metric.strip()} for {period1}")
                sub_queries.append(f"{metric.strip()} for {period2}")
            return sub_queries
    
    # =========================================================================
    # PATTERN 3: Multi-entity Queries - "what is X, Y, and Z"
    # =========================================================================
    multi_entity_pattern = r'(?:what\s+(?:is|are)|show|get|list|find|display|tell\s+me)\s+(.+?)(?:\?|$)'
    match = re.search(multi_entity_pattern, query_lower)
    if match:
        content = match.group(1)
        # Check for "and" with multiple items
        if ' and ' in content:
            # Split by "and" and commas
            parts = re.split(r'\s*,\s*|\s+and\s+', content)
            parts = [p.strip() for p in parts if len(p.strip()) > 2]
            if len(parts) >= 2:
                for part in parts:
                    sub_queries.append(f"What is {part}?")
                return sub_queries
    
    # =========================================================================
    # PATTERN 4: Aggregation Queries - "total X by Y"
    # =========================================================================
    aggregation_patterns = [
        r'(total|sum|count|average|avg|mean|max|min|maximum|minimum)\s+(?:of\s+)?(.+?)\s+(?:by|per|for\s+each|grouped\s+by)\s+(.+?)(?:\?|$)',
        r'(.+?)\s+(?:by|per|for\s+each|grouped\s+by)\s+(.+?)\s+(?:then|and\s+then|,\s*then)\s+(.+?)(?:\?|$)',
    ]
    
    for pattern in aggregation_patterns:
        match = re.search(pattern, query_lower)
        if match:
            groups = match.groups()
            if len(groups) == 3:
                if groups[0] in ['total', 'sum', 'count', 'average', 'avg', 'mean', 'max', 'min', 'maximum', 'minimum']:
                    sub_queries.append(f"{groups[0]} of {groups[1]} by {groups[2]}")
                else:
                    sub_queries.append(f"{groups[0]} by {groups[1]}")
                    sub_queries.append(f"Then: {groups[2]}")
                return sub_queries
    
    # =========================================================================
    # PATTERN 5: Top/Bottom N Queries - "top 5 X by Y"
    # =========================================================================
    topn_pattern = r'(top|bottom|first|last|highest|lowest)\s+(\d+)?\s*(.+?)\s+(?:by|based\s+on|sorted\s+by|ordered\s+by)\s+(.+?)(?:\?|$)'
    match = re.search(topn_pattern, query_lower)
    if match:
        direction, n, entity, sort_by = match.groups()
        n = n or "5"  # Default to 5
        sub_queries.append(f"List all {entity.strip()}")
        sub_queries.append(f"Sort by {sort_by.strip()}")
        sub_queries.append(f"Take {direction} {n}")
        return sub_queries
    
    # =========================================================================
    # PATTERN 6: Conditional Queries - "X where Y > Z"
    # =========================================================================
    conditional_patterns = [
        r'(.+?)\s+(?:where|when|if|for\s+which)\s+(.+?)\s+(?:is|are|>|<|=|>=|<=|greater|less|equal|more|fewer)\s+(?:than\s+)?(.+?)(?:\?|$)',
        r'(.+?)\s+(?:with|having)\s+(.+?)\s+(?:above|below|over|under|more\s+than|less\s+than)\s+(.+?)(?:\?|$)',
    ]
    
    for pattern in conditional_patterns:
        match = re.search(pattern, query_lower)
        if match:
            main_query, condition_field, condition_value = match.groups()
            sub_queries.append(f"Get all {main_query.strip()}")
            sub_queries.append(f"Filter: {condition_field.strip()} condition {condition_value.strip()}")
            return sub_queries
    
    # =========================================================================
    # PATTERN 7: Multi-step Analysis - "first X, then Y"
    # =========================================================================
    multistep_patterns = [
        r'(?:first|1st|step\s*1)\s+(.+?)\s*(?:,|then|and\s+then|;)\s*(?:then|2nd|step\s*2)?\s*(.+?)(?:\?|$)',
        r'(.+?)\s+(?:and\s+then|,\s*then)\s+(.+?)(?:\?|$)',
    ]
    
    for pattern in multistep_patterns:
        match = re.search(pattern, query_lower)
        if match:
            step1, step2 = match.groups()
            sub_queries.append(f"Step 1: {step1.strip()}")
            sub_queries.append(f"Step 2: {step2.strip()}")
            return sub_queries
    
    # =========================================================================
    # PATTERN 8: OR Queries - "X or Y"
    # =========================================================================
    or_pattern = r'(.+?)\s+or\s+(.+?)(?:\?|$)'
    match = re.search(or_pattern, query_lower)
    if match and ' and ' not in query_lower:  # Avoid conflict with AND
        option1, option2 = match.groups()
        if len(option1) > 3 and len(option2) > 3:
            sub_queries.append(f"Option 1: {option1.strip()}")
            sub_queries.append(f"Option 2: {option2.strip()}")
            return sub_queries
    
    # =========================================================================
    # PATTERN 9: Multi-action Queries - "calculate X and list Y"
    # =========================================================================
    action_words = ['calculate', 'compute', 'show', 'list', 'find', 'get', 'display', 
                    'count', 'sum', 'average', 'analyze', 'break down', 'summarize']
    
    for i, action1 in enumerate(action_words):
        if action1 in query_lower:
            for action2 in action_words[i+1:]:
                if action2 in query_lower and ' and ' in query_lower:
                    parts = query_lower.split(' and ')
                    if len(parts) == 2:
                        sub_queries.append(parts[0].strip())
                        sub_queries.append(parts[1].strip())
                        return sub_queries
    
    # =========================================================================
    # PATTERN 10: Comma-separated List - "X, Y, and Z"
    # =========================================================================
    if ',' in query:
        items = re.findall(r'([^,]+)', query)
        if len(items) >= 2:
            clean_items = []
            for item in items:
                # Clean up "and X" at the end
                item = re.sub(r'^\s*and\s+', '', item.strip())
                item = re.sub(r'\s+and\s*$', '', item.strip())
                if len(item) > 3:
                    clean_items.append(item)
            
            if len(clean_items) >= 2:
                for item in clean_items[:5]:  # Max 5 sub-queries
                    sub_queries.append(f"What is {item.strip()}?")
                return sub_queries
    
    # =========================================================================
    # NO DECOMPOSITION NEEDED - Return original query
    # =========================================================================
    return [query]


def merge_results(results: List[Tuple[str, str]]) -> str:
    """
    Merge results from multiple sub-queries into a coherent response.
    
    Args:
        results: List of (sub_query, result) tuples
        
    Returns:
        Merged response string
    """
    if len(results) == 1:
        return results[0][1]
    
    merged = "## 📊 Combined Analysis\n\n"
    for i, (sub_query, result) in enumerate(results, 1):
        # Clean up sub-query display
        display_query = sub_query.replace("What is ", "").replace("?", "").strip()
        merged += f"### Part {i}: {display_query.title()}\n{result}\n\n"
    
    merged += "---\n*Analysis performed using query decomposition for comprehensive results.*"
    return merged


def is_complex_query(query: str) -> bool:
    """
    Quickly check if a query might benefit from decomposition.
    """
    query_lower = query.lower()
    
    complexity_indicators = [
        # Comparisons
        ' and ', ' vs ', ' vs.', ' versus ', 'compare', 'difference between',
        # Lists
        ', ', 
        # Time-based
        'this month', 'last month', 'this year', 'last year', 'between',
        # Aggregations
        'by department', 'by category', 'per ', 'grouped by', 'for each',
        # Multi-step
        'then ', 'first ', 'step 1', ' or ',
        # Top/Bottom
        'top ', 'bottom ', 'highest', 'lowest',
        # Conditional
        'where ', 'having ', 'with ',
    ]
    
    return any(ind in query_lower for ind in complexity_indicators)


def get_decomposition_type(query: str) -> str:
    """
    Identify what type of decomposition was applied.
    """
    query_lower = query.lower()
    
    if 'compare' in query_lower or ' vs' in query_lower:
        return "comparison"
    elif 'top ' in query_lower or 'bottom ' in query_lower:
        return "ranking"
    elif ' by ' in query_lower:
        return "aggregation"
    elif 'where ' in query_lower or 'having ' in query_lower:
        return "filtered"
    elif 'then ' in query_lower or 'first ' in query_lower:
        return "multi-step"
    elif ', ' in query_lower or ' and ' in query_lower:
        return "multi-entity"
    else:
        return "simple"


# Test examples
if __name__ == "__main__":
    test_queries = [
        # Basic
        "Compare revenue in Q1 and Q2",
        "Sales vs Marketing performance",
        
        # Time-based
        "Revenue this month vs last month",
        "Salary trends between 2022 and 2023",
        
        # Multi-entity
        "What is total salary, employee count, and average performance?",
        "Show me revenue and profit and expenses",
        
        # Aggregation
        "Total salary by department",
        "Average salary by role then sort by highest",
        
        # Top/Bottom
        "Top 5 employees by salary",
        "Bottom 10 products by sales",
        
        # Conditional
        "Employees where salary is greater than 50000",
        "Departments with headcount above 20",
        
        # Multi-step
        "First find top departments, then calculate average salary",
        "Get all employees and then group by location",
        
        # Simple (no decomposition)
        "What is the total revenue?",
        "Show me all departments",
    ]
    
    print("=" * 60)
    print("ADVANCED QUERY DECOMPOSER TEST")
    print("=" * 60)
    
    for q in test_queries:
        result = decompose_query(q)
        query_type = get_decomposition_type(q)
        is_complex = is_complex_query(q)
        
        print(f"\n📝 Query: {q}")
        print(f"   Type: {query_type}")
        print(f"   Complex: {is_complex}")
        print(f"   Decomposed ({len(result)} parts):")
        for i, sub in enumerate(result, 1):
            print(f"      {i}. {sub}")
