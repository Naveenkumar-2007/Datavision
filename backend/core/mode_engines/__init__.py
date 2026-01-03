"""
Mode Engines Package
====================

5 Unique Powerful Modes - Like OpenAI's Model Lineup:

1. Analyst - Smart data analysis with auto RAG routing
2. Deep Think - Complex reasoning with chain-of-thought
3. Vision - Image and document understanding
4. Predict - Forecasting and what-if scenarios
5. Agent - Full autonomous AI with all tools

Each mode is a DISTINCT powerhouse with unique capabilities.
"""

from .analyst_engine import AnalystEngine, analyst_response
from .deepthink_engine import DeepThinkEngine, deepthink_response
from .vision_engine import VisionEngine, vision_response
from .predict_engine import predict_response, predict_response_sync
from .agent_engine import AgentEngine, agent_response

__all__ = [
    'AnalystEngine', 'analyst_response',
    'DeepThinkEngine', 'deepthink_response',
    'VisionEngine', 'vision_response',
    'predict_response', 'predict_response_sync',
    'AgentEngine', 'agent_response',
]
