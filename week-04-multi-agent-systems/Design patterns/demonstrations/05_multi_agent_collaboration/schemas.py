"""Schemas and State definitions for Pattern 05: Multi-Agent Collaboration."""

from typing import TypedDict, Annotated, List, Optional, Dict, Any
from enum import Enum
import operator
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage


class AgentRole(str, Enum):
    RESEARCHER = "researcher"
    CODER = "coder"
    REVIEWER = "reviewer"
    SYNTHESIZER = "synthesizer"
    FINISH = "FINISH"


class SupervisorDecision(BaseModel):
    """The structured routing decision made by the Supervisor agent."""
    next_agent: AgentRole = Field(
        description="The next specialized agent role to act, or 'FINISH' if task is fully resolved"
    )
    delegation_instructions: str = Field(
        description="Specific objective and instructions for the assigned agent"
    )


class SecurityReviewResult(BaseModel):
    """Code and security review verdict from the Reviewer Agent."""
    is_approved: bool = Field(description="True if code is production-ready, safe, and meets all requirements")
    security_vulnerabilities: List[str] = Field(default_factory=list, description="List of identified security risks")
    performance_issues: List[str] = Field(default_factory=list, description="Identified performance bottlenecks")
    actionable_fix_instructions: Optional[str] = Field(default=None, description="Exact feedback for the Coder if rejected")


class MultiAgentState(TypedDict):
    """LangGraph Shared State across all collaborating agents."""
    task_goal: str
    messages: Annotated[List[BaseMessage], operator.add]
    current_agent: Optional[str]
    next_agent: Optional[str]
    supervisor_notes: Optional[str]
    research_summary: Optional[str]
    code_artifact: Optional[str]
    review_verdict: Optional[Dict[str, Any]]
    iteration_count: int
    max_iterations: int
    final_deliverable: Optional[str]
