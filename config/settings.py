import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Settings:
    # API Keys
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    # LLM Configuration - ONLY GROQ
    LLM_MODEL = "openai/gpt-oss-20b"
    LLM_TEMPERATURE = 0.7
    MAX_TOKENS = 2048
    
    # Vision Configuration - Google Gemini
    GEMINI_VISION_MODEL = os.getenv("GEMINI_VISION_MODEL", "gemini-pro-vision")

    # Embeddings via SentenceTransformers only
    SENTENCE_MODEL = os.getenv("SENTENCE_MODEL", "all-MiniLM-L6-v2")
    EMBED_DIM = 384

    # Directories
    BASE_DIR = Path(".").resolve()
    STORAGE = BASE_DIR / "storage"
    UPLOADS = STORAGE / "uploads"
    FAISS_DIR = STORAGE / "faiss"
    GRAPH_DIR = STORAGE / "graph"
    MEMORY_DIR = STORAGE / "memory"

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

# Create all required directories
for p in [Settings.UPLOADS, Settings.FAISS_DIR, Settings.GRAPH_DIR, Settings.MEMORY_DIR]:
    p.mkdir(parents=True, exist_ok=True)
