"""
Intelligent Query Router
=========================

Detects user intent from query and routes to appropriate:
- Response type: text, chart, table, graph visualization
- Mode: RAG, GraphRAG, Hybrid, Vision, Prediction
- Model: DeepSeek, Claude, GPT-4V based on complexity

No hardcoding - all pattern-based detection.
"""

import re
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ResponseType(Enum):
    TEXT = "text"
    CHART = "chart"
    TABLE = "table"
    GRAPH = "graph"  # Knowledge graph visualization
    MIXED = "mixed"  # Text + visuals


class QueryIntent(Enum):
    LOOKUP = "lookup"           # Simple fact retrieval
    ANALYSIS = "analysis"       # Deeper analysis
    COMPARISON = "comparison"   # Compare entities
    TREND = "trend"             # Time-based trends
    BREAKDOWN = "breakdown"     # Category breakdown
    PREDICTION = "prediction"   # Future forecasting
    VISUALIZATION = "visualization"  # Explicit chart request
    RELATIONSHIP = "relationship"    # Entity relationships
    SUMMARY = "summary"         # Overview/summary


@dataclass
class QueryAnalysis:
    """Result of query analysis"""
    intent: QueryIntent
    response_type: ResponseType
    suggested_mode: str
    suggested_model: str
    chart_type: Optional[str]
    entities: List[str]
    metrics: List[str]
    time_reference: Optional[str]
    confidence: float


# Intent detection patterns (no hardcoding - pattern-based)
INTENT_PATTERNS = {
    QueryIntent.COMPARISON: [
        r'\bcompare\b', r'\bvs\b', r'\bversus\b', r'\bdifference\b',
        r'\bhigher\b.*\bthan\b', r'\blower\b.*\bthan\b', r'\bbetter\b.*\bthan\b',
        r'\bwhich\b.*\b(more|less|higher|lower|better)\b'
    ],
    QueryIntent.TREND: [
        r'\btrend\b', r'\bover time\b', r'\bhistory\b', r'\bgrowth\b',
        r'\bchange\b.*\b(over|since|from)\b', r'\bmonthly\b', r'\byearly\b',
        r'\bquarterly\b', r'\blast\b.*\b(months?|years?|weeks?)\b'
    ],
    QueryIntent.BREAKDOWN: [
        r'\bby\b.*\b(department|category|type|region|product)\b',
        r'\bbreakdown\b', r'\bdistribution\b', r'\bsplit\b',
        r'\bper\b', r'\beach\b', r'\bgroup\b.*\bby\b'
    ],
    QueryIntent.PREDICTION: [
        r'\bpredict\b', r'\bforecast\b', r'\bestimate\b', r'\bproject\b',
        r'\bwill\b.*\bbe\b', r'\bnext\b.*\b(month|year|quarter)\b',
        r'\bfuture\b', r'\bexpect\b'
    ],
    QueryIntent.VISUALIZATION: [
        r'\bchart\b', r'\bgraph\b', r'\bvisualize\b', r'\bplot\b',
        r'\bshow\b.*\b(me|chart|graph)\b', r'\bdisplay\b.*\b(chart|graph)\b',
        r'\bbar\b.*\bchart\b', r'\bpie\b.*\bchart\b', r'\bline\b.*\bchart\b'
    ],
    QueryIntent.RELATIONSHIP: [
        r'\brelate\b', r'\bconnect\b', r'\blink\b', r'\bdepend\b',
        r'\brelationship\b', r'\bnetwork\b', r'\bwho\b.*\b(works|reports|manages)\b'
    ],
    QueryIntent.SUMMARY: [
        r'\bsummary\b', r'\boverview\b', r'\bsummarize\b', r'\bhighlight\b',
        r'\bkey\b.*\b(points|metrics|insights)\b', r'\btop\b.*\b\d+\b'
    ],
    QueryIntent.ANALYSIS: [
        r'\banalyze\b', r'\banalysis\b', r'\bexplain\b', r'\bwhy\b',
        r'\bunderstand\b', r'\binsight\b', r'\bpattern\b'
    ],
}

