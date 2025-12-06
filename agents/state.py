"""Agent state model for workflow transitions."""

from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class AgentState(BaseModel):
    company_id: str
    question: str
    route: str = "rag"
    answer: str = ""
    context: Dict[str, Any] = {}
    sources: List[str] = []
