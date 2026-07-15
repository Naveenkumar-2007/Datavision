"""
Core LLM module for DataVision
Handles all interaction with Large Language Models
Enterprise-grade error handling and logging
SECURED: AI security filter for prompt injection protection
"""
import logging
from typing import List, Dict, Any, Optional, Union
import os
import contextvars

# Global context var to store requested model per-request
_requested_model: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("requested_model", default=None)

def set_requested_model(model: str):
    """Set the requested model for the current context (used by FastAPI endpoints)"""
    _requested_model.set(model)

# 🔒 SECURITY: Import AI security filter
try:
    from core.ai_security import get_ai_security_filter, sanitize_user_input
    AI_SECURITY_AVAILABLE = True
except ImportError:
    AI_SECURITY_AVAILABLE = False

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
except Exception as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"SentenceTransformer not available: {e}")
    
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

# Import product knowledge
try:
    from core.product_knowledge import DATAVISION_PRODUCT_KNOWLEDGE, is_product_question
    PRODUCT_KNOWLEDGE_AVAILABLE = True
except ImportError:
    DATAVISION_PRODUCT_KNOWLEDGE = ""
    PRODUCT_KNOWLEDGE_AVAILABLE = False

CHATGPT_SYSTEM_PROMPT = f"""You are DataVision AI Assistant - a professional data analyst and product guide.

## YOUR THREE ROLES:

1. 📊 **DATA ANALYST** - Answer questions about user's uploaded data
2. 🌐 **AI KNOWLEDGE** - Answer general questions using AI knowledge
3. 💡 **PRODUCT GUIDE** - Help users navigate and use DataVision features

{DATAVISION_PRODUCT_KNOWLEDGE if PRODUCT_KNOWLEDGE_AVAILABLE else ""}

## RESPONSE RULES:

### For DATA Questions (about their uploaded files):
📊 **From Your Data:**
[Use actual numbers from their data - NEVER make up values]

### For GENERAL Questions (not about their data):
🌐 **AI Knowledge:**
[Provide helpful AI-powered answers]

### For PRODUCT Questions (how to use DataVision):
💡 **How to do this:**
[Step-by-step instructions with page names]

## CRITICAL RULES:

1. **NO HALLUCINATION** - For data questions, ONLY use actual provided data
2. **ALWAYS BE HELPFUL** - Never refuse to answer, use appropriate knowledge source
3. **BE DIRECT** - Answer first, then explain
4. **GUIDE USERS** - If they're asking "how to" questions, give step-by-step help

## DETECTING QUESTION TYPE:

- "What are my sales?" → DATA question (use their data)
- "What is machine learning?" → GENERAL question (use AI knowledge)
- "How do I train a model?" → PRODUCT question (guide them)
- "How do I upload data?" → PRODUCT question (guide them)

Be friendly, professional, and genuinely helpful like ChatGPT!"""

