# MCP Vision OCR Module
"""
Vision and OCR tools for MCP integration.

Features:
- Text extraction from images
- Table detection and extraction
- Chart analysis and data extraction
- Document structure recognition
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import re
import json


@dataclass
class ExtractedTable:
    """Extracted table from image"""
    headers: List[str]
    rows: List[List[str]]
    confidence: float
    location: Dict[str, int]  # x, y, width, height


@dataclass
class ChartData:
    """Extracted data from chart"""
    chart_type: str
    title: Optional[str]
    x_axis_label: Optional[str]
    y_axis_label: Optional[str]
    data_points: List[Dict[str, Any]]
    legend: List[str]


def extract_text_from_image(
    image_path: str,
    language: str = "en"
) -> Dict:
    """
    Extract text from image using OCR.
    
    Args:
        image_path: Path to image file
        language: Language code for OCR
        
    Returns:
        Extracted text and metadata
    """
    try:
        # Try using Gemini Vision for OCR
        from core.vision import analyze_image_with_gemini
        
        prompt = """Extract ALL text from this image.
        
Output format:
- Return ONLY the text content
- Preserve the structure (headings, paragraphs, lists)
- Include any numbers, dates, and special characters
- If there are tables, format them as plain text with | separators"""
        
        result = analyze_image_with_gemini(image_path, prompt)
        
        if result and not result.startswith("⚠️"):
            return {
                "success": True,
                "text": result,
                "method": "gemini_vision",
                "language": language
            }
        
        # Fallback error
        return {
            "success": False,
            "error": result if result else "OCR extraction failed",
            "text": ""
        }
        
    except ImportError:
        return {
            "success": False,
            "error": "Vision module not available",
            "text": ""
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "text": ""
        }


def extract_tables_from_image(
    image_path: str,
    output_format: str = "json"
) -> Dict:
    """
    Extract tables from image.
    
    Args:
        image_path: Path to image file
        output_format: "json", "csv", or "markdown"
        
    Returns:
        Extracted tables
    """
    try:
        from core.vision import analyze_image_with_gemini
        
        prompt = """Analyze this image and extract ALL tables.

For each table found:
1. List the column headers
2. List all data rows
3. Preserve exact numbers and text

Return as JSON array:
[
  {
    "headers": ["Col1", "Col2", ...],
    "rows": [
      ["val1", "val2", ...],
      ...
    ]
  }
]

If no tables found, return: []"""
        
        result = analyze_image_with_gemini(image_path, prompt)
        
        if not result or result.startswith("⚠️"):
            return {
                "success": False,
                "error": result if result else "Table extraction failed",
                "tables": []
            }
        
        # Try to parse JSON from response
        tables = _parse_tables_from_response(result)
        
        # Convert to requested format
        if output_format == "csv":
            formatted_tables = [_table_to_csv(t) for t in tables]
        elif output_format == "markdown":
            formatted_tables = [_table_to_markdown(t) for t in tables]
        else:
            formatted_tables = tables
        
        return {
            "success": True,
            "tables": formatted_tables,
            "table_count": len(tables),
            "format": output_format
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "tables": []
        }


def _parse_tables_from_response(response: str) -> List[Dict]:
    """Parse table data from LLM response"""
    tables = []
    
    # Try to find JSON array in response
    json_pattern = r'\[\s*\{.*?\}\s*\]'
    matches = re.findall(json_pattern, response, re.DOTALL)
    
    for match in matches:
        try:
            parsed = json.loads(match)
            if isinstance(parsed, list):
                tables.extend(parsed)
            else:
                tables.append(parsed)
        except json.JSONDecodeError:
            continue
    
    # If no JSON found, try to parse markdown tables
    if not tables:
        tables = _parse_markdown_tables(response)
    
    return tables


def _parse_markdown_tables(text: str) -> List[Dict]:
    """Parse markdown-style tables from text"""
    tables = []
    
    # Find table blocks (lines with |)
    lines = text.split('\n')
    current_table = []
    
    for line in lines:
        if '|' in line:
            current_table.append(line)
        elif current_table:
            # End of table
            table = _parse_single_markdown_table(current_table)
            if table:
                tables.append(table)
            current_table = []
    
    # Handle last table
    if current_table:
        table = _parse_single_markdown_table(current_table)
        if table:
            tables.append(table)
    
    return tables


def _parse_single_markdown_table(lines: List[str]) -> Optional[Dict]:
    """Parse a single markdown table"""
    if len(lines) < 2:
        return None
    
    # Remove separator line (contains only |-:)
    content_lines = [l for l in lines if not re.match(r'^[\|\s\-:]+$', l)]
    
    if not content_lines:
        return None
    
    # Parse header
    headers = [cell.strip() for cell in content_lines[0].split('|') if cell.strip()]
    
    # Parse rows
    rows = []
    for line in content_lines[1:]:
        cells = [cell.strip() for cell in line.split('|') if cell.strip()]
        if cells:
            rows.append(cells)
    
    return {
        "headers": headers,
        "rows": rows
    }


def _table_to_csv(table: Dict) -> str:
    """Convert table dict to CSV string"""
    lines = []
    headers = table.get("headers", [])
    rows = table.get("rows", [])
    
    if headers:
        lines.append(','.join(f'"{h}"' for h in headers))
    
    for row in rows:
        lines.append(','.join(f'"{c}"' for c in row))
    
    return '\n'.join(lines)


def _table_to_markdown(table: Dict) -> str:
    """Convert table dict to markdown string"""
    lines = []
    headers = table.get("headers", [])
    rows = table.get("rows", [])
    
    if headers:
        lines.append('| ' + ' | '.join(headers) + ' |')
        lines.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')
    
    for row in rows:
        lines.append('| ' + ' | '.join(row) + ' |')
    
    return '\n'.join(lines)


def analyze_chart(
    image_path: str,
    chart_type: Optional[str] = None
) -> Dict:
    """
    Analyze chart image and extract data.
    
    Args:
        image_path: Path to chart image
        chart_type: Hint about chart type (bar, line, pie, etc.)
        
    Returns:
        Extracted chart data
    """
    try:
        from core.vision import analyze_image_with_gemini
        
        type_hint = f"This appears to be a {chart_type} chart." if chart_type else ""
        
        prompt = f"""Analyze this chart/graph image and extract ALL data.
{type_hint}

