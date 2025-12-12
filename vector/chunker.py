# Enterprise Adaptive Document Chunker
"""
Intelligent document chunking for optimal RAG performance.

Features:
- Adaptive chunk sizes based on document type
- Semantic boundary detection
- Token-aware chunking
- Overlap management
- Metadata preservation
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
import re


class DocumentType(Enum):
    """Supported document types"""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    WORD = "word"
    POWERPOINT = "powerpoint"
    TEXT = "text"
    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"
    IMAGE = "image"


@dataclass
class ChunkConfig:
    """Configuration for chunking"""
    base_chunk_size: int = 500
    max_chunk_size: int = 1000
    min_chunk_size: int = 100
    overlap_size: int = 50
    respect_boundaries: bool = True
    preserve_tables: bool = True
    preserve_lists: bool = True


@dataclass
class DocumentChunk:
    """A chunk of document with metadata"""
    text: str
    chunk_id: int
    source: str
    document_type: DocumentType
    start_position: int
    end_position: int
    metadata: Dict
    token_count: int
    semantic_context: str  # Brief context description


class AdaptiveChunker:
    """
    Enterprise-grade adaptive document chunker.
    
    Adapts chunking strategy based on:
    - Document type (PDF, Excel, etc.)
    - Content structure (tables, lists, paragraphs)
    - Semantic boundaries (sentences, sections)
    - Token budget for LLM context
    """
    
    # Optimal chunk sizes by document type
    TYPE_CONFIGS = {
        DocumentType.PDF: ChunkConfig(
            base_chunk_size=600,
            max_chunk_size=1200,
            overlap_size=100,
            respect_boundaries=True
        ),
        DocumentType.EXCEL: ChunkConfig(
            base_chunk_size=400,
            max_chunk_size=800,
            overlap_size=50,
            preserve_tables=True
        ),
        DocumentType.CSV: ChunkConfig(
            base_chunk_size=300,
            max_chunk_size=600,
            overlap_size=30,
            preserve_tables=True
        ),
        DocumentType.WORD: ChunkConfig(
            base_chunk_size=500,
            max_chunk_size=1000,
            overlap_size=80,
            respect_boundaries=True
        ),
        DocumentType.POWERPOINT: ChunkConfig(
            base_chunk_size=300,
            max_chunk_size=500,
            overlap_size=30,
            respect_boundaries=True
        ),
        DocumentType.TEXT: ChunkConfig(
            base_chunk_size=500,
            max_chunk_size=1000,
            overlap_size=50
        ),
        DocumentType.MARKDOWN: ChunkConfig(
            base_chunk_size=500,
            max_chunk_size=1000,
            overlap_size=80,
            respect_boundaries=True,
            preserve_lists=True
        ),
        DocumentType.JSON: ChunkConfig(
            base_chunk_size=400,
            max_chunk_size=800,
            overlap_size=0,
            respect_boundaries=True
        ),
        DocumentType.HTML: ChunkConfig(
            base_chunk_size=500,
            max_chunk_size=1000,
            overlap_size=50,
            respect_boundaries=True
        )
    }
    
    # Semantic boundary patterns
    SECTION_PATTERNS = [
        r'^#{1,6}\s+.+$',           # Markdown headers
        r'^[A-Z][^.!?]*[.!?]$',     # Title-like sentences
        r'^\d+\.\s+.+$',            # Numbered sections
        r'^[A-Z]{2,}:',             # ALL CAPS labels
        r'^---+$',                   # Horizontal rules
        r'^={3,}$',                  # Equals separators
    ]
    
    PARAGRAPH_END = r'(?<=[.!?])\s+(?=[A-Z])'
    SENTENCE_END = r'(?<=[.!?])\s+'
    
    def __init__(self, config: Optional[ChunkConfig] = None):
        self.default_config = config or ChunkConfig()
    
    def detect_document_type(self, filename: str) -> DocumentType:
        """Detect document type from filename"""
        ext = filename.lower().split('.')[-1] if '.' in filename else 'txt'
        
        type_map = {
            'pdf': DocumentType.PDF,
            'xlsx': DocumentType.EXCEL,
            'xls': DocumentType.EXCEL,
            'csv': DocumentType.CSV,
            'tsv': DocumentType.CSV,
            'doc': DocumentType.WORD,
            'docx': DocumentType.WORD,
            'ppt': DocumentType.POWERPOINT,
            'pptx': DocumentType.POWERPOINT,
            'txt': DocumentType.TEXT,
            'md': DocumentType.MARKDOWN,
            'markdown': DocumentType.MARKDOWN,
            'json': DocumentType.JSON,
            'html': DocumentType.HTML,
            'htm': DocumentType.HTML,
            'png': DocumentType.IMAGE,
            'jpg': DocumentType.IMAGE,
            'jpeg': DocumentType.IMAGE,
        }
        
        return type_map.get(ext, DocumentType.TEXT)
    
    def get_config(self, doc_type: DocumentType) -> ChunkConfig:
        """Get configuration for document type"""
        return self.TYPE_CONFIGS.get(doc_type, self.default_config)
    
    def chunk_document(
        self,
        text: str,
        source: str,
        doc_type: Optional[DocumentType] = None,
        custom_config: Optional[ChunkConfig] = None
    ) -> List[DocumentChunk]:
        """
        Chunk a document adaptively.
        
        Args:
            text: Document text content
            source: Source filename/identifier
            doc_type: Document type (auto-detected if None)
            custom_config: Override default config
            
        Returns:
            List of DocumentChunk objects
        """
        if not text or not text.strip():
            return []
        
        # Detect type and get config
        if doc_type is None:
            doc_type = self.detect_document_type(source)
        
        config = custom_config or self.get_config(doc_type)
        
        # Handle special document types
        if doc_type == DocumentType.EXCEL or doc_type == DocumentType.CSV:
            return self._chunk_tabular(text, source, doc_type, config)
        elif doc_type == DocumentType.JSON:
            return self._chunk_json(text, source, config)
        else:
            return self._chunk_text(text, source, doc_type, config)
    
    def _chunk_text(
        self,
        text: str,
        source: str,
        doc_type: DocumentType,
        config: ChunkConfig
    ) -> List[DocumentChunk]:
        """Chunk general text documents"""
        chunks = []
        
        # Find semantic boundaries
        boundaries = self._find_boundaries(text, config)
        
        if boundaries and config.respect_boundaries:
            # Chunk along boundaries
            chunks = self._chunk_by_boundaries(text, boundaries, source, doc_type, config)
        else:
            # Fall back to sliding window
            chunks = self._sliding_window_chunk(text, source, doc_type, config)
        
        return chunks
    
    def _find_boundaries(self, text: str, config: ChunkConfig) -> List[int]:
        """Find semantic boundaries in text"""
        boundaries = [0]
        
        # Find section headers
        for pattern in self.SECTION_PATTERNS:
            for match in re.finditer(pattern, text, re.MULTILINE):
                boundaries.append(match.start())
        
        # Find paragraph boundaries
        for match in re.finditer(self.PARAGRAPH_END, text):
            boundaries.append(match.end())
        
        # Sort and deduplicate
        boundaries = sorted(set(boundaries))
        boundaries.append(len(text))
        
        return boundaries
    
    def _chunk_by_boundaries(
        self,
        text: str,
        boundaries: List[int],
        source: str,
        doc_type: DocumentType,
        config: ChunkConfig
    ) -> List[DocumentChunk]:
        """Chunk text along semantic boundaries"""
        chunks = []
        current_start = 0
        current_text = ""
        chunk_id = 0
        
        for i, boundary in enumerate(boundaries[1:], 1):
            segment = text[boundaries[i-1]:boundary]
            
            # Check if adding segment exceeds max size
            if len(current_text) + len(segment) > config.max_chunk_size:
                # Save current chunk if it meets minimum size
                if len(current_text) >= config.min_chunk_size:
                    chunks.append(self._create_chunk(
                        text=current_text.strip(),
                        chunk_id=chunk_id,
                        source=source,
                        doc_type=doc_type,
                        start=current_start,
                        end=boundaries[i-1]
                    ))
                    chunk_id += 1
                
                # Start new chunk with overlap
                overlap_text = current_text[-config.overlap_size:] if config.overlap_size > 0 else ""
                current_text = overlap_text + segment
                current_start = boundaries[i-1] - len(overlap_text)
            else:
                current_text += segment
        
        # Don't forget the last chunk
        if len(current_text.strip()) >= config.min_chunk_size:
            chunks.append(self._create_chunk(
                text=current_text.strip(),
                chunk_id=chunk_id,
                source=source,
                doc_type=doc_type,
                start=current_start,
                end=len(text)
            ))
        
        return chunks
    
    def _sliding_window_chunk(
        self,
        text: str,
        source: str,
        doc_type: DocumentType,
        config: ChunkConfig
    ) -> List[DocumentChunk]:
        """Simple sliding window chunking"""
        chunks = []
        chunk_id = 0
        start = 0
        
        while start < len(text):
            end = min(start + config.base_chunk_size, len(text))
            
            # Try to end at sentence boundary
            if end < len(text):
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start + config.min_chunk_size:
                    end = sentence_end + 1
            
            chunk_text = text[start:end].strip()
            
            if len(chunk_text) >= config.min_chunk_size:
                chunks.append(self._create_chunk(
                    text=chunk_text,
                    chunk_id=chunk_id,
                    source=source,
                    doc_type=doc_type,
                    start=start,
                    end=end
                ))
                chunk_id += 1
            
            start = end - config.overlap_size
            if start >= len(text) - config.min_chunk_size:
                break
        
        return chunks
    
    def _chunk_tabular(
        self,
        text: str,
        source: str,
        doc_type: DocumentType,
        config: ChunkConfig
    ) -> List[DocumentChunk]:
        """Chunk tabular data (CSV/Excel) preserving row groups"""
        chunks = []
        lines = text.strip().split('\n')
        
        if not lines:
            return []
        
        # First line is usually header
        header = lines[0] if lines else ""
        data_lines = lines[1:] if len(lines) > 1 else []
        
        chunk_id = 0
        current_lines = [header]  # Always include header
        current_start = 0
        
        for i, line in enumerate(data_lines):
            current_lines.append(line)
            current_text = '\n'.join(current_lines)
            
            if len(current_text) >= config.base_chunk_size:
                chunks.append(self._create_chunk(
                    text=current_text,
                    chunk_id=chunk_id,
                    source=source,
                    doc_type=doc_type,
                    start=current_start,
                    end=current_start + len(current_text),
                    metadata={"row_start": current_start, "row_end": i + 1, "has_header": True}
                ))
                chunk_id += 1
                
                # Reset with header
                current_lines = [header]
                current_start = i + 1
        
        # Last chunk
        if len(current_lines) > 1:  # More than just header
            current_text = '\n'.join(current_lines)
            chunks.append(self._create_chunk(
                text=current_text,
                chunk_id=chunk_id,
                source=source,
                doc_type=doc_type,
                start=current_start,
                end=len(text),
                metadata={"row_start": current_start, "row_end": len(lines), "has_header": True}
            ))
        
        return chunks
    
    def _chunk_json(
        self,
        text: str,
        source: str,
        config: ChunkConfig
    ) -> List[DocumentChunk]:
        """Chunk JSON data preserving structure"""
        import json
        
        try:
            data = json.loads(text)
            
            # If it's a list, chunk by items
            if isinstance(data, list):
                return self._chunk_json_list(data, source, config)
            else:
                # Single object - treat as one chunk
                return [self._create_chunk(
                    text=json.dumps(data, indent=2),
                    chunk_id=0,
                    source=source,
                    doc_type=DocumentType.JSON,
                    start=0,
                    end=len(text)
                )]
        except json.JSONDecodeError:
            # Fall back to text chunking
            return self._sliding_window_chunk(text, source, DocumentType.TEXT, config)
    
    def _chunk_json_list(
        self,
        data: list,
        source: str,
        config: ChunkConfig
    ) -> List[DocumentChunk]:
        """Chunk JSON list by grouping items"""
        import json
        
        chunks = []
        chunk_id = 0
        current_items = []
        current_size = 0
        
        for i, item in enumerate(data):
            item_str = json.dumps(item, indent=2)
            
            if current_size + len(item_str) > config.base_chunk_size and current_items:
                chunks.append(self._create_chunk(
                    text=json.dumps(current_items, indent=2),
                    chunk_id=chunk_id,
                    source=source,
                    doc_type=DocumentType.JSON,
                    start=chunk_id * config.base_chunk_size,
                    end=(chunk_id + 1) * config.base_chunk_size,
                    metadata={"item_count": len(current_items)}
                ))
                chunk_id += 1
                current_items = []
                current_size = 0
            
            current_items.append(item)
            current_size += len(item_str)
        
        if current_items:
            chunks.append(self._create_chunk(
                text=json.dumps(current_items, indent=2),
                chunk_id=chunk_id,
                source=source,
                doc_type=DocumentType.JSON,
                start=chunk_id * config.base_chunk_size,
                end=len(json.dumps(data)),
                metadata={"item_count": len(current_items)}
            ))
        
        return chunks
    
    def _create_chunk(
        self,
        text: str,
        chunk_id: int,
        source: str,
        doc_type: DocumentType,
        start: int,
        end: int,
        metadata: Optional[Dict] = None
    ) -> DocumentChunk:
        """Create a DocumentChunk with computed metadata"""
        # Estimate token count (rough: ~4 chars per token)
        token_count = len(text) // 4
        
        # Generate semantic context (first 50 chars cleaned)
        semantic_context = text[:50].strip().replace('\n', ' ')
        if len(text) > 50:
            semantic_context += "..."
        
        return DocumentChunk(
            text=text,
            chunk_id=chunk_id,
            source=source,
            document_type=doc_type,
            start_position=start,
            end_position=end,
            metadata=metadata or {},
            token_count=token_count,
            semantic_context=semantic_context
        )
    
    def estimate_total_tokens(self, chunks: List[DocumentChunk]) -> int:
        """Estimate total tokens across all chunks"""
        return sum(c.token_count for c in chunks)


# Singleton instance
_chunker = None

def get_chunker() -> AdaptiveChunker:
    """Get or create singleton chunker"""
    global _chunker
    if _chunker is None:
        _chunker = AdaptiveChunker()
    return _chunker


def chunk_document(text: str, source: str) -> List[DocumentChunk]:
    """
    Convenience function to chunk a document.
    
    Args:
        text: Document content
        source: Source filename
        
    Returns:
        List of DocumentChunk objects
    """
    chunker = get_chunker()
    return chunker.chunk_document(text, source)
