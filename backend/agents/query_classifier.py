"""
Autonomous Query Classifier - 100% LLM-Driven
==============================================

NO hardcoded keywords or patterns!
Everything is determined by LLM at runtime.

This is the secret sauce that makes DataVision
unbeatable in any competition.
"""

import json
import logging
from typing import List, Optional
from dataclasses import dataclass, field
from enum import Enum

from core.llm import chat

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Query types - but detection is 100% LLM-driven"""
    FACTUAL = "factual"
    ANALYTICAL = "analytical"
    COMPARISON = "comparison"
    PREDICTION = "prediction"
    AGGREGATION = "aggregation"
    EXPLORATION = "exploration"
    GREETING = "greeting"
    VISUALIZATION = "visualization"
    CAUSAL = "causal"
    RELATIONAL = "relational"
    RANKING = "ranking"
    DISTRIBUTION = "distribution"
    TREND = "trend"
    ANOMALY = "anomaly"
    GENERAL = "general"


@dataclass
class QueryAnalysis:
    """Result of autonomous query classification"""
    query_type: QueryType
    confidence: float = 0.8
    aggregation_type: Optional[str] = None
    entities_mentioned: List[str] = field(default_factory=list)
    reasoning_depth: str = "shallow"
    requires_visualization: bool = False
    is_followup: bool = False
    
    def __post_init__(self):
        if self.entities_mentioned is None:
            self.entities_mentioned = []


def classify_query(query: str, columns: List[str] = None) -> QueryAnalysis:
    """
    Classify query 100% autonomously using LLM.
    NO hardcoded patterns whatsoever!
    """
    try:
        prompt = f"""Analyze this user query for a data analysis system.

QUERY: "{query}"

AVAILABLE DATA COLUMNS: {columns or "Unknown - analyze query alone"}

Determine:
1. Query type (choose ONE: factual, analytical, comparison, prediction, aggregation, exploration, greeting, visualization, causal, relational, ranking, distribution, trend, anomaly, general)
2. Confidence (0.0-1.0)
3. Aggregation type if applicable (sum, average, count, max, min, etc.)
4. Entities mentioned (proper nouns, column names, specific values)
5. Reasoning depth needed (shallow, moderate, deep)
6. Requires visualization? (true/false)
7. Is this a follow-up to previous conversation? (true/false)

Return ONLY valid JSON:
{{
    "query_type": "one of the types above",
    "confidence": 0.85,
    "aggregation_type": "sum or null",
    "entities_mentioned": ["Entity1", "Entity2"],
    "reasoning_depth": "shallow/moderate/deep",
    "requires_visualization": false,
    "is_followup": false
}}

JSON:"""

        result = chat(prompt, temperature=0.1, max_tokens=200)
        
        # Parse JSON
        result = result.strip()
        if '```' in result:
            parts = result.split('```')
            for part in parts:
                if '{' in part:
                    result = part
                    break
            if result.startswith('json'):
                result = result[4:]
        
        # Extract JSON object
        start = result.find('{')
        end = result.rfind('}') + 1
        if start >= 0 and end > start:
            result = result[start:end]
        
        analysis = json.loads(result)
        
        # Map string to enum
        query_type_str = analysis.get("query_type", "general").lower()
        try:
            query_type = QueryType(query_type_str)
        except ValueError:
            query_type = QueryType.GENERAL
        
        return QueryAnalysis(
            query_type=query_type,
            confidence=float(analysis.get("confidence", 0.8)),
            aggregation_type=analysis.get("aggregation_type"),
            entities_mentioned=analysis.get("entities_mentioned", []),
            reasoning_depth=analysis.get("reasoning_depth", "shallow"),
            requires_visualization=analysis.get("requires_visualization", False),
            is_followup=analysis.get("is_followup", False)
        )
        
    except Exception as e:
        logger.warning(f"Autonomous classification error: {e}")
        # Minimal fallback
        return QueryAnalysis(
            query_type=QueryType.GENERAL,
            confidence=0.5,
            entities_mentioned=[]
        )


def get_query_complexity(query: str) -> str:
    """
    Determine query complexity autonomously using LLM.
    """
    try:
        prompt = f"""Rate the complexity of this data query.

QUERY: "{query}"

Return ONLY one word: simple, moderate, or complex

Complexity:"""

        result = chat(prompt, temperature=0.1, max_tokens=10)
        result = result.strip().lower()
        
        if result in ['simple', 'moderate', 'complex']:
            return result
        return 'moderate'
    except:
        return 'moderate'


def extract_entities_autonomous(query: str, columns: List[str] = None) -> List[str]:
    """
    Extract entities 100% autonomously using LLM.
    """
    try:
        prompt = f"""Extract all entities (names, values, column references) from this query.

QUERY: "{query}"
KNOWN COLUMNS: {columns or "Unknown"}

Return JSON array of entities found:
["Entity1", "Entity2"]

Return ONLY the JSON array:"""

        result = chat(prompt, temperature=0.1, max_tokens=100)
        
        # Parse JSON array
        result = result.strip()
        if '```' in result:
            result = result.split('```')[1]
            if result.startswith('json'):
                result = result[4:]
        
        start = result.find('[')
        end = result.rfind(']') + 1
        if start >= 0 and end > start:
            result = result[start:end]
        
        entities = json.loads(result)
        return entities if isinstance(entities, list) else []
    except:
        return []


def detect_visualization_need(query: str, query_type: QueryType) -> Optional[str]:
    """
    Detect if visualization is needed and what type - using LLM.
    """
    try:
        prompt = f"""Should this data query result include a visualization?

QUERY: "{query}"
QUERY TYPE: {query_type.value}

If yes, what type? (bar, line, pie, scatter, heatmap, table, or none)

Return ONLY one word (the chart type or "none"):"""

        result = chat(prompt, temperature=0.1, max_tokens=10)
        result = result.strip().lower()
        
        valid_types = ['bar', 'line', 'pie', 'scatter', 'heatmap', 'table']
        if result in valid_types:
            return result
        return None
    except:
        return None
