# Persistent Memory Module - Company-Specific Personalization
"""
Persistent memory for user/company-specific context:
1. User preferences (currency, date format, etc.)
2. Company context (industry, products, key metrics)
3. Conversation history summaries
4. Learned patterns from interactions

This enables personalized responses without re-asking questions.
"""

import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict, field
from datetime import datetime


@dataclass
class UserProfile:
    """User/Company profile for personalization"""
    user_id: str
    company_name: str = ""
    industry: str = ""
    
    # Preferences
    currency: str = "USD"
    currency_symbol: str = "$"
    date_format: str = "YYYY-MM-DD"
    timezone: str = "UTC"
    language: str = "en"
    
    # Business context
    key_products: List[str] = field(default_factory=list)
    key_customers: List[str] = field(default_factory=list)
    key_metrics: List[str] = field(default_factory=list)
    fiscal_year_start: str = "January"
    
    # Learned context
    common_queries: List[str] = field(default_factory=list)
    important_dates: Dict[str, str] = field(default_factory=dict)  # {"Q1 end": "2024-03-31"}
    custom_terms: Dict[str, str] = field(default_factory=dict)    # {"SKU123": "Premium Widget"}
    
    # Metadata
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    total_queries: int = 0
    
    def to_context_string(self) -> str:
        """Generate context string for LLM prompts"""
        parts = []
        
        if self.company_name:
            parts.append(f"Company: {self.company_name}")
        if self.industry:
            parts.append(f"Industry: {self.industry}")
        if self.key_products:
            parts.append(f"Key Products: {', '.join(self.key_products[:5])}")
        if self.key_customers:
            parts.append(f"Key Customers: {', '.join(self.key_customers[:5])}")
        if self.key_metrics:
            parts.append(f"Focus Metrics: {', '.join(self.key_metrics)}")
        if self.custom_terms:
            terms = [f"{k}={v}" for k, v in list(self.custom_terms.items())[:5]]
            parts.append(f"Custom Terms: {', '.join(terms)}")
        
        parts.append(f"Currency: {self.currency_symbol} ({self.currency})")
        
        return "\n".join(parts)


@dataclass
class ConversationSummary:
    """Compressed summary of conversation history"""
    conversation_id: str
    user_id: str
    summary: str
    key_topics: List[str]
    insights_mentioned: List[str]
    timestamp: float
    message_count: int


