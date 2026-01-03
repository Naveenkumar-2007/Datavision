"""
Universal AI Engine - DataVision's Core Intelligence
======================================================

The brain of DataVision. Works with ANY data type:
- Business data (sales, revenue, customers)
- HR data (employees, salaries, departments)
- Scientific data (experiments, measurements)
- IoT data (sensors, devices, metrics)
- Healthcare data (patients, treatments)
- Financial data (stocks, transactions)
- And ANY other structured data!

Features:
1. 7-Step Query Pipeline
2. Three-Layer Memory System
3. Self-Audit for quality
4. Universal Intent Classification
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Universal query intents - works for any domain"""
    GREETING = "greeting"
    AGGREGATION = "aggregation"     # Sum, count, average
    RANKING = "ranking"             # Top N, bottom N
    COMPARISON = "comparison"       # Compare X vs Y
    TREND = "trend"                 # Over time analysis
    PREDICTION = "prediction"       # Forecasting
    LISTING = "listing"             # List all X
    EXPLANATION = "explanation"     # Explain, why
    FOLLOWUP = "followup"           # Follow-up question
    DISTRIBUTION = "distribution"   # Breakdown, percentage
    CORRELATION = "correlation"     # Relationship between variables
    ANOMALY = "anomaly"             # Outliers, unusual
    GENERAL = "general"


@dataclass
class PipelineResult:
    """Result from the query pipeline"""
    intent: QueryIntent
    entities: List[str] = field(default_factory=list)
    confidence: float = 0.8
    should_refuse: bool = False
    refuse_reason: Optional[str] = None
    context_used: List[str] = field(default_factory=list)
    suggested_visualization: Optional[str] = None
    detected_domain: str = "general"  # business, hr, scientific, etc.


@dataclass
class AuditResult:
    """Result from self-audit"""
    passed: bool
    issues: List[str] = field(default_factory=list)
    claims_verified: int = 0
    confidence_score: float = 0.8


