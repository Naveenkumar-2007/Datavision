# Adaptive RAG Module - Intelligent Query Routing & Retrieval
"""
Adaptive RAG intelligently selects the best retrieval strategy
based on query characteristics:

1. Query Classification:
   - Factual: Simple lookups → RAG
   - Analytical: Trends, patterns → GraphRAG
   - Comparative: Multiple entities → Hybrid
   - Exploratory: Open-ended → Graph + Semantic

2. Retrieval Adaptation:
   - Adjusts k (number of results)
   - Adjusts semantic weight for hybrid
   - Selects best data sources

3. Response Quality:
   - Validates response relevance
   - Triggers fallback if low confidence
"""

import re
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class QueryType(Enum):
    """Query classification types"""
    FACTUAL = "factual"          # What, show, list, total
    ANALYTICAL = "analytical"    # Why, trend, pattern, correlation
    COMPARATIVE = "comparative"  # Compare, vs, difference
    EXPLORATORY = "exploratory"  # Insights, analyze, overview
    TEMPORAL = "temporal"        # Time-based queries
    ENTITY = "entity"            # Specific entity lookup
    AGGREGATE = "aggregate"      # Sum, count, average


@dataclass
class QueryAnalysis:
    """Analysis of user query"""
    query: str
    query_type: QueryType
    confidence: float
    entities: List[str]
    time_references: List[str]
    metrics_mentioned: List[str]
    recommended_route: str
    recommended_k: int
    semantic_weight: float
    requires_graph: bool
    requires_vectors: bool


