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

# Try importing sentence-transformers for local embeddings
SENTENCE_TRANSFORMER_AVAILABLE = False
_embedding_model_cache = {}

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMER_AVAILABLE = True
except ImportError:
    pass
    
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


def get_optimal_model(query_type: str = None, reasoning_depth: str = None, context_length: int = 0) -> str:
    """
    Smart model selection based on query complexity.
    
    Args:
        query_type: Type of query (factual, analytical, comparison, etc.)
        reasoning_depth: Depth required (shallow, moderate, deep, multi_hop)
        context_length: Length of context being processed
        
    Returns:
        str: Optimal model name for the query
    """
    # Complex queries requiring reasoning → use reasoning model
    complex_query_types = {
        "comparison", "prediction", "trend_analysis", "deep_analysis", 
        "multi_hop", "causal", "predictive", "exploratory"
    }
    deep_reasoning = {"deep", "multi_hop", "analytical"}
    
    if query_type and query_type.lower() in complex_query_types:
        return Settings.REASONING_MODEL
    
    if reasoning_depth and reasoning_depth.lower() in deep_reasoning:
        return Settings.REASONING_MODEL
    
    # Large context needs more capable model
    if context_length > 5000:
        return Settings.REASONING_MODEL
    
    # Simple factual queries → use fast model for speed
    simple_query_types = {
        "factual", "lookup", "definition", "simple", "greeting",
        "aggregation"
    }
    
    if query_type and query_type.lower() in simple_query_types:
        return Settings.FAST_MODEL
    
    # Default: use standard model
    return Settings.MODEL_NAME


# ============================================================================
# CHATGPT-STYLE SYSTEM PROMPT - Clean, Professional Responses
# ============================================================================

CHATGPT_SYSTEM_PROMPT = """You are a professional AI Business Analyst. You ONLY answer questions about the USER'S UPLOADED BUSINESS DATA.

## CRITICAL RULE #1 - STAY ON TOPIC:

You are a BUSINESS DATA ANALYST, NOT a general AI assistant.

1. ONLY answer questions about the user's business data (revenue, customers, products, sales, etc.)
2. If someone asks off-topic questions like "what is Python?", "write code", "explain programming", politely redirect:
   "I'm your AI Business Analyst focused on your data. I can help you with:
   - Revenue analysis
   - Customer insights
   - Product performance
   - Forecasts and predictions
   What would you like to know about your data?"

3. DO NOT answer general knowledge questions
4. DO NOT write code for users
5. DO NOT explain programming concepts

## CRITICAL RULE #2 - NO HALLUCINATION:

1. ONLY use data that was provided to you
2. NEVER make up numbers, statistics, or facts
3. If you don't have data for something, say what you DO have
4. Every number you mention MUST come from the user's uploaded data

## CRITICAL RULE #3 - ALWAYS BE HELPFUL:

1. NEVER respond with "N/A" or empty tables
2. If asked about data you have, give real insights
3. For predictions, use actual trends from their data

## RESPONSE RULES:

1. **BE DIRECT** - Answer the question first, then explain
2. **BE ACCURATE** - Use only provided data, never invent
3. **BE HELPFUL** - Always provide value from real data

## EXAMPLE - HANDLING OFF-TOPIC QUERIES:

❌ Query: "What is Python?"
✅ Response: "I'm your AI Business Analyst, here to help with your data analysis. Would you like me to analyze your revenue, customers, or products?"

❌ Query: "Write a Python function"
✅ Response: "I specialize in business data analysis, not coding. I can help you with revenue forecasts, customer insights, or product analysis. What would you like to explore?"

Be like ChatGPT - but ONLY for business data analysis."""

