"""
👁️ CORE VISION MODULE - Image Analysis Functions
================================================

Provides image analysis using multimodal LLMs (Groq Llama 3.2 Vision primary).

Functions:
- analyze_image: General image analysis
- analyze_image_with_groq: Groq Llama 3.2 Vision
- extract_chart_data: Extract data from chart images
- extract_table_data: Extract data from table images
"""

import os
import base64
import logging
import json
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# Check for vision-capable APIs - Groq is primary
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

VISION_AVAILABLE = bool(GROQ_API_KEY or GOOGLE_API_KEY or OPENAI_API_KEY)


def _load_image_base64(image_path: str) -> Optional[str]:
    """Load image and convert to base64."""
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        return base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to load image: {e}")
        return None


def _get_image_mime_type(image_path: str) -> str:
    """Detect MIME type from image path."""
    ext = os.path.splitext(image_path)[1].lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.bmp': 'image/bmp'
    }
    return mime_types.get(ext, 'image/jpeg')


def analyze_image_with_groq(image_path: str, prompt: str = "Describe this image in detail.") -> str:
    """
    Analyze image using Groq's Llama 3.2 Vision API.
    
    Args:
        image_path: Path to image file OR base64 data URL (data:image/...)
        prompt: Analysis prompt
        
    Returns:
        Analysis text
    """
    if not GROQ_API_KEY:
        logger.warning("No GROQ_API_KEY found for vision")
        return "❌ Vision analysis requires GROQ_API_KEY to be configured."
    
    try:
        import litellm
        
        # Handle image input - could be file path or data URL
        if image_path.startswith('data:'):
            # Already a data URL from frontend
            image_url = image_path
            logger.info(f"Using data URL for vision (length: {len(image_path)})")
        elif os.path.exists(image_path):
            # Load from file path
            image_data = _load_image_base64(image_path)
            if not image_data:
                return "❌ Failed to load image file."
            mime_type = _get_image_mime_type(image_path)
            image_url = f"data:{mime_type};base64,{image_data}"
            logger.info(f"Loaded image from file: {image_path}")
        else:
            # Maybe it's raw base64 without data: prefix
            logger.warning(f"Unknown image format, trying as raw base64")
            image_url = f"data:image/jpeg;base64,{image_path}"
        
        logger.info(f"Calling Groq Vision with model: groq/llama-3.2-11b-vision-preview")
        
        # Use Groq's Llama 3.2 Vision model via litellm
        response = litellm.completion(
            model="groq/llama-3.2-11b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        }
                    ]
                }
            ],
            api_key=GROQ_API_KEY,
            max_tokens=1500
        )
        
        result = response.choices[0].message.content
        logger.info(f"Groq Vision success! Response length: {len(result)}")
        return result
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Groq Vision error: {error_msg}")
        
        # Check for specific errors
        if "model" in error_msg.lower() and "not found" in error_msg.lower():
            # Try fallback model
            try:
                logger.info("Trying fallback vision model: groq/llama-3.2-90b-vision-preview")
                response = litellm.completion(
                    model="groq/llama-3.2-90b-vision-preview",
                    messages=[
                        {
                            "role": "user", 
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": image_url}}
                            ]
                        }
                    ],
                    api_key=GROQ_API_KEY,
                    max_tokens=1500
                )
                return response.choices[0].message.content
            except Exception as e2:
                logger.error(f"Fallback also failed: {e2}")
        
        return f"❌ Groq Vision error: {error_msg}"


def analyze_image_with_gemini(image_path: str, prompt: str = "Describe this image in detail.") -> str:
    """
    Analyze image using Google Gemini Vision API.
    (Fallback - use Groq first)
    """
    if not GOOGLE_API_KEY:
        return "❌ Gemini requires GOOGLE_API_KEY."
    
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=GOOGLE_API_KEY)
        
        image_data = _load_image_base64(image_path)
        if not image_data:
            return "❌ Failed to load image file."
        
        mime_type = _get_image_mime_type(image_path)
        
        # Try different Gemini models
        for model_name in ['gemini-pro-vision', 'gemini-1.5-pro']:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content([
                    prompt,
                    {"mime_type": mime_type, "data": image_data}
                ])
                return response.text
            except:
                continue
        
        return "❌ No Gemini Vision model available."
        
    except Exception as e:
        logger.error(f"Gemini Vision error: {e}")
        return f"❌ Gemini error: {str(e)}"


