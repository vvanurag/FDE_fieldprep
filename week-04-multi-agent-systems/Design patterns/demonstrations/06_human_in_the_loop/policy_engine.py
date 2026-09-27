"""Deterministic enterprise risk and compliance policy engine."""

from typing import Tuple
from .schemas import RefundRequest, ActionPayload, TransactionRiskLevel

# Enterprise Threshold Policy: Transactions > $100 require supervisor approval
AUTO_APPROVAL_THRESHOLD_USD = 100.0


def evaluate_transaction_policy(request: RefundRequest) -> ActionPayload:
    """Evaluates whether an action can execute automatically or requires a human approval gate."""
    amount = request.requested_amount_usd
    
    if amount <= AUTO_APPROVAL_THRESHOLD_USD:
        return ActionPayload(
            transaction_id=request.transaction_id,
            customer_id=request.customer_id,
            amount_usd=amount,
            risk_level=TransactionRiskLevel.LOW_RISK,
            requires_human_approval=False,
            supervisor_approval_status="auto_approved",
            supervisor_notes=f"Amount (${amount:.2f}) is within automated threshold (<=${AUTO_APPROVAL_THRESHOLD_USD:.2f})."
        )
    else:
        return ActionPayload(
            transaction_id=request.transaction_id,
            customer_id=request.customer_id,
            amount_usd=amount,
            risk_level=TransactionRiskLevel.HIGH_RISK,
            requires_human_approval=True,
            supervisor_approval_status="pending_human_review",
            supervisor_notes=f"Amount (${amount:.2f}) exceeds automated threshold (> ${AUTO_APPROVAL_THRESHOLD_USD:.2f}). Human review required."
        )
