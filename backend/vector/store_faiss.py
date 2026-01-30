# FAISS vector store module
import faiss
import pickle
import numpy as np
from config.settings import Settings
from core.llm import embed_text

class FaissStore:
    def __init__(self):
        self.index = faiss.IndexFlatL2(Settings.EMBED_DIM)
        self.meta = []

    def add(self, emb, meta):
        self.index.add(np.array(emb, dtype="float32"))
        self.meta.extend(meta)

    def clear(self):
        """Clear all vectors and metadata - for retraining"""
        self.index = faiss.IndexFlatL2(Settings.EMBED_DIM)
        self.meta = []
        print("🗑️ FAISS store cleared for fresh retraining")

    def save(self, user_id: str = "user_001"):
        """Save FAISS index to per-user directory"""
        from pathlib import Path
        
        # Use per-user directory
        if user_id:
            user_faiss_dir = Settings.STORAGE / "users" / user_id / "faiss"
            user_faiss_dir.mkdir(parents=True, exist_ok=True)
        else:
            user_faiss_dir = Settings.FAISS_DIR
            user_faiss_dir.mkdir(parents=True, exist_ok=True)
        
        idx_path = user_faiss_dir / "index.faiss"
        meta_path = user_faiss_dir / "meta.pkl"
        
        print(f"💾 Saving FAISS to: {idx_path}")
        faiss.write_index(self.index, str(idx_path))
        with open(meta_path, "wb") as f:
            pickle.dump(self.meta, f)
        print(f"✅ FAISS saved: {self.index.ntotal} vectors, {len(self.meta)} metadata entries")

    @staticmethod
    def load_or_create(user_id: str = "user_001", fresh: bool = False):
        """
        Load or create FAISS store for specific user.
        
        Args:
            user_id: User identifier
            fresh: If True, create fresh store ignoring existing data (for retraining)
        """
        from pathlib import Path
        
        store = FaissStore()
        
        # If fresh=True, return empty store for clean retraining
        if fresh:
            print(f"🆕 Creating fresh FAISS store for user {user_id}")
            return store
        
        # Use per-user directory
        if user_id:
            user_faiss_dir = Settings.STORAGE / "users" / user_id / "faiss"
            idx = user_faiss_dir / "index.faiss"
            meta = user_faiss_dir / "meta.pkl"
        else:
            idx = Settings.FAISS_DIR / "index.faiss"
            meta = Settings.FAISS_DIR / "meta.pkl"

        print(f"📂 Loading FAISS from: {idx}")
        if idx.exists():
            store.index = faiss.read_index(str(idx))
            print(f"✅ FAISS loaded: {store.index.ntotal} vectors")
        else:
            print(f"⚠️ FAISS index not found at {idx}, creating new")
            
        if meta.exists():
            store.meta = pickle.load(open(meta, "rb"))
            print(f"✅ Metadata loaded: {len(store.meta)} entries")
        else:
            print(f"⚠️ Metadata not found at {meta}")

        return store

    @staticmethod
    def delete_index(user_id: str = "user_001"):
        """Delete FAISS index files for user - for clean retraining"""
        from pathlib import Path
        import shutil
        
        if user_id:
            user_faiss_dir = Settings.STORAGE / "users" / user_id / "faiss"
        else:
            user_faiss_dir = Settings.FAISS_DIR
        
        if user_faiss_dir.exists():
            shutil.rmtree(user_faiss_dir)
            user_faiss_dir.mkdir(parents=True, exist_ok=True)
            print(f"🗑️ Deleted FAISS index for user {user_id}")

    def search(self, query, k=5):
        """Search with automatic query embedding"""
        if self.index.ntotal == 0:
            print("⚠️ FAISS index is empty - no vectors to search")
            return []
        
        # Embed query text if it's a string
        if isinstance(query, str):
            query_vector = embed_text(query)
            if query_vector is None:
                print("⚠️ Failed to embed query")
                return []
        else:
            query_vector = query
        
        query_vector = np.array([query_vector], dtype="float32")
        
        # Limit k to available vectors
        actual_k = min(k, self.index.ntotal)
        _, ids = self.index.search(query_vector, actual_k)
        
        results = []
        for i in ids[0]:
            if 0 <= i < len(self.meta):
                meta = self.meta[i]
                results.append({
                    "text": meta.get("text", ""),
                    "metadata": meta
                })
        
        return results
