"""Executable Demonstration for Pattern 03: Router & Intent Classifier."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from .agent import build_router_agent
from .schemas import RouterAgentState

console = Console()


def print_banner():
    console.print(Panel.fit(
        "[bold yellow]Pattern 03: Dynamic Router & Intent Classifier[/bold yellow]\n"
        "[dim]Demonstrating structured classification, confidence threshold gating, and specialist dispatch.[/dim]",
        border_style="yellow"
    ))


def run_scenario(title: str, query: str, confidence_threshold: float = 0.75):
    console.print(f"\n[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")
    console.print(f"[bold green]▶ SCENARIO:[/bold green] [bold white]{title}[/bold white]")
    console.print(f"[bold cyan]💬 QUERY:[/bold cyan] {query}")
    console.print(f"[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")

    try:
        agent_app = build_router_agent(provider="openai", model_name="gpt-4o-mini")
    except Exception as e:
        console.print(f"[bold red]❌ Failed to initialize agent:[/bold red] {e}")
        console.print("[dim]Tip: Ensure OPENAI_API_KEY is configured in .env file.[/dim]")
        return

    initial_state: RouterAgentState = {
        "user_query": query,
        "classification": None,
        "confidence_threshold": confidence_threshold,
        "routed_specialist": None,
        "specialist_response": None
    }

    try:
        final_state = agent_app.invoke(initial_state)
        cls_data = final_state.get("classification") or {}

        # Classification Table
        table = Table(title="🔀 Router Classification Telemetry", border_style="cyan")
        table.add_column("Attribute", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        table.add_row("Primary Intent", str(cls_data.get("primary_intent")))
        table.add_row("Confidence Score", f"{cls_data.get('confidence_score', 0.0):.2f}")
        table.add_row("Threshold Gating", f"{confidence_threshold:.2f}")
        table.add_row("Extracted Entities", str(cls_data.get("detected_entities", {})))
        table.add_row("Routed Handler", f"[bold green]{final_state.get('routed_specialist')}[/bold green]")
        table.add_row("Router Reasoning", str(cls_data.get("reasoning")))

        console.print(table)

        # Output Panel
        console.print(Panel(
            final_state.get("specialist_response", "No response generated."),
            title=f"🎯 Response from {final_state.get('routed_specialist')}",
            border_style="green" if final_state.get("routed_specialist") != "Clarification / Fallback Gate" else "yellow"
        ))

    except Exception as e:
        console.print(f"[bold red]❌ Runtime execution error:[/bold red] {e}")


def main():
    print_banner()

    # Scenario 1: Billing & Invoice Query
    run_scenario(
        title="1. Explicit Billing & Invoicing Request",
        query="We were double charged on our annual subscription for invoice INV-48201. Can you issue a refund to our corporate card?"
    )

    # Scenario 2: Technical Support
    run_scenario(
        title="2. Technical Support / SRE Incident",
        query="Our Python SDK client is intermittently failing with '504 Gateway Timeout' during batch export on the /v2/records endpoint."
    )

    # Scenario 3: Enterprise Sales Inquiry
    run_scenario(
        title="3. Enterprise Sales & Volume Licensing",
        query="We are an engineering team of 300 developers evaluating your enterprise tier. Do you support custom SOC2 Type II audits and SSO via Okta?"
    )

    # Scenario 4: Ambiguous / Low Confidence Query (Triggers Clarification Gate)
    run_scenario(
        title="4. Ambiguous Query Triggering Clarification Gate",
        query="Hey, I need help with my account, something is not working right.",
        confidence_threshold=0.75
    )


if __name__ == "__main__":
    main()
