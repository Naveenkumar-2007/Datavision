# Enterprise Confidence Scoring System
"""
Advanced confidence scoring for AI responses.

Features:
- RAG similarity-based scoring
- Graph relevance scoring
- Hybrid fusion confidence
- Answer quality metrics
- Source attribution confidence
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import numpy as np
from enum import Enum


class ConfidenceLevel(Enum):
    """Confidence level categories"""
    VERY_HIGH = "very_high"   # 0.9+
    HIGH = "high"             # 0.75-0.9
    MODERATE = "moderate"     # 0.5-0.75
    LOW = "low"               # 0.25-0.5
    VERY_LOW = "very_low"     # <0.25


@dataclass
class SourceScore:
    """Score for individual source"""
    source_name: str
    relevance_score: float
    coverage_score: float
    recency_score: float
    combined_score: float


@dataclass
class RAGConfidence:
    """RAG-specific confidence metrics"""
    similarity_scores: List[float]
    average_similarity: float
    top_similarity: float
    coverage_ratio: float  # How much of query is covered
    source_diversity: float  # Variety of sources used
    overall_score: float


@dataclass
class GraphConfidence:
    """GraphRAG-specific confidence metrics"""
    path_relevance: float
    hop_count: int
    node_importance: float  # PageRank-based
    edge_strength: float
    reasoning_depth: float
    overall_score: float


@dataclass
class HybridConfidence:
    """Hybrid mode confidence combining RAG + Graph"""
    rag_confidence: RAGConfidence
    graph_confidence: GraphConfidence
    fusion_weight_rag: float
    fusion_weight_graph: float
    agreement_score: float  # How much RAG and Graph agree
    overall_score: float


@dataclass
class AnswerConfidence:
    """Complete answer confidence assessment"""
    mode: str
    overall_score: float
    confidence_level: ConfidenceLevel
    rag_metrics: Optional[RAGConfidence]
    graph_metrics: Optional[GraphConfidence]
    hybrid_metrics: Optional[HybridConfidence]
    source_scores: List[SourceScore]
    explanation: str
    should_flag_uncertainty: bool


class EnterpriseConfidenceScorer:
    """
    Enterprise-grade confidence scoring system.
    
    Provides calibrated confidence scores for:
    - RAG retrieval quality
    - Graph reasoning strength
    - Hybrid fusion reliability
    - Overall answer quality
    """
    
    # Thresholds for confidence levels
    THRESHOLDS = {
        ConfidenceLevel.VERY_HIGH: 0.9,
        ConfidenceLevel.HIGH: 0.75,
        ConfidenceLevel.MODERATE: 0.5,
        ConfidenceLevel.LOW: 0.25,
        ConfidenceLevel.VERY_LOW: 0.0
    }
    
    def __init__(self):
        self.calibration_factor = 1.0  # Can be tuned based on feedback
    
    def score_rag_confidence(
        self,
        similarity_scores: List[float],
        sources: List[str],
        query_terms: int,
        matched_terms: int
    ) -> RAGConfidence:
        """
        Calculate RAG retrieval confidence.
        
        Args:
            similarity_scores: Cosine similarity scores from retrieval
            sources: List of source documents
            query_terms: Number of terms in query
            matched_terms: Number of terms found in retrieved docs
        """
        if not similarity_scores:
            return RAGConfidence(
                similarity_scores=[],
                average_similarity=0.0,
                top_similarity=0.0,
                coverage_ratio=0.0,
                source_diversity=0.0,
                overall_score=0.0
            )
        
        # Normalize similarity scores (FAISS L2 to 0-1)
        normalized_scores = [self._normalize_similarity(s) for s in similarity_scores]
        
        avg_sim = np.mean(normalized_scores)
        top_sim = max(normalized_scores)
        
        # Coverage: how many query terms were found
        coverage = matched_terms / max(query_terms, 1)
        
        # Diversity: unique sources / total retrieved
        unique_sources = len(set(sources))
        diversity = unique_sources / max(len(sources), 1)
        
        # Combined score with weights
        overall = (
            0.35 * top_sim +
            0.25 * avg_sim +
            0.25 * coverage +
            0.15 * diversity
        ) * self.calibration_factor
        
        return RAGConfidence(
            similarity_scores=normalized_scores,
            average_similarity=avg_sim,
            top_similarity=top_sim,
            coverage_ratio=coverage,
            source_diversity=diversity,
            overall_score=min(1.0, overall)
        )
    
    def score_graph_confidence(
        self,
        paths_found: int,
        avg_path_length: float,
        node_pageranks: List[float],
        edge_weights: List[float],
        max_hops_used: int
    ) -> GraphConfidence:
        """
        Calculate GraphRAG reasoning confidence.
        
        Args:
            paths_found: Number of relevant paths found
            avg_path_length: Average path length in hops
            node_pageranks: PageRank scores of traversed nodes
            edge_weights: Weights of traversed edges
            max_hops_used: Maximum hop depth used
        """
        if paths_found == 0:
            return GraphConfidence(
                path_relevance=0.0,
                hop_count=0,
                node_importance=0.0,
                edge_strength=0.0,
                reasoning_depth=0.0,
                overall_score=0.0
            )
        
        # Path relevance (more paths = more confident, with diminishing returns)
        path_relevance = min(1.0, paths_found / 10) * 0.8 + 0.2
        
        # Shorter paths are more reliable
        hop_score = max(0, 1.0 - (avg_path_length - 1) * 0.15)
        
        # Node importance from PageRank
        node_importance = np.mean(node_pageranks) if node_pageranks else 0.5
        
        # Edge strength
        edge_strength = np.mean(edge_weights) if edge_weights else 0.5
        
        # Reasoning depth (deeper = potentially riskier but more insightful)
        depth_factor = 1.0 - (max_hops_used - 1) * 0.1  # Penalty for deep traversal
        
        # Combined score
        overall = (
            0.30 * path_relevance +
            0.25 * hop_score +
            0.20 * node_importance +
            0.15 * edge_strength +
            0.10 * depth_factor
        ) * self.calibration_factor
        
        return GraphConfidence(
            path_relevance=path_relevance,
            hop_count=max_hops_used,
            node_importance=node_importance,
            edge_strength=edge_strength,
            reasoning_depth=depth_factor,
            overall_score=min(1.0, overall)
        )
    
    def score_hybrid_confidence(
        self,
        rag_conf: RAGConfidence,
        graph_conf: GraphConfidence,
        query_type: str
    ) -> HybridConfidence:
        """
        Calculate hybrid mode confidence with intelligent weighting.
        
        Args:
            rag_conf: RAG confidence metrics
            graph_conf: Graph confidence metrics
            query_type: Type of query for weight adjustment
        """
        # Dynamic weighting based on query type
        if query_type in ["causal", "relational", "predictive"]:
            # Graph-heavy for reasoning queries
            weight_rag = 0.3
            weight_graph = 0.7
        elif query_type in ["factual", "aggregation"]:
            # RAG-heavy for factual queries
            weight_rag = 0.7
            weight_graph = 0.3
        else:
            # Balanced for comparison/trend
            weight_rag = 0.5
            weight_graph = 0.5
        
        # Adjust weights based on individual confidence
        total_conf = rag_conf.overall_score + graph_conf.overall_score
        if total_conf > 0:
            # Shift weight towards more confident source
            rag_share = rag_conf.overall_score / total_conf
            weight_rag = weight_rag * 0.5 + rag_share * 0.5
            weight_graph = 1 - weight_rag
        
        # Agreement: how similar are the confidence levels
        agreement = 1 - abs(rag_conf.overall_score - graph_conf.overall_score)
        
        # Combined score
        overall = (
            weight_rag * rag_conf.overall_score +
            weight_graph * graph_conf.overall_score
        ) * (0.8 + 0.2 * agreement)  # Boost when sources agree
        
        return HybridConfidence(
            rag_confidence=rag_conf,
            graph_confidence=graph_conf,
            fusion_weight_rag=weight_rag,
            fusion_weight_graph=weight_graph,
            agreement_score=agreement,
            overall_score=min(1.0, overall)
        )
    
    def score_sources(
        self,
        sources: List[Dict],
        query: str
    ) -> List[SourceScore]:
        """Score individual sources for attribution"""
        source_scores = []
        
        for source in sources:
            name = source.get("name", source.get("source", "Unknown"))
            text = source.get("text", "")
            
            # Relevance: keyword overlap with query
            query_words = set(query.lower().split())
            text_words = set(text.lower().split())
            overlap = len(query_words & text_words) / max(len(query_words), 1)
            relevance = min(1.0, overlap * 2)
            
            # Coverage: length of useful content
            coverage = min(1.0, len(text) / 500)
            
            # Recency: assume recent unless dated
            recency = 0.8  # Default
            
            combined = 0.5 * relevance + 0.3 * coverage + 0.2 * recency
            
            source_scores.append(SourceScore(
                source_name=name,
                relevance_score=relevance,
                coverage_score=coverage,
                recency_score=recency,
                combined_score=combined
            ))
        
        return sorted(source_scores, key=lambda x: x.combined_score, reverse=True)
    
    def get_confidence_level(self, score: float) -> ConfidenceLevel:
        """Map score to confidence level"""
        if score >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif score >= 0.75:
            return ConfidenceLevel.HIGH
        elif score >= 0.5:
            return ConfidenceLevel.MODERATE
        elif score >= 0.25:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def build_answer_confidence(
        self,
        mode: str,
        rag_conf: Optional[RAGConfidence] = None,
        graph_conf: Optional[GraphConfidence] = None,
        hybrid_conf: Optional[HybridConfidence] = None,
        sources: List[Dict] = None
    ) -> AnswerConfidence:
        """Build complete answer confidence assessment"""
        
        # Determine overall score based on mode
        if mode == "hybrid" and hybrid_conf:
            overall = hybrid_conf.overall_score
        elif mode == "graph" and graph_conf:
            overall = graph_conf.overall_score
        elif mode == "rag" and rag_conf:
            overall = rag_conf.overall_score
        else:
            overall = 0.5  # Default moderate confidence
        
        level = self.get_confidence_level(overall)
        source_scores = self.score_sources(sources or [], "")
        
        # Should we flag uncertainty?
        should_flag = level in [ConfidenceLevel.LOW, ConfidenceLevel.VERY_LOW]
        
        # Generate explanation
        explanation = self._generate_confidence_explanation(mode, overall, level)
        
        return AnswerConfidence(
            mode=mode,
            overall_score=overall,
            confidence_level=level,
            rag_metrics=rag_conf,
            graph_metrics=graph_conf,
            hybrid_metrics=hybrid_conf,
            source_scores=source_scores,
            explanation=explanation,
            should_flag_uncertainty=should_flag
        )
    
    def _normalize_similarity(self, score: float) -> float:
        """Normalize FAISS L2 distance to 0-1 similarity"""
        # L2 distance: lower is better, typically 0-2 range
        # Convert to similarity: 1 / (1 + distance)
        if score < 0:
            return 1.0
        return 1.0 / (1.0 + score)
    
    def _generate_confidence_explanation(
        self, 
        mode: str, 
        score: float, 
        level: ConfidenceLevel
    ) -> str:
        """Generate human-readable confidence explanation"""
        level_descriptions = {
            ConfidenceLevel.VERY_HIGH: "Very high confidence based on strong evidence",
            ConfidenceLevel.HIGH: "High confidence with good supporting data",
            ConfidenceLevel.MODERATE: "Moderate confidence - some uncertainty exists",
            ConfidenceLevel.LOW: "Low confidence - limited supporting evidence",
            ConfidenceLevel.VERY_LOW: "Very low confidence - answer may be unreliable"
        }
        
        mode_descriptions = {
            "rag": "document retrieval",
            "graph": "knowledge graph reasoning",
            "hybrid": "combined document and graph analysis",
            "vision": "image analysis"
        }
        
        return (
            f"{level_descriptions.get(level, 'Unknown confidence')} "
            f"from {mode_descriptions.get(mode, mode)}. "
            f"Score: {score:.2f}"
        )


# Singleton instance
_scorer = None

def get_confidence_scorer() -> EnterpriseConfidenceScorer:
    """Get or create singleton scorer"""
    global _scorer
    if _scorer is None:
        _scorer = EnterpriseConfidenceScorer()
    return _scorer


def score_answer(
    mode: str,
    similarity_scores: List[float] = None,
    sources: List[str] = None,
    paths_found: int = 0,
    query_type: str = "factual"
) -> AnswerConfidence:
    """
    Convenience function to score an answer.
    
    Args:
        mode: Processing mode used
        similarity_scores: RAG similarity scores
        sources: Source documents
        paths_found: Graph paths found
        query_type: Query classification type
        
    Returns:
        AnswerConfidence with complete assessment
    """
    scorer = get_confidence_scorer()
    
    rag_conf = None
    graph_conf = None
    hybrid_conf = None
    
    if mode in ["rag", "hybrid"]:
        rag_conf = scorer.score_rag_confidence(
            similarity_scores=similarity_scores or [],
            sources=sources or [],
            query_terms=5,  # Default
            matched_terms=3
        )
    
    if mode in ["graph", "hybrid"]:
        graph_conf = scorer.score_graph_confidence(
            paths_found=paths_found,
            avg_path_length=2.0,
            node_pageranks=[0.5],
            edge_weights=[0.7],
            max_hops_used=2
        )
    
    if mode == "hybrid" and rag_conf and graph_conf:
        hybrid_conf = scorer.score_hybrid_confidence(rag_conf, graph_conf, query_type)
    
    return scorer.build_answer_confidence(
        mode=mode,
        rag_conf=rag_conf,
        graph_conf=graph_conf,
        hybrid_conf=hybrid_conf,
        sources=[{"source": s} for s in (sources or [])]
    )
