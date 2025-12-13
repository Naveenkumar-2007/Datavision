"""
Settings configuration for the application
"""
from pathlib import Path

class Settings:
    """Application settings"""
    # Robust path determination
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    # Base paths
    STORAGE = BASE_DIR / "storage"
    UPLOADS = STORAGE / "uploads"
    FAISS_DIR = STORAGE / "faiss"
    GRAPH_DIR = STORAGE / "graph"
    
    # API settings
    API_VERSION = "v1"
    
    # Model settings
    MODEL_NAME = "openai/gpt-oss-120b"
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Chunking settings (for ingestion pipeline)
    CHUNK_SIZE = 700
    CHUNK_OVERLAP = 150
    
    # Embedding settings (for FAISS)
    EMBED_DIM = 384  # all-MiniLM-L6-v2 produces 384-dim vectors
    
    # Graph settings
    GRAPH_MAX_NODES = 100
    
    # Ensure directories exist
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories"""
        cls.STORAGE.mkdir(exist_ok=True, parents=True)
        cls.UPLOADS.mkdir(exist_ok=True, parents=True)
        cls.FAISS_DIR.mkdir(exist_ok=True, parents=True)
        cls.GRAPH_DIR.mkdir(exist_ok=True, parents=True)

# Create directories on import
Settings.ensure_directories()