def analyze_image(image_path: str, query: str = "Describe this image.") -> str:
    """
    Analyze image using best available vision model.
    
    Priority: Groq Llama 3.2 Vision > OpenAI > Gemini
    
    Args:
        image_path: Path to image file OR base64 data URL
        query: User's question about the image
        
    Returns:
        Analysis text
    """
    # Build comprehensive prompt
    prompt = f"""Analyze this image and answer the user's question.

USER QUESTION: {query}

Provide a detailed, accurate analysis. If this is a:
- Chart/Graph: Extract data points, describe trends
- Table: Extract rows and columns
- Document: Extract key text and information
- Photo: Describe content, objects, text visible

Be specific and provide actual values when visible."""
    
    # Try Groq first (fastest and free)
    if GROQ_API_KEY:
        result = analyze_image_with_groq(image_path, prompt)
        if not result.startswith("❌"):
            return result
    
    # Try OpenAI GPT-4V
    if OPENAI_API_KEY:
        try:
            import openai
            
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            
            # Handle both file path and data URL
            if image_path.startswith('data:'):
                image_url = image_path
            else:
                image_data = _load_image_base64(image_path)
                if not image_data:
                    return "❌ Failed to load image file."
                mime_type = _get_image_mime_type(image_path)
                image_url = f"data:{mime_type};base64,{image_data}"
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI Vision error: {e}")
    
    # Try Gemini as last resort
    if GOOGLE_API_KEY:
        return analyze_image_with_gemini(image_path, prompt)
    
    return """❌ **Vision Analysis Not Available**

To enable image analysis, configure GROQ_API_KEY in your .env file.
Groq provides FREE vision analysis with Llama 3.2 Vision."""


def extract_chart_data(image_path: str) -> Dict[str, Any]:
    """
    Extract structured data from chart images.
    
    Args:
        image_path: Path to chart image
        
    Returns:
        Dict with extracted data series and metadata
    """
    prompt = """Analyze this chart image and extract the data.

RESPOND IN JSON FORMAT ONLY:
{
    "chart_type": "bar|line|pie|scatter|area",
    "title": "Chart title if visible",
    "x_axis_label": "X axis label",
    "y_axis_label": "Y axis label",
    "data_series": [
        {
            "name": "Series name",
            "data": [
                {"x": "label1", "y": 100},
                {"x": "label2", "y": 200}
            ]
        }
    ],
    "insights": ["Key observation 1", "Key observation 2"]
}

Extract all visible data points accurately. If values aren't clear, provide estimates."""
    
    result = analyze_image(image_path, prompt)
    
    # Try to parse JSON from response
    try:
        # Find JSON block in response
        if "```json" in result:
            json_str = result.split("```json")[1].split("```")[0].strip()
        elif "```" in result:
            json_str = result.split("```")[1].split("```")[0].strip()
        elif result.strip().startswith("{"):
            json_str = result.strip()
        else:
            return {"success": False, "raw_analysis": result}
        
        parsed = json.loads(json_str)
        parsed["success"] = True
        return parsed
        
    except json.JSONDecodeError:
        return {"success": False, "raw_analysis": result}


def extract_table_data(image_path: str, output_format: str = "markdown") -> Dict[str, Any]:
    """
    Extract table data from image.
    
    Args:
        image_path: Path to table image
        output_format: "markdown" or "json"
        
    Returns:
        Dict with extracted tables
    """
    prompt = f"""Extract all tables from this image.

OUTPUT FORMAT: {output_format.upper()}

If markdown:
| Header1 | Header2 |
|---------|---------|
| Value1  | Value2  |

If JSON:
{{"tables": [{{"headers": ["H1", "H2"], "rows": [["V1", "V2"]]}}]}}

Extract ALL visible data accurately."""
    
    result = analyze_image(image_path, prompt)
    
    if output_format == "markdown":
        return {"success": True, "tables": [result]}
    
    # Try to parse JSON
    try:
        if "```json" in result:
            json_str = result.split("```json")[1].split("```")[0].strip()
        elif result.strip().startswith("{"):
            json_str = result.strip()
        else:
            return {"success": True, "tables": [result]}
        
        parsed = json.loads(json_str)
        parsed["success"] = True
        return parsed
        
    except json.JSONDecodeError:
        return {"success": True, "tables": [result]}


def vision_to_rag_context(image_path: str, query: str = "") -> Dict[str, Any]:
    """
    Extract text from image for RAG pipeline.
    
    Args:
        image_path: Path to image
        query: Optional context for extraction
        
    Returns:
        Dict with extracted text ready for RAG
    """
    prompt = """Extract all text and data from this image.

Provide structured output suitable for text search:
1. All visible text (OCR)
2. Data points and values
3. Labels and captions
4. Key information

Format as clean searchable text."""
    
    result = analyze_image(image_path, prompt)
    
    return {
        "success": True,
        "extracted_text": result,
        "ready_for_rag": True,
        "source": os.path.basename(image_path)
    }


# Module exports
__all__ = [
    'analyze_image',
    'analyze_image_with_gemini',
    'extract_chart_data',
    'extract_table_data',
    'vision_to_rag_context',
    'VISION_AVAILABLE'
]
