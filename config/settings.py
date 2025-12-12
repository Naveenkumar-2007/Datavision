import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Settings:
    # API Keys
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    # LLM Configuration - Groq (for all chat/RAG modes)
    # Gemini is ONLY used for vision - see GEMINI_VISION_MODEL below
    GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    LLM_TEMPERATURE = 0.7
    MAX_TOKENS = 2048
    
    # Vision Configuration - Google Gemini (ONLY for image analysis)
    GEMINI_VISION_MODEL = os.getenv("GEMINI_VISION_MODEL", "gemini-pro-vision")

    # Embeddings via SentenceTransformers only
    SENTENCE_MODEL = os.getenv("SENTENCE_MODEL", "all-MiniLM-L6-v2")
    EMBED_DIM = 384

    # Directories (dynamically overridden per-user at runtime)
    # See backend/utils/paths.py for multi-tenant storage: storage/users/{user_id}/
    BASE_DIR = Path(".").resolve()
    STORAGE = BASE_DIR / "storage"
    UPLOADS = STORAGE / "uploads"  # Overridden per-user
    FAISS_DIR = STORAGE / "faiss"  # Overridden per-user
    GRAPH_DIR = STORAGE / "graph"  # Overridden per-user
    MEMORY_DIR = STORAGE / "memory"  # Overridden per-user

    # Processing Configuration
    CHUNK_SIZE = 700
    CHUNK_OVERLAP = 150
    TOP_K_RETRIEVAL = 6

    # Graph Configuration
    GRAPH_MAX_NODES = 500

    # API Configuration
    API_HOST = "0.0.0.0"
    API_PORT = 8000
    CORS_ORIGINS = ["*"]

    # Reports Configuration
    WEEKLY_REPORT_DAY = "monday"
    ENABLE_AUTO_REPORTS = True

    # Default Company (for testing without auth)
    DEFAULT_COMPANY_ID = "demo-company"

# Create global storage directory (per-user dirs created in get_user_paths())
Settings.STORAGE.mkdir(parents=True, exist_ok=True)
