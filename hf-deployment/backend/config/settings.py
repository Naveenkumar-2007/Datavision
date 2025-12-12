"""
Settings configuration for the application
"""
from pathlib import Path

class Settings:
    """Application settings"""
    # Base paths
    STORAGE = Path("backend/storage")
    UPLOADS = STORAGE / "uploads"
    FAISS_DIR = STORAGE / "faiss"
    GRAPH_DIR = STORAGE / "graph"
    
    # API settings
    API_VERSION = "v1"
    
    # Model settings
    MODEL_NAME = "llama-3.1-70b-versatile"
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Ensure directories exist
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories"""
        cls.STORAGE.mkdir(exist_ok=True)
        cls.UPLOADS.mkdir(exist_ok=True, parents=True)
        cls.FAISS_DIR.mkdir(exist_ok=True, parents=True)
        cls.GRAPH_DIR.mkdir(exist_ok=True, parents=True)

# Create directories on import
Settings.ensure_directories()
