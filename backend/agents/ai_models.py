# AI Models Configuration
"""
Configuration for external AI models available in the chat interface.
These models are accessed via OpenRouter/LiteLLM.
"""

from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum


class AIModelProvider(Enum):
    """AI model providers"""
    GROQ = "groq"
    OPENROUTER = "openrouter"
    TOGETHER = "together"


@dataclass
class AIModelConfig:
    """Configuration for an AI model"""
    id: str                     # Frontend mode id (e.g., "deepseek-chat")
    name: str                   # Display name
    model_path: str             # LiteLLM model path
    provider: AIModelProvider
    max_tokens: int
    temperature: float
    description: str
    best_for: str               # What this model excels at
    speed: str                  # "fast", "medium", "slow"


# ============================================================================
# AI MODEL CONFIGURATIONS - FREE OPENROUTER MODELS ONLY
# Updated: Dec 2024 - Only verified working models
# Note: DeepSeek, OpenAI, Gemma removed due to errors
# ============================================================================

AI_MODELS: Dict[str, AIModelConfig] = {
    "mistral-7b": AIModelConfig(
        id="mistral-7b",
        name="Mistral Small",
        model_path="openrouter/mistralai/mistral-small-3.1-24b-instruct:free",
        provider=AIModelProvider.OPENROUTER,
        max_tokens=4000,
        temperature=0.7,
        description="FREE - Fast model for quick decision analysis",
        best_for="Quick analysis, summaries, decisions",
        speed="fast",
    ),
    
    "llama-70b": AIModelConfig(
        id="llama-70b",
        name="Llama 3.3 70B",
        model_path="openrouter/meta-llama/llama-3.3-70b-instruct:free",
        provider=AIModelProvider.OPENROUTER,
        max_tokens=4000,
        temperature=0.7,
        description="FREE - Meta's flagship model for comprehensive analysis",
        best_for="Deep analysis, complex reasoning, detailed reports",
        speed="medium",
    ),
}


def get_ai_model_config(mode_id: str) -> Optional[AIModelConfig]:
    """Get AI model configuration by mode ID"""
    return AI_MODELS.get(mode_id)


def is_ai_model_mode(mode: str) -> bool:
    """Check if the mode is an AI model (not RAG/Graph)"""
    return mode in AI_MODELS


def get_model_path(mode_id: str) -> str:
    """Get LiteLLM model path for a mode"""
    config = get_ai_model_config(mode_id)
    if config:
        return config.model_path
    return None


def get_all_ai_models() -> list:
    """Get list of all AI model configs"""
    return list(AI_MODELS.values())


# ============================================================================
# AI MODEL SYSTEM PROMPTS
# ============================================================================

AI_MODEL_SYSTEM_PROMPT = """You are an AI Business Analyst. Answer business questions accurately and concisely.

RULES:
1. Be direct and data-driven
2. Use tables for structured data
3. Use the user's preferred currency
4. If data is not provided, say "I don't have access to your data for this query"
5. Never invent numbers or statistics

For business queries, provide:
1. **One-line answer** (bolded)
2. Supporting details or table
3. Brief insight if applicable

Be professional, confident, and concise."""


def get_ai_model_system_prompt(model_id: str = None) -> str:
    """Get system prompt for AI model mode"""
    return AI_MODEL_SYSTEM_PROMPT
