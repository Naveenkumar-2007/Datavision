"""
Multi-Model Configuration
=========================

Dynamic configuration for all AI models used in the application.
No hardcoding - models are configured via environment or this file.
"""

import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ModelConfig:
    """Configuration for a single AI model"""
    id: str
    name: str
    provider: str
    api_id: str  # OpenRouter model ID
    description: str
    context_length: int = 4096
    supports_streaming: bool = True
    supports_vision: bool = False
    supports_charts: bool = True  # All models can generate text that includes chart code
    category: str = "general"  # general, vision, embedding
    badge: Optional[str] = None
    # Define what this model is BEST at
    strengths: List[str] = field(default_factory=lambda: ["text", "analysis"])


# ============================================================================
# MODEL REGISTRY - Best Models for DataVision
# Each model has specific strengths for different types of queries
# ============================================================================

MODELS: Dict[str, ModelConfig] = {
    # ----------------------
    # GENERAL MODELS - Best for Business Analysis
    # ----------------------
    "deepseek": ModelConfig(
        id="deepseek",
        name="DeepSeek Chat",
        provider="DeepSeek",
        api_id="deepseek/deepseek-chat",
        description="Fast • Accurate • Recommended",
        context_length=32768,
        supports_streaming=True,
        supports_charts=True,
        category="general",
        badge="Best",
        strengths=["quick_lookup", "data_analysis", "calculations", "summaries", "charts"]
    ),
    
    "claude-3.5": ModelConfig(
        id="claude-3.5",
        name="Claude 3.5 Sonnet",
        provider="Anthropic",
        api_id="anthropic/claude-3.5-sonnet-20241022",
        description="Advanced reasoning & deep analysis",
        context_length=200000,
        supports_streaming=True,
        supports_charts=True,
        category="general",
        badge="Pro",
        strengths=["complex_reasoning", "multi_step_analysis", "insights", "comparisons", "charts"]
    ),
    
    "llama": ModelConfig(
        id="llama",
        name="Llama 3.3 70B",
        provider="Meta",
        api_id="meta-llama/llama-3.3-70b-instruct:free",
        description="Comprehensive & detailed reports",
        context_length=131072,
        supports_streaming=True,
        supports_charts=True,
        category="general",
        strengths=["comprehensive_reports", "detailed_explanations", "charts", "tables"]
    ),
    
    # ----------------------
    # VISION MODELS - For Charts, Reports & Images
    # ----------------------
    "gpt4v": ModelConfig(
        id="gpt4v",
        name="GPT-4 Vision",
        provider="OpenAI",
        api_id="openai/gpt-4-vision-preview",
        description="Chart & image analysis",
        context_length=128000,
        supports_streaming=True,
        supports_vision=True,
        supports_charts=True,
        category="vision",
        badge="Vision",
        strengths=["image_analysis", "chart_reading", "visual_data_extraction", "charts"]
    ),
    
    "claude-vision": ModelConfig(
        id="claude-vision",
        name="Claude 3.5 Vision",
        provider="Anthropic",
        api_id="anthropic/claude-3.5-sonnet-20241022",
        description="Document & report understanding",
        context_length=200000,
        supports_streaming=True,
        supports_vision=True,
        supports_charts=True,
        category="vision",
        badge="Vision",
        strengths=["document_analysis", "report_reading", "table_extraction", "charts"]
    ),
    
    # ----------------------
    # EMBEDDING MODELS (for RAG)
    # ----------------------
    "embedding": ModelConfig(
        id="embedding",
        name="Text Embedding",
        provider="OpenAI",
        api_id="openai/text-embedding-3-small",
        description="Document embeddings",
        context_length=8191,
        supports_streaming=False,
        supports_charts=False,
        category="embedding",
        strengths=["embeddings", "similarity_search"]
    ),
}


def get_model(model_id: str) -> Optional[ModelConfig]:
    """Get model configuration by ID"""
    return MODELS.get(model_id)


def get_model_api_id(model_id: str, fallback: str = "deepseek/deepseek-chat") -> str:
    """Get OpenRouter API ID for a model"""
    model = MODELS.get(model_id)
    if model:
        return model.api_id
    return fallback


def get_models_by_category(category: str) -> List[ModelConfig]:
    """Get all models in a category"""
    return [m for m in MODELS.values() if m.category == category]


def get_vision_models() -> List[ModelConfig]:
    """Get all models that support vision/images"""
    return [m for m in MODELS.values() if m.supports_vision]


def get_free_models() -> List[ModelConfig]:
    """Get all free models"""
    return [m for m in MODELS.values() if m.is_free]


def get_streaming_models() -> List[ModelConfig]:
    """Get all models that support streaming"""
    return [m for m in MODELS.values() if m.supports_streaming]


def get_default_model() -> ModelConfig:
    """Get the default model for general use"""
    # Check environment for override
    default_id = os.getenv("DEFAULT_MODEL", "deepseek")
    return MODELS.get(default_id, MODELS["deepseek"])


def get_default_vision_model() -> ModelConfig:
    """Get the default vision model"""
    vision_id = os.getenv("DEFAULT_VISION_MODEL", "gpt4v")
    return MODELS.get(vision_id, MODELS.get("llava"))


def model_to_frontend_format(model: ModelConfig) -> Dict[str, Any]:
    """Convert model to frontend-compatible format"""
    return {
        "id": model.id,
        "label": model.name,
        "description": model.description,
        "badge": model.badge,
        "isAI": True,
        "supportsVision": model.supports_vision,
        "supportsStreaming": model.supports_streaming,
        "isFree": model.is_free,
        "provider": model.provider,
    }


def get_all_models_for_frontend() -> List[Dict[str, Any]]:
    """Get all models formatted for frontend dropdown"""
    return [model_to_frontend_format(m) for m in MODELS.values()]


# API endpoint for frontend
def get_available_models_api() -> Dict[str, Any]:
    """API response format for available models"""
    return {
        "models": get_all_models_for_frontend(),
        "default": get_default_model().id,
        "default_vision": get_default_vision_model().id if get_default_vision_model() else None,
        "categories": {
            "general": [m.id for m in get_models_by_category("general")],
            "vision": [m.id for m in get_vision_models()],
            "code": [m.id for m in get_models_by_category("code")],
        }
    }


# Test
if __name__ == "__main__":
    print("Available Models:")
    print("=" * 50)
    
    for model_id, model in MODELS.items():
        vision = "👁️" if model.supports_vision else "  "
        free = "🆓" if model.is_free else "  "
        stream = "🔄" if model.supports_streaming else "  "
        print(f"{vision}{free}{stream} {model.name:20} ({model.provider})")
    
    print("\n" + "=" * 50)
    print(f"Default: {get_default_model().name}")
    print(f"Vision models: {[m.name for m in get_vision_models()]}")
    print(f"Free models: {[m.name for m in get_free_models()]}")
