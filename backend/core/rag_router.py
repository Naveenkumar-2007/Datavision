"""
Advanced RAG Router - Intelligent Strategy Selection
=====================================================

The RAG Router analyzes queries and selects the BEST RAG technique:
1. Simple queries → Basic RAG
2. Complex reasoning → Self-RAG
3. Long documents → RAPTOR
4. Need freshness → Corrective RAG with web fallback
5. Context-heavy → Contextual Retrieval
6. Multi-hop → GraphRAG

This maximizes quality while minimizing latency and API costs.

Uses FREE APIs only (Groq/Gemini).
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from core.llm import chat

logger = logging.getLogger(__name__)


class RAGStrategy(Enum):
    """Available RAG strategies"""
    BASIC = "basic"                     # Simple retrieval + generation
    SELF_RAG = "self_rag"               # Self-reflective with validation
    CORRECTIVE = "corrective"           # With web fallback
    CONTEXTUAL = "contextual"           # Anthropic's contextual retrieval
    RAPTOR = "raptor"                   # Hierarchical for long docs
    GRAPH = "graph"                     # GraphRAG for relationships
    HYBRID = "hybrid"                   # Combines multiple strategies
    AGENTIC = "agentic"                 # Full agent-based approach


@dataclass
class RAGRoutingDecision:
    """Result of routing decision"""
    strategy: RAGStrategy
    confidence: float
    reasoning: str
    estimated_latency: str
    fallback_strategy: RAGStrategy


class QueryComplexity(Enum):
    """Complexity levels for queries"""
    SIMPLE = "simple"           # Single fact lookup
    MODERATE = "moderate"       # Some reasoning required
    COMPLEX = "complex"         # Multi-step reasoning
    EXPERT = "expert"           # Deep analysis needed


class AdvancedRAGRouter:
    """
    Intelligently routes queries to the best RAG strategy.
    
    This optimizes for:
    - Quality (best answer)
    - Speed (lowest latency)
    - Cost (fewer API calls)
    
    Uses FREE APIs (Groq/Gemini).
    """
    
    def __init__(self):
        self.routing_history: List[Dict[str, Any]] = []
        
        # Strategy characteristics
        self.strategy_info = {
            RAGStrategy.BASIC: {
                "latency": "fast",
                "quality": "good",
                "best_for": ["simple questions", "fact lookup", "definitions"]
            },
            RAGStrategy.SELF_RAG: {
                "latency": "medium",
                "quality": "excellent",
                "best_for": ["accuracy-critical", "needs verification", "complex answers"]
            },
            RAGStrategy.CORRECTIVE: {
                "latency": "slow",
                "quality": "excellent",
                "best_for": ["incomplete context", "needs external info", "current events"]
            },
            RAGStrategy.CONTEXTUAL: {
                "latency": "fast",
                "quality": "very good",
                "best_for": ["context-dependent", "multiple documents", "ambiguous chunks"]
            },
            RAGStrategy.RAPTOR: {
                "latency": "medium",
                "quality": "excellent",
                "best_for": ["long documents", "summarization", "overview questions"]
            },
            RAGStrategy.GRAPH: {
                "latency": "slow",
                "quality": "excellent",
                "best_for": ["relationships", "comparisons", "entity connections"]
            },
            RAGStrategy.HYBRID: {
                "latency": "slow",
                "quality": "best",
                "best_for": ["complex multi-part questions", "research tasks"]
            },
            RAGStrategy.AGENTIC: {
                "latency": "slowest",
                "quality": "best",
                "best_for": ["actions needed", "multi-step plans", "tool use"]
            }
        }
    
    def _analyze_query_type(self, query: str) -> Dict[str, Any]:
        """
        Analyze query characteristics using heuristics.
        Fast local analysis before LLM if needed.
        """
        
        query_lower = query.lower()
        
        analysis = {
            "is_simple_lookup": False,
            "needs_comparison": False,
            "needs_calculation": False,
            "needs_visualization": False,
            "needs_current_info": False,
            "is_multi_part": False,
            "needs_action": False,
            "document_scope": "unknown"
        }
        
        # Simple lookup patterns
        simple_patterns = ["what is", "who is", "when was", "where is", "define", "list"]
        if any(query_lower.startswith(p) for p in simple_patterns):
            analysis["is_simple_lookup"] = True
        
        # Comparison patterns
        if any(p in query_lower for p in ["compare", "vs", "versus", "difference between", "better"]):
            analysis["needs_comparison"] = True
        
        # Calculation patterns
        if any(p in query_lower for p in ["calculate", "total", "sum", "average", "percentage", "growth"]):
            analysis["needs_calculation"] = True
        
        # Visualization patterns
        if any(p in query_lower for p in ["chart", "graph", "visualize", "plot", "show me", "trend"]):
            analysis["needs_visualization"] = True
        
        # Current info patterns
        if any(p in query_lower for p in ["latest", "current", "today", "now", "this week", "recent"]):
            analysis["needs_current_info"] = True
        
        # Multi-part patterns
        if any(p in query_lower for p in [" and ", " also ", " then ", "first,", "second,"]):
            analysis["is_multi_part"] = True
        
        # Action patterns
        if any(p in query_lower for p in ["send", "email", "notify", "create", "update", "schedule"]):
            analysis["needs_action"] = True
        
        # Document scope
        if any(p in query_lower for p in ["all documents", "across", "summary of all", "overview"]):
            analysis["document_scope"] = "multi"
        elif any(p in query_lower for p in ["this document", "this file", "the report"]):
            analysis["document_scope"] = "single"
        
        return analysis
    
    def _estimate_complexity(self, query: str, analysis: Dict[str, Any]) -> QueryComplexity:
        """
        Estimate query complexity.
        """
        
        score = 0
        
        if analysis["is_simple_lookup"]:
            score -= 2
        if analysis["needs_comparison"]:
            score += 1
        if analysis["needs_calculation"]:
            score += 1
        if analysis["is_multi_part"]:
            score += 2
        if analysis["needs_action"]:
            score += 3
        if len(query.split()) > 20:
            score += 1
        
        if score <= 0:
            return QueryComplexity.SIMPLE
        elif score <= 2:
            return QueryComplexity.MODERATE
        elif score <= 4:
            return QueryComplexity.COMPLEX
        else:
            return QueryComplexity.EXPERT
    
    def route(
        self,
        query: str,
        context_available: bool = True,
        document_count: int = 1,
        prefer_speed: bool = False,
        prefer_quality: bool = False
    ) -> RAGRoutingDecision:
        """
        Route query to the best RAG strategy.
        
        Uses heuristics for fast routing (no LLM call!).
        
        Args:
            query: User's question
            context_available: Whether we have document context
            document_count: Number of documents in context
            prefer_speed: Prioritize speed over quality
            prefer_quality: Prioritize quality over speed
        """
        
        # Analyze query
        analysis = self._analyze_query_type(query)
        complexity = self._estimate_complexity(query, analysis)
        
        logger.info(f"RAG Router: Complexity={complexity.value}, Analysis={analysis}")
        
        # Decision logic
        if analysis["needs_action"]:
            strategy = RAGStrategy.AGENTIC
            reasoning = "Query requires taking action, using full agentic approach"
            
        elif not context_available or analysis["needs_current_info"]:
            strategy = RAGStrategy.CORRECTIVE
            reasoning = "Need external information or context incomplete, using corrective RAG with web fallback"
            
        elif analysis["needs_comparison"] or complexity == QueryComplexity.EXPERT:
            strategy = RAGStrategy.SELF_RAG
            reasoning = "Complex comparison or expert-level question, using self-reflective RAG for accuracy"
            
        elif document_count > 3 or analysis["document_scope"] == "multi":
            strategy = RAGStrategy.RAPTOR
            reasoning = "Multiple documents or need overview, using hierarchical RAPTOR"
            
        elif analysis["is_multi_part"]:
            strategy = RAGStrategy.HYBRID
            reasoning = "Multi-part question, using hybrid approach"
            
        elif prefer_speed or (analysis["is_simple_lookup"] and complexity == QueryComplexity.SIMPLE):
            strategy = RAGStrategy.BASIC
            reasoning = "Simple lookup, using basic fast RAG"
            
        elif prefer_quality:
            strategy = RAGStrategy.SELF_RAG
            reasoning = "Quality-first mode, using self-reflective RAG"
            
        else:
            # Default: contextual retrieval as good balance
            strategy = RAGStrategy.CONTEXTUAL
            reasoning = "Standard query, using contextual retrieval for balanced performance"
        
        # Determine fallback
        fallback_map = {
            RAGStrategy.BASIC: RAGStrategy.CONTEXTUAL,
            RAGStrategy.SELF_RAG: RAGStrategy.CORRECTIVE,
            RAGStrategy.CORRECTIVE: RAGStrategy.AGENTIC,
            RAGStrategy.CONTEXTUAL: RAGStrategy.SELF_RAG,
            RAGStrategy.RAPTOR: RAGStrategy.SELF_RAG,
            RAGStrategy.GRAPH: RAGStrategy.SELF_RAG,
            RAGStrategy.HYBRID: RAGStrategy.AGENTIC,
            RAGStrategy.AGENTIC: RAGStrategy.CORRECTIVE
        }
        
        # Confidence based on match quality
        confidence = 0.85
        if prefer_speed and strategy in [RAGStrategy.BASIC, RAGStrategy.CONTEXTUAL]:
            confidence = 0.95
        if prefer_quality and strategy in [RAGStrategy.SELF_RAG, RAGStrategy.AGENTIC]:
            confidence = 0.95
        
        # Latency estimate
        latency_map = {
            RAGStrategy.BASIC: "~1-2s",
            RAGStrategy.CONTEXTUAL: "~2-3s",
            RAGStrategy.SELF_RAG: "~3-5s",
            RAGStrategy.CORRECTIVE: "~5-8s",
            RAGStrategy.RAPTOR: "~3-5s",
            RAGStrategy.GRAPH: "~5-10s",
            RAGStrategy.HYBRID: "~8-12s",
            RAGStrategy.AGENTIC: "~10-20s"
        }
        
        decision = RAGRoutingDecision(
            strategy=strategy,
            confidence=confidence,
            reasoning=reasoning,
            estimated_latency=latency_map.get(strategy, "unknown"),
            fallback_strategy=fallback_map.get(strategy, RAGStrategy.BASIC)
        )
        
        # Record decision
        self.routing_history.append({
            "query": query[:100],
            "strategy": strategy.value,
            "confidence": confidence
        })
        
        return decision
    
    async def route_with_llm(
        self,
        query: str,
        context_preview: str = ""
    ) -> RAGRoutingDecision:
        """
        Use LLM for more accurate routing (slower but smarter).
        
        Only use for complex queries where heuristics might fail.
        """
        
        prompt = f"""You are a RAG strategy selector. Choose the best retrieval strategy for this query.