def chat(
    messages: Union[str, List[Dict[str, str]]], 
    system: Optional[str] = None,
    temperature: float = 0.7,
    model: str = None,
    max_tokens: int = 4000,
    images: Optional[List[str]] = None,
    **kwargs
) -> str:
    """
    Send chat to LLM and get response.
    Uses Groq as primary with automatic Gemini fallback.
    SECURED: Applies AI security filter to prevent prompt injection.
    
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

    # Use requested model from context if not explicitly provided
    if model is None:
        model = _requested_model.get()

    # 🔒 SECURITY: Apply AI security filter to user input
    ai_filter = None
    if AI_SECURITY_AVAILABLE:
        ai_filter = get_ai_security_filter()
    
    # Prepare messages
    final_messages = []
    
    # Add system prompt - use ChatGPT prompt by default for cleaner responses
    effective_system = system if system else CHATGPT_SYSTEM_PROMPT
    final_messages.append({"role": "system", "content": effective_system})
        
    # Handle input: If string, convert to user message
    if isinstance(messages, str):
        # 🔒 SECURITY: Sanitize user input
        safe_message = messages
        if ai_filter:
            safe_message, was_suspicious, pattern = ai_filter.filter_input(messages)
            if was_suspicious:
                logger.warning(f"Prompt injection attempt detected: {pattern}")
        final_messages.append({"role": "user", "content": safe_message})
    else:
        # 🔒 SECURITY: Sanitize each user message in the list
        for msg in messages:
            if msg.get("role") == "user" and ai_filter:
                safe_content, was_suspicious, pattern = ai_filter.filter_input(msg.get("content", ""))
                if was_suspicious:
                    logger.warning(f"Prompt injection attempt detected: {pattern}")
                
                # Handle multimodal content formatting
                if images and msg == messages[-1]: # Only attach images to the latest user message
                    content_block = [{"type": "text", "text": safe_content}]
                    for img in images:
                        # Add base64 prefix if missing
                        img_str = img if img.startswith("data:image") else f"data:image/jpeg;base64,{img}"
                        content_block.append({"type": "image_url", "image_url": {"url": img_str}})
                    final_messages.append({"role": "user", "content": content_block})
                else:
                    final_messages.append({"role": msg["role"], "content": safe_content})
            else:
                final_messages.append(msg)
                
    # If it was a string prompt and we have images, format the single message
    if isinstance(messages, str) and images and final_messages[-1]["role"] == "user":
        safe_content = final_messages.pop()["content"]
        content_block = [{"type": "text", "text": safe_content}]
        for img in images:
            img_str = img if img.startswith("data:image") else f"data:image/jpeg;base64,{img}"
            content_block.append({"type": "image_url", "image_url": {"url": img_str}})
        final_messages.append({"role": "user", "content": content_block})
    
    # =========================================================================
    # ☁️ CASCADING PROVIDER FALLBACK CHAIN
    # Chain: Nvidia NIM -> HuggingFace -> Ollama
    # =========================================================================
    
    # 1. Build the Provider Chain
    providers = []
    
    nv_key = os.environ.get("NVIDIA_API_KEY")
    groq_key = os.environ.get("GROQ_API_KEY")
    hf_key = os.environ.get("HUGGINGFACE_API_KEY")
    
    # Check if we have any remote API keys
    has_remote_keys = bool(nv_key or groq_key or hf_key)
    
    # --- 1. PRIMARY: GROQ (Ultra-Fast) ---
    if groq_key:
        providers.append({
            "name": "Groq-Llama3",
            "model": "groq/llama-3.1-70b-versatile",
            "api_key": groq_key,
            "api_base": None
        })
    
    # --- 2. SECONDARY: NVIDIA LLAMA ---
    if nv_key:
        providers.append({
            "name": "Nvidia-Llama",
            "model": "openai/meta/llama-3.1-70b-instruct",
            "api_key": nv_key,
            "api_base": "https://integrate.api.nvidia.com/v1"
        })
        

    # --- HUGGINGFACE ---
    if hf_key:
        providers.append({
            "name": "HuggingFace",
            "model": "huggingface/meta-llama/Meta-Llama-3-8B-Instruct",
            "api_key": hf_key,
            "api_base": None
        })
        
    # --- OLLAMA (Local fallback) ---
    providers.append({
        "name": "Ollama",
        "model": "ollama/llama3",
        "api_key": None,
        "api_base": "http://localhost:11434"
    })
    
    # 2. Execute the Chain
    last_error = None
    import time as time_module
    
    for i, p in enumerate(providers):
        try:
            logger.info(f"Try {i+1}/{len(providers)}: {p['name']} ({p['model']})")
            
            call_kwargs = {
                "model": p["model"],
                "messages": final_messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            # Inject any additional kwargs (like response_format, tools, tool_choice)
            call_kwargs.update(kwargs)
            
            if p["api_key"]:
                call_kwargs["api_key"] = p["api_key"]
            if p["api_base"]:
                call_kwargs["api_base"] = p["api_base"]
                
            is_raw_response = call_kwargs.pop('raw_response', False)
                
            # 🔥 FIX: Set ultra-low timeout (15s) so the UI doesn't hang!
            if "timeout" not in call_kwargs:
                call_kwargs["timeout"] = 15
            
            # 🩹 FIX: Disable OpenAI client's internal retries - let our cascade handle failover
            # Without this, the OpenAI client retries internally (the "Retrying request..." logs)
            # which can cause requests to hang for 5+ minutes before our cascade kicks in
            if "num_retries" not in call_kwargs:
                call_kwargs["num_retries"] = 0
                
            response = litellm.completion(**call_kwargs)
            logger.info(f"Success with {p['name']}")
            
            if is_raw_response:
                return response
                
            result = response.choices[0].message.content
            if ai_filter:
                result = ai_filter.filter_output(result)
            return result
            
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            
            # Fast-Fail Check
            is_rate_limit = 'rate_limit' in error_str or 'rate limit' in error_str or '429' in error_str
            is_auth_error = 'api_key' in error_str or 'unauthorized' in error_str or 'authentication' in error_str or '401' in error_str
            is_org_restricted = 'organization' in error_str and ('restricted' in error_str or 'blocked' in error_str)
            is_bad_request = 'badrequest' in error_str.replace(' ', '') or 'invalid_request' in error_str
            is_connection = 'connection' in error_str or 'timeout' in error_str
            
            reason = 'Rate Limit' if is_rate_limit else ('Org Restricted' if is_org_restricted else ('Bad Request' if is_bad_request else ('Auth Error' if is_auth_error else ('Connection Error' if is_connection else 'Unknown Error'))))
            
            if i < len(providers) - 1:
                logger.warning(f"{p['name']} failed ({reason}). Cascading to next provider...")
                continue
            else:
                logger.error(f"All providers in the cascade chain exhausted. Last error: {e}")
                break

    # 3. Handle Complete Failure
    e = last_error
    error_str = str(e).lower() if e else ''
    
    # Generic friendly message - don't expose technical details to users
    if not has_remote_keys and ('timeout' in error_str or 'connection' in error_str):
        return (
            "🚨 **API Key Missing:** I couldn't process your request because no AI Provider API Keys were found! "
            "Please go to your HuggingFace Space Settings -> **Variables and secrets**, and add your `GROQ_API_KEY` or `NVIDIA_API_KEY`."
        )
    elif 'context' in error_str or 'too large' in error_str or 'token' in error_str:
        return (
            "Your question is quite detailed! Could you try asking something more specific? "
            "This will help me give you a better answer."
        )
    elif 'timeout' in error_str or 'connection' in error_str:
        return (
            "I'm having trouble connecting right now. Please check your internet connection and try again."
        )
    else:
        return (
            f"I'm temporarily unable to process your request. Please try again in a moment. "
            f"If this continues, the system administrator has been notified. (Error: {reason if 'reason' in locals() else 'Unknown'})"
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
        # 1. Try local SentenceTransformer (Zero-cost, fast)
        if SENTENCE_TRANSFORMER_AVAILABLE and "sentence-transformers" in Settings.EMBEDDING_MODEL:
            if Settings.EMBEDDING_MODEL not in _embedding_model_cache:
                logger.info(f"📥 Loading local embedding model: {Settings.EMBEDDING_MODEL}")
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
                logger.info(f"📥 Loading local embedding model: {Settings.EMBEDDING_MODEL}")
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


