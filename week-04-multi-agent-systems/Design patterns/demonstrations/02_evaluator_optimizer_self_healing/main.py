"""Executable Demonstration for Pattern 02: Evaluator-Optimizer & Self-Healing."""

import json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from .agent import build_evaluator_optimizer_agent
from .schemas import EvaluatorOptimizerState

console = Console()


def print_banner():
    console.print(Panel.fit(
        "[bold magenta]Pattern 02: Evaluator-Optimizer & Self-Healing[/bold magenta]\n"
        "[dim]Demonstrating closed-loop evaluation, Pydantic guardrails, and error-directed refinement.[/dim]",
        border_style="magenta"
    ))


def run_scenario(title: str, narrative: str, max_retries: int = 3):
    console.print(f"\n[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")
    console.print(f"[bold green]▶ SCENARIO:[/bold green] [bold white]{title}[/bold white]")
    console.print(f"[bold cyan]📄 RAW NARRATIVE:[/bold cyan]\n{narrative.strip()}")
    console.print(f"[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")

    try:
        agent_app = build_evaluator_optimizer_agent(provider="openai", model_name="gpt-4o-mini")
    except Exception as e:
        console.print(f"[bold red]❌ Failed to initialize agent:[/bold red] {e}")
        console.print("[dim]Tip: Ensure OPENAI_API_KEY is configured in .env file.[/dim]")
        return

    initial_state: EvaluatorOptimizerState = {
        "raw_incident_narrative": narrative,
        "draft_output": "",
        "parsed_report": None,
        "validation_errors": None,
        "error_history": [],
        "retry_count": 0,
        "max_retries": max_retries,
        "is_approved": False,
        "final_message": None
    }

    try:
        final_state = agent_app.invoke(initial_state)

        # Summary Table
        table = Table(title="📊 Evaluator-Optimizer Execution Summary", border_style="cyan")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Result", style="white")

        table.add_row("Approved Status", "[bold green]PASSED[/bold green]" if final_state.get("is_approved") else "[bold red]FAILED[/bold red]")
        table.add_row("Total Retries Used", str(final_state.get("retry_count", 0)))
        table.add_row("Errors Resolved", str(len(final_state.get("error_history", []))))

        console.print(table)

        if final_state.get("parsed_report"):
            console.print(Panel(
                json.dumps(final_state["parsed_report"], indent=2),
                title="🎯 Final Validated Production JSON",
                border_style="green"
            ))
        else:
            console.print(Panel(
                f"Draft failed validation after {max_retries} retries:\n" +
                "\n".join(final_state.get("validation_errors", [])),
                title="❌ Rejected Output (Dead-Letter Queue)",
                border_style="red"
            ))

    except Exception as e:
        console.print(f"[bold red]❌ Runtime execution error:[/bold red] {e}")


def main():
    print_banner()

    # Scenario 1: Complex Incident Narrative (Requires formatting ID to INC-XXXXX and enforcing SLA rule)
    narrative_1 = """
    Incident report from On-Call Engineer:
    Ticket Ref: #98421 (or INC-98421 in Jira).
    At 03:15 UTC, the Auth Gateway and Payment Processing service dropped to 0% availability due to a database connection pool starvation bug in SQLite replica concurrency. 
    Total outage lasted approximately 42 minutes before roll-back completed.
    This was classified as a Critical Severity 1 outage.
    Engineers increased the pool size to 50 connections and added automated circuit breaker retries to prevent starvation.
    """

    run_scenario(
        title="1. Incident Extraction with Automatic Schema & SLA Invariant Healing",
        narrative=narrative_1,
        max_retries=3
    )

    # Scenario 2: Truncated / Messy log requiring error-directed refinement
    narrative_2 = """
    Incident INC-10492: SEV-2 issue on Checkout API.
    Downtime was roughly 8 minutes. Root cause was an invalid memory leak in node worker thread after deployment v2.4.
    Actions taken: Rolled back to v2.3 and enabled garbage collection telemetry flags.
    """

    run_scenario(
        title="2. SEV-2 Incident Extraction with Fast Verification",
        narrative=narrative_2,
        max_retries=3
    )


if __name__ == "__main__":
    main()
