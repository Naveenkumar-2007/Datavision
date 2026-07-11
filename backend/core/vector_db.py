import chromadb
from chromadb.config import Settings
import os
import logging

logger = logging.getLogger(__name__)

# Persistent storage path for ChromaDB
VECTOR_DB_PATH = os.path.join(os.getcwd(), "chroma_data")
os.makedirs(VECTOR_DB_PATH, exist_ok=True)

try:
    chroma_client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    logger.info("✅ ChromaDB Persistent Client Initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize ChromaDB: {e}")
    chroma_client = None

def get_or_create_collection(user_id: str):
    """
    Gets or creates a persistent vector collection for a specific user.
    This ensures RAG queries are scoped per user for privacy.
    """
    if not chroma_client:
        return None
        
    collection_name = f"user_{user_id.replace('-', '_')}_docs"
    try:
        return chroma_client.get_or_create_collection(name=collection_name)
    except Exception as e:
        logger.error(f"Error getting collection for user {user_id}: {e}")
        return None