def chat(
    messages: Union[str, List[Dict[str, str]]], 
    system: Optional[str] = None,
    temperature: float = 0.7,
    model: str = None,
    max_tokens: int = 4000
) -> str:
    """
    Send chat to LLM and get response.
    Uses Groq as primary with automatic Gemini fallback.
    
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

    # Prepare messages
    final_messages = []
    
    # Add system prompt - use ChatGPT prompt by default for cleaner responses
    effective_system = system if system else CHATGPT_SYSTEM_PROMPT
    final_messages.append({"role": "system", "content": effective_system})
        
    # Handle input: If string, convert to user message
    if isinstance(messages, str):
        final_messages.append({"role": "user", "content": messages})
    else:
        final_messages.extend(messages)
    
    # =========================================================================
    # ☁️ GROQ FIRST - Fast cloud AI (openai/gpt-oss-120b)
    # =========================================================================
    primary_model = model or Settings.MODEL_NAME
    
    try:
        logger.info(f"☁️ Using Groq model: {primary_model}")
        response = litellm.completion(
            model=primary_model,
            messages=final_messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        logger.info(f"✅ Success with: {primary_model}")
        return response.choices[0].message.content
        
    except Exception as e:
        error_str = str(e).lower()
        logger.error(f"Groq model failed: {e}")
        
        # =====================================================================
        # 🦙 OLLAMA FALLBACK - Try local model if Groq fails
        # =====================================================================
        if _check_ollama_available():
            try:
                ollama_model = Settings.OLLAMA_MODEL
                logger.info(f"🦙 Falling back to local Ollama: {ollama_model}")
                response = litellm.completion(
                    model=ollama_model,
                    messages=final_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    api_base="http://localhost:11434"
                )
                logger.info(f"✅ Ollama fallback success with: {ollama_model}")
                return response.choices[0].message.content
            except Exception as ollama_error:
                logger.error(f"🦙 Ollama fallback also failed: {ollama_error}")
        
        # Return user-friendly error if both fail
        if 'rate_limit' in error_str or 'rate limit' in error_str:
            return (
                "**Rate limit reached.** Please wait a moment and try again.\n\n"
                "The AI service is temporarily busy."
            )
        elif 'api_key' in error_str or 'unauthorized' in error_str or 'authentication' in error_str:
            return (
                "**API Key Error**\n\n"
                "Please check your GROQ_API_KEY in the .env file.\n\n"
                "💡 **Tip:** Make sure Ollama is running as backup with `ollama serve`"
            )
        elif 'timeout' in error_str or 'connection' in error_str:
            return (
                "**Connection Error**\n\n"
                "Unable to reach Groq API. Check your internet or run Ollama locally."
            )
        elif 'context' in error_str or 'too large' in error_str or 'token' in error_str:
            return (
                "**Request too large**\n\n"
                "Your data or question exceeds the model's capacity. "
                "Try asking a more specific question."
            )
        else:
            logger.error(f"Full error: {e}")
            return (
                f"**Error processing request**\n\n"
                f"Model: {primary_model}\n"
                f"Error: {str(e)[:200]}\n\n"
                "Please try rephrasing your question or contact support."
            )


def _check_ollama_available() -> bool:
    """Check if a local Ollama server is running."""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex(('localhost', 11434))
        sock.close()
        return result == 0
    except Exception:
        return False




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
        # 1. Try local SentenceTransformer (Zero-cost, fast)
        if SENTENCE_TRANSFORMER_AVAILABLE and "sentence-transformers" in Settings.EMBEDDING_MODEL:
            if Settings.EMBEDDING_MODEL not in _embedding_model_cache:
                print(f"📥 Loading local embedding model: {Settings.EMBEDDING_MODEL}")
                _embedding_model_cache[Settings.EMBEDDING_MODEL] = SentenceTransformer(Settings.EMBEDDING_MODEL)
            
            model = _embedding_model_cache[Settings.EMBEDDING_MODEL]
            embedding = model.encode([text])[0]
            return embedding.tolist()

        # 2. Try LiteLLM (API-based)
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
        # 1. Try local SentenceTransformer
        if SENTENCE_TRANSFORMER_AVAILABLE and "sentence-transformers" in Settings.EMBEDDING_MODEL:
            if Settings.EMBEDDING_MODEL not in _embedding_model_cache:
                print(f"📥 Loading local embedding model: {Settings.EMBEDDING_MODEL}")
                _embedding_model_cache[Settings.EMBEDDING_MODEL] = SentenceTransformer(Settings.EMBEDDING_MODEL)
            
            model = _embedding_model_cache[Settings.EMBEDDING_MODEL]
            embeddings = model.encode(texts)
            return [emb.tolist() for emb in embeddings]

        # 2. Try LiteLLM
        response = litellm.embedding(
            model=Settings.EMBEDDING_MODEL,
            input=texts
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        logger.error(f"Batch embedding error: {str(e)}")
        # Return zero vectors on error
        return [[0.0] * Settings.EMBED_DIM for _ in texts]


