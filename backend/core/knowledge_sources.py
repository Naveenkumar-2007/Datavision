
"""
🧠 KNOWLEDGE SOURCES - Hybrid Intelligence System
=================================================

Silicon Valley-grade knowledge source classification and response labeling.

Features:
- KnowledgeSource enum for DATA vs AI_KNOWLEDGE distinction
- SourceClassifier for intelligent query routing
- SourceBadge for clear response labeling
- Hybrid response combining with proper attribution
"""

import logging
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


# =============================================================================
# KNOWLEDGE SOURCE TYPES
# =============================================================================

class KnowledgeSource(Enum):
    """Types of knowledge sources for responses."""
    USER_DATA = "user_data"           # 📊 From user's uploaded data
    AI_KNOWLEDGE = "ai_knowledge"     # 🌐 LLM general knowledge
    WEB_SEARCH = "web_search"         # 🔍 Real-time web data
    HYBRID = "hybrid"                 # 🔀 Multiple sources combined


@dataclass
class SourceBadge:
    """Badge for source attribution in responses."""
    source: KnowledgeSource
    icon: str
    label: str
    confidence: float = 1.0
    
    def to_markdown(self) -> str:
        """Format badge for markdown display."""
        conf_str = f" ({self.confidence:.0%} confident)" if self.confidence < 1.0 else ""
        return f"{self.icon} **{self.label}**{conf_str}"
    
    def to_html(self) -> str:
        """Format badge for HTML display."""
        colors = {
            KnowledgeSource.USER_DATA: "#14b8a6",      # Teal
            KnowledgeSource.AI_KNOWLEDGE: "#8b5cf6",   # Purple
            KnowledgeSource.WEB_SEARCH: "#f59e0b",     # Amber
            KnowledgeSource.HYBRID: "#3b82f6"          # Blue
        }
        color = colors.get(self.source, "#6b7280")
        return f'<span class="source-badge" style="background:{color}">{self.icon} {self.label}</span>'


# Pre-defined badges for convenience
SOURCE_BADGES = {
    KnowledgeSource.USER_DATA: SourceBadge(
        source=KnowledgeSource.USER_DATA,
        icon="📊",
        label="From Your Data"
    ),
    KnowledgeSource.AI_KNOWLEDGE: SourceBadge(
        source=KnowledgeSource.AI_KNOWLEDGE,
        icon="🌐",
        label="AI Knowledge"
    ),
    KnowledgeSource.WEB_SEARCH: SourceBadge(
        source=KnowledgeSource.WEB_SEARCH,
        icon="🔍",
        label="Web Search"
    ),
    KnowledgeSource.HYBRID: SourceBadge(
        source=KnowledgeSource.HYBRID,
        icon="🔀",
        label="Combined Sources"
    )
}


# =============================================================================
# QUERY CLASSIFICATION
# =============================================================================