# Chart type detection patterns
CHART_PATTERNS = {
    'bar': [r'\bbar\b', r'\bcompar', r'\brank', r'\btop\b', r'\bby\b.*\b(department|category)\b'],
    'line': [r'\bline\b', r'\btrend\b', r'\bover time\b', r'\bgrowth\b', r'\bmonthly\b', r'\byearly\b'],
    'pie': [r'\bpie\b', r'\bdistribution\b', r'\bbreakdown\b', r'\bshare\b', r'\bproportion\b'],
    'scatter': [r'\bscatter\b', r'\bcorrelation\b', r'\brelation\b.*\bbetween\b'],
    'heatmap': [r'\bheatmap\b', r'\bmatrix\b', r'\bdensity\b'],
}


def detect_intent(query: str) -> QueryIntent:
    """Detect the primary intent of a query"""
    query_lower = query.lower()
    
    # Check each intent pattern
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, query_lower):
                return intent
    
    # Default to lookup for simple queries
    if len(query.split()) <= 5:
        return QueryIntent.LOOKUP
    
    return QueryIntent.ANALYSIS


def detect_response_type(query: str, intent: QueryIntent) -> ResponseType:
    """Determine what type of response the user wants"""
    query_lower = query.lower()
    
    # Explicit visualization request
    if intent == QueryIntent.VISUALIZATION:
        return ResponseType.CHART
    
    # Relationship queries → graph
    if intent == QueryIntent.RELATIONSHIP:
        return ResponseType.GRAPH
    
    # Trend/comparison/breakdown → chart
    if intent in [QueryIntent.TREND, QueryIntent.COMPARISON, QueryIntent.BREAKDOWN]:
        return ResponseType.CHART
    
    # Check for explicit table request
    if re.search(r'\btable\b|\blist\b.*\ball\b', query_lower):
        return ResponseType.TABLE
    
    # Check for "show me" pattern
    if re.search(r'\bshow\b.*\b(chart|graph|visual)\b', query_lower):
        return ResponseType.CHART
    
    # Summary/analysis with data → mixed
    if intent in [QueryIntent.SUMMARY, QueryIntent.ANALYSIS]:
        return ResponseType.MIXED
    
    return ResponseType.TEXT


def detect_chart_type(query: str, intent: QueryIntent) -> Optional[str]:
    """Detect which chart type is most appropriate"""
    query_lower = query.lower()
    
    for chart_type, patterns in CHART_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, query_lower):
                return chart_type
    
    # Default chart types based on intent
    intent_chart_map = {
        QueryIntent.TREND: 'line',
        QueryIntent.COMPARISON: 'bar',
        QueryIntent.BREAKDOWN: 'pie',
        QueryIntent.PREDICTION: 'line',
    }
    
    return intent_chart_map.get(intent)


def extract_entities(query: str) -> List[str]:
    """Extract entity names from query (departments, products, etc.)"""
    entities = []
    
    # Look for quoted terms
    quoted = re.findall(r'"([^"]+)"', query)
    entities.extend(quoted)
    
    # Look for capitalized words (likely proper nouns)
    words = query.split()
    for i, word in enumerate(words):
        # Skip first word and common words
        if i > 0 and word[0].isupper() and word.lower() not in ['the', 'a', 'an', 'and', 'or']:
            entities.append(word)
    
    return list(set(entities))


def extract_metrics(query: str) -> List[str]:
    """Extract metric/measure names from query"""
    metrics = []
    
    metric_patterns = [
        r'\b(salary|revenue|sales|cost|profit|expense|budget)\b',
        r'\b(count|total|average|sum|max|min|mean)\b',
        r'\b(performance|rating|score|percentage|rate)\b',
    ]
    
    query_lower = query.lower()
    for pattern in metric_patterns:
        matches = re.findall(pattern, query_lower)
        metrics.extend(matches)
    
    return list(set(metrics))


