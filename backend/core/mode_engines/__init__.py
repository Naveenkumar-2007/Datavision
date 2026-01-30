"""
DataVision Pro - Mode Engines Package
=====================================

5 Powerful Autonomous AI Modes:

1. 🎯 Pro Analyst - Smart data analysis with auto insights
2. 🧠 Pro DeepThink - Multi-step reasoning with evidence
3. 🤖 Pro Agent - Autonomous task execution
4. 👁️ Pro Vision - Image and document understanding  
5. 🔮 Pro Predict - ML predictions and model insights

Each mode is a DISTINCT powerhouse with unique capabilities.
Built for DataVision - Intelligence for ANY data!
"""

from .analyst_engine import ProAnalystEngine, AnalystEngine, analyst_response, analyst_response_sync
from .deepthink_engine import ProDeepThinkEngine, DeepThinkEngine, deepthink_response, deepthink_response_sync
from .vision_engine import ProVisionEngine, VisionEngine, vision_response, vision_response_sync
from .predict_engine import predict_response_sync
from .agent_engine import ProAgentEngine, AgentEngine, agent_response, agent_response_sync

# Try to import predict_response if async version exists
try:
    from .predict_engine import predict_response
except ImportError:
    predict_response = predict_response_sync

__all__ = [
    # Pro Analyst
    'ProAnalystEngine', 'AnalystEngine', 'analyst_response', 'analyst_response_sync',
    
    # Pro DeepThink
    'ProDeepThinkEngine', 'DeepThinkEngine', 'deepthink_response', 'deepthink_response_sync',
    
    # Pro Vision
    'ProVisionEngine', 'VisionEngine', 'vision_response', 'vision_response_sync',
    
    # Pro Predict
    'predict_response', 'predict_response_sync',
    
    # Pro Agent
    'ProAgentEngine', 'AgentEngine', 'agent_response', 'agent_response_sync',
]
