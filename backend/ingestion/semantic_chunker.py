# Semantic Chunking Module
"""
Intelligent chunking based on semantic boundaries (sentences, paragraphs)
instead of fixed character counts.

Benefits:
- Preserves complete thoughts/sentences
- Better RAG retrieval accuracy
- Handles tables and structured data properly
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Chunk:
    """Represents a semantic chunk"""
    text: str
    index: int
    char_start: int
    char_end: int
    chunk_type: str = "text"  # text, table, header, list


class SemanticChunker:
    """
    Semantic-aware document chunking
    
    Strategies:
    1. Sentence-based: Split on sentence boundaries
    2. Paragraph-based: Split on paragraph boundaries  
    3. Section-based: Split on headers/titles
    4. Table-aware: Keep tables intact
    """
    
    def __init__(
        self,
        max_chunk_size: int = 700,
        min_chunk_size: int = 100,
        overlap_sentences: int = 1,
        preserve_tables: bool = True
    ):
        """
        Args:
            max_chunk_size: Maximum characters per chunk
            min_chunk_size: Minimum characters (merge smaller chunks)
            overlap_sentences: Number of sentences to overlap
            preserve_tables: Keep tabular data together
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.overlap_sentences = overlap_sentences
        self.preserve_tables = preserve_tables
        
        # Sentence boundary patterns
        self.sentence_pattern = re.compile(
            r'(?<=[.!?])\s+(?=[A-Z])|'  # Standard sentence end
            r'(?<=[.!?])\s*\n|'          # Sentence end at line break
            r'\n\n+'                      # Paragraph break
        )
        
        # Table patterns (CSV-like, markdown tables)
        self.table_pattern = re.compile(
            r'(?:^|\n)[\|\+][-\|\+]+[\|\+]|'  # Markdown/ASCII tables
            r'(?:^|\n)(?:[^\n,]+,){2,}[^\n]+(?:\n|$)',  # CSV-like
            re.MULTILINE
        )
        
        # Header patterns
        self.header_pattern = re.compile(
            r'^#+\s+.+$|'                # Markdown headers
            r'^[A-Z][A-Z\s]+:?\s*$|'     # ALL CAPS headers
            r'^(?:\d+\.)+\s+.+$',        # Numbered sections
            re.MULTILINE
        )
    
    def chunk(self, text: str) -> List[Chunk]:
        """
        Main chunking method with semantic awareness
        
        Args:
            text: Document text to chunk
            
        Returns:
            List of Chunk objects
        """
        if not text or not text.strip():
            return []
        
        # Clean the text
        text = self._clean_text(text)
        
        # Detect if text contains tables
        if self.preserve_tables and self._has_tables(text):
            return self._chunk_with_tables(text)
        
        # Standard semantic chunking
        return self._semantic_chunk(text)
    
    def chunk_texts(self, text: str) -> List[str]:
        """
        Simplified interface returning just text strings
        
        Args:
            text: Document text
            
        Returns:
            List of chunk texts
        """
        chunks = self.chunk(text)
        return [c.text for c in chunks]
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Normalize whitespace but preserve paragraph breaks
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
    
    def _has_tables(self, text: str) -> bool:
        """Check if text contains tabular data"""
        return bool(self.table_pattern.search(text))
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Split on sentence boundaries
        sentences = self.sentence_pattern.split(text)
        
        # Filter empty and clean
        sentences = [s.strip() for s in sentences if s and s.strip()]
        
        return sentences
    
    def _semantic_chunk(self, text: str) -> List[Chunk]:
        """Chunk based on sentence boundaries"""
        sentences = self._split_sentences(text)
        
        if not sentences:
            return [Chunk(text=text, index=0, char_start=0, char_end=len(text))]
        
        chunks = []
        current_chunk = []
        current_length = 0
        char_position = 0
        chunk_index = 0
        
        for i, sentence in enumerate(sentences):
            sentence_len = len(sentence)
            
            # Check if adding sentence exceeds max size
            if current_length + sentence_len > self.max_chunk_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append(Chunk(
                    text=chunk_text,
                    index=chunk_index,
                    char_start=char_position - current_length,
                    char_end=char_position,
                    chunk_type="text"
                ))
                chunk_index += 1
                
                # Start new chunk with overlap
                overlap_start = max(0, len(current_chunk) - self.overlap_sentences)
                current_chunk = current_chunk[overlap_start:]
                current_length = sum(len(s) + 1 for s in current_chunk)
            
            current_chunk.append(sentence)
            current_length += sentence_len + 1
            char_position += sentence_len + 1
        
        # Save final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            if len(chunk_text) >= self.min_chunk_size or not chunks:
                chunks.append(Chunk(
                    text=chunk_text,
                    index=chunk_index,
                    char_start=char_position - current_length,
                    char_end=char_position,
                    chunk_type="text"
                ))
            elif chunks:
                # Merge with previous chunk if too small
                last_chunk = chunks[-1]
                chunks[-1] = Chunk(
                    text=last_chunk.text + ' ' + chunk_text,
                    index=last_chunk.index,
                    char_start=last_chunk.char_start,
                    char_end=char_position,
                    chunk_type="text"
                )
        
        return chunks
    
    def _chunk_with_tables(self, text: str) -> List[Chunk]:
        """Chunk while preserving tables"""
        chunks = []
        chunk_index = 0
        
        # Find table regions
        table_matches = list(self.table_pattern.finditer(text))
        
        if not table_matches:
            return self._semantic_chunk(text)
        
        last_end = 0
        
        for match in table_matches:
            # Process text before table
            if match.start() > last_end:
                pre_text = text[last_end:match.start()]
                pre_chunks = self._semantic_chunk(pre_text)
                for c in pre_chunks:
                    c.index = chunk_index
                    chunks.append(c)
                    chunk_index += 1
            
            # Extract complete table (expand to include all rows)
            table_text = self._extract_complete_table(text, match.start())
            
            if table_text:
                chunks.append(Chunk(
                    text=table_text,
                    index=chunk_index,
                    char_start=match.start(),
                    char_end=match.start() + len(table_text),
                    chunk_type="table"
                ))
                chunk_index += 1
                last_end = match.start() + len(table_text)
            else:
                last_end = match.end()
        
        # Process remaining text after last table
        if last_end < len(text):
            post_text = text[last_end:]
            post_chunks = self._semantic_chunk(post_text)
            for c in post_chunks:
                c.index = chunk_index
                chunks.append(c)
                chunk_index += 1
        
        return chunks
    
    def _extract_complete_table(self, text: str, start_pos: int) -> str:
        """Extract a complete table starting from position"""
        # Find table boundaries
        lines = text[start_pos:].split('\n')
        table_lines = []
        
        for line in lines:
            # Check if line looks like table row
            is_table_row = (
                '|' in line or 
                line.startswith('+') or
                (line.count(',') >= 2 and len(line) < 500)  # CSV-like
            )
            
            if is_table_row or (table_lines and line.strip() == ''):
                table_lines.append(line)
            elif table_lines:
                # End of table
                break
        
        return '\n'.join(table_lines).strip()


