"""Executable Demonstration for Pattern 06: Human-in-the-Loop (HITL)."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from langgraph.types import Command
from .agent import build_hitl_agent
from .schemas import HITLAgentState

console = Console()


def print_banner():
    console.print(Panel.fit(
        "[bold red]Pattern 06: Human-in-the-Loop (HITL)[/bold red]\n"
        "[dim]Demonstrating state persistence, interrupt gates, supervisor inspection, state editing, and workflow resumption.[/dim]",
        border_style="red"
    ))


def run_scenario_auto_approve():
    """Scenario 1: Low-Risk Transaction ($45.00) -> Executes without human interrupt."""
    console.print(f"\n[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")
    console.print("[bold green]▶ SCENARIO 1: Automated Low-Risk Transaction ($45.00)[/bold green]")
    console.print("[dim]Query is under the $100 policy threshold -> Should execute directly without human pause.[/dim]")
    console.print(f"[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")

    app = build_hitl_agent(provider="openai", model_name="gpt-4o-mini")
    config = {"configurable": {"thread_id": "thread_auto_001"}}

    query = "Customer CUST-104 requests a $45.00 refund on transaction TX-58201 due to duplicate item scan."
    state: HITLAgentState = {
        "customer_query": query,
        "refund_details": None,
        "pending_action": None,
        "human_verdict": None,
        "human_notes": None,
        "execution_result": None,
        "is_completed": False
    }

    result = app.invoke(state, config=config)
    
    console.print(Panel(
        f"Execution Result: {result.get('execution_result')}\nCompleted: {result.get('is_completed')}",
        title="✅ Scenario 1: Auto-Approved Result",
        border_style="green"
    ))


def run_scenario_high_risk_approval():
    """Scenario 2: High-Risk Transaction ($450.00) -> Pauses at interrupt, awaits supervisor approval, then resumes."""
    console.print(f"\n[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")
    console.print("[bold green]▶ SCENARIO 2: High-Risk Pause & Human Approval ($450.00)[/bold green]")
    console.print("[dim]Query exceeds $100 -> Pauses at interrupt gate, waits for human supervisor, then resumes.[/dim]")
    console.print(f"[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")

    app = build_hitl_agent(provider="openai", model_name="gpt-4o-mini")
    config = {"configurable": {"thread_id": "thread_approval_002"}}

    query = "Enterprise Customer CUST-992 requests a refund of $450.00 for annual license cancellation on transaction TX-99410."
    state: HITLAgentState = {
        "customer_query": query,
        "refund_details": None,
        "pending_action": None,
        "human_verdict": None,
        "human_notes": None,
        "execution_result": None,
        "is_completed": False
    }

    # Step 1: Initial invocation -> will pause at interrupt
    console.print("[cyan]1. Starting agent execution (will hit interrupt)...[/cyan]")
    paused_result = app.invoke(state, config=config)

    # Step 2: Check current state snapshot in checkpointer
    current_snapshot = app.get_state(config)
    console.print(f"\n[bold yellow]⏸️ Graph Paused at Checkpoint Node:[/bold yellow] {current_snapshot.next}")
    pending_info = current_snapshot.values.get("pending_action", {})
    
    table = Table(title="🧑‍💼 Supervisor Approval Queue Modal", border_style="yellow")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Transaction ID", str(pending_info.get("transaction_id")))
    table.add_row("Customer ID", str(pending_info.get("customer_id")))
    table.add_row("Amount USD", f"${pending_info.get('amount_usd', 0.0):.2f}")
    table.add_row("Risk Level", str(pending_info.get("risk_level")))
    console.print(table)

    # Step 3: Human Supervisor grants approval and resumes workflow
    console.print("\n[bold green]2. Human Supervisor clicks 'APPROVE' -> Resuming execution from checkpoint...[/bold green]")
    resume_command = Command(resume={"verdict": "approved", "notes": "Approved by Finance Director."})
    final_result = app.invoke(resume_command, config=config)

    console.print(Panel(
        f"Execution Result: {final_result.get('execution_result')}\nCompleted: {final_result.get('is_completed')}",
        title="🎯 Scenario 2: Resumed & Executed Result",
        border_style="green"
    ))


def run_scenario_state_editing():
    """Scenario 3: State Editing -> Supervisor modifies the refund amount from $1,200 to $600 before approval."""
    console.print(f"\n[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")
    console.print("[bold green]▶ SCENARIO 3: Review-and-Edit ($1,200 -> Edited to $600)[/bold green]")
    console.print("[dim]Supervisor intercepts payload, modifies amount parameter, and resumes with edited state.[/dim]")
    console.print(f"[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")

    app = build_hitl_agent(provider="openai", model_name="gpt-4o-mini")
    config = {"configurable": {"thread_id": "thread_edit_003"}}

    query = "Customer CUST-401 requests a refund of $1,200.00 on transaction TX-10932 for damaged equipment."
    state: HITLAgentState = {
        "customer_query": query,
        "refund_details": None,
        "pending_action": None,
        "human_verdict": None,
        "human_notes": None,
        "execution_result": None,
        "is_completed": False
    }

    # Step 1: Initial invocation
    app.invoke(state, config=config)
    snapshot = app.get_state(config)
    original_action = snapshot.values["pending_action"]
    console.print(f"[yellow]Original Pending Action Amount:[/yellow] ${original_action['amount_usd']:.2f}")

    # Step 2: Supervisor edits the state (caps refund at $600 per company damage cap policy)
    console.print("[bold cyan]✏️ Supervisor edits state: Capping refund to $600.00 per partial warranty policy...[/bold cyan]")
    edited_action = dict(original_action)
    edited_action["amount_usd"] = 600.0
    edited_action["supervisor_notes"] = "Partial damage warranty cap of $600 applied by supervisor."
    
    app.update_state(config, {"pending_action": edited_action, "human_verdict": "edited", "human_notes": "Capped at $600"})

    # Step 3: Resume execution
    console.print("[bold green]▶ Resuming execution with edited state...[/bold green]")
    resume_command = Command(resume={"verdict": "edited", "notes": "Approved with $600 cap."})
    final_result = app.invoke(resume_command, config=config)

    console.print(Panel(
        f"Execution Result: {final_result.get('execution_result')}\nCompleted: {final_result.get('is_completed')}",
        title="🎯 Scenario 3: State-Edited Execution Result",
        border_style="green"
    ))


def main():
    print_banner()
    run_scenario_auto_approve()
    run_scenario_high_risk_approval()
    run_scenario_state_editing()


if __name__ == "__main__":
    main()
