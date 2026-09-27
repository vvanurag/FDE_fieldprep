"""Executable Demonstration for Pattern 04: Planner-Executor-Critic."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from .agent import build_planner_critic_agent
from .schemas import PlannerExecutorState

console = Console()


def print_banner():
    console.print(Panel.fit(
        "[bold cyan]Pattern 04: Planner–Executor–Critic (Plan-and-Solve)[/bold cyan]\n"
        "[dim]Demonstrating task decomposition, parallel worker fan-out, and budget auditing with re-planning loops.[/dim]",
        border_style="cyan"
    ))


def run_scenario(title: str, travel_request: str, budget_limit_usd: float, max_revisions: int = 2):
    console.print(f"\n[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")
    console.print(f"[bold green]▶ SCENARIO:[/bold green] [bold white]{title}[/bold white]")
    console.print(f"[bold cyan]🌍 REQUEST:[/bold cyan] {travel_request}")
    console.print(f"[bold magenta]💰 BUDGET LIMIT:[/bold magenta] ${budget_limit_usd:,.2f}")
    console.print(f"[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")

    try:
        agent_app = build_planner_critic_agent(provider="openai", model_name="gpt-4o-mini")
    except Exception as e:
        console.print(f"[bold red]❌ Failed to initialize agent:[/bold red] {e}")
        console.print("[dim]Tip: Ensure OPENAI_API_KEY is configured in .env file.[/dim]")
        return

    initial_state: PlannerExecutorState = {
        "travel_request": travel_request,
        "budget_limit_usd": budget_limit_usd,
        "plan": None,
        "flight_results": None,
        "hotel_results": None,
        "activity_results": None,
        "critic_audit": None,
        "revision_count": 0,
        "max_revisions": max_revisions,
        "final_dossier": None
    }

    try:
        final_state = agent_app.invoke(initial_state)
        audit = final_state.get("critic_audit") or {}

        # Telemetry Table
        table = Table(title="📋 Planner-Executor-Critic Telemetry", border_style="cyan")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        table.add_row("Total Cost", f"${audit.get('total_estimated_cost_usd', 0.0):,.2f}")
        table.add_row("Budget Limit", f"${budget_limit_usd:,.2f}")
        table.add_row("Surplus / Deficit", f"${audit.get('budget_surplus_or_deficit', 0.0):,.2f}")
        table.add_row("Critic Verdict", "[bold green]APPROVED[/bold green]" if audit.get("is_approved") else "[bold red]REJECTED[/bold red]")
        table.add_row("Revisions Required", str(final_state.get("revision_count", 0)))

        console.print(table)

        # Output Dossier
        console.print(Panel(
            final_state.get("final_dossier", "No dossier generated."),
            title="🎯 Final Travel Dossier",
            border_style="green"
        ))

    except Exception as e:
        console.print(f"[bold red]❌ Runtime execution error:[/bold red] {e}")


def main():
    print_banner()

    # Scenario 1: Budget-Constrained Trip to Tokyo (Forces re-planning loop)
    run_scenario(
        title="1. Tight Budget Tokyo Itinerary (Triggers Critic Rejection & Re-planning)",
        travel_request="Plan a 6-night vacation to Tokyo including roundtrip flights from SFO, hotel stay in central Tokyo, and cultural sight-seeing activities.",
        budget_limit_usd=2300.0,
        max_revisions=2
    )

    # Scenario 2: Generous Budget Trip to Paris (Approved on First Pass)
    run_scenario(
        title="2. Premium Paris Vacation (Approved on First Pass)",
        travel_request="Plan a 5-night trip to Paris with comfortable flights from JFK, boutique accommodation, and museum passes.",
        budget_limit_usd=4000.0,
        max_revisions=2
    )


if __name__ == "__main__":
    main()
