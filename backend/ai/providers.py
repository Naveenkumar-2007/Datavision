"""
Free AI Model Integrations
Supports multiple free and paid AI providers
"""

import os
import aiohttp
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Base class for AI providers"""
    
    @abstractmethod
    async def generate(self, prompt: str, context: str = "", max_tokens: int = 2048) -> str:
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        pass


class GoogleGeminiProvider(AIProvider):
    """
    Google Gemini API (Free tier: 60 requests/minute)
    https://ai.google.dev/
    """
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.model = "gemini-1.5-flash"  # Fast and free
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    async def generate(self, prompt: str, context: str = "", max_tokens: int = 2048) -> str:
        if not self.is_configured():
            raise ValueError("Google AI API key not configured. Set GOOGLE_AI_API_KEY environment variable.")
        
        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": full_prompt}]
            }],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": 0.7
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    try:
                        return data["candidates"][0]["content"]["parts"][0]["text"]
                    except (KeyError, IndexError):
                        return "Unable to generate response"
                else:
                    error = await response.text()
                    raise Exception(f"Gemini API error: {error}")


class GroqProvider(AIProvider):
    """
    Groq API (Free tier available, very fast)
    https://console.groq.com/
    """
    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = "llama-3.1-8b-instant"  # Fast and free
        self.base_url = "https://api.groq.com/openai/v1"
    
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    async def generate(self, prompt: str, context: str = "", max_tokens: int = 2048) -> str:
        if not self.is_configured():
            raise ValueError("Groq API key not configured. Set GROQ_API_KEY environment variable.")
        
        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    error = await response.text()
                    raise Exception(f"Groq API error: {error}")


class HuggingFaceProvider(AIProvider):
    """
    HuggingFace Inference API (Free tier available)
    https://huggingface.co/inference-api
    """
    
    def __init__(self):
        self.api_key = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_API_KEY")
        self.model = "mistralai/Mistral-7B-Instruct-v0.2"
        self.base_url = "https://api-inference.huggingface.co/models"
    
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    async def generate(self, prompt: str, context: str = "", max_tokens: int = 2048) -> str:
        if not self.is_configured():
            raise ValueError("HuggingFace API key not configured. Set HUGGINGFACE_API_KEY environment variable.")
        
        full_prompt = f"[INST] {context}\n\n{prompt} [/INST]" if context else f"[INST] {prompt} [/INST]"
        
        payload = {
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.7,
                "return_full_text": False
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/{self.model}",
                json=payload,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, list) and len(data) > 0:
                        return data[0].get("generated_text", "")
                    return str(data)
                else:
                    error = await response.text()
                    raise Exception(f"HuggingFace API error: {error}")


class OpenAIProvider(AIProvider):
    """
    OpenAI API (Paid, but included for completeness)
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4-turbo-preview"
        self.base_url = "https://api.openai.com/v1"
    
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    async def generate(self, prompt: str, context: str = "", max_tokens: int = 2048) -> str:
        if not self.is_configured():
            raise ValueError("OpenAI API key not configured. Set OPENAI_API_KEY environment variable.")
        
        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    error = await response.text()
                    raise Exception(f"OpenAI API error: {error}")


class AnthropicProvider(AIProvider):
    """
    Anthropic Claude API (Paid, but excellent for analysis)
    """
    
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = "claude-3-sonnet-20240229"
        self.base_url = "https://api.anthropic.com/v1"
    
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    async def generate(self, prompt: str, context: str = "", max_tokens: int = 2048) -> str:
        if not self.is_configured():
            raise ValueError("Anthropic API key not configured. Set ANTHROPIC_API_KEY environment variable.")
        
        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": full_prompt}]
        }
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/messages",
                json=payload,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["content"][0]["text"]
                else:
                    error = await response.text()
                    raise Exception(f"Anthropic API error: {error}")


# Provider registry
PROVIDERS: Dict[str, type] = {
    "gemini": GoogleGeminiProvider,
    "groq": GroqProvider,
    "huggingface": HuggingFaceProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}


def get_available_providers() -> List[Dict[str, Any]]:
    """Get list of available (configured) AI providers"""
    available = []
    
    for name, provider_class in PROVIDERS.items():
        provider = provider_class()
        available.append({
            "id": name,
            "name": name.title(),
            "configured": provider.is_configured(),
            "free": name in ["gemini", "groq", "huggingface"]
        })
    
    return available


def get_provider(name: str = "auto") -> AIProvider:
    """
    Get an AI provider by name
    If 'auto', tries free providers first, then paid ones
    """
    if name != "auto" and name in PROVIDERS:
        return PROVIDERS[name]()
    
    # Auto-select: try free providers first
    priority_order = ["gemini", "groq", "huggingface", "openai", "anthropic"]
    
    for provider_name in priority_order:
        provider = PROVIDERS[provider_name]()
        if provider.is_configured():
            print(f"✅ Using {provider_name} AI provider")
            return provider
    
    raise ValueError("No AI provider configured. Set one of: GOOGLE_AI_API_KEY, GROQ_API_KEY, HUGGINGFACE_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY")


async def generate_response(
    prompt: str,
    context: str = "",
    provider: str = "auto",
    max_tokens: int = 2048
) -> str:
    """
    Generate AI response using the specified provider
    
    Args:
        prompt: User's question or prompt
        context: Additional context (e.g., data summary)
        provider: Provider name or 'auto' for automatic selection
        max_tokens: Maximum tokens in response
        
    Returns:
        Generated text response
    """
    ai_provider = get_provider(provider)
    return await ai_provider.generate(prompt, context, max_tokens)
