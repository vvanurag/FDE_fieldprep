"""Schemas, validation constraints, and State for Evaluator-Optimizer Pattern."""

from typing import TypedDict, List, Optional, Dict, Any
from enum import Enum
import re
from pydantic import BaseModel, Field, field_validator, model_validator


class IncidentSeverity(str, Enum):
    SEV1 = "SEV-1"
    SEV2 = "SEV-2"
    SEV3 = "SEV-3"


class IncidentRemediationReport(BaseModel):
    """Strict schema for production incident remediation reports."""
    incident_id: str = Field(
        description="Ticket ID matching format 'INC-XXXXX' (e.g., 'INC-40921')"
    )
    severity: IncidentSeverity = Field(
        description="Severity level: 'SEV-1' (Critical), 'SEV-2' (Major), 'SEV-3' (Minor)"
    )
    root_cause_summary: str = Field(
        min_length=20,
        description="Detailed summary of root cause (minimum 20 characters)"
    )
    impacted_services: List[str] = Field(
        min_length=1,
        description="List of impacted microservices or components"
    )
    estimated_downtime_minutes: float = Field(
        ge=0.0,
        description="Total system downtime in minutes"
    )
    sla_breached: bool = Field(
        description="Whether enterprise SLA was breached"
    )
    remediation_steps: List[str] = Field(
        min_length=2,
        description="At least 2 concrete engineering remediation actions"
    )

    @field_validator("incident_id")
    @classmethod
    def validate_incident_id(cls, v: str) -> str:
        v_clean = v.strip().upper()
        if not re.match(r"^INC-\d{4,6}$", v_clean):
            raise ValueError(f"Invalid incident_id format '{v}'. Must match 'INC-XXXXX' (e.g. INC-10294).")
        return v_clean

    @field_validator("impacted_services")
    @classmethod
    def validate_services(cls, v: List[str]) -> List[str]:
        cleaned = [s.strip() for s in v if s.strip()]
        if not cleaned:
            raise ValueError("impacted_services cannot be empty or contain blank entries.")
        return cleaned

    @model_validator(mode="after")
    def validate_business_rules(self) -> "IncidentRemediationReport":
        # Business Invariant 1: SEV-1 with downtime > 15 mins MUST be marked as sla_breached=True
        if self.severity == IncidentSeverity.SEV1 and self.estimated_downtime_minutes > 15.0:
            if not self.sla_breached:
                raise ValueError(
                    f"Business Rule Violation: Any SEV-1 incident with downtime > 15 minutes "
                    f"({self.estimated_downtime_minutes} mins) MUST have 'sla_breached': true."
                )
        return self


class EvaluatorOptimizerState(TypedDict):
    """LangGraph state tracking the generation, validation, and self-healing iterations."""
    raw_incident_narrative: str
    draft_output: str
    parsed_report: Optional[Dict[str, Any]]
    validation_errors: Optional[List[str]]
    error_history: List[str]
    retry_count: int
    max_retries: int
    is_approved: bool
    final_message: Optional[str]
