import json
from typing import Dict, Any, Tuple
from core.llm import chat
from ml.god_level_automl import GodLevelAutoML
import pandas as pd
from api.v1.endpoints.charts import get_user_data

def handle_nl_pipeline(user_id: str, query: str, df: pd.DataFrame = None) -> Tuple[str, list]:
    """
    Translates a Natural Language query into an ML pipeline specification,
    then kicks off GodLevelAutoML training asynchronously (or synchronously for fast mode).
    
    Returns a markdown response detailing what was detected and started.
    """
    if df is None:
        try:
            df = get_user_data(user_id)
        except Exception:
            pass
            
    if df is None or df.empty:
        return "❌ I need a dataset to train a model. Please upload a dataset in the DataHub first.", ["NL Pipeline Agent"]
        
    columns = list(df.columns)
    sample_data = df.head(3).to_dict()
    
    prompt = f"""You are an expert Machine Learning Engineer.
The user wants to train a machine learning model based on this request:
"{query}"

The dataset has the following columns:
{columns}

Sample data (first 3 rows):
{sample_data}

Determine the optimal parameters to train a model. Output ONLY a valid JSON object:
{{
    "target_column": "The column to predict (must be one of the dataset columns)",
    "task_type": "classification or regression",
    "rationale": "Brief explanation of why you chose this target and task type"
}}
"""
    try:
        response = chat(prompt, temperature=0.1)
        response = response.strip()
        if '```json' in response:
            response = response.split('```json')[1].split('```')[0]
        elif '```' in response:
            response = response.split('```')[1].split('```')[0]
            
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            response = response[start:end]
            
        config = json.loads(response)
        target = config.get("target_column")
        task_type = config.get("task_type")
        rationale = config.get("rationale")
        
        if target not in columns:
            return f"❌ I couldn't find a suitable target column for your request. I tried to use '{target}', but it's not in the dataset.", ["NL Pipeline Agent"]
            
        # Initialize AutoML (we won't block the chat forever, we just return that it's running)
        # For MVP, we can run it synchronously if we limit the modes, or just start it.
        # But wait, GodLevelAutoML train takes a while. 
        # Actually, since this is chat, we can just run a Fast train and return results inline!
        
        message = (
            f"🚀 **ML Pipeline Initiated**\n\n"
            f"- **Goal**: {query}\n"
            f"- **Target Column**: `{target}`\n"
            f"- **Task Type**: {task_type.capitalize()}\n"
            f"- **Reasoning**: {rationale}\n\n"
            f"> Navigate to the **AutoML** page to view live training progress!"
        )
        
        # We can kick off training asynchronously using a background thread
        import threading
        
        def run_automl_bg():
            try:
                print(f"🚀 Starting background AutoML for {user_id}, target={target}")
                engine = GodLevelAutoML(user_id=user_id)
                # Just fast mode to be safe
                engine.train(
                    df=df,
                    target_column=target,
                    task_type=task_type,
                    modes=['traditional'], 
                    algorithms=['auto']
                )
                print(f"✅ Background AutoML complete for {user_id}")
            except Exception as e:
                print(f"❌ Background AutoML failed for {user_id}: {e}")
                
        thread = threading.Thread(target=run_automl_bg)
        thread.daemon = True
        thread.start()
        
        return message, ["NL Pipeline Agent"]
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"❌ Failed to parse ML pipeline requirements: {str(e)}", ["NL Pipeline Agent"]
