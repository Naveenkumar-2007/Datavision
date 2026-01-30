"""
Memory Engine - Persistent Conversation Memory System
======================================================

Provides ChatGPT-level conversation memory:
1. Short-term: Current session context
2. Long-term: Persistent user preferences and facts
3. Episodic: Past conversation summaries

This enables the AI to remember:
- User's name and preferences
- Previous questions and answers
- Context from earlier in the conversation
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
import logging

from utils.paths import get_user_paths

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """A single turn in a conversation"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass  
class UserMemory:
    """Persistent memory about a user"""
    user_id: str
    name: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    facts: List[str] = field(default_factory=list)
    last_topics: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class MemoryEngine:
    """
    Enterprise-grade memory system for AI conversations.
    
    Features:
    - Short-term memory: Last N turns of current conversation
    - Long-term memory: Persistent user facts and preferences
    - Episodic memory: Summaries of past conversations
    - Context window management: Smart truncation for LLM limits
    """
    
    def __init__(self, user_id: str, max_short_term: int = 50):
        self.user_id = user_id
        self.max_short_term = max_short_term
        
        # Get storage paths
        self.paths = get_user_paths(user_id)
        self.memory_dir = self.paths.get("memory", Path(f"storage/users/{user_id}/memory"))
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # Memory files
        self.conversation_file = self.memory_dir / "conversation.json"
        self.user_memory_file = self.memory_dir / "user_memory.json"
        self.episodic_file = self.memory_dir / "episodic_memory.json"
        
        # Load memories
        self.short_term: List[ConversationTurn] = []
        self.user_memory: UserMemory = self._load_user_memory()
        self._load_conversation()
    
    def _load_user_memory(self) -> UserMemory:
        """Load persistent user memory from disk"""
        try:
            if self.user_memory_file.exists():
                with open(self.user_memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return UserMemory(**data)
        except Exception as e:
            logger.warning(f"Error loading user memory: {e}")
        
        return UserMemory(user_id=self.user_id)
    
    def _save_user_memory(self):
        """Save user memory to disk"""
        try:
            self.user_memory.updated_at = datetime.now().isoformat()
            with open(self.user_memory_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.user_memory), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving user memory: {e}")
    
    def _load_conversation(self):
        """Load conversation history from disk"""
        try:
            if self.conversation_file.exists():
                with open(self.conversation_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.short_term = [
                        ConversationTurn(**turn) for turn in data[-self.max_short_term:]
                    ]
        except Exception as e:
            logger.warning(f"Error loading conversation: {e}")
            self.short_term = []
    
    def _save_conversation(self):
        """Save conversation to disk"""
        try:
            with open(self.conversation_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(turn) for turn in self.short_term], f, indent=2)
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
    
    def add_turn(self, role: str, content: str, metadata: Dict = None):
        """Add a conversation turn to memory"""
        turn = ConversationTurn(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.short_term.append(turn)
        
        # Trim to max size
        if len(self.short_term) > self.max_short_term:
            self.short_term = self.short_term[-self.max_short_term:]
        
        # Extract user info if user message
        if role == "user":
            self._extract_user_info(content)
        
        # Save to disk
        self._save_conversation()
    
    def _extract_user_info(self, content: str):
        """Extract and save user information from messages"""
        import re
        
        content_lower = content.lower()
        
        # Extract name
        name_patterns = [
            r"(?:i'?m|i am|my name is|call me|this is)\s+([A-Z][a-z]+)",
            r"^([A-Z][a-z]+)\s+here",
        ]
        for pattern in name_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 1 and name.lower() not in ['the', 'a', 'an', 'i']:
                    self.user_memory.name = name
                    self._save_user_memory()
                    logger.info(f"📝 Remembered user name: {name}")
                    break
        
        # Extract company
        company_patterns = [
            r"(?:i work at|i'm from|from|at)\s+([A-Z][A-Za-z\s&]+(?:Inc|Corp|Ltd|LLC)?)",
            r"(?:company|organization|firm)\s+(?:is|called)\s+([A-Z][A-Za-z\s&]+)",
        ]
        for pattern in company_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                if len(company) > 2:
                    self.user_memory.company = company
                    self._save_user_memory()
                    break
        
        # Track topics discussed
        topic_keywords = {
            'revenue': ['revenue', 'sales', 'income'],
            'customers': ['customer', 'client', 'buyer'],
            'products': ['product', 'item', 'sku'],
            'trends': ['trend', 'growth', 'forecast', 'predict'],
            'comparison': ['compare', 'versus', 'vs', 'difference'],
            'metrics': ['kpi', 'margin', 'profit', 'roi', 'cost'],
            'segments': ['region', 'country', 'state', 'market', 'segment'],
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in content_lower for kw in keywords):
                if topic not in self.user_memory.last_topics:
                    self.user_memory.last_topics.append(topic)
                    if len(self.user_memory.last_topics) > 10:
                        self.user_memory.last_topics = self.user_memory.last_topics[-10:]
                    self._save_user_memory()
    
    def get_context_string(self, max_chars: int = 4000) -> str:
        """Get conversation context as a string for LLM"""
        parts = []
        
        # Add user memory context
        if self.user_memory.name:
            parts.append(f"User's name: {self.user_memory.name}")
        if self.user_memory.company:
            parts.append(f"User's company: {self.user_memory.company}")
        if self.user_memory.last_topics:
            parts.append(f"Recent topics: {', '.join(self.user_memory.last_topics[-5:])}")
        
        if parts:
            parts.append("---")
        
        # Add recent conversation
        parts.append("Recent conversation:")
        for turn in self.short_term[-10:]:
            role = "User" if turn.role == "user" else "Assistant"
            content = turn.content[:500]  # Truncate long messages
            parts.append(f"{role}: {content}")
        
        context = "\n".join(parts)
        
        # Truncate if too long
        if len(context) > max_chars:
            context = context[-max_chars:]
        
        return context
    
    def get_last_assistant_response(self) -> Optional[str]:
        """Get the last assistant response for follow-up context"""
        for turn in reversed(self.short_term):
            if turn.role == "assistant":
                return turn.content
        return None
    
    def get_last_user_query(self) -> Optional[str]:
        """Get the last user query"""
        for turn in reversed(self.short_term):
            if turn.role == "user":
                return turn.content
        return None
    
    def remember_fact(self, fact: str):
        """Store a fact about the user or their data"""
        if fact not in self.user_memory.facts:
            self.user_memory.facts.append(fact)
            if len(self.user_memory.facts) > 50:
                self.user_memory.facts = self.user_memory.facts[-50:]
            self._save_user_memory()
    
    def get_user_name(self) -> Optional[str]:
        """Get the user's name if known"""
        return self.user_memory.name
    
    def clear_conversation(self):
        """Clear current conversation but keep user memory"""
        self.short_term = []
        self._save_conversation()


# Global memory cache
_memory_cache: Dict[str, MemoryEngine] = {}


def get_memory_engine(user_id: str) -> MemoryEngine:
    """Get or create memory engine for a user"""
    if user_id not in _memory_cache:
        _memory_cache[user_id] = MemoryEngine(user_id)
    return _memory_cache[user_id]


def add_to_memory(user_id: str, role: str, content: str, metadata: Dict = None):
    """Quick function to add a turn to memory"""
    engine = get_memory_engine(user_id)
    engine.add_turn(role, content, metadata)


def get_conversation_context(user_id: str, max_chars: int = 4000) -> str:
    """Quick function to get conversation context"""
    engine = get_memory_engine(user_id)
    return engine.get_context_string(max_chars)


def get_last_response(user_id: str) -> Optional[str]:
    """Get last assistant response for a user"""
    engine = get_memory_engine(user_id)
    return engine.get_last_assistant_response()


def get_user_name(user_id: str) -> Optional[str]:
    """Get user's name if known"""
    engine = get_memory_engine(user_id)
    return engine.get_user_name()


# Shared memory singleton for chart context and cross-mode memory
_shared_memory: Dict[str, Any] = {}


def get_shared_memory() -> Dict[str, Any]:
    """
    Get the shared memory dictionary for storing cross-mode data.
    This is used for:
    - Chart context storage
    - Cross-mode communication
    - Temporary data caching
    """
    return _shared_memory


def set_shared_memory(key: str, value: Any):
    """Set a value in shared memory"""
    _shared_memory[key] = value


def get_shared_memory_value(key: str, default: Any = None) -> Any:
    """Get a value from shared memory"""
    return _shared_memory.get(key, default)


def clear_shared_memory():
    """Clear all shared memory (use with caution)"""
    _shared_memory.clear()
