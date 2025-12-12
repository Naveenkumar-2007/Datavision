"""
Google Gemini Vision Module - ONLY for image analysis
All other modes (RAG, Graph, Chat) use Groq

CRITICAL: ALL imports and configuration are LAZY LOADED inside functions.
DO NOT import google.generativeai at module level.
DO NOT call genai.configure() at module level.
This prevents API calls at import time.
"""

from typing import Optional
from config.settings import Settings

# Lazy loaded - DO NOT initialize at module level
_vision_model = None
_genai_configured = False


def _get_vision_model():
    """
    Lazy load vision model - only imports and configures Gemini when called.
    This prevents any API calls during module import.
    """
    global _vision_model, _genai_configured
    
    if _vision_model is None:
        # Only import when needed
        import google.generativeai as genai
        from PIL import Image  # Also lazy load PIL
        
        # Only configure once
        if not _genai_configured:
            genai.configure(api_key=Settings.GOOGLE_API_KEY)
            _genai_configured = True
            print("✅ Gemini API configured (lazy)")
        
        # Use gemini-2.5-flash for image analysis (latest working model)
        _vision_model = genai.GenerativeModel('gemini-2.5-flash')
        print("✅ Vision model loaded: gemini-2.5-flash")
    
    return _vision_model


def _load_image(image_path: str):
    """Lazy load PIL and open image."""
    from PIL import Image
    return Image.open(image_path)


def analyze_image_with_gemini(
    image_path: str,
    question: str,
    context: Optional[str] = None
) -> str:
    """
    Analyze an image using Google Gemini Pro Vision.
    """
    try:
        print(f"🔍 Using Gemini 2.5 Flash...")
        
        # Get model (lazy loaded)
        model = _get_vision_model()
        
        # Load image (lazy)
        img = _load_image(image_path)
        
        # Build comprehensive prompt for business data analysis
        prompt = f"""You are an expert business data analyst. Analyze this image in detail.

**Question:** {question}

**Instructions:**
1. Identify the chart type (bar, line, pie, etc.)
2. Extract ALL visible numbers, labels, and data points with EXACT values
3. List product names, categories, or dimensions
4. Describe axis labels, units, and scales
5. Provide insights and trends based on the data
6. Be extremely accurate with numbers - do NOT hallucinate

**Format your response with:**
- **CHART TYPE:** [type]
- **DATA POINTS:** [list all with exact values]
- **KEY INSIGHTS:** [analysis]"""

        if context:
            prompt += f"\n\n**Business Context for Reference:**\n{context[:500]}"
        
        # Generate analysis
        response = model.generate_content([prompt, img])
        analysis = response.text
        
        print(f"✅ Gemini 2.5 Flash response: {len(analysis)} chars")
        
        return analysis
        
    except Exception as e:
        error_msg = str(e)
        if "API_KEY_INVALID" in error_msg or "invalid" in error_msg.lower():
            raise Exception("Invalid Google API key. Please verify your GOOGLE_API_KEY.")
        elif "429" in error_msg or "quota" in error_msg.lower():
            print("❌ Quota exceeded for Google Gemini API.")
            return "⚠️ **Analysis Failed:** Google API daily quota exceeded. Please try again later or use a different API key."
        elif "404" in error_msg or "not found" in error_msg.lower():
            raise Exception(f"Model not found: {error_msg}")
        else:
            print(f"❌ Vision Error: {error_msg}")
            return f"⚠️ **Error:** {error_msg}"


def analyze_chart(image_path: str, data_context: Optional[str] = None) -> str:
    """Analyze business charts and graphs."""
    prompt = """Extract ALL data from this chart:
- Chart type and title
- All axis labels and values
- Every data point with EXACT numbers
- Key insights and trends
Be precise with numbers."""
    
    if data_context:
        prompt += f"\n\nBusiness Context: {data_context[:300]}"
    
    return analyze_image_with_gemini(image_path, prompt)


def analyze_invoice(image_path: str) -> str:
    """Extract invoice and receipt details."""
    prompt = """Extract ALL information from this invoice:
- Invoice number, date, company name
- All line items with quantities and prices
- Subtotal, tax, total amount
- Payment details
Be accurate with all numbers."""
    
    return analyze_image_with_gemini(image_path, prompt)


def analyze_screenshot(image_path: str, question: str, data_context: Optional[str] = None) -> str:
    """Analyze screenshots and dashboards."""
    prompt = f"""Analyze this image: {question}

Extract:
- All visible data, numbers, metrics
- Chart/table information
- Key insights

Be specific with exact values."""
    
    if data_context:
        prompt += f"\n\nContext: {data_context[:300]}"
    
    return analyze_image_with_gemini(image_path, prompt, data_context)


def analyze_image(image_path: str, question: str, context: Optional[str] = None) -> str:
    """
    Main function for image analysis - used by nodes.py vision_answer.
    Automatically detects image type and applies appropriate analysis.
    """
    question_lower = question.lower()
    
    # Detect analysis type from question
    if any(word in question_lower for word in ['invoice', 'receipt', 'bill']):
        return analyze_invoice(image_path)
    elif any(word in question_lower for word in ['chart', 'graph', 'plot', 'trend']):
        return analyze_chart(image_path, context)
    else:
        return analyze_image_with_gemini(image_path, question, context)
