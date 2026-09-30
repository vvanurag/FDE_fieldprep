"""🎯 Level 2 - Drill 03: Native `interrupt()` & `Command(resume=...)` HITL Pattern.

This module provides an in-depth, hands-on drill on modern LangGraph Human-in-the-Loop:
1. In-Node State Interruption: Using `from langgraph.types import interrupt` inside node logic.
2. Checkpoint Freezing: How LangGraph saves state and serializes the review payload for human operators.
3. Resuming with `Command(resume=...)`: Injecting human review decisions back into frozen nodes.
4. Tri-State Execution Branches: Demonstrating Approval, In-Flight Parameter Modification, and Rejection.

Run directly:
    python3 03_native_interrupt_and_command.py
    # or
    python3 -m week-04-multi-agent-systems.stategraph_mastery.level_2_advanced_topologies.03_native_interrupt_and_command
"""

import operator
from typing import Annotated, TypedDict, List, Dict, Any, Optional, Literal
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

console = Console()


# ============================================================================
# 1. STATE SCHEMA: FINANCIAL TRANSACTION / ACTION APPROVAL
# ============================================================================

class HumanReviewPayload(TypedDict):
    action: Literal["APPROVE", "MODIFY", "REJECT"]
    modified_amount: Optional[float]
    reviewer_name: str
    reviewer_notes: str


class WireTransferMasterState(TypedDict):
    # Transaction Details
    transaction_id: str
    recipient_account: str
    requested_amount: float
    purpose: str
    
    # Audit trail & status
    approval_status: Literal["PENDING", "APPROVED", "MODIFIED_APPROVED", "REJECTED"]
    final_executed_amount: Optional[float]
    audit_logs: Annotated[List[str], operator.add]


# ============================================================================
# 2. NODES: PREPARATION, HITL INTERRUPT GATE, AND EXECUTION
# ============================================================================

def compliance_precheck_node(state: WireTransferMasterState) -> Dict[str, Any]:
    """Node 1: Validates account format and flags high-risk transactions."""
    amount = state["requested_amount"]
    risk = "HIGH_RISK" if amount >= 10000.0 else "STANDARD"
    
    return {
        "audit_logs": [
            f"🔍 [Compliance] Pre-check passed for {state['recipient_account']}. "
            f"Amount: ${amount:,.2f} | Risk Assessment: {risk}"
        ]
    }


def human_approval_gate_node(state: WireTransferMasterState) -> Dict[str, Any]:
    """Node 2: The Core HITL Gate using modern LangGraph interrupt().
    
    When this node executes:
    1. It packages a review payload.
    2. Calls `human_decision = interrupt(payload)`.
    3. Graph execution freezes instantly and yields control back to caller.
    4. When resumed with `Command(resume=decision_dict)`, `human_decision` receives the dict!
    """
    review_package = {
        "transaction_id": state["transaction_id"],
        "recipient": state["recipient_account"],
        "amount": state["requested_amount"],
        "purpose": state["purpose"],
        "requires_dual_authorization": state["requested_amount"] >= 25000.0
    }
    
    # 🛑 FREEZE POINT: Yields review_package to human operator and halts graph
    human_decision: HumanReviewPayload = interrupt(review_package)
    
    # --- RESUME POINT: Code below only runs AFTER Command(resume=...) is called ---
    action = human_decision["action"]
    reviewer = human_decision.get("reviewer_name", "Unknown Operator")
    notes = human_decision.get("reviewer_notes", "No notes provided")
    
    if action == "APPROVE":
        return {
            "approval_status": "APPROVED",
            "final_executed_amount": state["requested_amount"],
            "audit_logs": [f"✅ [HITL Gate] Approved by {reviewer} as requested (${state['requested_amount']:,.2f}). Notes: {notes}"]
        }
    elif action == "MODIFY":
        mod_amount = human_decision.get("modified_amount", state["requested_amount"])
        return {
            "approval_status": "MODIFIED_APPROVED",
            "final_executed_amount": mod_amount,
            "audit_logs": [
                f"✏️ [HITL Gate] Modified & Approved by {reviewer}. "
                f"Amount adjusted from ${state['requested_amount']:,.2f} ➜ ${mod_amount:,.2f}. Notes: {notes}"
            ]
        }
    else:  # REJECT
        return {
            "approval_status": "REJECTED",
            "final_executed_amount": 0.0,
            "audit_logs": [f"❌ [HITL Gate] REJECTED by {reviewer}. Notes: {notes}"]
        }