class ThreeLayerMemory:
    """
    ChatGPT-style three-layer memory system.
    Works with any data domain.
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.immediate: List[Dict] = []  # Last 5 turns
        self.session: List[Dict] = []     # Full session
        self.persistent: Dict = {}         # User facts
        self.topics_discussed: List[str] = []
        self.metrics_mentioned: Dict[str, float] = {}
        self.detected_domain: str = "general"
    
    def add_turn(self, role: str, content: str, **metadata):
        """Add a conversation turn"""
        turn = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            **metadata
        }
        
        self.immediate.append(turn)
        self.session.append(turn)
        
        # Keep immediate to last 5
        if len(self.immediate) > 5:
            self.immediate = self.immediate[-5:]
        
        # Track topics
        if metadata.get("topic"):
            if metadata["topic"] not in self.topics_discussed:
                self.topics_discussed.append(metadata["topic"])
        
        # Track metrics
        if metadata.get("metrics"):
            self.metrics_mentioned.update(metadata["metrics"])
    
    def get_context(self, max_turns: int = 10) -> str:
        """Get memory context for LLM"""
        parts = []
        
        # Add persistent facts
        if self.persistent:
            parts.append("Known facts: " + ", ".join(
                f"{k}: {v}" for k, v in self.persistent.items()
            ))
        
        # Add recent topics
        if self.topics_discussed:
            parts.append(f"Topics discussed: {', '.join(self.topics_discussed[-5:])}")
        
        # Add detected domain
        if self.detected_domain != "general":
            parts.append(f"Data domain: {self.detected_domain}")
        
        # Add recent turns
        parts.append("\nRecent conversation:")
        for turn in self.session[-max_turns:]:
            role = "User" if turn["role"] == "user" else "AI"
            content = turn["content"][:300]
            parts.append(f"{role}: {content}")
        
        return "\n".join(parts)
    
    def get_last_answer(self) -> Optional[str]:
        """Get last assistant answer"""
        for turn in reversed(self.session):
            if turn["role"] == "assistant":
                return turn["content"]
        return None


# Global memory store
_memory_store: Dict[str, ThreeLayerMemory] = {}


def get_ai_memory(session_id: str) -> ThreeLayerMemory:
    """Get or create memory for a session"""
    if session_id not in _memory_store:
        _memory_store[session_id] = ThreeLayerMemory(session_id)
    return _memory_store[session_id]


def detect_data_domain(query: str, columns: List[str] = None) -> str:
    """
    Detect what domain the data belongs to.
    
    Domains: business, hr, scientific, healthcare, financial, iot, general
    """
    query_lower = query.lower()
    columns_str = " ".join(columns or []).lower()
    combined = query_lower + " " + columns_str
    
    # HR domain
    hr_keywords = ['employee', 'salary', 'department', 'hire', 'performance', 'leave', 'hr', 'staff']
    if any(kw in combined for kw in hr_keywords):
        return "hr"
    
    # Healthcare domain
    health_keywords = ['patient', 'diagnosis', 'treatment', 'hospital', 'doctor', 'medical', 'health']
    if any(kw in combined for kw in health_keywords):
        return "healthcare"
    
    # Financial domain
    finance_keywords = ['stock', 'portfolio', 'investment', 'trading', 'market', 'ticker', 'dividend']
    if any(kw in combined for kw in finance_keywords):
        return "financial"
    
    # IoT domain
    iot_keywords = ['sensor', 'device', 'temperature', 'humidity', 'reading', 'iot', 'mqtt']
    if any(kw in combined for kw in iot_keywords):
        return "iot"
    
    # Scientific domain
    science_keywords = ['experiment', 'sample', 'measurement', 'hypothesis', 'variable', 'control']
    if any(kw in combined for kw in science_keywords):
        return "scientific"
    
    # Business domain (default for common terms)
    business_keywords = ['customer', 'revenue', 'sales', 'product', 'order', 'invoice', 'profit']
    if any(kw in combined for kw in business_keywords):
        return "business"
    
    return "general"


def execute_query_pipeline(
    query: str,
    session_id: str,
    memory: ThreeLayerMemory = None,
    columns: List[str] = None
) -> PipelineResult:
    """
    Execute the 7-step query processing pipeline.
    Works with any data type!
    """
    query_lower = query.lower()
    
    # Step 1: Intent Classification
    intent = _classify_intent(query_lower)
    
    # Step 2: Entity Extraction
    entities = _extract_entities(query)
    
    # Step 3: Domain Detection
    domain = detect_data_domain(query, columns)
    if memory:
        memory.detected_domain = domain
    
    # Step 4: Context Gathering
    context_used = []
    if memory:
        if memory.get_last_answer():
            context_used.append("previous_answer")
        if memory.topics_discussed:
            context_used.append("topic_history")
    
    # Step 5: Visualization Detection
    suggested_viz = _detect_visualization(query_lower, intent)
    
    # Step 6: Confidence Scoring
    confidence = _calculate_confidence(intent, len(entities))
    
    return PipelineResult(
        intent=intent,
        entities=entities,
        confidence=confidence,
        should_refuse=False,
        context_used=context_used,
        suggested_visualization=suggested_viz,
        detected_domain=domain
    )


def _classify_intent(query_lower: str) -> QueryIntent:
    """Classify query intent - works for any domain"""
    
    # Greeting
    if query_lower.strip() in ['hi', 'hello', 'hey', 'start']:
        return QueryIntent.GREETING
    if query_lower.startswith(('hi ', 'hello ', 'hey ')):
        return QueryIntent.GREETING
    
    # Follow-up
    if any(w in query_lower for w in ['explain', 'what about', 'tell me more', 'elaborate', 'above', 'that']):
        return QueryIntent.FOLLOWUP
    
    # Distribution
    if any(w in query_lower for w in ['distribution', 'breakdown', 'percentage', 'share', 'portion']):
        return QueryIntent.DISTRIBUTION
    
    # Correlation
    if any(w in query_lower for w in ['correlation', 'relationship', 'affect', 'impact on']):
        return QueryIntent.CORRELATION
    
    # Anomaly
    if any(w in query_lower for w in ['anomaly', 'outlier', 'unusual', 'abnormal', 'exception']):
        return QueryIntent.ANOMALY
    
    # Aggregation
    if any(w in query_lower for w in ['total', 'sum', 'count', 'how many', 'how much', 'average', 'mean']):
        return QueryIntent.AGGREGATION
    
    # Ranking
    if any(w in query_lower for w in ['top', 'best', 'highest', 'lowest', 'worst', 'bottom', 'rank']):
        return QueryIntent.RANKING
    
    # Comparison
    if any(w in query_lower for w in ['compare', 'vs', 'versus', 'difference', 'between']):
        return QueryIntent.COMPARISON
    
    # Trend
    if any(w in query_lower for w in ['trend', 'over time', 'growth', 'monthly', 'weekly', 'change']):
        return QueryIntent.TREND
    
    # Prediction
    if any(w in query_lower for w in ['predict', 'forecast', 'will', 'future', 'next', 'estimate']):
        return QueryIntent.PREDICTION
    
    # Listing
    if any(w in query_lower for w in ['list', 'show all', 'give me all', 'all the', 'every']):
        return QueryIntent.LISTING
    
    return QueryIntent.GENERAL


def _detect_visualization(query_lower: str, intent: QueryIntent) -> Optional[str]:
    """Detect if visualization is needed and suggest type"""
    
    # Explicit requests
    if 'pie' in query_lower:
        return 'pie'
    if 'line' in query_lower or 'trend' in query_lower:
        return 'line'
    if 'bar' in query_lower:
        return 'bar'
    if 'scatter' in query_lower:
        return 'scatter'
    if 'heatmap' in query_lower:
        return 'heatmap'
    
    # Chart keyword
    if any(w in query_lower for w in ['chart', 'graph', 'plot', 'visualize', 'show me']):
        # Infer from intent
        if intent == QueryIntent.DISTRIBUTION:
            return 'pie'
        if intent == QueryIntent.TREND:
            return 'line'
        if intent in [QueryIntent.RANKING, QueryIntent.COMPARISON]:
            return 'bar'
        return 'auto'
    
    return None


def _calculate_confidence(intent: QueryIntent, num_entities: int) -> float:
    """Calculate confidence based on intent and entities"""
    base = 0.75
    
    # Higher confidence for structured queries
    if intent in [QueryIntent.AGGREGATION, QueryIntent.RANKING, QueryIntent.LISTING]:
        base = 0.9
    elif intent == QueryIntent.PREDICTION:
        base = 0.7
    
    # Entities add confidence
    if num_entities > 0:
        base += 0.05 * min(num_entities, 3)
    
    return min(0.95, base)


def _extract_entities(query: str) -> List[str]:
    """Extract entities from query"""
    import re
    
    entities = []
    
    # Quoted entities
    quoted = re.findall(r'"([^"]+)"', query)
    entities.extend(quoted)
    
    # Capitalized entities
    caps = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', query)
    skip_words = ['What', 'Who', 'When', 'Where', 'Which', 'How', 'Why', 
                  'Show', 'List', 'Find', 'Get', 'Give', 'Tell', 'The', 'Total', 'All']
    for cap in caps:
        if cap not in skip_words:
            entities.append(cap)
    
    return list(set(entities))


def self_audit(
    response: str,
    memory: ThreeLayerMemory,
    pipeline_result: PipelineResult
) -> AuditResult:
    """Self-audit the response for quality"""
    issues = []
    claims_verified = 0
    
    # Check not empty
    if len(response.strip()) < 20:
        issues.append("Response too short")
    
    # Check intent addressed
    if pipeline_result.intent == QueryIntent.AGGREGATION:
        if any(c.isdigit() for c in response):
            claims_verified += 1
        else:
            issues.append("Aggregation query but no numbers")
    
    if pipeline_result.intent == QueryIntent.RANKING:
        if any(w in response.lower() for w in ['1.', '2.', 'top', 'first', 'highest']):
            claims_verified += 1
    
    confidence = 0.9 - (len(issues) * 0.1)
    confidence = max(0.3, min(1.0, confidence))
    
    return AuditResult(
        passed=len(issues) == 0,
        issues=issues,
        claims_verified=claims_verified,
        confidence_score=confidence
    )


def should_refuse(pipeline_result: PipelineResult) -> Tuple[bool, Optional[str]]:
    """Check if we should refuse to answer"""
    return pipeline_result.should_refuse, pipeline_result.refuse_reason
