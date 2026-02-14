"""
Shared path utilities for multi-tenant storage
Consolidates duplicate get_user_paths() from endpoints
"""

from pathlib import Path
import os

# Import Settings to get the canonical storage path
from config.settings import Settings

# Detect if running in Docker (Hugging Face Spaces)
if os.path.exists("/app"):
    STORAGE_BASE = Path("/app/storage/users")
else:
    # Use Settings BASE_DIR directly for correct path resolution
    STORAGE_BASE = Settings.BASE_DIR / "storage" / "users"
    STORAGE_BASE.mkdir(parents=True, exist_ok=True)

print(f"📂 Storage Base Path: {STORAGE_BASE.resolve()}")


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
        "models": user_base / "models",
        "faiss": user_base / "faiss",
        "graph": user_base / "graph",
        "memory": user_base / "memory"
    }
    
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    
    return paths
