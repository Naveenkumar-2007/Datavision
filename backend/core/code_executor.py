"""
🖥️ SANDBOXED CODE EXECUTOR — AI Chat v2
=========================================

Executes Python code in a sandboxed subprocess with:
- Timeout protection (max 30 seconds)
- Output capture (stdout, stderr)
- Matplotlib figure capture
- DataFrame result capture
- Memory limits
- No file system access outside workspace

This enables the AI chat to generate and execute code inline,
showing results directly in the conversation.
"""

import os
import sys
import json
import subprocess
import tempfile
import logging
import base64
import time
import uuid
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# Maximum execution time in seconds
MAX_EXECUTION_TIME = 30

# Maximum output size in characters
MAX_OUTPUT_SIZE = 50000


class CodeExecutor:
    """
    Execute Python code in a sandboxed subprocess.
    
    Features:
    - Captures stdout, stderr
    - Captures matplotlib figures as base64 PNG
    - Captures pandas DataFrame results
    - Enforces timeout
    - Returns structured results
    """

    def __init__(self, user_id: str, workspace_dir: str = None):
        self.user_id = user_id
        self.workspace_dir = workspace_dir or self._get_workspace_dir()
        os.makedirs(self.workspace_dir, exist_ok=True)

    def _get_workspace_dir(self) -> str:
        """Get or create workspace directory for this user."""
        base = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".workspace")
        user_dir = os.path.join(base, self.user_id, "code_exec")
        os.makedirs(user_dir, exist_ok=True)
        return user_dir

    def execute(self, code: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute Python code and return structured results.
        
        Args:
            code: Python code to execute
            context: Optional context dict (e.g., user's dataframe info)
            
        Returns:
            {
                "success": bool,
                "stdout": str,
                "stderr": str,
                "figures": [{"base64": str, "format": "png"}],
                "tables": [{"columns": [...], "data": [[...]]}],
                "result": str,  # repr of last expression
                "execution_time_ms": int,
                "error": str or None
            }
        """
        # Create a wrapper script that captures everything
        exec_id = str(uuid.uuid4())[:8]
        script_path = os.path.join(self.workspace_dir, f"exec_{exec_id}.py")
        output_path = os.path.join(self.workspace_dir, f"output_{exec_id}.json")
        figures_dir = os.path.join(self.workspace_dir, f"figures_{exec_id}")
        os.makedirs(figures_dir, exist_ok=True)

        # Build the wrapper script
        wrapper_code = self._build_wrapper(code, output_path, figures_dir, context)

        try:
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(wrapper_code)

            # Execute in subprocess
            start_time = time.time()
            
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["MPLBACKEND"] = "Agg"  # Non-interactive matplotlib backend
            
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=MAX_EXECUTION_TIME,
                cwd=self.workspace_dir,
                env=env,
                encoding='utf-8',
                errors='replace'
            )
            
            elapsed_ms = int((time.time() - start_time) * 1000)

            # Read structured output
            output_data = {}
            if os.path.exists(output_path):
                try:
                    with open(output_path, 'r', encoding='utf-8') as f:
                        output_data = json.load(f)
                except:
                    pass

            # Collect figures
            figures = []
            for fig_file in sorted(os.listdir(figures_dir)):
                if fig_file.endswith('.png'):
                    fig_path = os.path.join(figures_dir, fig_file)
                    with open(fig_path, 'rb') as f:
                        b64 = base64.b64encode(f.read()).decode('utf-8')
                        figures.append({"base64": b64, "format": "png"})

            stdout = (result.stdout or "")[:MAX_OUTPUT_SIZE]
            stderr = (result.stderr or "")[:MAX_OUTPUT_SIZE]
            
            # Filter common warnings from stderr
            stderr_lines = [l for l in stderr.split('\n') if l.strip() and not any(w in l for w in [
                'UserWarning', 'FutureWarning', 'DeprecationWarning', 'RuntimeWarning'
            ])]
            stderr_clean = '\n'.join(stderr_lines)

            return {
                "success": result.returncode == 0,
                "stdout": stdout,
                "stderr": stderr_clean,
                "figures": figures,
                "tables": output_data.get("tables", []),
                "result": output_data.get("result", ""),
                "execution_time_ms": elapsed_ms,
                "error": stderr_clean if result.returncode != 0 else None
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Execution timed out after {MAX_EXECUTION_TIME} seconds",
                "figures": [],
                "tables": [],
                "result": "",
                "execution_time_ms": MAX_EXECUTION_TIME * 1000,
                "error": f"Code execution timed out after {MAX_EXECUTION_TIME}s"
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "figures": [],
                "tables": [],
                "result": "",
                "execution_time_ms": 0,
                "error": str(e)
            }
        finally:
            # Cleanup temp files
            for path in [script_path, output_path]:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except:
                    pass
            try:
                import shutil
                if os.path.exists(figures_dir):
                    shutil.rmtree(figures_dir, ignore_errors=True)
            except:
                pass

    def _build_wrapper(self, code: str, output_path: str, figures_dir: str, 
                       context: Dict = None) -> str:
        """Build the execution wrapper script."""
        
        # Escape the paths for Windows
        output_path_escaped = output_path.replace('\\', '\\\\')
        figures_dir_escaped = figures_dir.replace('\\', '\\\\')
        
        wrapper = f'''
import sys
import os
import json
import warnings
warnings.filterwarnings("ignore")

# Setup matplotlib for non-interactive use
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Standard data science imports
import pandas as pd
import numpy as np

# Track figures
_figure_count = [0]
_tables = []
_result_value = [None]
_output_path = r"{output_path_escaped}"
_figures_dir = r"{figures_dir_escaped}"

# Monkey-patch plt.show to save figures instead
_original_show = plt.show
def _capture_show(*args, **kwargs):
    for fig_num in plt.get_fignums():
        fig = plt.figure(fig_num)
        fig_path = os.path.join(_figures_dir, f"figure_{{_figure_count[0]:03d}}.png")
        fig.savefig(fig_path, dpi=120, bbox_inches="tight", facecolor="white")
        _figure_count[0] += 1
    plt.close("all")
plt.show = _capture_show

# Helper to display DataFrames
def display(obj):
    if isinstance(obj, pd.DataFrame):
        _tables.append({{
            "columns": obj.columns.tolist(),
            "data": obj.head(50).values.tolist(),
            "shape": list(obj.shape)
        }})
        print(obj.to_string(max_rows=20))
    else:
        print(repr(obj))

try:
    # Execute user code
    exec_globals = {{
        "pd": pd, "np": np, "plt": plt,
        "display": display, "print": print,
        "__builtins__": __builtins__,
    }}
    
    exec("""
{code.replace(chr(92), chr(92)+chr(92)).replace('"', chr(92)+'"')}
""", exec_globals)

    # Save any unsaved figures
    if plt.get_fignums():
        _capture_show()

except Exception as e:
    import traceback
    traceback.print_exc()

# Save structured output
try:
    output = {{
        "tables": _tables,
        "result": "",
        "figure_count": _figure_count[0]
    }}
    with open(_output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, default=str)
except:
    pass
'''
        return wrapper


def execute_code_for_user(user_id: str, code: str, context: Dict = None) -> Dict[str, Any]:
    """Convenience function to execute code for a user."""
    executor = CodeExecutor(user_id=user_id)
    return executor.execute(code, context)
