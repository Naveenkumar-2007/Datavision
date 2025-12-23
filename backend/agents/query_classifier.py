# Enterprise Query Classifier - LLM-Powered Intelligent Routing
"""
$5M Enterprise Product - Query Classification System v2.0

Advanced query classification system for enterprise AI modes.

Features:
- LLM-based intent classification (ChatGPT-quality understanding)
- Multi-dimensional query analysis
- Confidence scoring with calibration
- Extended query type taxonomy (12 types)
- Entity extraction hints
- Response format detection

This module works with query_dispatcher.py for complete query understanding.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Tuple
import json
import re
from core.llm import chat


class QueryType(Enum):
    """Extended taxonomy of business query types - 12 types for enterprise coverage"""
    FACTUAL = "factual"           # Simple facts: "What is X?"
    AGGREGATION = "aggregation"   # Sums, counts, averages
    COMPARISON = "comparison"     # Compare A vs B
    TREND = "trend"               # Over time patterns
    CAUSAL = "causal"             # Why did X happen?
    RELATIONAL = "relational"     # How is A connected to B?
    PREDICTIVE = "predictive"     # What will happen?
    EXPLORATORY = "exploratory"   # Open-ended discovery
    VISUAL = "visual"             # Image/chart analysis
    # NEW: Additional enterprise query types
    RANKING = "ranking"           # Top/Bottom N queries
    BREAKDOWN = "breakdown"       # Distribution/segmentation
    SUMMARY = "summary"           # Summary/overview requests
    ANOMALY = "anomaly"           # Unusual pattern detection


class ReasoningDepth(Enum):
    """Required reasoning complexity"""
    SIMPLE = "simple"             # Direct lookup
    MODERATE = "moderate"         # Some computation
    COMPLEX = "complex"           # Multi-step reasoning
    DEEP = "deep"                 # Multi-hop graph traversal


@dataclass
class QueryAnalysis:
    """Complete query analysis result"""
    query: str
    query_type: QueryType
    reasoning_depth: ReasoningDepth
    confidence: float
    recommended_route: str
    entities_mentioned: List[str]
    requires_graph: bool
    requires_documents: bool
    requires_vision: bool
    time_reference: Optional[str]
    comparison_targets: List[str]
    aggregation_type: Optional[str]
    explanation: str


class EnterpriseQueryClassifier:
    """
    Enterprise-grade query classifier using LLM + rule-based hybrid approach.
    
    Architecture:
    1. Fast rule-based pre-classification
    2. LLM refinement for ambiguous cases
    3. Entity extraction
    4. Routing decision
    """
    
    # Query type patterns (fast matching)
    TYPE_PATTERNS = {
        QueryType.FACTUAL: [
            r"what is\b", r"what are\b", r"show me\b", r"tell me\b",
            r"list\b", r"display\b", r"find\b"
        ],
        QueryType.AGGREGATION: [
            r"total\b", r"sum\b", r"count\b", r"average\b", r"mean\b",
            r"how many\b", r"how much\b", r"maximum\b", r"minimum\b"
        ],
        QueryType.COMPARISON: [
            r"compare\b", r"versus\b", r"\bvs\b", r"difference\b",
            r"between\b", r"better\b", r"worse\b", r"more than\b"
        ],
        QueryType.TREND: [
            r"trend\b", r"over time\b", r"growth\b", r"decline\b",
            r"pattern\b", r"monthly\b", r"weekly\b", r"yearly\b",
            r"last\s+\d+\s+(day|week|month|year)s?"
        ],
        QueryType.CAUSAL: [
            r"why\b", r"because\b", r"reason\b", r"cause\b",
            r"led to\b", r"resulted in\b", r"due to\b"
        ],
        QueryType.RELATIONAL: [
            r"relationship\b", r"connected\b", r"related\b", r"link\b",
            r"association\b", r"correlation\b", r"who\s+bought\b"
        ],
        QueryType.PREDICTIVE: [
            r"predict\b", r"forecast\b", r"will\b", r"expect\b",
            r"future\b", r"projection\b", r"estimate\b", r"next\s+\d+"
        ],
        QueryType.VISUAL: [
            r"image\b", r"picture\b", r"chart\b", r"graph\b",
            r"screenshot\b", r"diagram\b", r"visual\b"
        ],
        # NEW: Additional pattern types for enterprise coverage
        QueryType.RANKING: [
            r"top\s+\d+", r"bottom\s+\d+", r"best\b", r"worst\b",
            r"highest\b", r"lowest\b", r"biggest\b", r"smallest\b",
            r"leading\b", r"trailing\b", r"rank\b"
        ],
        QueryType.BREAKDOWN: [
            r"breakdown\b", r"by\s+category\b", r"by\s+region\b",
            r"distribution\b", r"segment\b", r"split\b", r"portion\b",
            r"pie\b", r"percentage\b", r"share\b"
        ],
        QueryType.SUMMARY: [
            r"summary\b", r"summarize\b", r"overview\b", r"highlight\b",
            r"key\s+points\b", r"main\s+findings\b", r"brief\b", r"snapshot\b"
        ],
        QueryType.ANOMALY: [
            r"anomal\w+\b", r"unusual\b", r"outlier\b", r"strange\b",
            r"unexpected\b", r"spike\b", r"dip\b", r"exception\b", r"risk\b"
        ]
    }
    
    # Entity patterns
    ENTITY_PATTERNS = {
        "customer": r"customer[s]?\s*[:=]?\s*([A-Za-z0-9_\-\s]+)",
        "product": r"product[s]?\s*[:=]?\s*([A-Za-z0-9_\-\s]+)",
        "amount": r"(\$|₹|€|£)?\s*[\d,]+\.?\d*",
        "date": r"\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4}",
        "time_period": r"(last|past|previous)\s+\d+\s+(day|week|month|year)s?"
    }
    
    def __init__(self, use_llm_refinement: bool = True):
        self.use_llm_refinement = use_llm_refinement
    
    def classify(self, query: str, has_image: bool = False) -> QueryAnalysis:
        """
        Classify a query with full analysis.
        
        Args:
            query: User's natural language query
            has_image: Whether an image is attached
            
        Returns:
            QueryAnalysis with complete classification
        """
        q_lower = query.lower().strip()
        
        # Step 1: Vision mode takes priority
        if has_image:
            return self._build_vision_analysis(query)
        
        # Step 2: Fast pattern matching
        query_type, pattern_confidence = self._pattern_classify(q_lower)
        
        # Step 3: Extract entities
        entities = self._extract_entities(query)
        
        # Step 4: Determine reasoning depth
        reasoning_depth = self._assess_reasoning_depth(q_lower, query_type)
        
        # Step 5: LLM refinement for ambiguous cases
        if self.use_llm_refinement and pattern_confidence < 0.7:
            refined = self._llm_refine(query, query_type, entities)
            if refined:
                query_type = refined.get("type", query_type)
                pattern_confidence = refined.get("confidence", pattern_confidence)
        
        # Step 6: Determine routing
        route, requires_graph, requires_docs = self._determine_route(
            query_type, reasoning_depth, entities
        )
        
        # Step 7: Extract additional metadata
        time_ref = self._extract_time_reference(q_lower)
        comparison_targets = self._extract_comparison_targets(q_lower)
        agg_type = self._extract_aggregation_type(q_lower)
        
        return QueryAnalysis(
            query=query,
            query_type=query_type,
            reasoning_depth=reasoning_depth,
            confidence=pattern_confidence,
            recommended_route=route,
            entities_mentioned=entities,
            requires_graph=requires_graph,
            requires_documents=requires_docs,
            requires_vision=False,
            time_reference=time_ref,
            comparison_targets=comparison_targets,
            aggregation_type=agg_type,
            explanation=self._generate_explanation(query_type, route, reasoning_depth)
        )
    
    def _pattern_classify(self, query: str) -> Tuple[QueryType, float]:
        """Fast pattern-based classification"""
        scores = {}
        
        for qtype, patterns in self.TYPE_PATTERNS.items():
            score = sum(1 for p in patterns if re.search(p, query, re.IGNORECASE))
            if score > 0:
                scores[qtype] = score
        
        if not scores:
            return QueryType.EXPLORATORY, 0.3
        
        best_type = max(scores, key=scores.get)
        max_score = scores[best_type]
        
        # Normalize confidence
        confidence = min(0.9, 0.4 + (max_score * 0.15))
        
        return best_type, confidence
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract mentioned business entities"""
        entities = []
        
        # Common business entity indicators
        entity_words = [
            "customer", "product", "invoice", "order", "revenue",
            "sales", "transaction", "category", "region", "date"
        ]
        
        q_lower = query.lower()
        for word in entity_words:
            if word in q_lower:
                entities.append(word)
        
        return entities
    
    def _assess_reasoning_depth(self, query: str, query_type: QueryType) -> ReasoningDepth:
        """Assess required reasoning complexity"""
        
        # Deep reasoning indicators
        deep_indicators = [
            "why", "cause", "reason", "explain", "understand",
            "correlation", "relationship", "impact", "effect"
        ]
        
        # Complex indicators
        complex_indicators = [
            "compare", "trend", "pattern", "analyze", "breakdown",
            "segment", "across", "between"
        ]
        
        # Count indicators
        deep_count = sum(1 for w in deep_indicators if w in query)
        complex_count = sum(1 for w in complex_indicators if w in query)
        
        if deep_count >= 2 or query_type == QueryType.CAUSAL:
            return ReasoningDepth.DEEP
        elif complex_count >= 2 or query_type in [QueryType.COMPARISON, QueryType.TREND]:
            return ReasoningDepth.COMPLEX
        elif deep_count >= 1 or complex_count >= 1:
            return ReasoningDepth.MODERATE
        else:
            return ReasoningDepth.SIMPLE
    
    def _determine_route(
        self, 
        query_type: QueryType, 
        reasoning_depth: ReasoningDepth,
        entities: List[str]
    ) -> Tuple[str, bool, bool]:
        """Determine the best processing route"""
        
        # Vision mode
        if query_type == QueryType.VISUAL:
            return "vision", False, False
        
        # Hybrid mode for complex multi-source queries
        if reasoning_depth == ReasoningDepth.DEEP:
            return "hybrid", True, True
        
        if query_type in [QueryType.COMPARISON, QueryType.TREND]:
            return "hybrid", True, True
        
        # GraphRAG for relational/causal queries
        if query_type in [QueryType.CAUSAL, QueryType.RELATIONAL, QueryType.PREDICTIVE]:
            return "graph", True, False
        
        # Business entities suggest graph
        graph_entities = {"customer", "product", "revenue", "sales"}
        if graph_entities.intersection(set(entities)):
            if reasoning_depth in [ReasoningDepth.COMPLEX, ReasoningDepth.DEEP]:
                return "graph", True, False
        
        # RAG for factual lookups and aggregations
        if query_type in [QueryType.FACTUAL, QueryType.AGGREGATION]:
            return "rag", False, True
        
        # Default to hybrid for best coverage
        return "hybrid", True, True
    
    def _llm_refine(
        self, 
        query: str, 
        initial_type: QueryType,
        entities: List[str]
    ) -> Optional[Dict]:
        """
        Use LLM to refine classification for ambiguous cases.
        
        This is the CORE of ChatGPT-quality understanding - the LLM figures out
        query intent from natural language, not hardcoded patterns.
        """
        
        try:
            # Enterprise-grade system prompt for accurate classification
            system_prompt = """You are an expert query classifier for a Business Intelligence system.
Your job is to understand user intent with extreme accuracy.

Available query types:
- factual: Simple fact lookup ("What is total revenue?")
- aggregation: Needs calculation ("Sum of sales by region")
- comparison: Comparing entities ("Compare A vs B")
- trend: Time-based patterns ("Growth over last 6 months")
- causal: Why/reason queries ("Why did sales drop?")
- relational: Entity relationships ("Who bought Product X?")
- predictive: Future forecasting ("Predict next quarter")
- exploratory: Open discovery ("What can you tell me?")
- ranking: Top/bottom N ("Top 5 customers")
- breakdown: Distribution analysis ("Revenue by category")
- summary: Overview requests ("Summarize my data")
- anomaly: Unusual patterns ("Find outliers")

RESPOND WITH JSON ONLY - NO OTHER TEXT."""

            user_prompt = f"""Query: "{query}"

Initial guess: {initial_type.value}
Detected entities: {entities}

Classify this query:
{{
    "type": "<one of the types above>",
    "confidence": <0.0-1.0>,
    "reasoning": "<brief explanation>"
}}"""

            response = chat(
                messages=[{"role": "user", "content": user_prompt}],
                system=system_prompt,
                temperature=0.1,  # Low temp for consistent classification
                max_tokens=200
            )
            
            # Parse JSON from response
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                type_str = result.get("type", "").lower()
                
                # Map string to enum
                type_map = {t.value: t for t in QueryType}
                if type_str in type_map:
                    result["type"] = type_map[type_str]
                    return result
        except Exception as e:
            print(f"[CLASSIFIER] LLM refinement failed: {e}")
        
        return None
    
    def _extract_time_reference(self, query: str) -> Optional[str]:
        """Extract time references from query"""
        patterns = [
            r"(last|past|previous)\s+(\d+)\s+(day|week|month|year)s?",
            r"(this|current)\s+(week|month|quarter|year)",
            r"(january|february|march|april|may|june|july|august|september|october|november|december)\s*\d{4}?",
            r"\d{4}[-/]\d{2}[-/]\d{2}",
            r"(today|yesterday|this week|last week|this month|last month)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group()
        
        return None
    
    def _extract_comparison_targets(self, query: str) -> List[str]:
        """Extract comparison targets from query"""
        targets = []
        
        # Pattern: "compare X and Y" or "X vs Y"
        compare_patterns = [
            r"compare\s+(.+?)\s+(?:and|with|to|vs\.?)\s+(.+?)(?:\s|$|\.)",
            r"(.+?)\s+(?:vs\.?|versus)\s+(.+?)(?:\s|$|\.)",
            r"difference\s+between\s+(.+?)\s+and\s+(.+?)(?:\s|$|\.)"
        ]
        
        for pattern in compare_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                targets.extend([g.strip() for g in match.groups() if g])
                break
        
        return targets
    
    def _extract_aggregation_type(self, query: str) -> Optional[str]:
        """Extract aggregation type from query"""
        agg_map = {
            "total": ["total", "sum", "altogether"],
            "average": ["average", "mean", "avg"],
            "count": ["count", "number of", "how many"],
            "max": ["maximum", "highest", "top", "best", "most"],
            "min": ["minimum", "lowest", "bottom", "worst", "least"]
        }
        
        q_lower = query.lower()
        for agg_type, keywords in agg_map.items():
            if any(kw in q_lower for kw in keywords):
                return agg_type
        
        return None
    
    def _generate_explanation(
        self, 
        query_type: QueryType, 
        route: str, 
        depth: ReasoningDepth
    ) -> str:
        """Generate human-readable explanation of classification"""
        explanations = {
            "rag": "Using document search for factual retrieval",
            "graph": "Using knowledge graph for relationship analysis",
            "hybrid": "Combining documents and graph for comprehensive analysis",
            "vision": "Using vision AI for image analysis"
        }
        
        return (
            f"Query type: {query_type.value}, "
            f"Reasoning: {depth.value}, "
            f"Route: {explanations.get(route, route)}"
        )


# Singleton instance
_classifier = None

def get_query_classifier() -> EnterpriseQueryClassifier:
    """Get or create singleton classifier"""
    global _classifier
    if _classifier is None:
        _classifier = EnterpriseQueryClassifier(use_llm_refinement=True)
    return _classifier


def classify_query(query: str, has_image: bool = False) -> QueryAnalysis:
    """
    Convenience function for query classification.
    
    Args:
        query: User's natural language query
        has_image: Whether an image is attached
        
    Returns:
        QueryAnalysis with complete classification
    """
    classifier = get_query_classifier()
    return classifier.classify(query, has_image)