QUERY: {query}

CONTEXT PREVIEW (if any):
{context_preview[:500]}

AVAILABLE STRATEGIES:
1. basic - Fast, simple retrieval for straightforward questions
2. self_rag - Self-reflective, validates answers, great for accuracy
3. corrective - Falls back to web search if context insufficient
4. contextual - Adds document context to chunks, good for multi-doc
5. raptor - Hierarchical summarization, great for long documents
6. graph - Knowledge graph-based, great for relationships
7. hybrid - Combines multiple strategies for complex queries
8. agentic - Full agent approach with tools, for actions

Select ONE strategy and explain briefly.

Respond with JSON:
{{"strategy": "strategy_name", "confidence": 0.0-1.0, "reasoning": "why"}}"""

        try:
            result = chat(prompt, temperature=0.1)
            
            # Parse response
            import re
            json_match = re.search(r'\{[^{}]*\}', result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                strategy = RAGStrategy(data.get("strategy", "basic"))
                confidence = float(data.get("confidence", 0.8))
                reasoning = data.get("reasoning", "")
                
                return RAGRoutingDecision(
                    strategy=strategy,
                    confidence=confidence,
                    reasoning=reasoning,
                    estimated_latency="varies",
                    fallback_strategy=RAGStrategy.BASIC
                )
                
        except Exception as e:
            logger.warning(f"LLM routing failed: {e}, using heuristics")
        
        # Fall back to heuristic routing
        return self.route(query)
    
    def get_strategy_executor(self, strategy: RAGStrategy):
        """
        Get the executor function for a strategy.
        Import here to avoid circular dependencies.
        """
        
        executors = {
            RAGStrategy.BASIC: "core.rag_engine.query",
            RAGStrategy.SELF_RAG: "core.self_rag.self_rag_query",
            RAGStrategy.CORRECTIVE: "core.corrective_rag.correctiverag_pipeline",
            RAGStrategy.CONTEXTUAL: "core.contextual_retrieval.contextualize_chunks",
            RAGStrategy.RAPTOR: "core.raptor_rag.build_raptor_tree",
            RAGStrategy.GRAPH: "core.graph_rag.query",
            RAGStrategy.AGENTIC: "core.agentic_rag.AgenticRAG.run"
        }
        
        return executors.get(strategy, "core.rag_engine.query")


# Global router instance
_router = None

def get_router() -> AdvancedRAGRouter:
    """Get or create the global router"""
    global _router
    if _router is None:
        _router = AdvancedRAGRouter()
    return _router


def route_query(
    query: str,
    context_available: bool = True,
    prefer_speed: bool = False,
    prefer_quality: bool = False
) -> RAGRoutingDecision:
    """
    Simple interface to route a query.
    """
    router = get_router()
    return router.route(query, context_available, prefer_speed=prefer_speed, prefer_quality=prefer_quality)


# Test
if __name__ == "__main__":
    router = AdvancedRAGRouter()
    
    test_queries = [
        "What is the total revenue?",
        "Compare Q3 vs Q4 performance and explain the difference",
        "What's the latest news about our industry?",
        "Show me a chart of monthly sales trend",
        "First calculate growth rate, then identify top customers, and create a report",
        "Send email to the team with the weekly summary",
        "Give me an overview of all our financial documents"
    ]
    
    print("RAG Routing Tests:\n")
    for query in test_queries:
        decision = router.route(query)
        print(f"Query: {query[:50]}...")
        print(f"  Strategy: {decision.strategy.value}")
        print(f"  Latency: {decision.estimated_latency}")
        print(f"  Reasoning: {decision.reasoning}")
        print()
