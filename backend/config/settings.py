"""
Settings configuration for the application
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure Basic Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("settings")

# Load .env file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
BACKEND_ENV = Path(__file__).resolve().parent.parent / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
    logger.info(f"Loaded .env from: {ENV_PATH}")
elif BACKEND_ENV.exists():
    load_dotenv(BACKEND_ENV)
    logger.info(f"Loaded .env from: {BACKEND_ENV}")
else:
    load_dotenv()
    logger.warning("No specific .env file found, using system environment")

class Settings:
    """Application settings"""
    # Base paths
    BASE_DIR = Path(__file__).resolve().parent.parent
    STORAGE = BASE_DIR / "storage"
    UPLOADS = STORAGE / "uploads"
    FAISS_DIR = STORAGE / "faiss"
    GRAPH_DIR = STORAGE / "graph"
    
    # API settings
    API_VERSION = "v1"
    
    # Model settings - GROQ PRIMARY
    MODEL_NAME = "groq/llama-3.3-70b-versatile"
    FAST_MODEL = "groq/llama-3.1-8b-instant"
    REASONING_MODEL = "groq/llama-3.3-70b-versatile"
    FALLBACK_MODEL = "groq/llama-3.1-8b-instant"
    
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

    # API Keys Management
    GROQ_API_KEYS = []
    
    # Processing settings
    CHUNK_SIZE = 700
    CHUNK_OVERLAP = 150
    EMBED_DIM = 384
    GRAPH_MAX_NODES = 100
    
    # Exchange Rates (MVP Static Source)
    EXCHANGE_RATES = {
        "INR_TO_USD": 88.0,
        "INR_TO_EUR": 92.0,
        "INR_TO_GBP": 110.0,
        "USD_TO_INR": 88.0,
        "EUR_TO_INR": 92.0,
        "GBP_TO_INR": 110.0,
    }
    
    @classmethod
    def load_api_keys(cls):
        """Robustly load API keys"""
        # Primary Key
        main_key = os.environ.get("GROQ_API_KEY")
        if main_key:
            cls.GROQ_API_KEYS.append(main_key)
            
        # Fallback Keys (GROQ_KEY_1 to GROQ_KEY_10)
        for i in range(1, 11):
            key = os.environ.get(f"GROQ_KEY_{i}")
            if key and key not in cls.GROQ_API_KEYS:
                cls.GROQ_API_KEYS.append(key)
                
        # List Keys
        if os.environ.get("GROQ_API_KEYS_LIST"):
            for k in os.environ.get("GROQ_API_KEYS_LIST").split(","):
                clean_k = k.strip()
                if clean_k and clean_k not in cls.GROQ_API_KEYS:
                    cls.GROQ_API_KEYS.append(clean_k)
                    
        if not cls.GROQ_API_KEYS:
            logger.warning("No GROQ API keys found! Set GROQ_API_KEY in .env")
        else:
            # Set the primary key for libraries that expect it env-wide
            os.environ["GROQ_API_KEY"] = cls.GROQ_API_KEYS[0]
            logger.info(f"Loaded {len(cls.GROQ_API_KEYS)} Groq API keys")

        # Gemini / Google
        if os.environ.get("GEMINI_API_KEY"):
            os.environ["GOOGLE_API_KEY"] = os.environ.get("GEMINI_API_KEY")

    @classmethod
    def ensure_directories(cls):
        """Create necessary directories"""
        for path in [cls.STORAGE, cls.UPLOADS, cls.FAISS_DIR, cls.GRAPH_DIR]:
            path.mkdir(exist_ok=True, parents=True)

# Initialize
Settings.load_api_keys()
Settings.ensure_directories()