class SourceClassifier:
    """
    Intelligent classifier to determine which knowledge source to use.
    
    Routes queries to:
    - USER_DATA: Questions about specific metrics, values, entities in their data
    - AI_KNOWLEDGE: General questions, best practices, industry knowledge
    - WEB_SEARCH: Current events, real-time data, external lookups
    - HYBRID: Comparative questions, benchmarking, context-needing queries
    """
    
    # Keywords indicating user data queries
    DATA_KEYWORDS = [
        # Possessive/specific
        'my', 'our', 'your data', 'uploaded', 'the data', 'in the data',
        'this dataset', 'these records', 'from the file',
        
        # Data operations
        'total', 'sum', 'average', 'mean', 'count', 'max', 'min',
        'show', 'list', 'display', 'get', 'find', 'filter',
        
        # Entity references (will check against actual columns)
        'revenue', 'sales', 'customers', 'products', 'orders',
        'transactions', 'employees', 'departments'
    ]
    
    # Keywords indicating AI knowledge queries
    AI_KEYWORDS = [
        # General knowledge
        'what is', 'how do', 'how to', 'explain', 'define',
        'best practice', 'industry standard', 'typically', 'generally',
        'recommend', 'suggest', 'advice', 'should i', 'could you',
        
        # Conceptual
        'difference between', 'compare concept', 'theory', 'methodology',
        'framework', 'strategy', 'approach', 'technique',
        
        # Learning
        'teach me', 'help me understand', 'what does', 'why is'
    ]
    
    # Keywords indicating web search needed
    WEB_KEYWORDS = [
        'current', 'today', 'latest', 'recent', 'news',
        'real-time', 'live', 'right now', 'this week', 'this month',
        'stock price', 'weather', 'exchange rate', 'market'
    ]
    
    # Keywords indicating hybrid query (data + context)
    HYBRID_KEYWORDS = [
        'compared to industry', 'benchmark', 'how does my', 'versus',
        'relative to', 'industry average', 'peer comparison',
        'better than', 'worse than', 'normal for', 'expected'
    ]
    
    def __init__(self, available_columns: List[str] = None):
        """
        Initialize classifier.
        
        Args:
            available_columns: Column names from user's data (for entity detection)
        """
        self.available_columns = available_columns or []
    
    def classify(self, query: str) -> Tuple[KnowledgeSource, float]:
        """
        Classify query to determine the best knowledge source.
        
        Args:
            query: User's question
            
        Returns:
            Tuple of (KnowledgeSource, confidence)
        """
        q_lower = query.lower().strip()
        
        # ==================================================================
        # STRONG PATTERN DETECTION - Check first before scoring
        # ==================================================================
        
        # Pattern: "What is X?" where X is NOT a data term → AI Knowledge
        what_is_pattern = re.match(r'^what\s+is\s+(.+?)[\?\.]?$', q_lower)
        if what_is_pattern:
            subject = what_is_pattern.group(1).strip()
            # Check if subject matches any column name
            is_data_term = any(
                col.lower() in subject or subject in col.lower() 
                for col in self.available_columns
            )
            if not is_data_term:
                # This is a general knowledge question
                return KnowledgeSource.AI_KNOWLEDGE, 0.9
        
        # Pattern: "Explain X", "Define X", "Tell me about X" → AI Knowledge
        general_patterns = [
            r'^explain\s+',
            r'^define\s+',
            r'^tell\s+me\s+about\s+',
            r'^how\s+does\s+.*\s+work',
            r'^what\s+are\s+the\s+benefits\s+of',
            r'^why\s+is\s+.*\s+important',
        ]
        for pattern in general_patterns:
            if re.match(pattern, q_lower):
                return KnowledgeSource.AI_KNOWLEDGE, 0.85
        
        # ==================================================================
        # SCORING - For ambiguous queries
        # ==================================================================
        scores = {
            KnowledgeSource.USER_DATA: 0.0,
            KnowledgeSource.AI_KNOWLEDGE: 0.0,
            KnowledgeSource.WEB_SEARCH: 0.0,
            KnowledgeSource.HYBRID: 0.0
        }
        
        # Check for explicit data keywords (requires possessive like "my", "our")
        data_possessives = ['my ', 'our ', 'my data', 'the data', 'in the data', 'from my', 'uploaded']
        for kw in data_possessives:
            if kw in q_lower:
                scores[KnowledgeSource.USER_DATA] += 3.0  # Strong signal
        
        # Check for data operation keywords (weaker signal alone)
        data_operations = ['total', 'sum', 'average', 'count', 'show', 'list', 'filter']
        for kw in data_operations:
            if kw in q_lower:
                scores[KnowledgeSource.USER_DATA] += 0.5
        
        # Check if query references actual columns (strong signal)
        for col in self.available_columns:
            col_lower = col.lower()
            if col_lower in q_lower or col_lower.replace('_', ' ') in q_lower:
                scores[KnowledgeSource.USER_DATA] += 2.0
        
        # Check for AI knowledge keywords (higher weight)
        for kw in self.AI_KEYWORDS:
            if kw in q_lower:
                scores[KnowledgeSource.AI_KNOWLEDGE] += 1.5
        
        # Check for web search keywords
        for kw in self.WEB_KEYWORDS:
            if kw in q_lower:
                scores[KnowledgeSource.WEB_SEARCH] += 1.5
        
        # Check for hybrid keywords
        for kw in self.HYBRID_KEYWORDS:
            if kw in q_lower:
                scores[KnowledgeSource.HYBRID] += 2.0
        
        # Determine winner
        max_score = max(scores.values())
        
        if max_score == 0:
            # Default: If no keywords matched, use AI knowledge (safer default)
            return KnowledgeSource.AI_KNOWLEDGE, 0.6
        
        # Get winning source
        winner = max(scores, key=scores.get)
        
        # Calculate confidence
        total = sum(scores.values())
        confidence = scores[winner] / total if total > 0 else 0.5
        
        return winner, min(confidence, 0.95)
    
    def get_detailed_classification(self, query: str) -> Dict[str, Any]:
        """Get detailed classification with all scores."""
        source, confidence = self.classify(query)
        
        return {
            "primary_source": source.value,
            "confidence": confidence,
            "badge": SOURCE_BADGES[source].to_markdown(),
            "requires_data": source in [KnowledgeSource.USER_DATA, KnowledgeSource.HYBRID],
            "requires_web": source == KnowledgeSource.WEB_SEARCH
        }


