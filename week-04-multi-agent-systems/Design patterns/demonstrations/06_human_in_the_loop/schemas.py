"""Schemas, risk levels, and State for Human-in-the-Loop (HITL) pattern."""

from typing import TypedDict, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class TransactionRiskLevel(str, Enum):
    LOW_RISK = "LOW_RISK"
    HIGH_RISK = "HIGH_RISK"


class RefundRequest(BaseModel):
    """Structured customer refund request."""
    transaction_id: str = Field(description="Transaction reference ID, e.g. 'TX-90421'")
    customer_id: str = Field(description="Customer account ID, e.g. 'CUST-883'")
    requested_amount_usd: float = Field(ge=0.0, description="Amount in USD requested for refund")
    reason: str = Field(description="Reason for the refund request")


class ActionPayload(BaseModel):
    """Action payload evaluated by the policy gate and human supervisor."""
    action_type: str = "ISSUE_REFUND"
    transaction_id: str
    customer_id: str
    amount_usd: float
    risk_level: TransactionRiskLevel
    requires_human_approval: bool
    supervisor_approval_status: Optional[str] = None  # 'approved', 'edited', 'rejected'
    supervisor_notes: Optional[str] = None


class HITLAgentState(TypedDict):
    """LangGraph state persisted in checkpointer during HITL pauses."""
    customer_query: str
    refund_details: Optional[Dict[str, Any]]
    pending_action: Optional[Dict[str, Any]]
    human_verdict: Optional[str]      # 'approved', 'edited', 'rejected'
    human_notes: Optional[str]
    execution_result: Optional[Dict[str, Any]]
    is_completed: bool
