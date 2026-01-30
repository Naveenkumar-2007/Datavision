# Enterprise Agent State - Extended for Advanced AI Modes
"""
State management for the AI Business Analyst agent.

Tracks:
- Query information
- Routing decisions
- Context and sources
- Confidence metrics
- Traversal paths
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class AgentState:
    """
    State object passed through agent workflow.
    
    Attributes:
        company_id: User/tenant identifier
        question: Original user question
        route: Selected processing mode (rag, graph, hybrid, vision)
        answer: Generated response
        context: Additional context and metadata
        sources: List of sources used in response
        confidence: Confidence score (0-1)
        query_type: Classified query type
        reasoning_depth: Required reasoning complexity
    """
    company_id: str
    question: str
    route: str = ""
    answer: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    sources: List[str] = field(default_factory=list)
    
    # Enhanced fields for enterprise modes
    confidence: float = 0.0
    query_type: str = ""
    reasoning_depth: str = ""
    entities: List[str] = field(default_factory=list)
    
    # Graph traversal metadata
    traversal_paths: int = 0
    visited_nodes: int = 0
    max_hops: int = 0
    
    # Hybrid fusion metadata
    fusion_weights: Dict[str, float] = field(default_factory=dict)
    primary_mode: str = ""
    
    # Vision metadata
    vision_extracted_text: str = ""
    vision_tables: List[Dict] = field(default_factory=list)
    vision_chart_data: Dict = field(default_factory=dict)
    
    # Performance metrics
    processing_time_ms: float = 0.0
    token_count: int = 0
    
    # Role Intelligence
    user_role: str = "analyst"  # executive, manager, analyst, operator
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary"""
        return {
            "company_id": self.company_id,
            "question": self.question,
            "route": self.route,
            "answer": self.answer,
            "sources": self.sources,
            "confidence": self.confidence,
            "query_type": self.query_type,
            "reasoning_depth": self.reasoning_depth,
            "entities": self.entities,
            "traversal_paths": self.traversal_paths,
            "visited_nodes": self.visited_nodes,
            "max_hops": self.max_hops,
            "fusion_weights": self.fusion_weights,
            "primary_mode": self.primary_mode,
            "processing_time_ms": self.processing_time_ms,
            "token_count": self.token_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentState":
        """Create state from dictionary"""
        return cls(
            company_id=data.get("company_id", ""),
            question=data.get("question", ""),
            route=data.get("route", ""),
            answer=data.get("answer", ""),
            context=data.get("context", {}),
            sources=data.get("sources", []),
            confidence=data.get("confidence", 0.0),
            query_type=data.get("query_type", ""),
            reasoning_depth=data.get("reasoning_depth", ""),
            entities=data.get("entities", []),
            traversal_paths=data.get("traversal_paths", 0),
            visited_nodes=data.get("visited_nodes", 0),
            max_hops=data.get("max_hops", 0),
            fusion_weights=data.get("fusion_weights", {}),
            primary_mode=data.get("primary_mode", ""),
            processing_time_ms=data.get("processing_time_ms", 0.0),
            token_count=data.get("token_count", 0)
        )
    
    def add_source(self, source: str) -> None:
        """Add a source if not already present"""
        if source and source not in self.sources:
            self.sources.append(source)
    
    def set_context(self, key: str, value: Any) -> None:
        """Set a context value"""
        self.context[key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get a context value"""
        return self.context.get(key, default)
    
    def merge_context(self, new_context: Dict[str, Any]) -> None:
        """Merge new context into existing"""
        self.context.update(new_context)
