"""
🤖 Agentic AutoML - Complete Agent Package

This package contains all components for the autonomous multi-agent AutoML system.

Agents:
1. Data Quality Agent - Detects and fixes dataset issues
2. Preprocessing Agent - Smart encoding and scaling
3. Feature Engineer Agent - Feature creation and selection
4. Model Strategy Agent - Algorithm selection
5. Hyperparameter Agent - Optuna optimization
6. Training Validator Agent - Bias-variance analysis
7. Evaluation Agent - Final approval gate
8. Visualization Agent - Explainability charts
9. Deployment Agent - Production inference
"""

# Base components
from .base import (
    BaseAgent,
    AgentResult,
    AgentStatus,
    AgentMessage,
    MessageType,
    Phase,
    AgentRegistry
)

# Memory and orchestration
from .memory import AgentMemory, StateEntry, Artifact
from .orchestrator import AgentOrchestrator, PipelineStatus

# Data agents
from .data_quality import DataQualityAgent
from .preprocessing import PreprocessingAgent
from .feature_engineer import FeatureEngineerAgent

# Model agents
from .model_strategy import ModelStrategyAgent
from .hyperparam import HyperparamAgent
from .training_validator import TrainingValidatorAgent

# Validation agents
from .evaluation import EvaluationAgent
from .visualization import VisualizationAgent
from .deployment import DeploymentAgent


def create_agentic_pipeline() -> AgentOrchestrator:
    """
    Factory function to create a fully configured agentic AutoML pipeline.
    
    Returns:
        AgentOrchestrator with all agents registered
    """
    orchestrator = AgentOrchestrator()
    
    # Register all agents
    orchestrator.register_agent("data_quality", DataQualityAgent())
    orchestrator.register_agent("preprocessing", PreprocessingAgent())
    orchestrator.register_agent("feature_engineer", FeatureEngineerAgent())
    orchestrator.register_agent("model_strategy", ModelStrategyAgent())
    orchestrator.register_agent("hyperparam", HyperparamAgent())
    orchestrator.register_agent("training_validator", TrainingValidatorAgent())
    orchestrator.register_agent("evaluation", EvaluationAgent())
    orchestrator.register_agent("visualization", VisualizationAgent())
    orchestrator.register_agent("deployment", DeploymentAgent())
    
    return orchestrator


__all__ = [
    # Base
    'BaseAgent',
    'AgentResult', 
    'AgentStatus',
    'AgentMessage',
    'MessageType',
    'Phase',
    'AgentRegistry',
    
    # Memory
    'AgentMemory',
    'StateEntry',
    'Artifact',
    
    # Orchestrator
    'AgentOrchestrator',
    'PipelineStatus',
    
    # Agents
    'DataQualityAgent',
    'PreprocessingAgent',
    'FeatureEngineerAgent',
    'ModelStrategyAgent',
    'HyperparamAgent',
    'TrainingValidatorAgent',
    'EvaluationAgent',
    'VisualizationAgent',
    'DeploymentAgent',
    
    # Factory
    'create_agentic_pipeline'
]
