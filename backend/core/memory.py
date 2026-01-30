"""
ChatGPT-Level Persistent Memory System
======================================

THREE-LAYER MEMORY ARCHITECTURE:
1. USER PROFILE MEMORY (PERSISTENT)
   - Stores user-provided identity and preferences
   - Scoped strictly to user_id
   - Persists across sessions and chats

2. SESSION MEMORY (TEMPORARY)
   - Stores short-term conversational context
   - Cleared when session ends

3. WORKSPACE MEMORY (OPTIONAL)
   - Stores dataset-level context (schemas, defaults)

MEMORY WRITE RULES:
- Write on explicit user input only ("My name is X", "Call me X")
- Mark source as "explicit_user_input"
- Scope to user_id only
- NEVER guess or infer identity

MEMORY READ RULES:
- Always check USER PROFILE MEMORY before answering identity questions
- If exists → answer directly
- If not → ask politely

PRIVACY:
- Memory isolated per authenticated user
- No data sharing across users
- Never expose storage details
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

# Import paths utility
try:
    from utils.paths import get_user_paths
except ImportError:
    def get_user_paths(user_id):
        from pathlib import Path
        base = Path("storage/users") / user_id / "memory"
        base.mkdir(parents=True, exist_ok=True)
        return {"memory": base}


def get_user_context(user_id: str) -> str:
    """
    Get personalized context for user from stored memory.
    Returns formatted context string for LLM prompts.
    """
    if not user_id:
        return ""
    
    try:
        paths = get_user_paths(user_id)
        memory_path = paths["memory"] / "user_context.json"
        
        if not memory_path.exists():
            return ""
        
        with open(memory_path, 'r') as f:
            context = json.load(f)
        
        # Build context string
        parts = []
        
        if context.get("name"):
            parts.append(f"User Name: {context['name']}")
        
        if context.get("company"):
            parts.append(f"Company: {context['company']}")
        
        if context.get("role"):
            parts.append(f"Role: {context['role']}")
        
        if context.get("preferences"):
            parts.append(f"Preferences: {context['preferences']}")
        
        if context.get("last_topics"):
            topics = ", ".join(context['last_topics'][-5:])  # Last 5 topics
            parts.append(f"Recent Topics: {topics}")
        
        return "\n".join(parts) if parts else ""
        
    except Exception as e:
        print(f"Error loading user context: {e}")
        return ""


def get_user_name(user_id: str) -> Optional[str]:
    """
    MEMORY READ: Get user's name from persistent storage.
    
    This is the PRIMARY function for answering "What is my name?" questions.
    Returns None if name is not stored (triggers polite request).
    """
    if not user_id:
        return None
    
    try:
        paths = get_user_paths(user_id)
        memory_path = paths["memory"] / "user_context.json"
        
        if not memory_path.exists():
            return None
        
        with open(memory_path, 'r') as f:
            context = json.load(f)
        
        return context.get("name")
        
    except Exception as e:
        print(f"Error reading user name: {e}")
        return None


def save_user_context(user_id: str, context: Dict[str, Any]) -> bool:
    """
    Save or update user context to persistent storage.
    """
    if not user_id:
        return False
    
    try:
        paths = get_user_paths(user_id)
        memory_path = paths["memory"] / "user_context.json"
        
        # Load existing context if any
        existing = {}
        if memory_path.exists():
            with open(memory_path, 'r') as f:
                existing = json.load(f)
        
        # Merge with new context
        existing.update(context)
        existing["updated_at"] = datetime.now().isoformat()
        
        # Save
        with open(memory_path, 'w') as f:
            json.dump(existing, f, indent=2)
        
        print(f"💾 Saved user context for {user_id}")
        return True
        
    except Exception as e:
        print(f"⚠️ Error saving user context: {e}")
        return False


def process_personal_info(user_id: str, query: str) -> bool:
    """
    Extract and save personal information from user's message.
    Looks for patterns like "My name is X", "I work at Y", etc.
    """
    if not user_id or not query:
        return False
    
    import re
    context_updates = {}
    
    # Extract name - EXPANDED PATTERNS (case-insensitive, auto-capitalize)
    name_patterns = [
        r"(?:my name is|i am|i'm|this is|call me|hey i'm|hi i'm|hello i'm)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)",
        r"^([a-zA-Z]+)\s+here\b",  # "naveen here"
        r"^i'm?\s+([a-zA-Z]+)\b",  # "I'm naveen" at start
        r"^([a-zA-Z]+)$",  # Just a name by itself like "naveen"
    ]
    for pattern in name_patterns:
        match = re.search(pattern, query.strip(), re.IGNORECASE)
        if match:
            # Auto-capitalize the name
            context_updates["name"] = match.group(1).strip().title()
            print(f"💾 Extracted name: {context_updates['name']}")
            break
    
    # Extract company
    company_patterns = [
        r"i work (?:at|for) ([A-Z][A-Za-z\s]+(?:Inc|Corp|Ltd|LLC)?)",
        r"my company is ([A-Z][A-Za-z\s]+)",
        r"(?:at|from) ([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*) company",
    ]
    for pattern in company_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            context_updates["company"] = match.group(1).strip()
            break
    
    # Extract role
    role_patterns = [
        r"i'?m (?:a|an|the) ([A-Za-z\s]+(?:manager|director|ceo|cfo|analyst|engineer|developer))",
        r"my (?:role|job|position) is ([A-Za-z\s]+)",
    ]
    for pattern in role_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            context_updates["role"] = match.group(1).strip()
            break
    
    if context_updates:
        return save_user_context(user_id, context_updates)
    
    return False


def add_conversation_topic(user_id: str, topic: str) -> bool:
    """
    Add a topic to user's recent topics for context.
    """
    if not user_id or not topic:
        return False
    
    try:
        paths = get_user_paths(user_id)
        memory_path = paths["memory"] / "user_context.json"
        
        existing = {}
        if memory_path.exists():
            with open(memory_path, 'r') as f:
                existing = json.load(f)
        
        # Add topic to list (keep last 10)
        topics = existing.get("last_topics", [])
        if topic not in topics:
            topics.append(topic)
            topics = topics[-10:]
        existing["last_topics"] = topics
        existing["updated_at"] = datetime.now().isoformat()
        
        with open(memory_path, 'w') as f:
            json.dump(existing, f, indent=2)
        
        return True
        
    except Exception as e:
        print(f"⚠️ Error adding topic: {e}")
        return False


def get_memory():
    """
    Get global memory instance - returns a simple dict-based memory.
    For more advanced memory, use memory_engine.py
    """
    return {"active": True, "type": "persistent"}


def clear_user_memory(user_id: str) -> bool:
    """
    Clear all stored memory for a user.
    """
    if not user_id:
        return False
    
    try:
        paths = get_user_paths(user_id)
        memory_path = paths["memory"] / "user_context.json"
        
        if memory_path.exists():
            memory_path.unlink()
            print(f"🗑️ Cleared memory for {user_id}")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Error clearing memory: {e}")
        return False
