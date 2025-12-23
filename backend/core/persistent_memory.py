"""
Enterprise Persistent Memory - $5M AI System
=============================================

Cross-session memory that remembers:
1. User preferences
2. Previous analyses
3. Important findings
4. Conversation context

This makes the AI behave like ChatGPT - remembering context across sessions.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class MemoryEntry:
    """A single memory entry"""
    key: str
    value: Any
    category: str  # "preference", "finding", "context", "analysis"
    timestamp: str
    importance: float  # 0-1, higher = more important to remember


@dataclass
class UserProfile:
    """User's persistent profile"""
    name: Optional[str]
    preferred_currency: str
    preferred_chart_type: str
    industry: Optional[str]
    timezone: Optional[str]
    language: str


class EnterprisePersistentMemory:
    """
    Persistent memory system for ChatGPT-level context retention.
    
    Stores:
    - User preferences (currency, charts, language)
    - Key findings from analyses
    - Important metrics and trends
    - Conversation context
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.memory_file = self._get_memory_file()
        self.memory: Dict[str, Any] = self._load_memory()
    
    def _get_memory_file(self) -> Path:
        """Get path to persistent memory file"""
        try:
            from utils.paths import get_user_paths
            paths = get_user_paths(self.user_id)
            return paths["memory"] / "persistent_memory.json"
        except:
            return Path(f"storage/users/{self.user_id}/memory/persistent_memory.json")
    
    def _load_memory(self) -> Dict[str, Any]:
        """Load memory from disk"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[MEMORY] Load error: {e}")
        
        return {
            "profile": {
                "name": None,
                "preferred_currency": "₹",
                "preferred_chart_type": "bar",
                "industry": None,
                "timezone": "Asia/Kolkata",
                "language": "en",
            },
            "findings": [],
            "context": [],
            "preferences": {},
            "last_topics": [],
            "important_metrics": {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
    
    def _save_memory(self):
        """Save memory to disk"""
        try:
            self.memory_file.parent.mkdir(parents=True, exist_ok=True)
            self.memory["updated_at"] = datetime.now().isoformat()
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[MEMORY] Save error: {e}")
    
    # ========================================================================
    # USER PROFILE
    # ========================================================================
    
    def set_user_name(self, name: str):
        """Remember user's name"""
        self.memory["profile"]["name"] = name
        self._save_memory()
        print(f"[MEMORY] Saved user name: {name}")
    
    def get_user_name(self) -> Optional[str]:
        """Get user's name"""
        return self.memory["profile"].get("name")
    
    def set_currency(self, currency: str):
        """Set preferred currency"""
        self.memory["profile"]["preferred_currency"] = currency
        self._save_memory()
    
    def get_currency(self) -> str:
        """Get preferred currency"""
        return self.memory["profile"].get("preferred_currency", "₹")
    
    def set_industry(self, industry: str):
        """Set user's industry"""
        self.memory["profile"]["industry"] = industry
        self._save_memory()
    
    def get_profile(self) -> Dict:
        """Get complete user profile"""
        return self.memory.get("profile", {})
    
    # ========================================================================
    # FINDINGS & CONTEXT
    # ========================================================================
    
    def add_finding(self, finding: str, category: str = "analysis", importance: float = 0.5):
        """Store an important finding"""
        entry = {
            "finding": finding,
            "category": category,
            "importance": importance,
            "timestamp": datetime.now().isoformat(),
        }
        
        findings = self.memory.get("findings", [])
        findings.append(entry)
        
        # Keep only top 50 findings by importance
        findings = sorted(findings, key=lambda x: x.get("importance", 0), reverse=True)[:50]
        self.memory["findings"] = findings
        self._save_memory()
    
    def get_findings(self, category: str = None, limit: int = 10) -> List[Dict]:
        """Get recent findings"""
        findings = self.memory.get("findings", [])
        
        if category:
            findings = [f for f in findings if f.get("category") == category]
        
        return findings[:limit]
    
    def add_context(self, topic: str, summary: str):
        """Add conversation context"""
        entry = {
            "topic": topic,
            "summary": summary,
            "timestamp": datetime.now().isoformat(),
        }
        
        context = self.memory.get("context", [])
        context.append(entry)
        self.memory["context"] = context[-20:]  # Keep last 20
        self._save_memory()
    
    def get_recent_context(self, limit: int = 5) -> List[Dict]:
        """Get recent conversation context"""
        return self.memory.get("context", [])[-limit:]
    
    # ========================================================================
    # IMPORTANT METRICS
    # ========================================================================
    
    def remember_metric(self, metric_name: str, value: Any, source: str = None):
        """Remember an important metric"""
        self.memory["important_metrics"][metric_name] = {
            "value": value,
            "source": source,
            "timestamp": datetime.now().isoformat(),
        }
        self._save_memory()
    
    def get_metric(self, metric_name: str) -> Optional[Any]:
        """Get a remembered metric"""
        metric = self.memory.get("important_metrics", {}).get(metric_name)
        return metric.get("value") if metric else None
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all remembered metrics"""
        return self.memory.get("important_metrics", {})
    
    # ========================================================================
    # TOPIC TRACKING
    # ========================================================================
    
    def add_topic(self, topic: str):
        """Track discussed topics"""
        topics = self.memory.get("last_topics", [])
        topics.append({
            "topic": topic,
            "timestamp": datetime.now().isoformat(),
        })
        self.memory["last_topics"] = topics[-20:]  # Keep last 20
        self._save_memory()
    
    def get_last_topic(self) -> Optional[str]:
        """Get the last discussed topic"""
        topics = self.memory.get("last_topics", [])
        return topics[-1]["topic"] if topics else None
    
    def get_recent_topics(self, limit: int = 5) -> List[str]:
        """Get recent topics"""
        topics = self.memory.get("last_topics", [])
        return [t["topic"] for t in topics[-limit:]]
    
    # ========================================================================
    # CONVERSATION HISTORY
    # ========================================================================
    
    def add_conversation_turn(self, role: str, content: str):
        """Add a conversation turn"""
        if "conversation" not in self.memory:
            self.memory["conversation"] = []
        
        self.memory["conversation"].append({
            "role": role,
            "content": content[:2000],  # Truncate long content
            "timestamp": datetime.now().isoformat(),
        })
        
        # Keep last 50 turns
        self.memory["conversation"] = self.memory["conversation"][-50:]
        self._save_memory()
    
    def get_last_response(self) -> Optional[str]:
        """Get the last assistant response"""
        conv = self.memory.get("conversation", [])
        for turn in reversed(conv):
            if turn["role"] == "assistant":
                return turn["content"]
        return None
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict]:
        """Get recent conversation history"""
        return self.memory.get("conversation", [])[-limit:]
    
    # ========================================================================
    # PREFERENCES
    # ========================================================================
    
    def set_preference(self, key: str, value: Any):
        """Set a user preference"""
        if "preferences" not in self.memory:
            self.memory["preferences"] = {}
        self.memory["preferences"][key] = value
        self._save_memory()
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference"""
        return self.memory.get("preferences", {}).get(key, default)
    
    # ========================================================================
    # CONTEXT BUILDING
    # ========================================================================
    
    def build_context_for_llm(self) -> str:
        """Build context string for LLM prompt"""
        context_parts = []
        
        # User profile
        profile = self.get_profile()
        if profile.get("name"):
            context_parts.append(f"User's name: {profile['name']}")
        if profile.get("industry"):
            context_parts.append(f"Industry: {profile['industry']}")
        
        # Recent findings
        findings = self.get_findings(limit=3)
        if findings:
            context_parts.append("Recent findings:")
            for f in findings:
                context_parts.append(f"  - {f['finding']}")
        
        # Important metrics
        metrics = self.get_all_metrics()
        if metrics:
            context_parts.append("Important metrics:")
            for name, data in list(metrics.items())[:5]:
                context_parts.append(f"  - {name}: {data['value']}")
        
        # Recent topics
        topics = self.get_recent_topics(3)
        if topics:
            context_parts.append(f"Recent topics: {', '.join(topics)}")
        
        return "\n".join(context_parts) if context_parts else ""


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_persistent_memory(user_id: str) -> EnterprisePersistentMemory:
    """Get persistent memory instance for user"""
    return EnterprisePersistentMemory(user_id)


def remember_finding(user_id: str, finding: str, importance: float = 0.5):
    """Quick function to store a finding"""
    memory = get_persistent_memory(user_id)
    memory.add_finding(finding, importance=importance)


def get_user_context(user_id: str) -> str:
    """Get user context for LLM prompt"""
    memory = get_persistent_memory(user_id)
    return memory.build_context_for_llm()