class PersistentMemory:
    """
    Persistent memory store for user personalization
    
    Storage structure:
    storage/users/{user_id}/
        - profile.json      (User preferences & context)
        - memory.json       (Learned patterns)
        - summaries/        (Conversation summaries)
    """
    
    def __init__(self, storage_base: Path):
        """
        Args:
            storage_base: Base storage directory
        """
        self.storage_base = storage_base
        self._profiles: Dict[str, UserProfile] = {}
        self._summaries: Dict[str, List[ConversationSummary]] = {}
    
    def _get_user_dir(self, user_id: str) -> Path:
        """Get user-specific storage directory"""
        user_dir = self.storage_base / "users" / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    
    def get_profile(self, user_id: str) -> UserProfile:
        """
        Get or create user profile
        
        Args:
            user_id: User identifier
            
        Returns:
            UserProfile instance
        """
        # Check cache
        if user_id in self._profiles:
            return self._profiles[user_id]
        
        # Load from disk
        user_dir = self._get_user_dir(user_id)
        profile_path = user_dir / "profile.json"
        
        if profile_path.exists():
            try:
                with open(profile_path, 'r') as f:
                    data = json.load(f)
                profile = UserProfile(**data)
            except Exception as e:
                print(f"⚠️ Error loading profile: {e}")
                profile = UserProfile(user_id=user_id)
        else:
            profile = UserProfile(user_id=user_id)
        
        self._profiles[user_id] = profile
        return profile
    
    def save_profile(self, profile: UserProfile):
        """Save user profile to disk"""
        profile.updated_at = time.time()
        
        user_dir = self._get_user_dir(profile.user_id)
        profile_path = user_dir / "profile.json"
        
        with open(profile_path, 'w') as f:
            json.dump(asdict(profile), f, indent=2)
        
        self._profiles[profile.user_id] = profile
        print(f"💾 Profile saved for {profile.user_id}")
    
    def update_profile(self, user_id: str, **updates):
        """
        Update specific profile fields
        
        Args:
            user_id: User identifier
            **updates: Fields to update
        """
        profile = self.get_profile(user_id)
        
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        self.save_profile(profile)
    
    def learn_from_query(self, user_id: str, query: str, answer: str):
        """
        Learn from user query to improve future responses
        
        Extracts:
        - Common query patterns
        - Mentioned products/customers
        - Important metrics
        """
        profile = self.get_profile(user_id)
        profile.total_queries += 1
        
        # Track common queries (simplified - just store last 10)
        if query not in profile.common_queries:
            profile.common_queries.append(query)
            profile.common_queries = profile.common_queries[-10:]
        
        # Extract entities mentioned (simple keyword extraction)
        self._extract_entities(profile, query, answer)
        
        self.save_profile(profile)
    
    def _extract_entities(self, profile: UserProfile, query: str, answer: str):
        """Extract and learn entities from query/answer"""
        import re
        
        combined = f"{query} {answer}"
        
        # Currency detection
        currency_patterns = {
            r'₹|rupee|inr': ('INR', '₹'),
            r'\$|usd|dollar': ('USD', '$'),
            r'€|euro|eur': ('EUR', '€'),
            r'£|pound|gbp': ('GBP', '£'),
        }
        
        for pattern, (currency, symbol) in currency_patterns.items():
            if re.search(pattern, combined, re.IGNORECASE):
                profile.currency = currency
                profile.currency_symbol = symbol
                break
        
        # Industry detection
        industry_keywords = {
            'retail': ['sales', 'store', 'inventory', 'customer', 'product'],
            'finance': ['revenue', 'profit', 'margin', 'investment', 'portfolio'],
            'healthcare': ['patient', 'diagnosis', 'treatment', 'medical'],
            'technology': ['software', 'api', 'development', 'tech', 'system'],
            'manufacturing': ['production', 'factory', 'assembly', 'supply chain'],
        }
        
        for industry, keywords in industry_keywords.items():
            matches = sum(1 for kw in keywords if kw in combined.lower())
            if matches >= 2 and not profile.industry:
                profile.industry = industry
                break
    
    def get_context_for_query(self, user_id: str) -> str:
        """
        Get personalized context string for LLM prompts
        
        Args:
            user_id: User identifier
            
        Returns:
            Context string to prepend to prompts
        """
        profile = self.get_profile(user_id)
        
        if not profile.company_name and profile.total_queries == 0:
            return ""  # No personalization yet
        
        context = f"""**User Context:**
{profile.to_context_string()}

**Note:** Use {profile.currency_symbol} for currency values. Format dates as {profile.date_format}."""
        
        return context
    
    def save_conversation_summary(
        self,
        user_id: str,
        conversation_id: str,
        messages: List[Dict],
        summary: str = None
    ):
        """
        Save compressed conversation summary
        
        Args:
            user_id: User identifier
            conversation_id: Conversation ID
            messages: List of message dicts
            summary: Pre-generated summary (optional)
        """
        if not summary:
            summary = self._generate_summary(messages)
        
        # Extract key topics
        key_topics = self._extract_topics(messages)
        
        conv_summary = ConversationSummary(
            conversation_id=conversation_id,
            user_id=user_id,
            summary=summary,
            key_topics=key_topics,
            insights_mentioned=[],
            timestamp=time.time(),
            message_count=len(messages)
        )
        
        # Save to disk
        user_dir = self._get_user_dir(user_id)
        summaries_dir = user_dir / "summaries"
        summaries_dir.mkdir(exist_ok=True)
        
        summary_path = summaries_dir / f"{conversation_id}.json"
        with open(summary_path, 'w') as f:
            json.dump(asdict(conv_summary), f, indent=2)
        
        # Cache
        if user_id not in self._summaries:
            self._summaries[user_id] = []
        self._summaries[user_id].append(conv_summary)
    
    def _generate_summary(self, messages: List[Dict]) -> str:
        """Generate simple summary of conversation"""
        if not messages:
            return "Empty conversation"
        
        # Get user messages
        user_msgs = [m.get('content', '')[:100] for m in messages if m.get('role') == 'user']
        
        if not user_msgs:
            return "No user messages"
        
        return f"User asked about: {'; '.join(user_msgs[:3])}"
    
    def _extract_topics(self, messages: List[Dict]) -> List[str]:
        """Extract key topics from messages"""
        topics = set()
        
        topic_keywords = [
            'revenue', 'sales', 'profit', 'customer', 'product',
            'trend', 'growth', 'decline', 'comparison', 'forecast'
        ]
        
        for msg in messages:
            content = msg.get('content', '').lower()
            for keyword in topic_keywords:
                if keyword in content:
                    topics.add(keyword)
        
        return list(topics)[:5]
    
    def get_recent_context(self, user_id: str, limit: int = 3) -> str:
        """
        Get recent conversation summaries for context
        
        Args:
            user_id: User identifier
            limit: Number of recent summaries
            
        Returns:
            Context string with recent history
        """
        # Load summaries if not cached
        if user_id not in self._summaries:
            self._load_summaries(user_id)
        
        summaries = self._summaries.get(user_id, [])
        
        if not summaries:
            return ""
        
        # Get most recent
        recent = sorted(summaries, key=lambda s: s.timestamp, reverse=True)[:limit]
        
        context_parts = ["**Recent Conversations:**"]
        for s in recent:
            date = datetime.fromtimestamp(s.timestamp).strftime("%Y-%m-%d")
            context_parts.append(f"- {date}: {s.summary}")
        
        return "\n".join(context_parts)
    
    def _load_summaries(self, user_id: str):
        """Load conversation summaries from disk"""
        user_dir = self._get_user_dir(user_id)
        summaries_dir = user_dir / "summaries"
        
        if not summaries_dir.exists():
            self._summaries[user_id] = []
            return
        
        summaries = []
        for summary_file in summaries_dir.glob("*.json"):
            try:
                with open(summary_file, 'r') as f:
                    data = json.load(f)
                summaries.append(ConversationSummary(**data))
            except Exception as e:
                print(f"⚠️ Error loading summary {summary_file}: {e}")
        
        self._summaries[user_id] = summaries


# Global memory instance
_memory_instance: Optional[PersistentMemory] = None


def get_memory() -> PersistentMemory:
    """Get or create global memory instance"""
    global _memory_instance
    
    if _memory_instance is None:
        from config.settings import Settings
        _memory_instance = PersistentMemory(Settings.STORAGE)
    
    return _memory_instance


def get_user_context(user_id: str) -> str:
    """
    Get full personalized context for user
    
    Args:
        user_id: User identifier
        
    Returns:
        Combined context string
    """
    memory = get_memory()
    
    profile_context = memory.get_context_for_query(user_id)
    recent_context = memory.get_recent_context(user_id, limit=2)
    
    if profile_context or recent_context:
        return f"{profile_context}\n\n{recent_context}".strip()
    
    return ""