class SemanticProcessor:
    """
    Enhanced processor using semantic chunking
    Drop-in replacement for the basic Processor class
    """
    
    def __init__(self, size: int = 700, overlap: int = 150):
        """
        Args:
            size: Max chunk size (characters)
            overlap: Overlap (in sentences, not characters)
        """
        self.chunker = SemanticChunker(
            max_chunk_size=size,
            min_chunk_size=100,
            overlap_sentences=max(1, overlap // 100),  # Convert char overlap to sentence count
            preserve_tables=True
        )
    
    @staticmethod
    def clean(text: str) -> str:
        """Clean text while preserving structure"""
        # Remove excessive whitespace but keep paragraph breaks
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
    
    def chunk(self, text: str) -> List[str]:
        """
        Semantic chunking - API compatible with original Processor
        
        Args:
            text: Document text
            
        Returns:
            List of chunk strings
        """
        return self.chunker.chunk_texts(text)


# Convenience function for direct use
def semantic_chunk(text: str, max_size: int = 700) -> List[str]:
    """
    Quick semantic chunking of text
    
    Args:
        text: Text to chunk
        max_size: Maximum chunk size
        
    Returns:
        List of chunks
    """
    chunker = SemanticChunker(max_chunk_size=max_size)
    return chunker.chunk_texts(text)
