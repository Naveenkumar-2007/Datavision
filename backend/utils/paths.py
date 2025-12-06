"""
Shared path utilities for multi-tenant storage
Consolidates duplicate get_user_paths() from endpoints
"""

from pathlib import Path

STORAGE_BASE = Path("storage/users")


def get_user_paths(user_id: str) -> dict:
    """
    Get all storage paths for a specific user.
    Creates directories if they don't exist.
    
    Args:
        user_id: Unique user identifier
        
    Returns:
        Dictionary of path objects for user's storage locations
    """
    user_base = STORAGE_BASE / user_id
    paths = {
        "base": user_base,
        "files": user_base / "files",
        "faiss": user_base / "faiss",
        "graph": user_base / "graph",
        "memory": user_base / "memory"
    }
    
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    
    return paths