def post_approval_router(state: WireTransferMasterState) -> Literal["execute_transfer", "cancellation_notice"]:
    """Conditional edge routing based on human decision."""
    if state["approval_status"] in ["APPROVED", "MODIFIED_APPROVED"]:
        return "execute_transfer"
    return "cancellation_notice"


def execute_transfer_node(state: WireTransferMasterState) -> Dict[str, Any]:
    """Node 3A: Executes the wire transfer to the recipient."""
    amount = state["final_executed_amount"]
    return {
        "audit_logs": [
            f"🏦 [Bank Rail] Wire transfer of ${amount:,.2f} successfully executed to {state['recipient_account']}."
        ]
    }


def cancellation_notice_node(state: WireTransferMasterState) -> Dict[str, Any]:
    """Node 3B: Logs rejection and sends notification to initiator."""
    return {
        "audit_logs": [
            f"🚫 [Cancellation Rail] Transaction {state['transaction_id']} aborted. Initiator notified of denial."
        ]
    }


# ============================================================================
# 3. GRAPH CONSTRUCTION
# ============================================================================

def build_hitl_wire_transfer_graph(checkpointer: MemorySaver):
    """Builds the HITL Wire Transfer Graph.
    
    Topology:
                                                        ┌──> execute_transfer ────┐
    START ──> compliance_precheck ──> human_approval ───┤                         ├──> END
                                      [interrupt()]     └──> cancellation_notice ─┘
    """
    builder = StateGraph(WireTransferMasterState)
    
    builder.add_node("compliance_precheck", compliance_precheck_node)
    builder.add_node("human_approval", human_approval_gate_node)
    builder.add_node("execute_transfer", execute_transfer_node)
    builder.add_node("cancellation_notice", cancellation_notice_node)
    
    builder.add_edge(START, "compliance_precheck")
    builder.add_edge("compliance_precheck", "human_approval")
    
    builder.add_conditional_edges(
        "human_approval",
        post_approval_router,
        {
            "execute_transfer": "execute_transfer",
            "cancellation_notice": "cancellation_notice"
        }
    )
    
    builder.add_edge("execute_transfer", END)
    builder.add_edge("cancellation_notice", END)
    
    # CRITICAL: Checkpointer is required to freeze & resume state
    return builder.compile(checkpointer=checkpointer)


# ============================================================================
# 4. INTERACTIVE DEMONSTRATION SCENARIOS
# ============================================================================