class AdaptiveRouter:
    """
    Intelligent query routing with adaptive retrieval
    """
    
    # Query type patterns
    FACTUAL_PATTERNS = [
        r'\bwhat (is|are|was|were)\b',
        r'\bshow me\b',
        r'\blist\b',
        r'\btotal\b',
        r'\bhow many\b',
        r'\bdisplay\b',
        r'\bget\b',
    ]
    
    ANALYTICAL_PATTERNS = [
        r'\bwhy\b',
        r'\bhow did\b',
        r'\btrend\b',
        r'\bpattern\b',
        r'\bcorrelation\b',
        r'\bcause\b',
        r'\breason\b',
        r'\binsight\b',
        r'\banalysis\b',
        r'\bexplain\b',
    ]
    
    COMPARATIVE_PATTERNS = [
        r'\bcompare\b',
        r'\bvs\b',
        r'\bversus\b',
        r'\bdifference\b',
        r'\bbetween\b.*\band\b',
        r'\bmore than\b',
        r'\bless than\b',
    ]
    
    TEMPORAL_PATTERNS = [
        r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b',
        r'\b(q1|q2|q3|q4)\b',
        r'\b\d{4}\b',  # Year
        r'\blast (week|month|year|quarter)\b',
        r'\bthis (week|month|year|quarter)\b',
        r'\byesterday\b',
        r'\btoday\b',
    ]
    
    AGGREGATE_PATTERNS = [
        r'\btotal\b',
        r'\bsum\b',
        r'\baverage\b',
        r'\bcount\b',
        r'\bmaximum\b',
        r'\bminimum\b',
        r'\bmax\b',
        r'\bmin\b',
    ]
    
    # Entity patterns
    ENTITY_PATTERNS = [
        r'\bcustomer[:\s]+([A-Za-z0-9_\s]+)',
        r'\bproduct[:\s]+([A-Za-z0-9_\s]+)',
        r'\binvoice[:\s#]+([A-Za-z0-9_]+)',
    ]
    
    def __init__(self):
        """Initialize router with compiled patterns"""
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficiency"""
        self.factual_re = [re.compile(p, re.IGNORECASE) for p in self.FACTUAL_PATTERNS]
        self.analytical_re = [re.compile(p, re.IGNORECASE) for p in self.ANALYTICAL_PATTERNS]
        self.comparative_re = [re.compile(p, re.IGNORECASE) for p in self.COMPARATIVE_PATTERNS]
        self.temporal_re = [re.compile(p, re.IGNORECASE) for p in self.TEMPORAL_PATTERNS]
        self.aggregate_re = [re.compile(p, re.IGNORECASE) for p in self.AGGREGATE_PATTERNS]
        self.entity_re = [re.compile(p, re.IGNORECASE) for p in self.ENTITY_PATTERNS]
    
    def analyze_query(self, query: str) -> QueryAnalysis:
        """
        Analyze query and determine optimal retrieval strategy
        
        Args:
            query: User's query string
            
        Returns:
            QueryAnalysis with routing recommendations
        """
        query_lower = query.lower()
        
        # Calculate scores for each type
        scores = {
            QueryType.FACTUAL: self._score_patterns(query, self.factual_re),
            QueryType.ANALYTICAL: self._score_patterns(query, self.analytical_re),
            QueryType.COMPARATIVE: self._score_patterns(query, self.comparative_re),
            QueryType.TEMPORAL: self._score_patterns(query, self.temporal_re),
            QueryType.AGGREGATE: self._score_patterns(query, self.aggregate_re),
        }
        
        # Determine primary type
        primary_type, confidence = max(scores.items(), key=lambda x: x[1])
        
        # Default to analytical if low confidence (encourages graph-first)
        if confidence < 0.3:
            primary_type = QueryType.ANALYTICAL
            confidence = 0.5
        
        # Extract entities
        entities = self._extract_entities(query)
        
        # Extract time references
        time_refs = self._extract_time_references(query)
        
        # Extract metrics
        metrics = self._extract_metrics(query)
        
        # Determine route and parameters
        route, k, semantic_weight, requires_graph, requires_vectors = \
            self._determine_strategy(primary_type, entities, time_refs, confidence)
        
        return QueryAnalysis(
            query=query,
            query_type=primary_type,
            confidence=confidence,
            entities=entities,
            time_references=time_refs,
            metrics_mentioned=metrics,
            recommended_route=route,
            recommended_k=k,
            semantic_weight=semantic_weight,
            requires_graph=requires_graph,
            requires_vectors=requires_vectors
        )
    
    def _score_patterns(self, query: str, patterns: List[re.Pattern]) -> float:
        """Score query against pattern list"""
        matches = sum(1 for p in patterns if p.search(query))
        return min(1.0, matches / 3)  # Normalize to 0-1
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract named entities from query"""
        entities = []
        for pattern in self.entity_re:
            matches = pattern.findall(query)
            entities.extend(matches)
        return list(set(entities))
    
    def _extract_time_references(self, query: str) -> List[str]:
        """Extract time references from query"""
        refs = []
        for pattern in self.temporal_re:
            matches = pattern.findall(query)
            if matches:
                refs.extend(matches if isinstance(matches[0], str) else [m[0] for m in matches])
        return list(set(refs))
    
    def _extract_metrics(self, query: str) -> List[str]:
        """Extract business metrics mentioned"""
        metrics = []
        metric_keywords = [
            'revenue', 'sales', 'profit', 'margin', 'growth',
            'cost', 'expense', 'income', 'roi', 'conversion'
        ]
        query_lower = query.lower()
        for metric in metric_keywords:
            if metric in query_lower:
                metrics.append(metric)
        return metrics
    
    def _determine_strategy(
        self,
        query_type: QueryType,
        entities: List[str],
        time_refs: List[str],
        confidence: float
    ) -> Tuple[str, int, float, bool, bool]:
        """
        Determine retrieval strategy based on query analysis
        
        Returns: (route, k, semantic_weight, requires_graph, requires_vectors)
        """
        # Default: Graph-first architecture
        route = "graph"
        k = 5
        semantic_weight = 0.6
        requires_graph = True
        requires_vectors = True
        
        if query_type == QueryType.FACTUAL:
            # Factual queries benefit from RAG
            route = "rag" if not entities else "hybrid"
            k = 6
            semantic_weight = 0.5
            requires_graph = len(entities) > 0
            requires_vectors = True
            
        elif query_type == QueryType.ANALYTICAL:
            # Analytical queries need graph reasoning
            route = "graph"
            k = 4
            semantic_weight = 0.7
            requires_graph = True
            requires_vectors = len(time_refs) > 0
            
        elif query_type == QueryType.COMPARATIVE:
            # Comparative queries need both
            route = "hybrid"
            k = 8
            semantic_weight = 0.5
            requires_graph = True
            requires_vectors = True
            
        elif query_type == QueryType.TEMPORAL:
            # Time-based queries need graph + vectors
            route = "hybrid"
            k = 6
            semantic_weight = 0.6
            requires_graph = True
            requires_vectors = True
            
        elif query_type == QueryType.AGGREGATE:
            # Aggregations work best with graph
            route = "graph"
            k = 4
            semantic_weight = 0.5
            requires_graph = True
            requires_vectors = False
        
        # Adjust if specific entities mentioned
        if entities:
            k += 2
            requires_graph = True
        
        return route, k, semantic_weight, requires_graph, requires_vectors


