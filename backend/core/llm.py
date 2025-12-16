"""
Core LLM module for AI Business Analyst
Handles all interaction with Large Language Models
Enterprise-grade error handling and logging
"""
import logging
from typing import List, Dict, Any, Optional, Union
import os

# Try importing litellm, handle if missing or broken
LITELLM_AVAILABLE = False
try:
    # 🩹 MONKEY PATCH: Fix aiohttp compatibility for LiteLLM
    # Some environments have broken aiohttp/litellm combos
    import aiohttp
    if not hasattr(aiohttp, 'ConnectionTimeoutError'):
        # Inject the missing attribute aliased to ClientTimeout or generic ClientError
        # This prevents LiteLLM from crashing on import
        if hasattr(aiohttp, 'ClientTimeout'):
             setattr(aiohttp, 'ConnectionTimeoutError', aiohttp.ClientTimeout)
             setattr(aiohttp, 'SocketTimeoutError', aiohttp.ClientTimeout)
        else:
             setattr(aiohttp, 'ConnectionTimeoutError', Exception)
             setattr(aiohttp, 'SocketTimeoutError', Exception)
             
    import litellm
    LITELLM_AVAILABLE = True
except Exception as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import litellm: {e}")
    LITELLM_AVAILABLE = False
    
from config.settings import Settings

logger = logging.getLogger(__name__)

# Configure LiteLLM if available
if LITELLM_AVAILABLE:
    litellm.drop_params = True
    litellm.logging = False
    # Suppress verbose logging
    os.environ["LITELLM_LOG"] = "ERROR"
    
    # 🩹 ALIAS MAP: Route user's model to Groq with correct path
    # The model 'openai/gpt-oss-120b' exists on Groq Console
    # 'groq/openai/gpt-oss-120b' tells litellm: use Groq, request model 'openai/gpt-oss-120b'
    litellm.model_alias_map = {
        "openai/gpt-oss-120b": "groq/openai/gpt-oss-120b"
    }

def chat(
    messages: Union[str, List[Dict[str, str]]], 
    system: Optional[str] = None,
    temperature: float = 0.7,
    model: str = None,
    max_tokens: int = 4000
) -> str:
    """
    Send chat to LLM and get response
    
    Args:
        messages: List of message dicts (role, content) OR single string prompt
        system: Optional system prompt (will be prepended)
        temperature: Sampling temperature
        model: Optional model override
        max_tokens: Max tokens to generate
        
    Returns:
        str: Helper response content
    """
    if not LITELLM_AVAILABLE:
        logger.error("LiteLLM not installed. Please install: pip install litellm")
        return "Error: LLM driver (LiteLLM) missing."

    try:
        # Prepare messages
        final_messages = []
        
        # Add system prompt if provided
        if system:
            final_messages.append({"role": "system", "content": system})
            
        # Handle input: If string, convert to user message
        if isinstance(messages, str):
            final_messages.append({"role": "user", "content": messages})
        else:
            final_messages.extend(messages)
        
        # Determine model
        model_name = model or Settings.MODEL_NAME
        
        # Call LLM (synchronous)
        response = litellm.completion(
            model=model_name,
            messages=final_messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        error_str = str(e).lower()
        logger.error(f"LLM Chat Error: {str(e)}")
        
        # Sanitize error message - NEVER expose API details to users
        if 'rate_limit' in error_str or 'rate limit' in error_str or 'too large' in error_str:
            return (
                "**SERVICE LIMIT REACHED**\n\n"
                "The request was too large for the current model. "
                "Please try:\n"
                "- Asking a more specific question\n"
                "- Selecting a different AI model\n"
                "- Uploading smaller data files"
            )
        elif 'api_key' in error_str or 'unauthorized' in error_str or 'authentication' in error_str:
            return (
                "**CONFIGURATION ERROR**\n\n"
                "There's an issue with the AI model configuration. "
                "Please contact the administrator."
            )
        elif 'timeout' in error_str or 'connection' in error_str:
            return (
                "**CONNECTION ERROR**\n\n"
                "Unable to reach the AI service. Please try again in a moment."
            )
        else:
            # Generic error - don't expose details
            return (
                "**PROCESSING ERROR**\n\n"
                "Unable to process your request. Please try:\n"
                "- Rephrasing your question\n"
                "- Selecting a different AI model\n"
                "- Trying again in a moment"
            )


def embed_text(text: str) -> List[float]:
    """
    Generate embedding for a single text string
    
    Args:
        text: Input text
        
    Returns:
        List[float]: Embedding vector
    """
    if not LITELLM_AVAILABLE:
        logger.warning("LiteLLM not available for embedding, returning zero vector")
        return [0.0] * Settings.EMBED_DIM

    try:
        # Generate embedding
        response = litellm.embedding(
            model=Settings.EMBEDDING_MODEL,
            input=[text]
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Embedding error: {str(e)}")
        # Return zero vector on error to prevent partial failure
        return [0.0] * Settings.EMBED_DIM

def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts
    
    Args:
        texts: List of input texts
        
    Returns:
        List[List[float]]: List of embedding vectors
    """
    if not LITELLM_AVAILABLE:
        logger.warning("LiteLLM not available for batch embedding, returning zero vectors")
        return [[0.0] * Settings.EMBED_DIM for _ in texts]

    try:
        # Generate embeddings in batch
        response = litellm.embedding(
            model=Settings.EMBEDDING_MODEL,
            input=texts
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        logger.error(f"Batch embedding error: {str(e)}")
        # Return zero vectors on error
        return [[0.0] * Settings.EMBED_DIM for _ in texts]


