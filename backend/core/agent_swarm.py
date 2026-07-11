import json
import logging
import asyncio
from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime

from core.llm import chat
from core.autonomous_data_ops import AutonomousDataOps
from api.v1.endpoints.charts import get_user_data, _set_cached_df

logger = logging.getLogger(__name__)

class CollaborationSwarm:
    """
    Agent Swarm for the Collaboration Hub.
    Routes intents and performs data analysis or data cleaning (autofix) in real-time.
    """
    
    def __init__(self):
        self.data_agent = AutonomousDataOps()
        
    def _get_context(self, user_id: str) -> Optional[pd.DataFrame]:
        df = get_user_data(user_id)
        if df is None or df.empty:
            return None
        return df

    async def process_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Process an @ai message and return an insight dictionary.
        """
        df = self._get_context(user_id)
        
        if df is None:
            return {
                "id": str(int(datetime.now().timestamp() * 1000) + 1),
                "user": "DataVision AI",
                "avatar": "✨",
                "message": "I don't see any uploaded data yet. Please upload a dataset in the Data Hub first, then I can analyze it for you!",
                "time": "Just now",
                "isAi": True,
            }

        source_file = df['_source_file'].iloc[0] if '_source_file' in df.columns else "your data"
        
        # Simple Intent Routing
        msg_lower = message.lower()
        if "autofix" in msg_lower or "clean" in msg_lower or "fix" in msg_lower:
            return await self._run_autofix_agent(user_id, df, source_file)
        else:
            return await self._run_data_analyst_agent(user_id, df, source_file, message)
            
    async def _run_autofix_agent(self, user_id: str, df: pd.DataFrame, source_file: str) -> Dict[str, Any]:
        """Run the Data Engineer / Autofix Agent"""
        try:
            logger.info("Triggering Autofix Agent...")
            fixed_df, report = self.data_agent.auto_fix(df)
            
            # Save the fixed dataframe back to the user cache
            _set_cached_df(user_id, fixed_df)
            
            # Construct a rich response
            message = f"✅ **Autofix Complete for {source_file}**\n\n"
            message += f"I analyzed {report.original_rows} rows and {report.original_cols} columns. Here is what I fixed:\n"
            
            if report.fixes_applied:
                for fix in report.fixes_applied[:5]:
                    message += f"- {fix.action_taken}: {fix.details}\n"
                if len(report.fixes_applied) > 5:
                    message += f"- ...and {len(report.fixes_applied) - 5} more fixes.\n"
            else:
                message += "- The data was already clean! No major fixes were needed.\n"
                
            if report.enrichments_added:
                message += "\n**Enrichments Added:**\n"
                for enr in report.enrichments_added:
                    message += f"- {enr}\n"
                    
            message += f"\nQuality Score improved to **{report.quality_score_after}/100**."
            
            return {
                "id": str(int(datetime.now().timestamp() * 1000) + 1),
                "user": "Autofix Agent",
                "avatar": "🛠️",
                "message": message,
                "time": "Just now",
                "isAi": True,
            }
        except Exception as e:
            logger.error(f"Autofix Agent error: {e}")
            return {
                "id": str(int(datetime.now().timestamp() * 1000) + 1),
                "user": "Autofix Agent",
                "avatar": "🛠️",
                "message": f"I encountered an issue while trying to autofix your data: {e}",
                "time": "Just now",
                "isAi": True,
            }
            
    async def _run_data_analyst_agent(self, user_id: str, df: pd.DataFrame, source_file: str, query: str) -> Dict[str, Any]:
        """Run the Data Analyst Agent using the LLM orchestrator"""
        try:
            # Prepare data context for LLM
            import numpy as np
            numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns if not c.startswith('_')]
            categorical_cols = [c for c in df.select_dtypes(include=['object', 'category']).columns if not c.startswith('_')]
            
            sample_data = df.head(3).to_markdown()
            
            context = f"""
You are the Data Analyst Agent in a Collaboration Hub swarm.
The user is asking a question about their dataset.

Dataset Context:
- Source File: {source_file}
- Total Rows: {len(df)}
- Numeric Columns: {numeric_cols}
- Categorical Columns: {categorical_cols}

Sample Data (first 3 rows):
{sample_data}

Answer the user's question clearly, concisely, and professionally based on the data context provided. 
If the question is unrelated to the data, answer it to the best of your ability as an AI assistant.
"""
            # We use loop.run_in_executor to avoid blocking the asyncio event loop since chat() is synchronous
            loop = asyncio.get_event_loop()
            llm_response = await loop.run_in_executor(None, lambda: chat(
                messages=query,
                system=context,
                temperature=0.3
            ))
            
            return {
                "id": str(int(datetime.now().timestamp() * 1000) + 1),
                "user": "Data Analyst Agent",
                "avatar": "🧠",
                "message": llm_response,
                "time": "Just now",
                "isAi": True,
            }
        except Exception as e:
            logger.error(f"Data Analyst Agent error: {e}")
            return {
                "id": str(int(datetime.now().timestamp() * 1000) + 1),
                "user": "Data Analyst Agent",
                "avatar": "🧠",
                "message": f"I encountered an issue analyzing your data: {e}",
                "time": "Just now",
                "isAi": True,
            }

