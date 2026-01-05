"""
Settings configuration for the application
"""
from pathlib import Path
import os
from dotenv import load_dotenv

# Load .env file from the PROJECT ROOT (parent of backend)
# The .env file is in ai_business_analyst/.env, not backend/.env
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # backend/../.. = project root
ENV_PATH = PROJECT_ROOT / ".env"

# Try loading from root first, then fallback to backend folder
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
    print(f"✅ Loaded .env from: {ENV_PATH}")
else:
    # Fallback: try backend folder
    BACKEND_ENV = Path(__file__).resolve().parent.parent / ".env"
    if BACKEND_ENV.exists():
        load_dotenv(BACKEND_ENV)
        print(f"✅ Loaded .env from: {BACKEND_ENV}")
    else:
        load_dotenv()  # Try default locations
        print("⚠️ .env file not found, using system environment")

# Verify API keys are loaded
# Handle case where GROQ_API_KEY on first line might have encoding issues
groq_key = os.environ.get("GROQ_API_KEY")
if not groq_key:
    # Try fallback keys (GROQ_KEY_1, GROQ_KEY_2, GROQ_KEY_3)
    for fallback in ["GROQ_KEY_1", "GROQ_KEY_2", "GROQ_KEY_3"]:
        if os.environ.get(fallback):
            groq_key = os.environ.get(fallback)
            os.environ["GROQ_API_KEY"] = groq_key  # Set the main key
            print(f"✅ Using {fallback} as GROQ_API_KEY")
            break

if groq_key:
    print("✅ GROQ_API_KEY loaded successfully")
else:
    print("⚠️ WARNING: No GROQ API key found!")
    print("   Get your FREE key at: https://console.groq.com/keys")

if os.environ.get("GEMINI_API_KEY"):
    print("✅ GEMINI_API_KEY loaded successfully")
    # Also set GOOGLE_API_KEY for LiteLLM
    os.environ["GOOGLE_API_KEY"] = os.environ.get("GEMINI_API_KEY")

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
    
    # Collect all available GROQ keys for fallback
    GROQ_API_KEYS = []
    
    # 1. Add primary key
    if os.environ.get("GROQ_API_KEY"):
        GROQ_API_KEYS.append(os.environ.get("GROQ_API_KEY"))
        
    # 2. Add numbered fallback keys (GROQ_KEY_1 to GROQ_KEY_10)
    for i in range(1, 11):
        key_name = f"GROQ_KEY_{i}"
        key_val = os.environ.get(key_name)
        if key_val and key_val not in GROQ_API_KEYS:
            GROQ_API_KEYS.append(key_val)
            
    # 3. Add comma-separated keys from GROQ_API_KEYS_LIST env var (if exists)
    if os.environ.get("GROQ_API_KEYS_LIST"):
        extra_keys = os.environ.get("GROQ_API_KEYS_LIST").split(",")
        for k in extra_keys:
            clean_k = k.strip()
            if clean_k and clean_k not in GROQ_API_KEYS:
                GROQ_API_KEYS.append(clean_k)
    
    # Fallback
    FALLBACK_MODEL = "groq/llama-3.1-8b-instant"
    
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"




    
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