# =============================================================================
# HYBRID RESPONSE COMBINER
# =============================================================================

class HybridResponseCombiner:
    """
    Combines responses from multiple sources with proper attribution.
    """
    
    @staticmethod
    def combine(
        data_response: str = None,
        ai_response: str = None,
        web_response: str = None,
        primary_source: KnowledgeSource = KnowledgeSource.USER_DATA
    ) -> str:
        """
        Combine responses with clear source labels.
        
        Args:
            data_response: Response from user data analysis
            ai_response: Response from AI knowledge
            web_response: Response from web search
            primary_source: Which source is primary
            
        Returns:
            Combined response with source badges
        """
        sections = []
        
        # Add data response if available
        if data_response and data_response.strip():
            badge = SOURCE_BADGES[KnowledgeSource.USER_DATA].to_markdown()
            sections.append(f"{badge}\n\n{data_response}")
        
        # Add AI response if available  
        if ai_response and ai_response.strip():
            badge = SOURCE_BADGES[KnowledgeSource.AI_KNOWLEDGE].to_markdown()
            sections.append(f"{badge}\n\n{ai_response}")
        
        # Add web response if available
        if web_response and web_response.strip():
            badge = SOURCE_BADGES[KnowledgeSource.WEB_SEARCH].to_markdown()
            sections.append(f"{badge}\n\n{web_response}")
        
        if not sections:
            return "No information available."
        
        # Join with separator
        return "\n\n---\n\n".join(sections)
    
    @staticmethod
    def add_source_badge(response: str, source: KnowledgeSource) -> str:
        """Add a source badge to a response."""
        badge = SOURCE_BADGES[source].to_markdown()
        return f"{badge}\n\n{response}"
    
    @staticmethod
    def wrap_data_section(content: str, title: str = "From Your Data") -> str:
        """Wrap content with data source styling."""
        return f"""📊 **{title}**

{content}"""
    
    @staticmethod
    def wrap_ai_section(content: str, title: str = "AI Insights") -> str:
        """Wrap content with AI knowledge styling."""
        return f"""🌐 **{title}**

{content}"""


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def classify_query(query: str, columns: List[str] = None) -> Dict[str, Any]:
    """Quick function to classify a query."""
    classifier = SourceClassifier(columns)
    return classifier.get_detailed_classification(query)


def get_source_badge(source: KnowledgeSource) -> str:
    """Get markdown badge for a source."""
    return SOURCE_BADGES[source].to_markdown()


def combine_hybrid_response(
    data_response: str = None,
    ai_response: str = None,
    primary: str = "data"
) -> str:
    """Quick function to combine hybrid responses."""
    primary_source = KnowledgeSource.USER_DATA if primary == "data" else KnowledgeSource.AI_KNOWLEDGE
    return HybridResponseCombiner.combine(
        data_response=data_response,
        ai_response=ai_response,
        primary_source=primary_source
    )


# Module exports
__all__ = [
    'KnowledgeSource',
    'SourceBadge',
    'SOURCE_BADGES',
    'SourceClassifier',
    'HybridResponseCombiner',
    'classify_query',
    'get_source_badge',
    'combine_hybrid_response'
]
