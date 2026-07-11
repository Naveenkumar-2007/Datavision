import os
import uuid
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional
from core.llm import chat
import logging
import ast

logger = logging.getLogger(__name__)

# Ensure non-interactive backend for matplotlib
matplotlib.use('Agg')

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
CHARTS_DIR = os.path.join(STATIC_DIR, 'charts')
os.makedirs(CHARTS_DIR, exist_ok=True)

def generate_image_dashboard(query: str, df: pd.DataFrame) -> Optional[str]:
    """
    Generates a literal .png dashboard image using matplotlib and seaborn,
    driven by LLM code generation. Returns the markdown image link.
    """
    try:
        # Limit rows to 100 for code execution context to keep it fast
        sample_df = df.head(100)
        
        # Save temp CSV for the generated code to read safely
        temp_csv_path = os.path.join(CHARTS_DIR, f"temp_{uuid.uuid4().hex}.csv")
        # Replace backslashes for python code block
        temp_csv_path_safe = temp_csv_path.replace("\\", "/")
        sample_df.to_csv(temp_csv_path, index=False)
        
        # Output PNG path
        img_id = uuid.uuid4().hex
        img_filename = f"dashboard_{img_id}.png"
        img_filepath = os.path.join(CHARTS_DIR, img_filename)
        img_filepath_safe = img_filepath.replace("\\", "/")
        
        # Prompt LLM to write ONLY pure Python code
        prompt = f"""You are a Silicon Valley Data Engineer. 
The user wants an image dashboard for this query: "{query}"

Write Python code using `matplotlib.pyplot` and `seaborn` to generate a beautiful, dark-mode data visualization.
The data is available at this local path: `{temp_csv_path_safe}`
The output image MUST be saved to: `{img_filepath_safe}`

RULES:
1. ONLY output valid Python code. NO markdown formatting, NO explanations.
2. Use dark mode aesthetics: `plt.style.use('dark_background')` and sleek colors (cyan, purple, etc.).
3. Handle missing values natively.
4. Call `plt.savefig('{img_filepath_safe}', bbox_inches='tight', dpi=150, facecolor='#111827')` at the end.
5. Call `plt.close('all')` at the very end.
6. Make it look like a premium dashboard.

Data Summary:
Columns: {list(df.columns)}
Shape: {df.shape}
Sample Data:
{df.head(3).to_string()}
"""

        # Generate code
        response = chat(prompt, temperature=0.1, max_tokens=2000)
        
        # Clean response
        code = response.strip()
        if '```python' in code:
            code = code.split('```python')[1].split('```')[0]
        elif '```' in code:
            code = code.split('```')[1].split('```')[0]
            
        code = code.strip()
        
        # Execute the code safely in this sandbox context
        local_vars = {}
        global_vars = {
            'pd': pd, 
            'plt': plt, 
            'sns': sns, 
            '__builtins__': __builtins__
        }
        
        try:
            exec(code, global_vars, local_vars)
        except Exception as exec_err:
            logger.error(f"Image Agent code execution failed: {exec_err}")
            return f"\n\n> [!WARNING]\n> **Image Generation Failed**\n> The AI made a syntax error while drawing the chart: `{exec_err}`\n\n"
        
        
        # Check if the image was actually created
        if os.path.exists(img_filepath):
            # Clean up temp csv
            if os.path.exists(temp_csv_path):
                os.remove(temp_csv_path)
                
            return f"\n\n![Dashboard Visualization](/static/charts/{img_filename})\n\n"
        else:
            logger.error("Image Agent code executed but no image was saved.")
            return f"\n\n> [!WARNING]\n> **Image Generation Failed**\n> The AI executed successfully but failed to save the image file to `{img_filepath}`.\n\n"
            
    except Exception as e:
        logger.error(f"Image Agent failed: {e}")
        return f"\n\n> [!WARNING]\n> **Image Generation Failed**\n> An unexpected error occurred: `{e}`\n\n"
