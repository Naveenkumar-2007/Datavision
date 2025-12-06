# Ingestion pipeline module
"""
Enhanced ingestion with:
1. Semantic chunking for better RAG
2. Cache invalidation on data change
3. Hybrid search index building
"""
import shutil
from pathlib import Path
from typing import List
from fastapi import UploadFile

from config.settings import Settings
from ingestion.loader import Loader
from ingestion.processor import Processor
from core.llm import embed_texts
from vector.store_faiss import FaissStore
from graph.builder import GraphBuilder


class IngestionPipeline:
    def __init__(self):
        # Use semantic chunking by default for better RAG accuracy
        self.processor = Processor(
            Settings.CHUNK_SIZE,
            Settings.CHUNK_OVERLAP,
            strategy="semantic"  # Changed from fixed to semantic
        )
        # Don't create store in __init__ - create it in ingest() after paths are set
        self.store = None

    def ingest(self, company_id: str, files: List[UploadFile], fresh: bool = False, skip_save: bool = False):
        """
        Ingest uploaded files: load, process, embed, and build graph.
        
        Args:
            company_id: User/company identifier
            files: List of file objects to process
            fresh: If True, create fresh indexes (for retraining after file deletion)
            skip_save: If True, don't save files (they already exist - for retraining)
        """
        # Invalidate cache for this user since data is changing
        self._invalidate_user_cache(company_id)
        
        # For retraining, use parent directory (files are already in their location)
        if skip_save:
            company_dir = Settings.UPLOADS
        else:
            company_dir = Settings.UPLOADS / company_id
            company_dir.mkdir(parents=True, exist_ok=True)

        texts = []
        tables = []
        metadata = []
        processed_files = []
        
        print(f"📥 Ingesting {len(files)} files for {company_id} (fresh={fresh}, skip_save={skip_save})")
        print(f"📂 Working directory: {company_dir}")
        print(f"📝 Using semantic chunking for better RAG accuracy")

        for file in files:
            # For retraining (skip_save=True), file path is the actual path
            # For new uploads, we need to construct the path
            if skip_save:
                # File already exists - get path from file object if available
                if hasattr(file, '_path'):
                    file_path = file._path
                else:
                    file_path = company_dir / file.filename
            else:
                file_path = company_dir / file.filename
            
            # Only save file if not skipping (new upload vs retrain)
            if not skip_save:
                # Reset file pointer to beginning
                file.file.seek(0)
                
                with open(file_path, "wb") as f:
                    shutil.copyfileobj(file.file, f)
                print(f"💾 Saved file: {file.filename}")
            else:
                # For retraining, file already exists - just reset pointer
                file.file.seek(0)
                print(f"📄 Processing existing file: {file.filename} at {file_path}")

            # Verify file exists before loading
            if not file_path.exists():
                print(f"⚠️ File not found: {file_path}, skipping")
                continue

            # Load file content
            try:
                result = Loader.load(file_path)
                processed_files.append(file.filename)
            except Exception as e:
                print(f"⚠️ Error loading {file.filename}: {e}")
                continue

            if result["type"] == "text":
                # Process text content with semantic chunking
                clean_text = self.processor.clean(result["content"])
                chunks = self.processor.chunk(clean_text)
                texts.extend(chunks)
                metadata.extend([
                    {"company": company_id, "source": file.filename, "chunk": i, "text": chunks[i]}
                    for i in range(len(chunks))
                ])
                print(f"📝 Text file: {len(chunks)} semantic chunks")

            elif result["type"] == "table":
                tables.append(result["df"])
                # Also chunk table as text for RAG
                table_text = result["df"].to_string()
                chunks = self.processor.chunk(table_text)
                texts.extend(chunks)
                metadata.extend([
                    {"company": company_id, "source": file.filename, "chunk": i, "type": "table", "text": chunks[i]}
                    for i in range(len(chunks))
                ])
                print(f"📊 Table file: {len(result['df'])} rows, {len(chunks)} chunks")

            elif result["type"] == "json":
                # Convert JSON to text and chunk
                import json
                json_text = json.dumps(result["json"], indent=2)
                chunks = self.processor.chunk(json_text)
                texts.extend(chunks)
                metadata.extend([
                    {"company": company_id, "source": file.filename, "chunk": i, "type": "json", "text": chunks[i]}
                    for i in range(len(chunks))
                ])
                print(f"📋 JSON file: {len(chunks)} chunks")

        # Embed and store text chunks
        if texts:
            # Create FRESH store for retraining, or load existing for new uploads
            if self.store is None:
                self.store = FaissStore.load_or_create(user_id=company_id, fresh=fresh)
            
            print(f"🧠 Embedding {len(texts)} text chunks from {len(processed_files)} files...")
            embeddings = embed_texts(texts)
            self.store.add(embeddings, metadata)
            self.store.save(user_id=company_id)
            print(f"✅ FAISS index saved with {self.store.index.ntotal} vectors")
            
            # Rebuild hybrid search index
            self._rebuild_hybrid_index(company_id)
        else:
            print(f"⚠️ No text chunks to embed")

        # Build knowledge graph from tables (always fresh for consistency)
        if tables:
            print(f"🔗 Building knowledge graph from {len(tables)} tables...")
            GraphBuilder.build(company_id, tables)
            print(f"✅ Knowledge graph built")
        else:
            print(f"ℹ️ No tables found for graph building")

        result = {"chunks": len(texts), "tables": len(tables), "files_processed": len(processed_files)}
        print(f"✅ Ingestion complete: {result}")
        return result
    
    def _invalidate_user_cache(self, company_id: str):
        """Invalidate query cache when data changes"""
        try:
            from agents.workflow import invalidate_user_cache
            invalidate_user_cache(company_id)
            print(f"🗑️ Cache invalidated for {company_id}")
        except ImportError:
            pass
        except Exception as e:
            print(f"⚠️ Cache invalidation error: {e}")
    
    def _rebuild_hybrid_index(self, company_id: str):
        """Rebuild BM25 index for hybrid search"""
        try:
            from vector.hybrid_search import HybridSearcher
            store = FaissStore.load_or_create(user_id=company_id)
            searcher = HybridSearcher(store)
            searcher.rebuild_index()
            print(f"✅ Hybrid search index rebuilt")
        except ImportError:
            print(f"ℹ️ Hybrid search not available")
        except Exception as e:
            print(f"⚠️ Hybrid index rebuild error: {e}")

