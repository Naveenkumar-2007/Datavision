"""
🤖 Agentic AutoML - Shared Memory Manager

Implements the shared state architecture:
- Immutable storage per stage
- Version tracking
- Artifact management
- State history for debugging
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import copy
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class StateEntry:
    """A single entry in the shared state"""
    key: str
    value: Any
    stage: str
    version: int
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "key": self.key,
            "stage": self.stage,
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "value_type": type(self.value).__name__
        }


@dataclass
class Artifact:
    """An artifact produced by an agent (model, chart, report)"""
    id: str
    type: str  # model, chart, report, features, etc.
    producer: str  # Agent that created it
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class AgentMemory:
    """
    Centralized shared memory for all agents.
    
    Features:
    - Immutable state per stage (each write creates new version)
    - Full history for debugging and replay
    - Artifact storage for models, charts, etc.
    - Thread-safe operations (TODO: add locks for production)
    """
    
    def __init__(self):
        # Current state (latest version of each key)
        self._state: Dict[str, Any] = {}
        
        # State history (key -> list of StateEntry)
        self._history: Dict[str, List[StateEntry]] = defaultdict(list)
        
        # Artifacts storage
        self._artifacts: Dict[str, Artifact] = {}
        
        # Logs for debugging
        self._logs: List[Dict] = []
        
        # Version counters
        self._versions: Dict[str, int] = defaultdict(int)
        
        # Pipeline metadata
        self.pipeline_id: str = ""
        self.created_at: datetime = datetime.now()
    
    # =========================================================================
    # STATE MANAGEMENT
    # =========================================================================
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get current value for a key"""
        return self._state.get(key, default)
    
    def set(self, key: str, value: Any, stage: str):
        """
        Set a value (creates new version, doesn't overwrite history)
        """
        self._versions[key] += 1
        version = self._versions[key]
        
        # Create entry
        entry = StateEntry(
            key=key,
            value=copy.deepcopy(value),  # Deep copy to ensure immutability
            stage=stage,
            version=version
        )
        
        # Store in history
        self._history[key].append(entry)
        
        # Update current state
        self._state[key] = value
        
        logger.debug(f"📝 Memory[{key}] = {type(value).__name__} (v{version} by {stage})")
    
    def get_history(self, key: str) -> List[StateEntry]:
        """Get full history for a key"""
        return self._history.get(key, [])
    
    def get_version(self, key: str, version: int) -> Optional[Any]:
        """Get a specific version of a value"""
        history = self._history.get(key, [])
        for entry in history:
            if entry.version == version:
                return entry.value
        return None
    
    def get_by_stage(self, key: str, stage: str) -> Optional[Any]:
        """Get value as set by a specific stage"""
        history = self._history.get(key, [])
        for entry in reversed(history):  # Latest first
            if entry.stage == stage:
                return entry.value
        return None
    
    # =========================================================================
    # ARTIFACT MANAGEMENT
    # =========================================================================
    
    def store_artifact(self, artifact_id: str, artifact_type: str, 
                       producer: str, data: Any, metadata: Dict = None):
        """Store an artifact"""
        artifact = Artifact(
            id=artifact_id,
            type=artifact_type,
            producer=producer,
            data=data,
            metadata=metadata or {}
        )
        self._artifacts[artifact_id] = artifact
        logger.info(f"📦 Artifact stored: {artifact_type} by {producer}")
    
    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """Get an artifact by ID"""
        return self._artifacts.get(artifact_id)
    
    def get_artifacts(self, artifact_type: str) -> List[Artifact]:
        """Get all artifacts of a specific type"""
        return [a for a in self._artifacts.values() if a.type == artifact_type]
    
    def get_latest_artifact(self, artifact_type: str) -> Optional[Artifact]:
        """Get the most recent artifact of a type"""
        artifacts = self.get_artifacts(artifact_type)
        if artifacts:
            return max(artifacts, key=lambda a: a.timestamp)
        return None
    
    # =========================================================================
    # LOGGING
    # =========================================================================
    
    def log(self, agent: str, message: str, level: str = "info", data: Dict = None):
        """Add a log entry"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "level": level,
            "message": message,
            "data": data or {}
        }
        self._logs.append(entry)
    
    def get_logs(self, agent: str = None, level: str = None) -> List[Dict]:
        """Get logs, optionally filtered"""
        logs = self._logs
        if agent:
            logs = [l for l in logs if l["agent"] == agent]
        if level:
            logs = [l for l in logs if l["level"] == level]
        return logs
    
    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================
    
    @property
    def dataset(self):
        """Get the current dataset"""
        return self.get("dataset")
    
    @property
    def features(self):
        """Get the current feature matrix"""
        return self.get("features")
    
    @property
    def target(self):
        """Get the current target variable"""
        return self.get("target")
    
    @property
    def best_model(self):
        """Get the best model artifact"""
        return self.get_latest_artifact("model")
    
    @property
    def metrics(self) -> Dict[str, float]:
        """Get the current metrics"""
        return self.get("metrics", {})
    
    # =========================================================================
    # SERIALIZATION
    # =========================================================================
    
    def get_state_summary(self) -> Dict:
        """Get a summary of current state"""
        return {
            "pipeline_id": self.pipeline_id,
            "created_at": self.created_at.isoformat(),
            "keys": list(self._state.keys()),
            "artifact_count": len(self._artifacts),
            "log_count": len(self._logs),
            "versions": dict(self._versions)
        }
    
    def export_logs(self) -> str:
        """Export logs as JSON string"""
        return json.dumps(self._logs, indent=2, default=str)
    
    def clear(self):
        """Clear all state (for new pipeline)"""
        self._state.clear()
        self._history.clear()
        self._artifacts.clear()
        self._logs.clear()
        self._versions.clear()
        self.pipeline_id = ""
        self.created_at = datetime.now()
