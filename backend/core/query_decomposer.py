"""
Advanced Query Decomposer - Break complex queries into sub-queries
==================================================================

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
from typing import List, Tuple, Dict


def decompose_query(query: str) -> List[str]:
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
