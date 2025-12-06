"""
Google Gemini Vision Module for $50,000 AI Business Analyst Product
Provides enterprise-grade image analysis for charts, invoices, and documents.
"""

from typing import Optional
import google.generativeai as genai
from PIL import Image

# Configure Gemini API (hardcoded for reliability)
genai.configure(api_key="AIzaSyBkJlt3lCglsfs5N4lISJzt5RsSOiZk62g")


def analyze_image_with_gemini(
    image_path: str,
    question: str,
    context: Optional[str] = None
) -> str:
    """
    Analyze an image using Google Gemini 2.5 Flash (FREE).
    
    Args:
        image_path: Path to the image file
        question: User's question about the image
        context: Optional business context for better analysis
        
    Returns:
        Detailed analysis of the image
        
    Raises:
        Exception: If analysis fails
    """
    try:
        print(f"🔍 Using Google Gemini 2.5 Flash (FREE)...")
        
        # Initialize model
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        # Load image
        img = Image.open(image_path)
        
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
        elif "QUOTA" in error_msg or "quota" in error_msg.lower():
            raise Exception("Google API quota exceeded. Wait a few minutes or upgrade your plan.")
        elif "404" in error_msg or "not found" in error_msg.lower():
            raise Exception(f"Model not found: {error_msg}")
        else:
            raise Exception(f"Gemini Vision error: {error_msg}")


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
