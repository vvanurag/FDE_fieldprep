"""Common Pydantic data schemas used across agent systems."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class AgentMessage(BaseModel):
    """Standardized representation of a message exchanged in agent workflows."""
    sender: str
    recipient: Optional[str] = None
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentExecutionResult(BaseModel):
    """Encapsulates the final outcome, metadata, and token telemetry of an agent run."""
    success: bool
    output: Any
    steps_taken: int = 0
    intermediate_steps: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    execution_time_seconds: float = 0.0
