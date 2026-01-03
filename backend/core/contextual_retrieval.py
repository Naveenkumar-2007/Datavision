"""
Contextual Retrieval - Anthropic's Technique
=============================================

The key insight: Chunks lose context when split from their parent document.
Solution: Prepend each chunk with document-level context BEFORE embedding.

This dramatically reduces retrieval failures (67% improvement per Anthropic).

Example:
  Original chunk: "Revenue was $2.5M this quarter."
  With context: "[CONTEXT: This is from Q4 2024 Financial Report for Acme Inc.] 
                 Revenue was $2.5M this quarter."

Uses FREE APIs only (Groq/Gemini).
"""

import os
import json
import hashlib
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

from core.llm import chat

logger = logging.getLogger(__name__)


@dataclass
class ContextualChunk:
    """A chunk with prepended context"""
    original_text: str
    context: str
    contextualized_text: str
    document_id: str
    chunk_index: int
    metadata: Dict[str, Any]
    

class ContextualRetrieval:
    """
    Implements Anthropic's Contextual Retrieval technique.
    
    Prepends document-level context to each chunk before embedding,
    making retrieval more accurate without losing context.
    
    Uses FREE APIs (Groq/Gemini).
    """
    
    def __init__(self, cache_contexts: bool = True):
        self.context_cache: Dict[str, str] = {}
        self.cache_contexts = cache_contexts
        
    def _get_cache_key(self, document_id: str) -> str:
        """Generate cache key for document context"""
        return hashlib.md5(document_id.encode()).hexdigest()
    
    async def generate_document_context(
        self, 
        document_text: str, 
        document_name: str = ""
    ) -> str:
        """
        Generate a concise context summary for a document.
        This context will be prepended to every chunk from this document.
        """
        
        # Limit document text for prompt
        doc_preview = document_text[:3000]
        
        prompt = f"""You are a document analyzer. Generate a brief context summary for this document.

DOCUMENT NAME: {document_name}

DOCUMENT PREVIEW:
{doc_preview}

Generate a single paragraph (2-3 sentences) that describes:
1. What type of document this is
2. The main subject/entity it's about
3. The time period or key identifiers

Keep it concise and factual. This context will help with information retrieval.

CONTEXT SUMMARY:"""

        try:
            context = chat(prompt, temperature=0.1, max_tokens=200)
            context = context.strip()
            
            # Cache if enabled
            if self.cache_contexts and document_name:
                cache_key = self._get_cache_key(document_name)
                self.context_cache[cache_key] = context
            
            return context
            
        except Exception as e:
            logger.warning(f"Error generating context: {e}")
            return f"Document: {document_name}" if document_name else "Document from user data"
    
    def contextualize_chunk(
        self,
        chunk_text: str,
        document_context: str,
        document_id: str = "",
        chunk_index: int = 0,
        metadata: Dict[str, Any] = None
    ) -> ContextualChunk:
        """
        Prepend context to a chunk.
        
        This is the core of Contextual Retrieval.
        """
        
        contextualized = f"[CONTEXT: {document_context}]\n\n{chunk_text}"
        
        return ContextualChunk(
            original_text=chunk_text,
            context=document_context,
            contextualized_text=contextualized,
            document_id=document_id,
            chunk_index=chunk_index,
            metadata=metadata or {}
        )
    
    async def process_document(
        self,
        chunks: List[str],
        document_text: str,
        document_name: str = "",
        document_id: str = ""
    ) -> List[ContextualChunk]:
        """
        Process all chunks from a document with contextual enrichment.
        
        Args:
            chunks: List of text chunks from the document
            document_text: Full document text (for context generation)
            document_name: Name/title of the document
            document_id: Unique identifier
            
        Returns:
            List of ContextualChunk objects
        """
        
        # Generate document-level context
        context = await self.generate_document_context(document_text, document_name)
        logger.info(f"Generated context for {document_name}: {context[:100]}...")
        
        # Contextualize each chunk
        contextual_chunks = []
        for i, chunk in enumerate(chunks):
            ctx_chunk = self.contextualize_chunk(
                chunk_text=chunk,
                document_context=context,
                document_id=document_id or document_name,
                chunk_index=i,
                metadata={
                    "document_name": document_name,
                    "chunk_position": f"{i+1}/{len(chunks)}"
                }
            )
            contextual_chunks.append(ctx_chunk)
        
        return contextual_chunks
    
    def get_embedding_texts(self, chunks: List[ContextualChunk]) -> List[str]:
        """
        Get the contextualized texts for embedding.
        These should be embedded instead of the original chunks.
        """
        return [chunk.contextualized_text for chunk in chunks]
    
    def restore_original(self, contextualized_text: str) -> str:
        """
        Extract original text from contextualized chunk.
        Useful for displaying results without the context prefix.
        """
        if "[CONTEXT:" in contextualized_text and "]\n\n" in contextualized_text:
            return contextualized_text.split("]\n\n", 1)[1]
        return contextualized_text


