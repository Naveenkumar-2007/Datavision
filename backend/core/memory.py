"""
User Memory Module - Persistent Context for Enterprise Chatbot
Stores user name, preferences, and recent conversation context
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from utils.paths import get_user_paths, STORAGE_BASE


def get_user_profile_path(user_id: str) -> Path:
    """Get path to user profile file"""
    paths = get_user_paths(user_id)
    return Path(paths["base"]) / "user_profile.json"


def save_user_profile(user_id: str, profile: Dict):
    """Save user profile to disk"""
    profile_path = get_user_profile_path(user_id)
    profile["updated_at"] = datetime.now().isoformat()
    
    with open(profile_path, 'w') as f:
        json.dump(profile, f, indent=2)


def load_user_profile(user_id: str) -> Dict:
    """Load user profile from disk"""
    profile_path = get_user_profile_path(user_id)
    
    if profile_path.exists():
        with open(profile_path, 'r') as f:
            return json.load(f)
    
    # Return default profile
    return {
        "name": None,
        "preferences": {},
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }


def extract_user_name(message: str) -> Optional[str]:
    """Extract user name from message like 'I am Naveen' or 'My name is Naveen'"""
    import re
    
    patterns = [
        r"(?:i am|i'm|my name is|call me|this is)\s+([A-Z][a-z]+)",  # Case sensitive
        r"(?:i am|i'm|my name is|call me|this is)\s+(\w+)",  # Case insensitive fallback
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            name = match.group(1)
            # Filter out common words
            if name.lower() not in ['the', 'a', 'an', 'your', 'my', 'here', 'asking', 'looking', 'interested']:
                return name.capitalize()
    
    return None


def update_user_name(user_id: str, name: str):
    """Update user's name in profile"""
    profile = load_user_profile(user_id)
    profile["name"] = name
    save_user_profile(user_id, profile)
    print(f"💾 Saved user name: {name}")


def get_user_name(user_id: str) -> Optional[str]:
    """Get user's name from profile"""
    profile = load_user_profile(user_id)
    return profile.get("name")


def get_recent_conversation_context(user_id: str, limit: int = 5) -> str:
    """Get recent conversation messages as context"""
    paths = get_user_paths(user_id)
    memory_dir = Path(paths["memory"])
    
    if not memory_dir.exists():
        return ""
    
    # Find most recent conversation file
    conv_files = list(memory_dir.glob("*.json"))
    if not conv_files:
        return ""
    
    # Sort by modification time
    conv_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    try:
        with open(conv_files[0], 'r') as f:
            data = json.load(f)
            messages = data.get("messages", [])[-limit:]
            
            context = ""
            for msg in messages:
                role = msg.get("role", "").upper()
                content = msg.get("content", "")[:200]  # Limit content length
                context += f"{role}: {content}\n"
            
            return context
    except:
        return ""


def get_user_context(user_id: str) -> str:
    """
    Get full user context for injection into prompts.
    Includes: name, preferences, recent conversation.
    """
    profile = load_user_profile(user_id)
    context_parts = []
    
    # Add name
    if profile.get("name"):
        context_parts.append(f"User's name: {profile['name']}")
    
    # Add preferences
    prefs = profile.get("preferences", {})
    if prefs:
        pref_str = ", ".join([f"{k}: {v}" for k, v in prefs.items()])
        context_parts.append(f"User preferences: {pref_str}")
    
    # Add recent conversation
    recent = get_recent_conversation_context(user_id, limit=3)
    if recent:
        context_parts.append(f"Recent context:\n{recent}")
    
    if context_parts:
        return "\n".join(context_parts)
    
    return ""


def process_personal_info(user_id: str, message: str) -> bool:
    """
    Process incoming message for personal information.
    Returns True if personal info was detected and saved.
    """
    # Try to extract and save name
    name = extract_user_name(message)
    if name:
        update_user_name(user_id, name)
        return True
    
    return False
