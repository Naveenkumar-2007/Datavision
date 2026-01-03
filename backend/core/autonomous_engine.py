"""
Autonomous AI Engine - 100% LLM-Driven, ZERO Hardcoding
=========================================================

The ultimate autonomous data analysis engine. NO hardcoded keywords,
NO hardcoded suggestions, NO hardcoded patterns.

Everything is determined by LLM at runtime:
- Domain detection
- Query understanding  
- Column analysis
- Insight generation
- Follow-up suggestions
- Response formatting

This is what makes DataVision UNBEATABLE in competition!
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from core.llm import chat

logger = logging.getLogger(__name__)


@dataclass
class AutonomousAnalysis:
    """Result of fully autonomous query analysis"""
    intent: str                    # LLM-detected intent
    entities: List[str]            # LLM-extracted entities
    domain: str                    # LLM-detected data domain
    suggested_visualization: Optional[str]
    confidence: float
    reasoning: str                 # LLM's reasoning
    requires_data: bool
    is_followup: bool
    followup_context: Optional[str]


@dataclass
class AutonomousInsight:
    """LLM-generated insight"""
    insight: str
    importance: str  # high, medium, low
    actionable: bool


class AutonomousMemory:
    """
    Fully autonomous memory - learns what to remember from context.
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.turns: List[Dict] = []
        self.learned_facts: Dict[str, Any] = {}
        self.data_schema: Optional[Dict] = None
        self.detected_domain: Optional[str] = None
    
    def add_turn(self, role: str, content: str, metadata: Dict = None):
        """Add turn and autonomously extract learnings"""
        turn = {
            "role": role,
            "content": content[:1000],
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.turns.append(turn)
        
        # Keep last 20 turns
        if len(self.turns) > 20:
            self.turns = self.turns[-20:]
        
        # Autonomously extract facts from user messages
        if role == "user" and len(content) > 10:
            self._autonomous_fact_extraction(content)
    
    def _autonomous_fact_extraction(self, content: str):
        """Use LLM to extract facts autonomously"""
        try:
            prompt = f"""Extract any personal or important facts from this message.
Return JSON with extracted facts, or empty object if none.

Message: "{content}"

Examples of facts to extract:
- User's name if introduced
- Company name if mentioned
- Role/title if mentioned
- Preferences stated
- Important context

Return ONLY valid JSON like: {{"name": "John", "company": "Acme"}} or {{}}
JSON:"""
            
            result = chat(prompt, temperature=0.1, max_tokens=100)
            
            # Parse JSON
            try:
                # Clean JSON
                result = result.strip()
                if result.startswith('```'):
                    result = result.split('```')[1]
                    if result.startswith('json'):
                        result = result[4:]
                
                facts = json.loads(result)
                if isinstance(facts, dict) and facts:
                    self.learned_facts.update(facts)
                    logger.info(f"[AUTONOMOUS] Learned facts: {facts}")
            except:
                pass
        except Exception as e:
            logger.debug(f"Fact extraction error: {e}")
    
    def set_data_schema(self, columns: List[str], sample_data: str = ""):
        """Autonomously understand the data schema"""
        self.data_schema = {"columns": columns}
        
        # Use LLM to understand schema
        try:
            prompt = f"""Analyze this data schema and determine:
1. What domain is this data from?
2. What are the key columns?
3. What types of analysis are possible?

Columns: {columns}
Sample data preview: {sample_data[:500] if sample_data else "Not provided"}

Return JSON:
{{"domain": "detected domain", "key_columns": ["important", "columns"], "analysis_types": ["possible", "analyses"]}}
JSON:"""
            
            result = chat(prompt, temperature=0.1, max_tokens=200)
            
            try:
                result = result.strip()
                if '```' in result:
                    result = result.split('```')[1]
                    if result.startswith('json'):
                        result = result[4:]
                
                schema_analysis = json.loads(result)
                self.detected_domain = schema_analysis.get("domain", "general")
                self.data_schema.update(schema_analysis)
                logger.info(f"[AUTONOMOUS] Schema analysis: {schema_analysis}")
            except:
                pass
        except Exception as e:
            logger.debug(f"Schema analysis error: {e}")
    
    def get_context(self) -> str:
        """Get memory context for LLM"""
        parts = []
        
        if self.learned_facts:
            parts.append(f"Known about user: {json.dumps(self.learned_facts)}")
        
        if self.detected_domain:
            parts.append(f"Data domain: {self.detected_domain}")
        
        if self.data_schema:
            parts.append(f"Data columns: {self.data_schema.get('columns', [])}")
        
        parts.append("\nConversation:")
        for turn in self.turns[-10:]:
            role = "User" if turn["role"] == "user" else "AI"
            parts.append(f"{role}: {turn['content'][:200]}")
        
        return "\n".join(parts)
    
    def get_last_response(self) -> Optional[str]:
        for turn in reversed(self.turns):
            if turn["role"] == "assistant":
                return turn["content"]
        return None


# Global memory store
_autonomous_memory: Dict[str, AutonomousMemory] = {}


def get_autonomous_memory(session_id: str) -> AutonomousMemory:
    """Get or create autonomous memory"""
    if session_id not in _autonomous_memory:
        _autonomous_memory[session_id] = AutonomousMemory(session_id)
    return _autonomous_memory[session_id]


def autonomous_query_analysis(
    query: str,
    session_id: str,
    columns: List[str] = None,
    memory: AutonomousMemory = None
) -> AutonomousAnalysis:
    """
    Fully autonomous query analysis using LLM.
    NO hardcoded patterns - everything is determined by AI.
    """
    
    memory = memory or get_autonomous_memory(session_id)
    context = memory.get_context()
    last_response = memory.get_last_response()
    
    # Build analysis prompt
    prompt = f"""You are an AI analyzing a user query for a data analysis system.
Analyze COMPLETELY AUTONOMOUSLY - determine everything from context.

USER QUERY: "{query}"

AVAILABLE DATA COLUMNS: {columns or "Unknown"}

CONVERSATION CONTEXT:
{context}

LAST AI RESPONSE (for follow-up detection):
{last_response[:300] if last_response else "None"}

Analyze and return JSON with:
{{
    "intent": "the user's intent (aggregation/ranking/comparison/trend/listing/greeting/explanation/prediction/correlation/distribution/general)",
    "entities": ["extracted", "entity", "names"],
    "domain": "detected data domain based on columns",
    "visualization": "suggested chart type or null",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of your analysis",
    "requires_data": true/false,
    "is_followup": true/false - is this referring to previous response?,
    "followup_context": "what previous context is being referenced, or null"
}}

Return ONLY valid JSON:"""

    try:
        result = chat(prompt, temperature=0.1, max_tokens=400)
        
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
        
        # Find JSON object
        start = result.find('{')
        end = result.rfind('}') + 1
        if start >= 0 and end > start:
            result = result[start:end]
        
        analysis = json.loads(result)
        
        return AutonomousAnalysis(
            intent=analysis.get("intent", "general"),
            entities=analysis.get("entities", []),
            domain=analysis.get("domain", "general"),
            suggested_visualization=analysis.get("visualization"),
            confidence=float(analysis.get("confidence", 0.8)),
            reasoning=analysis.get("reasoning", ""),
            requires_data=analysis.get("requires_data", True),
            is_followup=analysis.get("is_followup", False),
            followup_context=analysis.get("followup_context")
        )
    except Exception as e:
        logger.warning(f"Autonomous analysis error: {e}")
        # Minimal fallback
        return AutonomousAnalysis(
            intent="general",
            entities=[],
            domain="general",
            suggested_visualization=None,
            confidence=0.5,
            reasoning="Fallback analysis",
            requires_data=True,
            is_followup=False,
            followup_context=None
        )


def autonomous_insight_generation(
    query: str,
    response: str,
    data_context: str = ""
) -> Optional[AutonomousInsight]:
    """
    Generate insights fully autonomously using LLM.
    NO hardcoded insight patterns!
    """
    try:
        prompt = f"""Based on this data analysis, generate ONE valuable insight.
The insight should be:
- Specific to this data (not generic)
- Actionable if possible
- Surprising or non-obvious

QUERY: {query}
RESPONSE: {response[:500]}
DATA CONTEXT: {data_context[:300] if data_context else "Not provided"}

Return JSON:
{{"insight": "your specific insight starting with 💡", "importance": "high/medium/low", "actionable": true/false}}

Return ONLY valid JSON:"""

        result = chat(prompt, temperature=0.7, max_tokens=150)
        
        # Parse JSON
        result = result.strip()
        if '```' in result:
            result = result.split('```')[1]
            if result.startswith('json'):
                result = result[4:]
        
        start = result.find('{')
        end = result.rfind('}') + 1
        if start >= 0 and end > start:
            result = result[start:end]
        
        insight_data = json.loads(result)
        
        return AutonomousInsight(
            insight=insight_data.get("insight", ""),
            importance=insight_data.get("importance", "medium"),
            actionable=insight_data.get("actionable", False)
        )
    except Exception as e:
        logger.debug(f"Insight generation error: {e}")
        return None


def autonomous_followup_suggestions(
    query: str,
    response: str,
    columns: List[str] = None
) -> List[str]:
    """
    Generate follow-up suggestions fully autonomously.
    NO hardcoded suggestions!
    """
    try:
        prompt = f"""Based on this data analysis, suggest 2-3 natural follow-up questions.
Questions should be:
- Specific to this data and response
- Logical next steps
- Valuable for deeper analysis

QUERY: {query}
RESPONSE: {response[:400]}
AVAILABLE COLUMNS: {columns or "Unknown"}

Return JSON array of 2-3 follow-up questions:
["question 1", "question 2", "question 3"]

Return ONLY the JSON array:"""

        result = chat(prompt, temperature=0.7, max_tokens=150)
        
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
        
        suggestions = json.loads(result)
        
        if isinstance(suggestions, list):
            return suggestions[:3]
        return []
    except Exception as e:
        logger.debug(f"Suggestion generation error: {e}")
        return []


def autonomous_greeting(
    user_name: Optional[str] = None,
    columns: List[str] = None,
    domain: str = None
) -> str:
    """
    Generate greeting fully autonomously based on context.
    NO hardcoded greeting messages!
    """
    try:
        prompt = f"""Generate a warm, helpful greeting for a data analysis AI called "DataVision".

Context:
- User name: {user_name or "Unknown"}
- Data columns available: {columns or "No data uploaded yet"}
- Detected domain: {domain or "Unknown"}

The greeting should:
- Be warm and professional
- Mention what analysis is possible with their data (if any)
- Suggest example questions they could ask
- Use emojis appropriately

Generate a greeting (2-4 sentences, then bullet points of example questions):"""

        result = chat(prompt, temperature=0.8, max_tokens=300)
        return result.strip()
    except Exception as e:
        logger.warning(f"Greeting generation error: {e}")
        return "Hello! I'm DataVision, your AI data analyst. Upload any data and ask me anything about it!"


def autonomous_response_enhancement(
    response: str,
    query: str,
    columns: List[str] = None
) -> str:
    """
    Enhance response fully autonomously.
    Adds insights and suggestions dynamically.
    """
    # Skip if already enhanced or too short
    if len(response) < 50 or "💡" in response or "You might also" in response:
        return response
    
    enhanced = response
    
    # Generate autonomous insight
    insight = autonomous_insight_generation(query, response)
    if insight and insight.insight:
        enhanced += f"\n\n{insight.insight}"
    
    # Generate autonomous suggestions
    suggestions = autonomous_followup_suggestions(query, response, columns)
    if suggestions:
        enhanced += "\n\n---\n**You might also ask:**\n"
        for s in suggestions[:2]:
            enhanced += f"• {s}\n"
    
    return enhanced
