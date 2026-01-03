"""
RAG Search Module - Simple wrapper for vector search
"""

import os
from typing import List, Tuple
from pathlib import Path

# Try to import vectorizer components
try:
    from mcp.vectorizer import get_vectorizer, query_vectors
    VECTORIZER_AVAILABLE = True
except ImportError:
    VECTORIZER_AVAILABLE = False
    print("⚠️ Vectorizer not available for RAG")

def rag_search(user_id: str, query: str, k: int = 5) -> Tuple[str, List[str]]:
    """
    Simple RAG search - retrieves relevant context from user's data
    
    Args:
        user_id: User ID for data isolation
        query: Search query
        k: Number of results to return
        
    Returns:
        Tuple of (context_string, list of sources)
    """
    context = ""
    sources = []
    
    try:
        # Try to load user's CSV data as context
        from utils.paths import get_user_paths
        paths = get_user_paths(user_id)
        files_dir = paths.get("files")
        
        if files_dir and files_dir.exists():
            import pandas as pd
            
            for file_path in files_dir.iterdir():
                if file_path.suffix.lower() in ['.csv', '.xlsx', '.xls']:
                    try:
                        if file_path.suffix.lower() == '.csv':
                            df = pd.read_csv(file_path)
                        else:
                            df = pd.read_excel(file_path)
                        
                        # Create basic context from data summary
                        context += f"\n\n## Data from {file_path.name}:\n"
                        context += f"Columns: {', '.join(df.columns.tolist())}\n"
                        context += f"Total rows: {len(df)}\n"
                        
                        # Add sample rows
                        context += f"\nSample data:\n{df.head(10).to_string()}\n"
                        
                        # Add basic stats for numeric columns
                        numeric_cols = df.select_dtypes(include=['number']).columns
                        if len(numeric_cols) > 0:
                            context += f"\nNumeric summaries:\n{df[numeric_cols].describe().to_string()}\n"
                        
                        sources.append(file_path.name)
                        print(f"📄 Loaded data from {file_path.name}: {len(df)} rows")
                        
                    except Exception as e:
                        print(f"⚠️ Error reading {file_path.name}: {e}")
        
        if not context:
            context = "No data files found. Please upload a CSV or Excel file first."
            
    except Exception as e:
        print(f"⚠️ RAG search error: {e}")
        context = f"Error loading data: {str(e)}"
    
    return context, sources


def get_relevant_context(user_id: str, query: str) -> str:
    """Alias for rag_search that returns just the context"""
    context, _ = rag_search(user_id, query)
    return context
