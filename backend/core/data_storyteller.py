import pandas as pd
import json
import logging
from core.llm import chat
from typing import Dict, Any

logger = logging.getLogger(__name__)

class DataStoryteller:
    """Generates AI-powered narrative data stories from datasets"""
    
    @staticmethod
    def generate_story(df: pd.DataFrame, dataset_name: str, topic: str = None) -> Dict[str, Any]:
        """
        Analyzes the dataset and generates a 4-5 slide presentation narrative.
        """
        # Take a sample of the data to send to the LLM
        sample = df.head(5).to_dict()
        describe = df.describe().to_dict()
        
        prompt = f"""You are an elite Data Storyteller and McKinsey consultant.
Analyze this dataset '{dataset_name}' and create a compelling narrative presentation.
Topic/Goal (if any): {topic or 'Discover the most interesting insights'}

DATASET PREVIEW:
{sample}

STATISTICAL SUMMARY:
{describe}

Create a structured JSON presentation with exactly 4-5 slides following this arc:
1. Executive Summary (The hook)
2. The Core Trend (The setup)
3. Deep Dive / Anomaly (The conflict/interesting part)
4. Strategic Recommendations (The resolution)

Ensure the output is ONLY valid JSON matching this schema:
{{
    "title": "Compelling Presentation Title",
    "subtitle": "A one-sentence summary",
    "slides": [
        {{
            "slide_number": 1,
            "title": "Slide Title",
            "narrative": "A paragraph of compelling narrative text.",
            "key_metric": "A bold metric (e.g., '+$45k' or '23% drop')",
            "suggested_chart": "bar|line|pie|scatter|none",
            "chart_x_column": "column_name for X axis (if applicable)",
            "chart_y_column": "column_name for Y axis (if applicable)"
        }}
    ]
}}
"""
        try:
            response = chat(prompt, temperature=0.7)
            response = response.strip()
            
            # Parse JSON
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]
                
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                response = response[start:end]
                
            story = json.loads(response)
            
            # Validate columns exist in the dataframe to prevent frontend crashes
            columns = set(df.columns)
            for slide in story.get("slides", []):
                x_col = slide.get("chart_x_column")
                y_col = slide.get("chart_y_column")
                if x_col and x_col not in columns:
                    slide["suggested_chart"] = "none"
                if y_col and y_col not in columns:
                    slide["suggested_chart"] = "none"
                    
            return story
            
        except Exception as e:
            logger.error(f"Failed to generate story: {e}")
            # Fallback story
            return {
                "title": f"Analysis of {dataset_name}",
                "subtitle": "Data Story unavailable due to processing error.",
                "slides": [
                    {
                        "slide_number": 1,
                        "title": "Error generating story",
                        "narrative": str(e),
                        "key_metric": "Error",
                        "suggested_chart": "none"
                    }
                ]
            }
