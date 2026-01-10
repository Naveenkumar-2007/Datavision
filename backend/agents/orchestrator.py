"""
🤖 Agentic AutoML - Agent Orchestrator

The central coordinator that:
- Manages agent execution order
- Handles two-phase optimization (Fast Discovery → Deep Validation)
- Implements feedback loops and retry logic
- Routes messages between agents
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum
import logging
import uuid
import time

from .base import (
    BaseAgent, AgentResult, AgentStatus, AgentMessage, 
    MessageType, Phase, AgentRegistry
)
from .memory import AgentMemory

logger = logging.getLogger(__name__)


class PipelineStatus(Enum):
    """Overall pipeline status"""
    IDLE = "idle"
    RUNNING = "running"
    FAST_DISCOVERY = "fast_discovery"
    DEEP_VALIDATION = "deep_validation"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentOrchestrator:
    """
    Central orchestrator for the Agentic AutoML pipeline.
    
    Responsibilities:
    1. Coordinate agent execution order
    2. Manage two-phase optimization strategy
    3. Handle message routing between agents
    4. Implement feedback loops for failure recovery
    5. Track pipeline state and metrics
    """
    
    def __init__(self):
        self.memory = AgentMemory()
        self.agents: Dict[str, BaseAgent] = {}
        self.status = PipelineStatus.IDLE
        self.current_phase = Phase.FAST_DISCOVERY
        self.iteration = 0
        self.max_iterations = 5
        self.message_queue: List[AgentMessage] = []
        self.execution_log: List[Dict] = []
        
        # Thresholds for phase transition
        self.fast_phase_threshold = 0.5  # Minimum score to enter deep phase
        self.approval_threshold = 0.7     # Minimum score for final approval
        
        # Callbacks
        self.on_progress: Optional[Callable[[str, float], None]] = None
        self.check_cancellation: Optional[Callable[[], None]] = None
        
        # Timing
        self.start_time: Optional[datetime] = None
        
    # =========================================================================
    # AGENT REGISTRATION
    # =========================================================================
    
    def register_agent(self, name: str, agent: BaseAgent):
        """Register an agent with the orchestrator"""
        agent.memory = self.memory
        self.agents[name] = agent
        logger.info(f"📝 Registered agent: {name}")
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get an agent by name"""
        return self.agents.get(name)
    
    # =========================================================================
    # PIPELINE EXECUTION
    # =========================================================================
    
    def run(self, 
            dataset, 
            target_column: str,
            task_type: str = None,
            on_progress: Callable[[str, float], None] = None,
            check_cancellation: Callable[[], None] = None) -> Dict[str, Any]:
        """
        Run the complete agentic AutoML pipeline.
        
        Args:
            dataset: Input DataFrame
            target_column: Name of target column
            task_type: 'classification' or 'regression' (auto-detected if None)
            on_progress: Callback for progress updates
            check_cancellation: Callback to check for user cancellation
        
        Returns:
            Dict with results, metrics, and artifacts
        """
        self.start_time = datetime.now()
        self.on_progress = on_progress
        self.check_cancellation = check_cancellation
        self.status = PipelineStatus.RUNNING
        self.iteration = 0
        
        # Initialize memory
        self.memory.clear()
        self.memory.pipeline_id = str(uuid.uuid4())[:8]
        self.memory.set("dataset", dataset, "orchestrator")
        self.memory.set("target_column", target_column, "orchestrator")
        self.memory.set("task_type", task_type, "orchestrator")
        
        logger.info(f"🚀 Starting Agentic AutoML Pipeline (ID: {self.memory.pipeline_id})")
        self._report_progress("Initializing pipeline", 0.0)
        
        try:
            # ========== PHASE 1: FAST DISCOVERY ==========
            self.current_phase = Phase.FAST_DISCOVERY
            self.status = PipelineStatus.FAST_DISCOVERY
            logger.info("⚡ PHASE 1: FAST DISCOVERY")
            
            fast_result = self._run_fast_discovery()
            
            if not fast_result['success']:
                return self._build_failure_result(fast_result.get('errors', []))
            
            # Check if we should proceed to deep validation
            fast_score = fast_result.get('score', 0)
            if fast_score < self.fast_phase_threshold:
                logger.warning(f"⚠️ Fast phase score ({fast_score:.2f}) below threshold")
                return self._build_result(fast_result, approved=False)
            
            # ========== PHASE 2: DEEP VALIDATION ==========
            self.current_phase = Phase.DEEP_VALIDATION
            self.status = PipelineStatus.DEEP_VALIDATION
            logger.info("🔍 PHASE 2: DEEP VALIDATION")
            
            deep_result = self._run_deep_validation()
            
            if not deep_result['success']:
                # Failed deep validation - return best fast phase result
                logger.warning("⚠️ Deep validation failed, using fast phase result")
                return self._build_result(fast_result, approved=False)
            
            # ========== FINAL APPROVAL ==========
            final_score = deep_result.get('score', 0)
            approved = final_score >= self.approval_threshold
            
            self.status = PipelineStatus.SUCCESS if approved else PipelineStatus.FAILED
            
            return self._build_result(deep_result, approved=approved)
            
        except Exception as e:
            logger.error(f"❌ Pipeline error: {str(e)}")
            self.status = PipelineStatus.FAILED
            return self._build_failure_result([str(e)])
    
    # =========================================================================
    # PHASE EXECUTION
    # =========================================================================
    
    def _run_fast_discovery(self) -> Dict[str, Any]:
        """
        Fast Discovery Phase:
        - Limited algorithms (top 3-4)
        - Shallow hyperparameter search
        - Quick feature screening
        - Single train-test split
        """
        self._check_cancelled()
        
        # Set all agents to fast phase
        for agent in self.agents.values():
            agent.set_phase(Phase.FAST_DISCOVERY)
        
        # Execute data pipeline
        self._report_progress("Data Quality Check", 0.1)
        data_result = self._run_agent("data_quality")
        if not data_result.success:
            return {"success": False, "errors": data_result.errors}
        
        self._report_progress("Preprocessing", 0.2)
        prep_result = self._run_agent("preprocessing")
        if not prep_result.success:
            return {"success": False, "errors": prep_result.errors}
        
        self._report_progress("Feature Engineering", 0.3)
        feature_result = self._run_agent("feature_engineer")
        if not feature_result.success:
            return {"success": False, "errors": feature_result.errors}
        
        # Execute model pipeline
        self._report_progress("Model Selection", 0.4)
        model_result = self._run_agent("model_strategy")
        if not model_result.success:
            return {"success": False, "errors": model_result.errors}
        
        self._report_progress("Hyperparameter Tuning", 0.5)
        hyperparam_result = self._run_agent("hyperparam")
        if not hyperparam_result.success:
            return {"success": False, "errors": hyperparam_result.errors}
        
        self._report_progress("Training Validation", 0.6)
        training_result = self._run_agent("training_validator")
        
        # Handle training validation result with feedback loop
        if training_result.should_retry:
            return self._handle_feedback_loop(training_result)
        
        if not training_result.success:
            return {"success": False, "errors": training_result.errors}
        
        return {
            "success": True,
            "score": training_result.metrics.get("score", 0),
            "metrics": training_result.metrics,
            "phase": "fast_discovery"
        }
    
    def _run_deep_validation(self) -> Dict[str, Any]:
        """
        Deep Validation Phase:
        - Robust cross-validation
        - Stability checks
        - Overfitting detection
        - Feature ablation
        - Drift sensitivity
        """
        self._check_cancelled()
        
        # Set all agents to deep phase
        for agent in self.agents.values():
            agent.set_phase(Phase.DEEP_VALIDATION)
        
        self._report_progress("Evaluation & Generalization", 0.7)
        eval_result = self._run_agent("evaluation")
        
        if eval_result.should_retry:
            return self._handle_feedback_loop(eval_result)
        
        if not eval_result.success:
            return {"success": False, "errors": eval_result.errors}
        
        # Only generate visualizations if evaluation passed
        self._report_progress("Generating Explanations", 0.85)
        viz_result = self._run_agent("visualization")
        
        # Prepare for deployment
        self._report_progress("Deployment Preparation", 0.95)
        deploy_result = self._run_agent("deployment")
        
        return {
            "success": True,
            "score": eval_result.metrics.get("score", 0),
            "metrics": eval_result.metrics,
            "phase": "deep_validation",
            "approved": deploy_result.success
        }
    
    # =========================================================================
    # FEEDBACK LOOPS
    # =========================================================================
    
    def _handle_feedback_loop(self, result: AgentResult) -> Dict[str, Any]:
        """
        Handle feedback from validators.
        Routes back to appropriate agent based on recommendations.
        """
        self.iteration += 1
        
        if self.iteration >= self.max_iterations:
            logger.warning(f"⚠️ Max iterations ({self.max_iterations}) reached")
            return {"success": False, "errors": ["Max iterations reached"]}
        
        logger.info(f"🔄 Feedback loop iteration {self.iteration}")
        
        # Parse recommendations to determine which agent to retry
        for msg in result.messages:
            if msg.type == MessageType.RETRY:
                target_agent = msg.receiver
                logger.info(f"   → Routing to {target_agent}")
                
                # Re-run from that agent
                retry_result = self._run_agent(target_agent)
                if retry_result.success:
                    # Continue from where we left off
                    if self.current_phase == Phase.FAST_DISCOVERY:
                        return self._run_fast_discovery()
                    else:
                        return self._run_deep_validation()
        
        # Default: retry current phase
        if self.current_phase == Phase.FAST_DISCOVERY:
            return self._run_fast_discovery()
        else:
            return self._run_deep_validation()
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _run_agent(self, agent_name: str) -> AgentResult:
        """Run a specific agent"""
        agent = self.agents.get(agent_name)
        
        if not agent:
            logger.warning(f"⚠️ Agent not found: {agent_name}")
            return AgentResult(
                status=AgentStatus.SUCCESS,  # Skip gracefully
                agent_name=agent_name,
                phase=self.current_phase
            )
        
        self._check_cancelled()
        
        result = agent.run()
        
        # Log execution
        self.execution_log.append({
            "agent": agent_name,
            "status": result.status.value,
            "duration": result.duration_seconds,
            "timestamp": datetime.now().isoformat()
        })
        
        # Process any messages
        for msg in result.messages:
            self.message_queue.append(msg)
        
        return result
    
    def _check_cancelled(self):
        """Check if pipeline was cancelled"""
        if self.check_cancellation:
            self.check_cancellation()
    
    def _report_progress(self, stage: str, progress: float):
        """Report progress to callback"""
        logger.info(f"📍 {stage} ({progress*100:.0f}%)")
        if self.on_progress:
            self.on_progress(stage, progress)
    
    def _build_result(self, phase_result: Dict, approved: bool) -> Dict[str, Any]:
        """Build final result dictionary"""
        duration = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        return {
            "success": True,
            "approved": approved,
            "pipeline_id": self.memory.pipeline_id,
            "status": self.status.value,
            "phase": phase_result.get("phase", "unknown"),
            "score": phase_result.get("score", 0),
            "metrics": phase_result.get("metrics", {}),
            "duration_seconds": duration,
            "iterations": self.iteration,
            "model": self.memory.best_model,
            "execution_log": self.execution_log
        }
    
    def _build_failure_result(self, errors: List[str]) -> Dict[str, Any]:
        """Build failure result dictionary"""
        duration = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        return {
            "success": False,
            "approved": False,
            "pipeline_id": self.memory.pipeline_id,
            "status": PipelineStatus.FAILED.value,
            "errors": errors,
            "duration_seconds": duration,
            "iterations": self.iteration,
            "execution_log": self.execution_log
        }