class AdaptiveRetriever:
    """
    Executes adaptive retrieval based on query analysis
    """
    
    def __init__(self, user_id: str):
        """
        Args:
            user_id: User/company identifier
        """
        self.user_id = user_id
        self.router = AdaptiveRouter()
    
    def retrieve(self, query: str) -> Dict[str, Any]:
        """
        Perform adaptive retrieval
        
        Args:
            query: User query
            
        Returns:
            Dictionary with context, analysis, and metadata
        """
        # Analyze query
        analysis = self.router.analyze_query(query)
        
        context_parts = []
        sources = []
        
        # Get vector context if needed
        if analysis.requires_vectors:
            vector_context = self._get_vector_context(
                query,
                k=analysis.recommended_k,
                alpha=analysis.semantic_weight
            )
            if vector_context:
                context_parts.append(("Documents", vector_context["text"]))
                sources.extend(vector_context["sources"])
        
        # Get graph context if needed
        if analysis.requires_graph:
            graph_context = self._get_graph_context(query)
            if graph_context:
                context_parts.append(("Knowledge Graph", graph_context))
        
        # Combine context
        combined_context = self._format_context(context_parts)
        
        return {
            "context": combined_context,
            "sources": sources,
            "analysis": analysis,
            "route": analysis.recommended_route
        }
    
    def _get_vector_context(self, query: str, k: int, alpha: float) -> Optional[Dict]:
        """Get context from vector store using hybrid search"""
        try:
            from vector.hybrid_search import hybrid_retrieve
            
            results = hybrid_retrieve(query, k=k, user_id=self.user_id, alpha=alpha)
            
            if not results:
                return None
            
            texts = []
            sources = []
            
            for r in results:
                texts.append(r.get("text", ""))
                source = r.get("source") or r.get("metadata", {}).get("source", "Unknown")
                if source not in sources:
                    sources.append(source)
            
            return {
                "text": "\n\n".join(texts),
                "sources": sources[:3]
            }
            
        except Exception as e:
            print(f"⚠️ Vector retrieval error: {e}")
            
            # Fallback to basic retrieval
            try:
                from vector.retriever import retrieve
                results = retrieve(query, k=k, user_id=self.user_id)
                
                if results:
                    texts = [r.get("text", "") for r in results]
                    sources = [r.get("metadata", {}).get("source", "Unknown") for r in results]
                    return {
                        "text": "\n\n".join(texts),
                        "sources": list(set(sources))[:3]
                    }
            except:
                pass
            
            return None
    
    def _get_graph_context(self, query: str) -> Optional[str]:
        """Get context from knowledge graph"""
        try:
            from graph.query import graph_snapshot, revenue_dataframe, get_graph_stats
            
            # Get graph statistics
            stats = get_graph_stats(self.user_id)
            
            if stats.get("total_nodes", 0) == 0:
                return None
            
            # Get graph snapshot
            snapshot = graph_snapshot(self.user_id, max_nodes=50)
            
            # Get revenue data summary
            df = revenue_dataframe(self.user_id)
            revenue_summary = ""
            
            if df is not None and not df.empty:
                amount_col = 'amount' if 'amount' in df.columns else 'total_amount'
                if amount_col in df.columns:
                    total = df[amount_col].sum()
                    avg = df[amount_col].mean()
                    revenue_summary = f"\nRevenue: Total ${total:,.2f}, Avg ${avg:,.2f}"
            
            return f"{snapshot}{revenue_summary}"
            
        except Exception as e:
            print(f"⚠️ Graph context error: {e}")
            return None
    
    def _format_context(self, parts: List[Tuple[str, str]]) -> str:
        """Format context parts into combined string"""
        if not parts:
            return ""
        
        formatted = []
        for title, content in parts:
            formatted.append(f"**{title}:**\n{content}")
        
        return "\n\n---\n\n".join(formatted)


def adaptive_retrieve(query: str, user_id: str = "user_001") -> Dict[str, Any]:
    """
    Main adaptive retrieval function
    
    Args:
        query: User query
        user_id: User identifier
        
    Returns:
        Retrieval results with context and metadata
    """
    retriever = AdaptiveRetriever(user_id)
    return retriever.retrieve(query)


def get_query_analysis(query: str) -> QueryAnalysis:
    """
    Analyze query without retrieval
    
    Args:
        query: User query
        
    Returns:
        QueryAnalysis object
    """
    router = AdaptiveRouter()
    return router.analyze_query(query)