Identify and extract:
1. **Chart Type**: (bar, line, pie, scatter, etc.)
2. **Title**: (if visible)
3. **X-Axis Label**: and categories/values
4. **Y-Axis Label**: and scale
5. **Data Points**: Extract EVERY visible data point with exact values
6. **Legend**: (if present)

Return as JSON:
{{
  "chart_type": "...",
  "title": "...",
  "x_axis_label": "...",
  "y_axis_label": "...",
  "data_series": [
    {{
      "name": "Series Name",
      "data": [
        {{"x": "Category1", "y": 100}},
        {{"x": "Category2", "y": 200}}
      ]
    }}
  ],
  "legend": ["Series1", "Series2"]
}}

Be precise with all numbers. Do not estimate or approximate visible values."""
        
        result = analyze_image_with_gemini(image_path, prompt)
        
        if not result or result.startswith("⚠️"):
            return {
                "success": False,
                "error": result if result else "Chart analysis failed",
                "chart_data": None
            }
        
        # Try to parse JSON
        chart_data = _parse_chart_data(result)
        
        return {
            "success": True,
            "chart_data": chart_data,
            "raw_analysis": result
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "chart_data": None
        }


def _parse_chart_data(response: str) -> Dict:
    """Parse chart data from LLM response"""
    # Try to find JSON in response
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, response, re.DOTALL)
    
    for match in matches:
        try:
            parsed = json.loads(match)
            if "chart_type" in parsed or "data_series" in parsed:
                return parsed
        except json.JSONDecodeError:
            continue
    
    # If no JSON, return structured text
    return {
        "raw_text": response,
        "parsed": False
    }


def extract_document_structure(image_path: str) -> Dict:
    """
    Extract document structure from image.
    
    Args:
        image_path: Path to document image
        
    Returns:
        Document structure (headings, sections, etc.)
    """
    try:
        from core.vision import analyze_image_with_gemini
        
        prompt = """Analyze this document image and extract its structure.

Identify:
1. **Headings/Titles**: With their hierarchy levels (H1, H2, H3)
2. **Paragraphs**: Brief summary of each
3. **Lists**: Bullet or numbered items
4. **Tables**: If present
5. **Images/Figures**: If present
6. **Key Data Points**: Important numbers, dates, names

Return as JSON:
{
  "title": "Document Title",
  "sections": [
    {
      "heading": "Section Name",
      "level": 1,
      "content_summary": "Brief description",
      "has_table": false,
      "has_image": false
    }
  ],
  "key_data": [
    {"type": "date", "value": "2024-01-15"},
    {"type": "amount", "value": "$1,000"}
  ]
}"""
        
        result = analyze_image_with_gemini(image_path, prompt)
        
        if not result or result.startswith("⚠️"):
            return {
                "success": False,
                "error": result if result else "Structure extraction failed",
                "structure": None
            }
        
        # Try to parse JSON
        structure = _parse_document_structure(result)
        
        return {
            "success": True,
            "structure": structure,
            "raw_analysis": result
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "structure": None
        }


def _parse_document_structure(response: str) -> Dict:
    """Parse document structure from LLM response"""
    # Try to find JSON
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, response, re.DOTALL)
    
    for match in matches:
        try:
            parsed = json.loads(match)
            if "sections" in parsed or "title" in parsed:
                return parsed
        except json.JSONDecodeError:
            continue
    
    return {
        "raw_text": response,
        "parsed": False
    }


def vision_to_rag_context(
    image_path: str,
    question: str
) -> Dict:
    """
    Process image and prepare context for RAG pipeline.
    
    Args:
        image_path: Path to image
        question: User's question about the image
        
    Returns:
        Structured context for RAG
    """
    try:
        # Extract text
        text_result = extract_text_from_image(image_path)
        
        # Extract tables
        table_result = extract_tables_from_image(image_path, output_format="json")
        
        # Build context
        context_parts = []
        
        if text_result.get("success") and text_result.get("text"):
            context_parts.append(f"## Extracted Text\n{text_result['text']}")
        
        if table_result.get("success") and table_result.get("tables"):
            context_parts.append("## Extracted Tables")
            for i, table in enumerate(table_result["tables"]):
                md_table = _table_to_markdown(table)
                context_parts.append(f"### Table {i+1}\n{md_table}")
        
        context = "\n\n".join(context_parts) if context_parts else "No content extracted from image."
        
        return {
            "success": True,
            "context": context,
            "has_text": bool(text_result.get("text")),
            "table_count": len(table_result.get("tables", [])),
            "ready_for_rag": bool(context_parts)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "context": ""
        }