def demonstrate_scenario(
    scenario_title: str,
    thread_id: str,
    initial_payload: WireTransferMasterState,
    human_decision: HumanReviewPayload,
    app
):
    console.print(f"\n[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")
    console.print(f"[bold green]▶ SCENARIO: {scenario_title}[/bold green]")
    console.print(f"[dim]Thread ID: {thread_id}[/dim]")
    console.print(f"[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")

    config = {"configurable": {"thread_id": thread_id}}

    # PHASE 1: Launch graph execution until it hits interrupt()
    console.print("[bold cyan]1. Initiating transaction workflow...[/bold cyan]")
    app.invoke(initial_payload, config=config)

    # Inspect the frozen state
    frozen_state = app.get_state(config)
    console.print(f"[bold yellow]⏸️  GRAPH PAUSED: Node '{frozen_state.next[0]}' triggered interrupt()[/bold yellow]")

    # Retrieve the interrupt payload presented to the human reviewer
    interrupt_payload = frozen_state.tasks[0].interrupts[0].value
    
    review_table = Table(title="📋 Human Review Screen (Serialized from interrupt())", border_style="yellow")
    review_table.add_column("Field", style="cyan")
    review_table.add_column("Value", style="bold white")
    for k, v in interrupt_payload.items():
        review_table.add_row(str(k), str(v))
    console.print(review_table)

    # PHASE 2: Human Operator issues Command(resume=...)
    console.print(f"\n[bold cyan]2. Operator submitting decision: [bold magenta]{human_decision['action']}[/bold magenta] via Command(resume=...)[/bold cyan]")
    
    resume_command = Command(resume=human_decision)
    final_result = app.invoke(resume_command, config=config)

    # Display final audit log
    audit_table = Table(title="📜 Final Transaction Audit Trail", border_style="green")
    audit_table.add_column("Step", justify="center", style="cyan")
    audit_table.add_column("Audit Entry", style="white")
    for idx, entry in enumerate(final_result["audit_logs"], 1):
        audit_table.add_row(str(idx), entry)
    console.print(audit_table)

    status_color = "green" if "APPROVED" in final_result["approval_status"] else "red"
    console.print(Panel(
        f"[bold]Final Status:[/bold] [{status_color}]{final_result['approval_status']}[/{status_color}]\n"
        f"[bold]Executed Amount:[/bold] ${final_result['final_executed_amount']:,.2f}",
        title="🎯 Transaction Complete",
        border_style=status_color
    ))


def main():
    console.print(Panel.fit(
        "[bold cyan]🎯 StateGraph Mastery - Level 2 Drill 03[/bold cyan]\n"
        "[bold white]Native interrupt() & Command(resume=...) Human-in-the-Loop[/bold white]",
        border_style="cyan"
    ))

    checkpointer = MemorySaver()
    app = build_hitl_wire_transfer_graph(checkpointer=checkpointer)

    # Scenario 1: Clean Human Approval ($15,000 to Vendor Alpha)
    demonstrate_scenario(
        scenario_title="1. Full Approval of Standard Wire",
        thread_id="txn_wire_101",
        initial_payload={
            "transaction_id": "TXN-8801",
            "recipient_account": "US-CHASE-00921448",
            "requested_amount": 15000.0,
            "purpose": "Enterprise Cloud Hosting Q3",
            "approval_status": "PENDING",
            "final_executed_amount": None,
            "audit_logs": []
        },
        human_decision={
            "action": "APPROVE",
            "modified_amount": None,
            "reviewer_name": "Elena Rostova (VP Finance)",
            "reviewer_notes": "Invoice verified against vendor contract."
        },
        app=app
    )

    # Scenario 2: In-Flight Modification ($75,000 reduced to $45,000 limit)
    demonstrate_scenario(
        scenario_title="2. Human In-Flight Parameter Modification",
        thread_id="txn_wire_102",
        initial_payload={
            "transaction_id": "TXN-8802",
            "recipient_account": "US-BOFA-99120831",
            "requested_amount": 75000.0,
            "purpose": "Offshore Consulting Engagement",
            "approval_status": "PENDING",
            "final_executed_amount": None,
            "audit_logs": []
        },
        human_decision={
            "action": "MODIFY",
            "modified_amount": 45000.0,
            "reviewer_name": "Marcus Vance (CFO)",
            "reviewer_notes": "Cap payment to Milestone 1 deliverable ($45k)."
        },
        app=app
    )

    # Scenario 3: Human Rejection ($120,000 flagged transaction)
    demonstrate_scenario(
        scenario_title="3. Human Outright Rejection (Security Block)",
        thread_id="txn_wire_103",
        initial_payload={
            "transaction_id": "TXN-8803",
            "recipient_account": "KY-UNKNOWN-7729104",
            "requested_amount": 120000.0,
            "purpose": "Unverified Hardware Purchase",
            "approval_status": "PENDING",
            "final_executed_amount": None,
            "audit_logs": []
        },
        human_decision={
            "action": "REJECT",
            "modified_amount": None,
            "reviewer_name": "Sarah Connor (Risk Compliance)",
            "reviewer_notes": "Unregistered offshore routing number. Suspicious activity."
        },
        app=app
    )


if __name__ == "__main__":
    main()
