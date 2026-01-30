"""
🤖 Agentic AutoML - Base Agent Framework

This module defines the foundational components for the multi-agent system:
- Message types for agent communication
- Base Agent class with lifecycle methods
- Agent result and status types
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# MESSAGE TYPES - For inter-agent communication
# =============================================================================

class MessageType(Enum):
    """Types of messages agents can send"""
    # Decision messages
    APPROVAL = "approval"
    REJECTION = "rejection"
    RETRY = "retry"
    
    # Signal messages
    ESCALATE = "escalate"
    REQUEST_FEEDBACK = "request_feedback"
    PHASE_COMPLETE = "phase_complete"
    
    # Control messages
    ABORT = "abort"
    PAUSE = "pause"
    RESUME = "resume"


class AgentStatus(Enum):
    """Agent execution status"""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    WAITING = "waiting"
    RETRY = "retry"


class Phase(Enum):
    """Pipeline phases"""
    FAST_DISCOVERY = "fast_discovery"
    DEEP_VALIDATION = "deep_validation"


@dataclass
class AgentMessage:
    """Message passed between agents"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    sender: str = ""
    receiver: str = ""
    type: MessageType = MessageType.APPROVAL
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "sender": self.sender,
            "receiver": self.receiver,
            "type": self.type.value,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class AgentResult:
    """Result returned by an agent after execution"""
    status: AgentStatus
    agent_name: str
    phase: Phase
    data: Dict[str, Any] = field(default_factory=dict)
    messages: List[AgentMessage] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    duration_seconds: float = 0.0
    
    @property
    def success(self) -> bool:
        return self.status == AgentStatus.SUCCESS
    
    @property
    def should_retry(self) -> bool:
        return self.status == AgentStatus.RETRY
    
    def add_message(self, receiver: str, msg_type: MessageType, payload: Dict = None):
        """Helper to add a message to send"""
        self.messages.append(AgentMessage(
            sender=self.agent_name,
            receiver=receiver,
            type=msg_type,
            payload=payload or {}
        ))


# =============================================================================
# BASE AGENT CLASS
# =============================================================================

class BaseAgent(ABC):
    """
    Base class for all agents in the Agentic AutoML system.
    
    Each agent has:
    - A name and description
    - Access to shared memory
    - Ability to send/receive messages
    - Lifecycle methods (validate, execute, handle_failure)
    """
    
    name: str = "BaseAgent"
    description: str = "Base agent class"
    
    def __init__(self, memory: 'AgentMemory' = None):
        self.memory = memory
        self.current_phase = Phase.FAST_DISCOVERY
        self.retry_count = 0
        self.max_retries = 3
        self._start_time = None
        self.logger = logging.getLogger(f"agent.{self.name}")
    
    # =========================================================================
    # LIFECYCLE METHODS
    # =========================================================================
    
    def run(self, **kwargs) -> AgentResult:
        """
        Main entry point for agent execution.
        Handles timing, error catching, and retry logic.
        """
        import time
        self._start_time = time.time()
        
        try:
            # Pre-execution validation
            validation = self.validate(**kwargs)
            if not validation['valid']:
                return AgentResult(
                    status=AgentStatus.FAILED,
                    agent_name=self.name,
                    phase=self.current_phase,
                    errors=validation.get('errors', ['Validation failed']),
                    duration_seconds=time.time() - self._start_time
                )
            
            # Main execution
            self.logger.info(f"🤖 {self.name} starting...")
            result = self.execute(**kwargs)
            result.duration_seconds = time.time() - self._start_time
            
            # Log result
            if result.success:
                self.logger.info(f"✅ {self.name} completed in {result.duration_seconds:.2f}s")
            else:
                self.logger.warning(f"⚠️ {self.name} finished with status: {result.status.value}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ {self.name} error: {str(e)}")
            return self.handle_failure(e, **kwargs)
    
    def validate(self, **kwargs) -> Dict[str, Any]:
        """
        Validate inputs before execution.
        Override in subclasses for specific validation.
        """
        return {'valid': True}
    
    @abstractmethod
    def execute(self, **kwargs) -> AgentResult:
        """
        Main execution logic. Must be implemented by subclasses.
        """
        pass
    
    def handle_failure(self, error: Exception, **kwargs) -> AgentResult:
        """
        Handle execution failures. Can be overridden for custom recovery.
        """
        import time
        self.retry_count += 1
        
        if self.retry_count < self.max_retries:
            return AgentResult(
                status=AgentStatus.RETRY,
                agent_name=self.name,
                phase=self.current_phase,
                errors=[str(error)],
                recommendations=[f"Retry attempt {self.retry_count}/{self.max_retries}"],
                duration_seconds=time.time() - self._start_time if self._start_time else 0
            )
        
        return AgentResult(
            status=AgentStatus.FAILED,
            agent_name=self.name,
            phase=self.current_phase,
            errors=[str(error), f"Max retries ({self.max_retries}) exceeded"],
            duration_seconds=time.time() - self._start_time if self._start_time else 0
        )
    
    # =========================================================================
    # PHASE CONTROL
    # =========================================================================
    
    def set_phase(self, phase: Phase):
        """Set the current execution phase"""
        self.current_phase = phase
        self.logger.info(f"📍 Phase set to: {phase.value}")
    
    def is_fast_phase(self) -> bool:
        """Check if in fast discovery phase"""
        return self.current_phase == Phase.FAST_DISCOVERY
    
    def is_deep_phase(self) -> bool:
        """Check if in deep validation phase"""
        return self.current_phase == Phase.DEEP_VALIDATION
    
    # =========================================================================
    # MEMORY ACCESS
    # =========================================================================
    
    def read_state(self, key: str, default: Any = None) -> Any:
        """Read from shared memory"""
        if self.memory:
            return self.memory.get(key, default)
        return default
    
    def write_state(self, key: str, value: Any, stage: str = None):
        """Write to shared memory (immutable per stage)"""
        if self.memory:
            self.memory.set(key, value, stage or self.name)
    
    def get_artifacts(self, artifact_type: str) -> List[Any]:
        """Get artifacts of a specific type"""
        if self.memory:
            return self.memory.get_artifacts(artifact_type)
        return []


# =============================================================================
# AGENT REGISTRY
# =============================================================================

class AgentRegistry:
    """Registry for managing agent instances"""
    
    _agents: Dict[str, BaseAgent] = {}
    
    @classmethod
    def register(cls, agent: BaseAgent):
        """Register an agent"""
        cls._agents[agent.name] = agent
    
    @classmethod
    def get(cls, name: str) -> Optional[BaseAgent]:
        """Get an agent by name"""
        return cls._agents.get(name)
    
    @classmethod
    def all(cls) -> List[BaseAgent]:
        """Get all registered agents"""
        return list(cls._agents.values())
    
    @classmethod
    def clear(cls):
        """Clear all registered agents"""
        cls._agents.clear()
