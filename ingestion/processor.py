# Document processor module
"""
Text processing with support for both fixed-size and semantic chunking.
Default: Semantic chunking for better RAG accuracy.
"""
import re
from typing import List


class Processor:
    """
    Document processor with configurable chunking strategy.
    
    Strategies:
    - "semantic": Sentence-boundary aware chunking (default, better for RAG)
    - "fixed": Fixed-size character chunking (legacy)
    """
    
    def __init__(self, size: int = 700, overlap: int = 150, strategy: str = "semantic"):
        """
        Args:
            size: Max chunk size in characters
            overlap: Overlap size (characters for fixed, sentences for semantic)
            strategy: "semantic" or "fixed"
        """
        self.size = size
        self.overlap = overlap
        self.strategy = strategy
        
        # Initialize semantic chunker if needed
        self._semantic_chunker = None
        if strategy == "semantic":
            try:
                from ingestion.semantic_chunker import SemanticChunker
                self._semantic_chunker = SemanticChunker(
                    max_chunk_size=size,
                    min_chunk_size=100,
                    overlap_sentences=max(1, overlap // 100),
                    preserve_tables=True
                )
            except ImportError:
                print("⚠️ Semantic chunker not available, using fixed strategy")
                self.strategy = "fixed"

    @staticmethod
    def clean(text: str) -> str:
        """Clean text while preserving paragraph structure"""
        # Normalize whitespace but keep paragraph breaks
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def chunk(self, text: str) -> List[str]:
        """
        Split text into chunks using configured strategy
        
        Args:
            text: Document text to chunk
            
        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []
        
        if self.strategy == "semantic" and self._semantic_chunker:
            return self._semantic_chunk(text)
        else:
            return self._fixed_chunk(text)
    
    def _semantic_chunk(self, text: str) -> List[str]:
        """Semantic chunking using sentence boundaries"""
        return self._semantic_chunker.chunk_texts(text)
    
    def _fixed_chunk(self, text: str) -> List[str]:
        """Legacy fixed-size chunking"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.size
            chunks.append(text[start:end])
            start += self.size - self.overlap
        return chunks