def extract_time_reference(query: str) -> Optional[str]:
    """Extract time reference from query"""
    query_lower = query.lower()
    
    time_patterns = [
        (r'last\s+(\d+)\s+(day|week|month|year)s?', 'relative'),
        (r'this\s+(week|month|quarter|year)', 'current'),
        (r'(january|february|march|april|may|june|july|august|september|october|november|december)', 'month'),
        (r'(\d{4})', 'year'),
        (r'(q[1-4]|quarter\s*\d)', 'quarter'),
    ]
    
    for pattern, time_type in time_patterns:
        match = re.search(pattern, query_lower)
        if match:
            return f"{time_type}:{match.group(0)}"
    
    return None


def suggest_mode(intent: QueryIntent, response_type: ResponseType, has_image: bool = False) -> str:
    """Suggest the best mode for this query"""
    
    # Image attached → Vision mode
    if has_image:
        return "vision"
    
    # Prediction intent → Prediction mode
    if intent == QueryIntent.PREDICTION:
        return "prediction"
    
    # Relationship/network → GraphRAG
    if intent == QueryIntent.RELATIONSHIP or response_type == ResponseType.GRAPH:
        return "graphrag"
    
    # Complex analysis → Hybrid
    if intent in [QueryIntent.ANALYSIS, QueryIntent.COMPARISON] and response_type == ResponseType.MIXED:
        return "hybrid"
    
    # Default to RAG
    return "rag"


def suggest_model(intent: QueryIntent, query: str, has_image: bool = False) -> str:
    """Suggest the best model for this query"""
    
    # Vision required
    if has_image:
        return "gpt4v"
    
    # Complex reasoning → Claude
    if intent in [QueryIntent.ANALYSIS, QueryIntent.PREDICTION]:
        if len(query.split()) > 15:  # Long, complex query
            return "claude-3.5"
    
    # Default to DeepSeek (fast, accurate)
    return "deepseek"


def analyze_query(query: str, has_image: bool = False) -> QueryAnalysis:
    """
    Full query analysis - determines intent, response type, mode, and model.
    This is the main entry point.
    """
    intent = detect_intent(query)
    response_type = detect_response_type(query, intent)
    chart_type = detect_chart_type(query, intent) if response_type == ResponseType.CHART else None
    
    return QueryAnalysis(
        intent=intent,
        response_type=response_type,
        suggested_mode=suggest_mode(intent, response_type, has_image),
        suggested_model=suggest_model(intent, query, has_image),
        chart_type=chart_type,
        entities=extract_entities(query),
        metrics=extract_metrics(query),
        time_reference=extract_time_reference(query),
        confidence=0.8 if intent != QueryIntent.LOOKUP else 0.9
    )


def get_routing_decision(query: str, has_image: bool = False) -> Dict[str, Any]:
    """
    Get routing decision for the query.
    Returns dict with mode, model, response_type for use by send_message.
    """
    analysis = analyze_query(query, has_image)
    
    return {
        "mode": analysis.suggested_mode,
        "model": analysis.suggested_model,
        "response_type": analysis.response_type.value,
        "intent": analysis.intent.value,
        "chart_type": analysis.chart_type,
        "entities": analysis.entities,
        "metrics": analysis.metrics,
        "generate_chart": analysis.response_type in [ResponseType.CHART, ResponseType.MIXED],
    }


# Test
if __name__ == "__main__":
    test_queries = [
        "What is total salary?",
        "Compare Engineering and Sales salary",
        "Show me revenue trend over the last 6 months",
        "Create a pie chart of department distribution",
        "Who reports to the Engineering manager?",
        "Predict next quarter's revenue",
        "Give me a summary of key metrics",
    ]
    
    print("Query Intent Detection Test")
    print("=" * 60)
    
    for q in test_queries:
        result = get_routing_decision(q)
        print(f"\nQuery: {q}")
        print(f"  Intent: {result['intent']}")
        print(f"  Response: {result['response_type']}")
        print(f"  Mode: {result['mode']}")
        print(f"  Model: {result['model']}")
        print(f"  Chart: {result['chart_type']}")