class ContextualChunker:
    """
    Combines chunking with contextual enrichment.
    A complete pipeline for preparing documents for retrieval.
    """
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        add_context: bool = True
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.add_context = add_context
        self.contextual_retrieval = ContextualRetrieval()
    
    def _split_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap"""
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            if len(current_chunk) + len(para) < self.chunk_size:
                current_chunk += "\n\n" + para if current_chunk else para
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Handle overlap
        if self.chunk_overlap > 0 and len(chunks) > 1:
            overlapped_chunks = []
            for i, chunk in enumerate(chunks):
                if i > 0:
                    # Add last N chars from prev chunk
                    prev_overlap = chunks[i-1][-self.chunk_overlap:]
                    chunk = prev_overlap + "\n" + chunk
                overlapped_chunks.append(chunk)
            chunks = overlapped_chunks
        
        return chunks
    
    async def process(
        self,
        document_text: str,
        document_name: str = "",
        document_id: str = ""
    ) -> List[ContextualChunk]:
        """
        Full pipeline: Split document → Add context to each chunk.
        """
        
        # Split into chunks
        chunks = self._split_text(document_text)
        
        if not self.add_context:
            # Return simple chunks without context
            return [
                ContextualChunk(
                    original_text=chunk,
                    context="",
                    contextualized_text=chunk,
                    document_id=document_id,
                    chunk_index=i,
                    metadata={"document_name": document_name}
                )
                for i, chunk in enumerate(chunks)
            ]
        
        # Add context to each chunk
        return await self.contextual_retrieval.process_document(
            chunks=chunks,
            document_text=document_text,
            document_name=document_name,
            document_id=document_id
        )


# Convenience function for pipeline integration
async def contextualize_chunks(
    chunks: List[str],
    document_text: str,
    document_name: str = ""
) -> List[Dict[str, Any]]:
    """
    Simple interface to add context to chunks.
    
    Returns list of dicts with contextualized text for embedding.
    """
    
    cr = ContextualRetrieval()
    contextual_chunks = await cr.process_document(
        chunks=chunks,
        document_text=document_text,
        document_name=document_name
    )
    
    return [
        {
            "text": chunk.contextualized_text,
            "original": chunk.original_text,
            "context": chunk.context,
            "document": chunk.document_id,
            "index": chunk.chunk_index
        }
        for chunk in contextual_chunks
    ]


# Test
if __name__ == "__main__":
    import asyncio
    
    async def test():
        document = """
        Q4 2024 Financial Report - Acme Corporation
        
        Executive Summary:
        Total revenue for the quarter was $2.5 million, representing a 15% increase 
        from Q3 2024. Operating expenses remained stable at $1.8 million.
        
        Revenue Breakdown:
        - Product Sales: $1.8M (72%)
        - Services: $500K (20%)
        - Subscriptions: $200K (8%)
        
        Key Highlights:
        - Customer count grew to 1,250 (up 10% from Q3)
        - Churn rate decreased to 3.2%
        - Net Promoter Score improved to 72
        """
        
        chunker = ContextualChunker(chunk_size=300)
        chunks = await chunker.process(document, "Q4_2024_Financial_Report")
        
        print(f"Created {len(chunks)} contextual chunks\n")
        for chunk in chunks:
            print(f"--- Chunk {chunk.chunk_index} ---")
            print(f"Context: {chunk.context[:80]}...")
            print(f"Text: {chunk.original_text[:100]}...")
            print()
    
    asyncio.run(test())
