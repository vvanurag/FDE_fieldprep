"""Executable Demonstration for Pattern 05: Multi-Agent Collaboration & Networked Teams."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from .agent import build_multi_agent_team
from .schemas import MultiAgentState

console = Console()


def print_banner():
    console.print(Panel.fit(
        "[bold green]Pattern 05: Multi-Agent Collaboration (Hierarchical Team)[/bold green]\n"
        "[dim]Demonstrating role-specialized agents (Supervisor, Researcher, Coder, Reviewer, Synthesizer) over shared graph state.[/dim]",
        border_style="green"
    ))


def run_scenario(title: str, task_goal: str, max_iterations: int = 8):
    console.print(f"\n[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")
    console.print(f"[bold green]▶ SCENARIO:[/bold green] [bold white]{title}[/bold white]")
    console.print(f"[bold cyan]🎯 TASK GOAL:[/bold cyan] {task_goal}")
    console.print(f"[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")

    try:
        agent_app = build_multi_agent_team(provider="openai", model_name="gpt-4o-mini")
    except Exception as e:
        console.print(f"[bold red]❌ Failed to initialize agent:[/bold red] {e}")
        console.print("[dim]Tip: Ensure OPENAI_API_KEY is configured in .env file.[/dim]")
        return

    initial_state: MultiAgentState = {
        "task_goal": task_goal,
        "messages": [],
        "current_agent": None,
        "next_agent": None,
        "supervisor_notes": None,
        "research_summary": None,
        "code_artifact": None,
        "review_verdict": None,
        "iteration_count": 0,
        "max_iterations": max_iterations,
        "final_deliverable": None
    }

    try:
        final_state = agent_app.invoke(initial_state)

        # Team Activity Table
        table = Table(title="👥 Multi-Agent Collaboration Summary", border_style="cyan")
        table.add_column("Artifact / Metric", style="cyan", no_wrap=True)
        table.add_column("Status / Details", style="white")

        table.add_row("Total Coordination Turns", str(final_state.get("iteration_count", 0)))
        table.add_row("Research Component", "[bold green]Completed[/bold green]" if final_state.get("research_summary") else "[red]Missing[/red]")
        table.add_row("Code Artifact", "[bold green]Generated[/bold green]" if final_state.get("code_artifact") else "[red]Missing[/red]")
        
        review_data = final_state.get("review_verdict") or {}
        is_app = review_data.get("is_approved", False)
        table.add_row("Reviewer Security Audit", "[bold green]APPROVED[/bold green]" if is_app else "[yellow]Revisions Needed[/yellow]")

        console.print(table)

        # Output Deliverable
        console.print(Panel(
            final_state.get("final_deliverable", "No deliverable produced."),
            title="📦 Final Multi-Agent Deliverable",
            border_style="green"
        ))

    except Exception as e:
        console.print(f"[bold red]❌ Runtime execution error:[/bold red] {e}")


def main():
    print_banner()

    run_scenario(
        title="1. Enterprise Concurrency Feature: Token Bucket Rate Limiter",
        task_goal="Design and implement a thread-safe in-memory Token Bucket rate limiter in Python with millisecond accuracy, per-client tier limits, and comprehensive unit tests.",
        max_iterations=8
    )


if __name__ == "__main__":
    main()
