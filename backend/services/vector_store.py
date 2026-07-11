import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    from sentence_transformers import SentenceTransformer
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

logger = logging.getLogger(__name__)

class VectorStoreService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(VectorStoreService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return
            
        self.is_ready = QDRANT_AVAILABLE
        if not self.is_ready:
            logger.warning("Qdrant or SentenceTransformers not installed. Vector store disabled.")
            self._initialized = True
            return
            
        # Initialize local Qdrant
        # This creates a 'qdrant_data' directory locally (no Docker required!)
        qdrant_path = os.path.join(os.getcwd(), "qdrant_data")
        os.makedirs(qdrant_path, exist_ok=True)
        self.client = QdrantClient(path=qdrant_path)
        
        # Initialize lightweight local embedding model
        # all-MiniLM-L6-v2 is extremely fast and great for general semantic search
        logger.info("Loading local embedding model (SentenceTransformers)...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.vector_size = self.model.get_sentence_embedding_dimension()
        
        # Setup collections
        self.chat_collection = "chat_memory"
        self.doc_collection = "document_chunks"
        self._ensure_collections()
        self._initialized = True
        
    def _ensure_collections(self):
        """Ensure required collections exist in Qdrant"""
        collections = [c.name for c in self.client.get_collections().collections]
        
        for collection_name in [self.chat_collection, self.doc_collection]:
            if collection_name not in collections:
                logger.info(f"Creating Qdrant collection: {collection_name}")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
                )

    def add_chat_message(self, user_id: str, role: str, content: str, conversation_id: str) -> bool:
        if not self.is_ready: return False
        try:
            # Embed the message content
            vector = self.model.encode(content).tolist()
            
            # Store in Qdrant
            point_id = str(uuid.uuid4())
            self.client.upsert(
                collection_name=self.chat_collection,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={
                            "user_id": user_id,
                            "conversation_id": conversation_id,
                            "role": role,
                            "content": content,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                ]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add chat to vector store: {e}")
            return False

    def search_chat_history(self, user_id: str, query: str, limit: int = 5) -> List[Dict]:
        """Semantically search the user's past chat history (RAG over memory)"""
        if not self.is_ready: return []
        try:
            query_vector = self.model.encode(query).tolist()
            
            # Filter by user_id
            user_filter = Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id)
                    )
                ]
            )
            
            search_result = self.client.search(
                collection_name=self.chat_collection,
                query_vector=query_vector,
                query_filter=user_filter,
                limit=limit
            )
            
            return [hit.payload for hit in search_result]
        except Exception as e:
            logger.error(f"Failed to search chat history: {e}")
            return []

# Singleton instance
vector_store = VectorStoreService()
