"""
OpenRouter AI Provider
Access multiple free LLMs through OpenRouter API
"""

import os
import aiohttp
from typing import Optional, Dict, Any, List


# OpenRouter base URL
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


# Available FREE models via OpenRouter
OPENROUTER_MODELS = {
    # DeepSeek - Best free option
    "deepseek-chat": {
        "id": "deepseek/deepseek-chat",
        "name": "DeepSeek Chat",
        "description": "Best free option - Very good quality, Large context, Fast",
        "category": "chat",
        "free": True,
    },
    "deepseek-coder": {
        "id": "deepseek/deepseek-coder",
        "name": "DeepSeek Coder",
        "description": "Excellent for coding and technical analysis",
        "category": "coding",
        "free": True,
    },
    
    # Qwen (Alibaba) - Underrated but powerful
    "qwen-7b": {
        "id": "qwen/qwen-2-7b-instruct",
        "name": "Qwen 2 7B",
        "description": "Great for business analysis and data explanation",
        "category": "analysis",
        "free": True,
    },
    "qwen-14b": {
        "id": "qwen/qwen-14b-instruct",
        "name": "Qwen 14B",
        "description": "Larger model for complex analysis",
        "category": "analysis",
        "free": True,
    },
    
    # Nous - Open-source fine-tuned models
    "nous-mixtral": {
        "id": "nousresearch/nous-hermes-2-mixtral-8x7b-dpo",
        "name": "Nous Hermes Mixtral",
        "description": "Excellent for agent-style reasoning",
        "category": "reasoning",
        "free": True,
    },
    "nous-yi": {
        "id": "nousresearch/nous-hermes-2-yi-34b",
        "name": "Nous Hermes Yi",
        "description": "Great for long conversations",
        "category": "chat",
        "free": True,
    },
    
    # Google Gemini
    "gemini-flash": {
        "id": "google/gemini-flash-1.5",
        "name": "Gemini Flash 1.5",
        "description": "Fast Google model with free tier",
        "category": "general",
        "free": True,
    },
    
    # Meta Llama
    "llama-3.1-8b": {
        "id": "meta-llama/llama-3.1-8b-instruct:free",
        "name": "Llama 3.1 8B",
        "description": "Meta's open-source model, very capable",
        "category": "general",
        "free": True,
    },
    
    # Mistral
    "mistral-7b": {
        "id": "mistralai/mistral-7b-instruct:free",
        "name": "Mistral 7B",
        "description": "Fast and efficient open-source model",
        "category": "general",
        "free": True,
    },
}


def get_openrouter_api_key() -> Optional[str]:
    """Get OpenRouter API key from environment"""
    return os.getenv("OPENROUTER_API_KEY")


def is_configured() -> bool:
    """Check if OpenRouter is configured"""
    return bool(get_openrouter_api_key())


def get_available_models() -> List[Dict[str, Any]]:
    """Get list of available OpenRouter models"""
    configured = is_configured()
    return [
        {
            "key": key,
            "configured": configured,
            **model
        }
        for key, model in OPENROUTER_MODELS.items()
    ]


async def generate_response(
    prompt: str,
    context: str = "",
    model_key: str = "deepseek-chat",
    max_tokens: int = 2048,
    temperature: float = 0.7,
) -> str:
    """
    Generate AI response using OpenRouter
    
    Args:
        prompt: User's question or prompt
        context: Additional context (e.g., data summary from RAG)
        model_key: Key of the model to use
        max_tokens: Maximum tokens in response
        temperature: Creativity level (0.0-1.0)
        
    Returns:
        Generated text response
    """
    api_key = get_openrouter_api_key()
    if not api_key:
        raise ValueError("OpenRouter API key not configured. Set OPENROUTER_API_KEY in .env")
    
    # Get model details
    model = OPENROUTER_MODELS.get(model_key, OPENROUTER_MODELS["deepseek-chat"])
    model_id = model["id"]
    
    # Build messages
    messages = []
    
    # System context with instructions to avoid hallucination
    system_prompt = """You are an AI Business Analyst assistant. Answer based ONLY on the provided context and data.
    
IMPORTANT RULES:
1. Only answer based on the provided data context
2. If the data doesn't contain the answer, say "I don't have that information in the data"
3. Never make up numbers or statistics
4. Cite specific data points when answering
5. Be concise and business-focused"""

    if context:
        system_prompt += f"\n\nCONTEXT DATA:\n{context}"
    
    messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": model_id,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://ai-business-analyst.local",
        "X-Title": "AI Business Analyst"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            json=payload,
            headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data["choices"][0]["message"]["content"]
            else:
                error = await response.text()
                raise Exception(f"OpenRouter API error ({response.status}): {error}")


async def get_model_info() -> Dict[str, Any]:
    """Get info about available models and configuration status"""
    return {
        "configured": is_configured(),
        "models": get_available_models(),
        "default_model": "deepseek-chat",
        "api_key_env": "OPENROUTER_API_KEY",
    }
