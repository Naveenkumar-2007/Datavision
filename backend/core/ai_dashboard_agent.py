import pandas as pd
import json
import traceback
from typing import List, Dict

# Try to import the existing LLM chat function, if it exists in Datavision
try:
    from backend.utils.llm import chat
except ImportError:
    # Fallback to importing from core if that's where it is
    try:
        from core.llm import chat
    except ImportError:
        # We will assume 'chat' is globally available in real_dashboard or we mock it
        def chat(prompt, **kwargs):
            return ""

_schema_cache = {}

def build_dashboard_schema_agent(df: pd.DataFrame, domain: str, chat_func=None) -> Dict:
    """
    True AI Agent that designs the entire dashboard schema via LLM.
    Returns a list of ~24 chart specifications.
    """
    global _schema_cache
    
    # Fast cache return to support real-time data slicing/filtering
    cache_key = f"{domain}_{','.join(sorted(df.columns))}"
    if cache_key in _schema_cache:
        print("⚡ Skipping LLM Architect: Returning cached dashboard schema for filtered dataset.")
        return _schema_cache[cache_key]

    if chat_func is None:
        try:
            # We import the chat func from real_dashboard dynamically to avoid circular imports
            from core.real_dashboard import chat as chat_func
        except:
            pass

    columns = list(df.columns)
    dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
    
    # Get basic stats for numericals
    num_cols = df.select_dtypes(include=['number']).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    stats = {}
    for col in num_cols[:5]:  # Limit to avoid huge prompt
        stats[col] = {
            "min": float(df[col].min()) if not pd.isna(df[col].min()) else 0,
            "max": float(df[col].max()) if not pd.isna(df[col].max()) else 0,
            "mean": float(df[col].mean()) if not pd.isna(df[col].mean()) else 0
        }
        
    for col in cat_cols[:3]:
        stats[col] = {
            "unique_count": int(df[col].nunique()),
            "top_values": df[col].value_counts().head(3).index.tolist()
        }

    prompt = f"""
You are an expert Power BI / Tableau Dashboard Architect.
Your task is to design a highly dense, premium dashboard with exactly 20 unique charts for a {domain} dataset.

Dataset Schema:
Columns: {columns}
Data Types: {dtypes}
Sample Stats: {stats}

Available Chart Types: 
"stacked_bar", "grouped_bar", "line", "area", "horizontal_bar", "pie", "donut", "scatter", "bubble", "treemap", "heatmap", "waterfall", "funnel", "sunburst", "radar", "3d_scatter", "3d_surface", "3d_bubble", "polar_bar", "sankey", "choropleth", "violin", "bullet", "density_contour", "parallel_categories", "multi_sunburst", "hexbin"

CRITICAL INSTRUCTIONS:
1. Generate EXACTLY 20 charts.
2. Use a wide variety of chart types, prioritizing advanced data science visuals if the data fits (violin, density_contour, parallel_categories, hexbin, bullet, radar, 3d_surface, 3d_bubble, polar_bar, multi_sunburst).
3. The `x_column` and `y_column` MUST be EXACT strings from the Columns list provided above. You MUST provide BOTH x_column and y_column for EVERY chart.
4. For pie, donut, treemap, funnel, and waterfall: `x_column` is the category (Labels), and `y_column` is the numeric field to aggregate (Values).
5. For sankey and parallel_categories: `x_column` is Source Category, `y_column` is Target Category, and `color_by_column` is Value.
6. For 3d_scatter, 3d_surface, 3d_bubble: `x_column` is X, `y_column` is Y, and `color_by_column` is Z.
7. For choropleth: `x_column` MUST be a geographic location column (Country, State, City), `y_column` is the numeric value.
8. Ensure every chart uses logical column mappings based on the Data Types.
9. Architect a complete "Silicon Valley Premium" 'theme' for this dashboard based on the domain. Provide rich CSS gradients and glassmorphic colors.
    - `bg_gradient`: e.g., "linear-gradient(135deg, #0b1120 0%, #151e32 100%)"
    - `bg_pattern`: Select ONE of these 12 patterns based on domain: "grid", "dots", "mesh", "waves", "topography", "particles", "circuit", "honeycomb", "stripes", "boxes", "radial", "aurora"
    - `card_bg`: e.g., "rgba(20, 30, 50, 0.6)" (use rgba for glassmorphism)
    - `border_color`: e.g., "rgba(255,255,255,0.05)"
    - `text_primary` and `text_secondary`: Hex colors for text.
10. Respond ONLY with a valid JSON object containing exactly `theme` and `charts`. No markdown, no explanation.

JSON Format required:
{{
  "theme": {{
    "bg_gradient": "linear-gradient(to right, #000000, #1a1a1a)",
    "bg_pattern": "mesh",
    "card_bg": "rgba(25, 25, 25, 0.7)",
    "border_color": "rgba(255, 255, 255, 0.1)",
    "text_primary": "#ffffff",
    "text_secondary": "#a0a0a0",
    "chart_palette": ["#00ff00", "#ff0000", "#0000ff", "#ffff00", "#00ffff"]
  }},
  "charts": [
    {{
      "title": "Clear Business Title",
      "chart_type": "stacked_bar",
      "x_column": "exact_column_name_from_list",
      "y_column": "exact_column_name_from_list",
      "color_by_column": "exact_column_name_or_empty_string",
      "aggregation": "sum|mean|count"
    }}
  ]
}}
"""
    
    try:
        if chat_func:
            response = chat_func(prompt, temperature=0.3, max_tokens=2500)
        else:
            from core.real_dashboard import chat as fallback_chat
            response = fallback_chat(prompt, temperature=0.3, max_tokens=2500)
            
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:-3].strip()
        elif response.startswith('```'):
            response = response[3:-3].strip()
            
        schema = json.loads(response.strip())
        if isinstance(schema, dict) and "charts" in schema:
            _schema_cache[cache_key] = schema
            return schema
        elif isinstance(schema, list) and len(schema) > 0:
            # Handle legacy case where LLM just returns list
            final_schema = {
                "theme": {
                    "bg_gradient": "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
                    "bg_pattern": "mesh",
                    "card_bg": "rgba(30, 41, 59, 0.7)",
                    "border_color": "rgba(255, 255, 255, 0.1)",
                    "text_primary": "#f8fafc",
                    "text_secondary": "#94a3b8",
                    "chart_palette": ["#38bdf8", "#818cf8", "#c084fc", "#e879f9", "#22d3ee"]
                },
                "charts": schema
            }
            _schema_cache[cache_key] = final_schema
            return final_schema
    except Exception as e:
        print(f"AI Schema Agent failed: {e}")
        traceback.print_exc()
        
    # Fallback to a basic generated schema if LLM fails
    fallback_schema = []
    for i, num in enumerate(num_cols[:4]):
        for j, cat in enumerate(cat_cols[:3]):
            fallback_schema.append({
                "title": f"{num} by {cat}",
                "chart_type": "bar",
                "x_column": cat,
                "y_column": num,
                "color_by_column": "",
                "aggregation": "sum"
            })
            
    final_schema = {
        "theme": {
            "background_color": "#0b1120",
            "card_background": "#151e32",
            "border_color": "#2a3441",
            "text_color": "#f8fafc",
            "text_secondary": "#e2e8f0",
            "chart_palette": ["#38bdf8", "#818cf8", "#c084fc", "#e879f9", "#22d3ee"]
        },
        "charts": fallback_schema
    }
    _schema_cache[cache_key] = final_schema
    return final_schema
