"""LangGraph Human-in-the-Loop (HITL) StateGraph implementation with Checkpointers."""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt
from langchain_core.messages import SystemMessage, HumanMessage
from common.llm_factory import get_llm
from common.logging import get_logger
from .schemas import HITLAgentState, RefundRequest
from .policy_engine import evaluate_transaction_policy

logger = get_logger("hitl_agent")

INTAKE_SYSTEM_PROMPT = """You are a Customer Service Intake Agent for an enterprise fintech platform.
Extract structured refund request details from the customer message.
Ensure you accurately parse the transaction_id (e.g. TX-XXXXX), customer_id (e.g. CUST-XXX), requested amount, and reason.
"""


def build_hitl_agent(provider: str = "openai", model_name: str = "gpt-4o-mini", checkpointer: Any = None):
    """Compiles the HITL LangGraph StateGraph with persistent checkpointing."""
    
    base_llm = get_llm(provider=provider, model_name=model_name, temperature=0.0)
    structured_intake_llm = base_llm.with_structured_output(RefundRequest)
    memory = checkpointer or MemorySaver()

    # 1. Intake & Analysis Node
    def intake_node(state: HITLAgentState) -> Dict[str, Any]:
        query = state["customer_query"]
        logger.info(f"[bold cyan]📥 [Node: Intake] Parsing customer request:[/bold cyan] '{query}'")
        
        parsed: RefundRequest = structured_intake_llm.invoke([
            SystemMessage(content=INTAKE_SYSTEM_PROMPT),
            HumanMessage(content=query)
        ])
        
        logger.info(
            f"   [yellow]Parsed Details:[/yellow] TxID=[bold]{parsed.transaction_id}[/bold] | "
            f"Customer=[bold]{parsed.customer_id}[/bold] | "
            f"Amount=[bold]${parsed.requested_amount_usd:.2f}[/bold]"
        )
        
        return {"refund_details": parsed.model_dump()}

    # 2. Policy Gate Node
    def policy_gate_node(state: HITLAgentState) -> Dict[str, Any]:
        details = state["refund_details"] or {}
        req = RefundRequest(**details)
        
        payload = evaluate_transaction_policy(req)
        logger.info(
            f"[bold magenta]🛡️ [Node: Policy Gate] Risk Tier: {payload.risk_level.value} | "
            f"Requires Human Approval: [bold]{payload.requires_human_approval}[/bold][/bold magenta]"
        )
        
        return {"pending_action": payload.model_dump()}

    # 3. Human Approval Checkpoint Node (Pauses execution using LangGraph interrupt)
    def human_approval_node(state: HITLAgentState) -> Dict[str, Any]:
        pending = state.get("pending_action") or {}
        logger.warning(
            f"[bold yellow]⏸️ [Node: HITL Gate] Halting execution! Awaiting human supervisor review for Tx {pending.get('transaction_id')}...[/bold yellow]"
        )
        
        # Trigger native LangGraph interrupt primitive
        # Execution halts here, serializes state to checkpointer, and returns to caller
        human_input = interrupt({
            "action": "SUPERVISOR_APPROVAL_REQUIRED",
            "message": f"High-value refund (${pending.get('amount_usd'):.2f}) requires human supervisor approval.",
            "transaction_id": pending.get("transaction_id"),
            "customer_id": pending.get("customer_id"),
            "amount_usd": pending.get("amount_usd")
        })
        
        # When graph is resumed with graph.invoke(Command(resume=...)) or updated state:
        logger.info(f"[bold green]▶️ [HITL Gate Resumed] Received supervisor input: {human_input}[/bold green]")
        
        # Default to approved if resumed directly
        verdict = state.get("human_verdict") or (human_input.get("verdict") if isinstance(human_input, dict) else "approved")
        notes = state.get("human_notes") or (human_input.get("notes") if isinstance(human_input, dict) else "Supervisor approved via gate.")
        
        return {
            "human_verdict": verdict,
            "human_notes": notes
        }

    # 4. Execute Transaction Node (External Banking API simulation)
    def execute_transaction_node(state: HITLAgentState) -> Dict[str, Any]:
        pending = state.get("pending_action") or {}
        amt = pending.get("amount_usd", 0.0)
        tx_id = pending.get("transaction_id", "N/A")
        cust_id = pending.get("customer_id", "N/A")
        
        logger.info(f"[bold green]💰 [Node: Banking API] EXECUTING REFUND: ${amt:.2f} to {cust_id} (Tx: {tx_id})...[/bold green]")
        
        return {
            "execution_result": {
                "status": "SUCCESS",
                "payment_gateway_reference": f"stripe_re_{tx_id}_success",
                "disbursed_amount_usd": amt,
                "message": f"Successfully disbursed ${amt:.2f} to customer {cust_id}."
            },
            "is_completed": True
        }

    # 5. Abort Transaction Node
    def abort_transaction_node(state: HITLAgentState) -> Dict[str, Any]:
        pending = state.get("pending_action") or {}
        tx_id = pending.get("transaction_id", "N/A")
        reason = state.get("human_notes") or "Supervisor rejected transaction."
        
        logger.error(f"[bold red]🚫 [Node: Abort] TRANSACTION REJECTED: Tx {tx_id}. Reason: {reason}[/bold red]")
        
        return {
            "execution_result": {
                "status": "REJECTED",
                "message": f"Refund for {tx_id} was rejected by supervisor: {reason}"
            },
            "is_completed": True
        }

    # 6. Routing Logic
    def route_policy(state: HITLAgentState) -> str:
        pending = state.get("pending_action") or {}
        if pending.get("requires_human_approval", False):
            return "human_approval"
        return "execute"

    def route_verdict(state: HITLAgentState) -> str:
        verdict = (state.get("human_verdict") or "approved").lower()
        if verdict in ("approved", "edited", "auto_approved"):
            return "execute"
        return "abort"

    # Assemble StateGraph
    workflow = StateGraph(HITLAgentState)

    workflow.add_node("intake", intake_node)
    workflow.add_node("policy_gate", policy_gate_node)
    workflow.add_node("human_approval", human_approval_node)
    workflow.add_node("execute_transaction", execute_transaction_node)
    workflow.add_node("abort_transaction", abort_transaction_node)

    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "policy_gate")

    workflow.add_conditional_edges(
        "policy_gate",
        route_policy,
        {
            "human_approval": "human_approval",
            "execute": "execute_transaction"
        }
    )

    workflow.add_conditional_edges(
        "human_approval",
        route_verdict,
        {
            "execute": "execute_transaction",
            "abort": "abort_transaction"
        }
    )

    workflow.add_edge("execute_transaction", END)
    workflow.add_edge("abort_transaction", END)

    return workflow.compile(checkpointer=memory)
