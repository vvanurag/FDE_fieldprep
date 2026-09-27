"""Schemas, Intent Enums, and State definitions for Router & Intent Classifier."""

from typing import TypedDict, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class IntentCategory(str, Enum):
    BILLING = "billing"
    TECHNICAL_SUPPORT = "technical_support"
    SALES_INQUIRY = "sales_inquiry"
    GENERAL_FAQ = "general_faq"
    AMBIGUOUS = "ambiguous"


class IntentClassificationResult(BaseModel):
    """Structured output format produced by the Router LLM Classifier."""
    primary_intent: IntentCategory = Field(
        description="The classified intent category for the user query"
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 (uncertain) and 1.0 (certain)"
    )
    reasoning: str = Field(
        description="Brief reasoning for why this intent category was chosen"
    )
    detected_entities: Dict[str, Any] = Field(
        default_factory=dict,
        description="Key entities extracted (e.g. invoice_id, error_code, user_tier, seat_count)"
    )


class RouterAgentState(TypedDict):
    """LangGraph State tracking query classification and specialist execution."""
    user_query: str
    classification: Optional[Dict[str, Any]]
    confidence_threshold: float
    routed_specialist: Optional[str]
    specialist_response: Optional[str]
