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
    
    # Model settings - GROQ PRIMARY (Fast + High Quality)
    MODEL_NAME = "groq/llama-3.3-70b-versatile"      # Primary model - Best quality
    FAST_MODEL = "groq/llama-3.1-8b-instant"          # Fast model for simple queries
    REASONING_MODEL = "groq/llama-3.3-70b-versatile"  # For complex queries
    
    # Fallback
    FALLBACK_MODEL = "groq/llama-3.1-8b-instant"
    
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Ollama Local LLM (Fallback when Groq fails)
    OLLAMA_MODEL = "ollama/qwen2.5:3b"  # Smarter model for business analysis




    
    # Chunking settings (for ingestion pipeline)
    CHUNK_SIZE = 700
    CHUNK_OVERLAP = 150
    
    # Embedding settings (for FAISS)
    EMBED_DIM = 384  # all-MiniLM-L6-v2 produces 384-dim vectors
    
    # Graph settings
    GRAPH_MAX_NODES = 100
    
    # =========================================================================
    # AUTHORITATIVE CURRENCY EXCHANGE RATES (Single Source of Truth)
    # Update these rates as needed - they apply globally
    # =========================================================================
    EXCHANGE_RATES = {
        "INR_TO_USD": 88.0,   # ₹88 = $1 (current rate)
        "INR_TO_EUR": 92.0,   # ₹92 = €1
        "INR_TO_GBP": 110.0,  # ₹110 = £1
        "USD_TO_INR": 88.0,
        "EUR_TO_INR": 92.0,
        "GBP_TO_INR": 110.0,
    }
    
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
