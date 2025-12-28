"""
LLM Visual Strategist - AI-Powered Visualization Strategy
=========================================================
Uses Groq LLM (FREE API) to decide visualization strategy.

NO HARDCODING in prompts - everything comes from DeepDataProfiler.

The LLM receives REAL data intelligence and makes decisions:
- How many visuals to create
- What chart types to use
- Colors and emotions
- Layout strategy

Every decision is justified and data-driven.
"""

import os
import json
from typing import Dict, Any
from groq import Groq


class LLMVisualStrategist:
    """
    Uses AI (Groq Mixtral) to generate visualization strategy.
    Completely autonomous - no predefined rules.
    """
    
    def __init__(self):
        # Use FREE Groq API
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment")
        
        self.client = Groq(api_key=api_key)
        self.model = "mixtral-8x7b-32768"  # FREE, fast, intelligent
    
    def generate_strategy(self, df_summary: Dict, intelligence: Dict, mode: str) -> Dict[str, Any]:
        """
        Ask LLM to create visualization strategy based on REAL data analysis.
        
        Args:
            df_summary: DataFrame metadata (rows, columns, types)
            intelligence: DeepDataProfiler output (patterns, insights, relationships)
            mode: 'overview' or 'dashboard'
        
        Returns:
            Strategy dict with visual_count, chart types,colors, layout
        """
        # Build prompt dynamically from REAL data (NO HARDCODING!)
        prompt = self._build_dynamic_prompt(df_summary, intelligence, mode)
        
        print(f"\n{'='*60}")
        print(f"🤖 Asking LLM for {mode} strategy...")
        print(f"{'='*60}")
        print(f"Data Story: {intelligence['data_story'][:100]}...")
        print(f"Insights Found: {len(intelligence['insights'])}")
        print(f"{'='*60}\n")
        
        # Call LLM
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a world-class data visualization expert. Analyze data and suggest the MOST IMPACTFUL visualizations. Be creative and intelligent."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,  # Some creativity
                max_tokens=2000
            )
            
            # Parse LLM response
            llm_output = response.choices[0].message.content
            
            print(f"🎯 LLM Response:")
            print(f"{llm_output[:500]}...")
            print(f"\n{'='*60}\n")
            
            # Try to parse as JSON
            try:
                strategy = json.loads(llm_output)
            except:
                # If not JSON, extract manually
                strategy = self._extract_strategy_from_text(llm_output)
            
            # Validate and ensure required fields
            strategy = self._validate_strategy(strategy, intelligence, mode)
            
            return strategy
            
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            # Fallback to behavior-based strategy (current system)
            return self._fallback_strategy(df_summary,intelligence, mode)
    
    def _build_dynamic_prompt(self, df_summary: Dict, intelligence: Dict, mode: str) -> str:
        """
        Build prompt from REAL data analysis.
        NO TEMPLATES - adapts to what was actually found in the data.
        """
        # Extract REAL insights (not hardcoded!)
        insights_text = "\n".join([
            f"- {insight['insight']} (importance: {insight['importance']:.2f})"
            for insight in intelligence['insights'][:10]  # Top 10
        ])
        
        # Extract REAL patterns (discovered, not predicted!)
        patterns_text = ""
        if 'temporal' in intelligence.get('patterns', {}):
            patterns_text += "\nTemporal Patterns Found:\n"
            for pattern in intelligence['patterns']['temporal'][:5]:
                patterns_text += f"- {pattern['description']}\n"
        
        if 'categorical' in intelligence.get('patterns', {}):
            patterns_text += "\nCategorical Patterns Found:\n"
            for pattern in intelligence['patterns']['categorical'][:5]:
                patterns_text += f"- {pattern['description']}\n"
        
        # Extract REAL relationships
        relationships_text = ""
        if intelligence.get('relationships', {}).get('strong'):
            relationships_text = "\nStrong Correlations:\n"
            for rel in intelligence['relationships']['strong'][:5]:
                relationships_text += f"- {rel['description']}\n"
        
        # Extract REAL anomalies
        anomalies_text = ""
        if intelligence.get('anomalies'):
            anomalies_text = "\nAnomalies Detected:\n"
            for anomaly in intelligence['anomalies'][:5]:
                anomalies_text += f"- {anomaly['description']}\n"
        
        # Build dynamic prompt (changes based on data!)
        prompt = f"""
You are designing visualizations for {'an executive overview' if mode=='overview' else 'a detailed dashboard'}.

DATASET CHARACTERISTICS:
- Rows: {df_summary['row_count']}
- Columns: {df_summary['dimension_count']}
- Numeric columns: {', '.join(intelligence['columns']['numeric'][:10])}
- Categorical columns: {', '.join(intelligence['columns']['categorical'][:5])}
- Temporal columns: {', '.join(intelligence['columns']['datetime'])}

DATA STORY:
{intelligence['data_story']}

KEY INSIGHTS (data-driven, NOT assumptions):
{insights_text}

{patterns_text}

{relationships_text}

{anomalies_text}

TASK:
Design the MOST IMPACTFUL visualization strategy for {mode} mode.

For OVERVIEW: Focus on narrative, 5-10 visuals, tell the data story clearly.
For DASHBOARD: Be comprehensive, 10-25 visuals, enable exploration.

Decide:
1. How many visuals to create? (base on insight count and complexity)
2. What chart type for each visual? (choose from: area, line, bar, scatter, pie, radial_bar, treemap, heatmap, network, sankey, bubble, waterfall, funnel)
3. What color emotion? (e.g., growth, trust, urgency, calm)
4. Layout strategy? (hierarchical, grid, organic_flow)

Respond ONLY with valid JSON (no markdown):
{{
    "visual_count": <number 5-25>,
    "reasoning": "<why this count?>",
    "visuals": [
        {{
            "chart_type": "<type>",
            "data_focus": "<which insight this shows>",
            "priority": <0.0-1.0>,
            "rationale": "<why this chart type?>"
        }}
    ],
    "color_emotion": "<emotion>",
    "layout_strategy": "<strategy>"
}}
"""
        return prompt
    
    def _extract_strategy_from_text(self, text: str) -> Dict:
        """Extract strategy if LLM didn't return pure JSON."""
        # Try to find JSON in text
        import re
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        
        # Minimal fallback
        return {
            "visual_count": 10,
            "reasoning": "LLM response parsing failed",
            "visuals": [],
            "color_emotion": "professional",
            "layout_strategy": "grid"
        }
    
    def _validate_strategy(self, strategy: Dict, intelligence: Dict, mode: str) -> Dict:
        """Ensure strategy has all required fields."""
        # Ensure visual_count is reasonable
        if 'visual_count' not in strategy:
            # Calculate from insights
            insight_count = len(intelligence['insights'])
            strategy['visual_count'] = min(max(5, insight_count), 25)
        
        # Ensure within bounds
        strategy['visual_count'] = max(5, min(strategy['visual_count'], 30))
        
        # Ensure other fields exist
        strategy.setdefault('reasoning', 'Data-driven strategy')
        strategy.setdefault('visuals', [])
        strategy.setdefault('color_emotion', 'professional')
        strategy.setdefault('layout_strategy', 'grid')
        
        return strategy
    
    def _fallback_strategy(self, df_summary: Dict, intelligence: Dict, mode: str) -> Dict:
        """
        Fallback if LLM fails.
        Still behavior-driven (current system), not random.
        """
        insight_count = len(intelligence['insights'])
        
        if mode == 'overview':
            visual_count = min(max(5, insight_count // 2), 10)
        else:
            visual_count = min(max(10, insight_count), 25)
        
        return {
            "visual_count": visual_count,
            "reasoning": "Fallback: Based on insight count",
            "visuals": [],
            "color_emotion": "professional",
            "layout_strategy": "grid"
        }
