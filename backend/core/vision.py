"""
Core Vision Module - FREE Image Analysis using OpenRouter
Uses free vision models - no paid API required
Updated Dec 2024 with current working models
"""

import os
import base64
import requests
from typing import Optional
from pathlib import Path

# Current FREE vision models on OpenRouter (verified Dec 2024)
FREE_VISION_MODELS = [
    "google/gemma-3-12b-it:free",             # Google Gemma 3 - FREE, multimodal
    "google/gemma-3-27b-it:free",             # Google Gemma 3 27B - FREE
    "meta-llama/llama-4-maverick:free",       # Meta Llama 4 - FREE, vision
    "qwen/qwen2.5-vl-32b-instruct:free",      # Qwen 2.5 Vision - FREE
    "moonshotai/kimi-vl-a3b-thinking:free",   # Moonshot Kimi - FREE
    "amazon/nova-lite-v1:free",               # Amazon Nova Lite - FREE
]


def analyze_image(image_path: str, prompt: str = "Describe this image") -> str:
    """
    Analyze an image using FREE OpenRouter vision models.
    Uses OPENROUTER_API_KEY from environment.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        return "⚠️ OPENROUTER_API_KEY not configured. Add it to your .env file. Get free key at: https://openrouter.ai/"
    
    # Read and encode the image
    try:
        image_data = _encode_image(image_path)
        if not image_data:
            return f"⚠️ Could not read image file: {image_path}"
    except Exception as e:
        return f"⚠️ Error reading image: {str(e)}"
    
    # Get file extension to determine media type
    ext = Path(image_path).suffix.lower()
    media_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    media_type = media_types.get(ext, 'image/jpeg')
    
    # Try each free model until one works
    last_error = ""
    for model in FREE_VISION_MODELS:
        result = _try_openrouter_model(model, api_key, image_data, media_type, prompt)
        if result and not result.startswith("⚠️"):
            return result
        last_error = result
        print(f"⚠️ Model {model} failed, trying next...")
    
    return f"⚠️ All free vision models failed. Last error: {last_error}"


def _try_openrouter_model(model: str, api_key: str, image_data: str, media_type: str, prompt: str) -> str:
    """Try a specific OpenRouter model."""
    payload = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_data}"}}
            ]
        }],
        "max_tokens": 4096,
        "temperature": 0.3
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://ai-business-analyst.app",
        "X-Title": "AI Business Analyst - Vision"
    }
    
    try:
        print(f"🔍 Trying FREE model: {model}")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=90
        )
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                result = data["choices"][0]["message"]["content"]
                print(f"✅ Success with FREE model: {model}")
                return result
            return "⚠️ Empty response"
        else:
            error = response.text[:300]
            print(f"❌ {model} error ({response.status_code}): {error}")
            return f"⚠️ {model}: {error}"
            
    except requests.Timeout:
        return "⚠️ Vision analysis timed out."
    except Exception as e:
        return f"⚠️ Error: {str(e)}"


def analyze_image_with_gemini(image_path: str, prompt: str = "Analyze this image") -> str:
    """Wrapper for backward compatibility."""
    return analyze_image(image_path, prompt)


def _encode_image(image_path: str) -> Optional[str]:
    """Encode an image file to base64."""
    try:
        path = Path(image_path)
        if not path.exists():
            return None
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception:
        return None


def extract_chart_data(image_path: str) -> dict:
    """Extract data from a chart image."""
    prompt = """Analyze this chart/graph and extract ALL data.

Return as JSON:
{
    "chart_type": "bar/line/pie/donut/scatter",
    "title": "Chart Title",
    "data_series": [
        {
            "name": "Series Name",
            "data": [
                {"label": "Category1", "value": 100},
                {"label": "Category2", "value": 200}
            ]
        }
    ],
    "total": sum_of_all_values
}

Be precise with all numbers."""
    
    result = analyze_image(image_path, prompt)
    
    import json
    import re
    
    try:
        json_match = re.search(r'\{[\s\S]*\}', result)
        if json_match:
            return json.loads(json_match.group())
    except:
        pass
    
    return {"raw_analysis": result}


def extract_table_data(image_path: str) -> dict:
    """Extract table data from an image."""
    prompt = """Extract ALL tables from this image.

Return as JSON:
{
    "tables": [
        {
            "headers": ["Column1", "Column2", "Column3"],
            "rows": [
                ["Row1Col1", "Row1Col2", "Row1Col3"],
                ["Row2Col1", "Row2Col2", "Row2Col3"]
            ]
        }
    ]
}

Preserve EXACT numbers and text."""
    
    result = analyze_image(image_path, prompt)
    
    import json
    import re
    
    try:
        json_match = re.search(r'\{[\s\S]*\}', result)
        if json_match:
            return json.loads(json_match.group())
    except:
        pass
    
    return {"raw_analysis": result}
