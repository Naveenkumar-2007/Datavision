"""
VISION ENGINE - Image & Document Understanding
===============================================

Power: See and understand images, charts, documents.

Features:
- Image Analysis: Understand uploaded images
- OCR Extraction: Extract text from documents
- Chart Reading: Analyze existing charts/graphs
- Table Detection: Extract tables from images

This mode processes VISUAL content.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import base64

from core.llm import chat
from config.settings import Settings

logger = logging.getLogger(__name__)


class VisionEngine:
    """
    🔭 ENHANCED VISION ENGINE - See, Understand & Extract
    
    💡 WHEN TO USE:
    - 📊 Chart/Graph Analysis: Extract data from existing charts
    - 📄 Document OCR: Extract text from images of documents
    - 📋 Table Extraction: Pull tabular data from images
    - 🖼️ Image Understanding: Describe and analyze visual content
    - 📈 Pattern Recognition: Identify trends in visual data
    
    This mode processes VISUAL content and extracts structured data!
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
    
    async def process(
        self,
        query: str,
        image_path: str = None,
        image_base64: str = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Process an image with enhanced vision analysis.
        
        1. Image type detection (chart, document, photo)
        2. Specialized extraction based on type
        3. Structured data output
        4. Pattern recognition
        """
        
        start_time = datetime.now()
        logger.info(f"🔭 VISION ENGINE (Enhanced): Processing '{query[:50]}...'")
        
        has_image = bool(image_path or image_base64)
        
        if not has_image:
            return self._no_image_response()
        
        # Detect image type from query
        image_type = self._detect_image_type(query)
        logger.info(f"🖼️ Detected image type: {image_type}")
        
        # Process with Gemini Vision
        try:
            import google.generativeai as genai
            import os
            
            api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            
            if not api_key:
                return {
                    "answer": "Vision requires GEMINI_API_KEY. Please set it in .env",
                    "mode": "vision",
                    "has_image": True,
                    "error": "No API key"
                }
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Load image
            import PIL.Image
            if image_path:
                img = PIL.Image.open(image_path)
            elif image_base64:
                import io
                image_data = base64.b64decode(image_base64)
                img = PIL.Image.open(io.BytesIO(image_data))
            
            # Get specialized prompt based on image type
            vision_prompt = self._get_specialized_prompt(query, image_type)
            
            response = model.generate_content([vision_prompt, img])
            answer = response.text
            
            # Format response with structured output
            formatted = self._format_response(answer, image_type, query)
            
            # Extract any data found
            extracted_data = self._extract_structured_data(answer, image_type)

        except ImportError:
            formatted = "Vision mode requires google-generativeai package. Install with: pip install google-generativeai"
            extracted_data = None
        except Exception as e:
            logger.error(f"Vision error: {e}")
            formatted = f"Vision analysis error: {str(e)}"
            extracted_data = None
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        result = {
            "answer": formatted,
            "mode": "vision",
            "has_image": True,
            "image_type": image_type,
            "execution_time": f"{execution_time:.2f}s",
            "features_used": self._get_features_used(image_type),
            "sources": ["Vision AI", "Image Analysis"]
        }
        
        if extracted_data:
            result["extracted_data"] = extracted_data
        
        return result
    
    def _detect_image_type(self, query: str) -> str:
        """Detect what type of image analysis is needed"""
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in ['chart', 'graph', 'plot', 'trend', 'bar', 'pie', 'line']):
            return 'chart'
        elif any(kw in query_lower for kw in ['table', 'data', 'rows', 'columns', 'excel', 'spreadsheet']):
            return 'table'
        elif any(kw in query_lower for kw in ['document', 'text', 'ocr', 'read', 'pdf', 'letter']):
            return 'document'
        elif any(kw in query_lower for kw in ['diagram', 'flowchart', 'architecture', 'schema']):
            return 'diagram'
        else:
            return 'general'
    
    def _get_specialized_prompt(self, query: str, image_type: str) -> str:
        """Get specialized extraction prompt based on image type"""
        
        base_rules = """
⚠️ STRICT RULES:
1. ONLY describe what is ACTUALLY VISIBLE in the image
2. NEVER make up numbers or data not shown
3. If something is unclear, say "unclear in image"
4. Extract EXACT values when possible"""
        
        prompts = {
            'chart': f"""📊 CHART ANALYSIS MODE
{base_rules}

User's question: {query}

Analyze this chart/graph and extract:

## 📈 Chart Type
[Bar/Line/Pie/Scatter/Other]

## 🏷️ Title & Labels
- Title: [exact title if visible]
- X-Axis: [label]
- Y-Axis: [label]
- Legend: [categories]

## 📊 Data Points
Extract ALL visible data values in a table:
| Category/X | Value |
|------------|-------|
| [exact]    | [number] |

## 📉 Trends & Patterns
[What patterns do you see? Increasing/Decreasing/Stable?]

## 🎯 Key Insights
[Answer the user's specific question]""",

            'table': f"""📋 TABLE EXTRACTION MODE
{base_rules}

User's question: {query}

Extract the table data:

## 📊 Table Structure
- Rows: [count]
- Columns: [count]
- Headers: [list column names]

## 📝 Extracted Data
| Col1 | Col2 | Col3 | ... |
|------|------|------|-----|
| ...  | ...  | ...  | ... |

## 🔍 Data Quality
- Missing values: [yes/no, where]
- Data types: [text/numbers/dates]

## 🎯 Answer to Query
[Specific answer based on table content]""",

            'document': f"""📄 DOCUMENT OCR MODE
{base_rules}

User's question: {query}

Extract text from this document:

## 📝 Full Text Extraction
[Extract ALL readable text, preserving structure]

## 📋 Key Sections
[Identify main sections/headings]

## 📊 Any Numbers/Data
[List any numerical data found]

## 🎯 Answer to Query
[Address the user's question]""",

            'diagram': f"""🔗 DIAGRAM ANALYSIS MODE
{base_rules}

User's question: {query}

Analyze this diagram:

## 🏗️ Diagram Type
[Flowchart/Architecture/Process/Organizational/Other]

## 📦 Components
[List all boxes/nodes visible]

## 🔗 Connections
[Describe the relationships/arrows]

## 📊 Flow/Hierarchy
[Describe the overall structure]

## 🎯 Answer to Query
[Address the user's question]""",

            'general': f"""🖼️ IMAGE ANALYSIS MODE
{base_rules}

User's question: {query}

Analyze this image:

## 👁️ What You See
[Describe the main content]

## 📊 Any Data/Text
[Extract any numbers, text, or data visible]

## 🎯 Answer to Query
[Specifically address the user's question]

## 💡 Additional Observations
[Any other relevant details]"""
        }
        
        return prompts.get(image_type, prompts['general'])
    
    def _format_response(self, answer: str, image_type: str, query: str) -> str:
        """Format the response with proper structure"""
        
        type_emoji = {
            'chart': '📊',
            'table': '📋',
            'document': '📄',
            'diagram': '🔗',
            'general': '🖼️'
        }
        
        emoji = type_emoji.get(image_type, '👁️')
        type_name = image_type.title()
        
        return f"""{emoji} **Vision Analysis - {type_name} Mode**

{answer}

---
🔭 *Enhanced Vision AI | {type_name} Extraction Mode*
📸 *Analyzed with Gemini Vision*"""
    
    def _extract_structured_data(self, answer: str, image_type: str) -> Optional[Dict]:
        """Attempt to extract structured data from the response"""
        try:
            # Look for table-like data in the response
            if '|' in answer:
                lines = answer.split('\n')
                table_lines = [l for l in lines if '|' in l and '--' not in l]
                if len(table_lines) > 1:
                    return {
                        "type": "table",
                        "rows": len(table_lines),
                        "format": "markdown"
                    }
            return None
        except:
            return None
    
    def _get_features_used(self, image_type: str) -> List[str]:
        """Get list of features used based on image type"""
        base = ["Gemini Vision", "Image Analysis"]
        
        type_features = {
            'chart': ["Chart Recognition", "Data Extraction", "Trend Detection"],
            'table': ["Table OCR", "Data Extraction", "Structure Recognition"],
            'document': ["OCR", "Text Extraction", "Document Structure"],
            'diagram': ["Diagram Analysis", "Component Detection", "Flow Recognition"],
            'general': ["Visual Understanding", "Content Description"]
        }
        
        return base + type_features.get(image_type, [])
    
    def _no_image_response(self) -> Dict[str, Any]:
        """Response when no image is provided"""
        response = """🔭 **Enhanced Vision Mode Ready**

I can analyze images with specialized extraction! Choose what to analyze:

| Mode | What I Do | Best For |
|------|-----------|----------|
| 📊 **Chart** | Extract data from charts | Bar, line, pie graphs |
| 📋 **Table** | OCR tabular data | Spreadsheet screenshots |
| 📄 **Document** | Extract all text | PDFs, letters, docs |
| 🔗 **Diagram** | Map structure | Flowcharts, architecture |
| 🖼️ **General** | Describe content | Any image |

**How to use:**
1. 📸 **Paste** an image (Ctrl+V)
2. 📎 **Attach** a file (click +)
3. 🖼️ **Drag & drop** an image
4. Ask your question about it

**Ready!** Paste or attach an image to analyze."""

        return {
            "answer": response,
            "mode": "vision",
            "has_image": False,
            "execution_time": "0.1s",
            "features_used": ["Vision AI Ready"],
            "sources": []
        }


async def vision_response(
    user_id: str,
    query: str,
    image_path: str = None,
    image_base64: str = None
) -> Dict[str, Any]:
    """Quick function for vision response"""
    engine = VisionEngine(user_id)
    return await engine.process(query, image_path, image_base64)


def vision_response_sync(
    user_id: str,
    query: str,
    image_path: str = None
) -> str:
    """Synchronous vision response"""
    
    if not image_path:
        return """👁️ **Vision Mode Ready**

Paste or attach an image to analyze. I can:
- Read charts and extract data
- OCR documents and images
- Analyze visual content"""
    
    try:
        import google.generativeai as genai
        import os
        import PIL.Image
        
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return "Vision requires GEMINI_API_KEY."
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        img = PIL.Image.open(image_path)
        
        response = model.generate_content([query, img])
        return f"👁️ **Vision Analysis**\n\n{response.text}"
        
    except Exception as e:
        return f"Vision error: {str(e)}"
