"""Main executable runner for Pattern 01: ReAct Tool-Calling Loop Demonstration."""

import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from langchain_core.messages import HumanMessage
from .agent import build_react_agent
from .schemas import ReActAgentState

console = Console()


def print_banner():
    console.print(Panel.fit(
        "[bold cyan]Pattern 01: ReAct (Reason + Act) / Tool-Calling Loop[/bold cyan]\n"
        "[dim]Demonstrating dynamic multi-step tool execution, self-healing, and recursion bounds.[/dim]",
        border_style="cyan"
    ))


def run_scenario(title: str, query: str, max_iterations: int = 6):
    console.print(f"\n[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")
    console.print(f"[bold green]▶ SCENARIO:[/bold green] [bold white]{title}[/bold white]")
    console.print(f"[bold cyan]💬 USER QUERY:[/bold cyan] {query}")
    console.print(f"[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")

    # Build agent
    try:
        agent_app = build_react_agent(provider="openai", model_name="gpt-4o-mini")
    except Exception as e:
        console.print(f"[bold red]❌ Failed to initialize agent:[/bold red] {e}")
        console.print("[dim]Tip: Ensure OPENAI_API_KEY is configured in .env file.[/dim]")
        return

    initial_state: ReActAgentState = {
        "messages": [HumanMessage(content=query)],
        "iteration_count": 0,
        "visited_tools": [],
        "max_iterations": max_iterations,
        "is_terminated": False,
        "final_output": None
    }

    try:
        final_state = agent_app.invoke(initial_state)
        
        # Display Tool Call History Table
        table = Table(title="🛠 Tool Invocation Execution Trace", border_style="yellow")
        table.add_column("Step", justify="center", style="cyan", no_wrap=True)
        table.add_column("Tool Name", style="magenta")
        table.add_column("Arguments", style="white")

        for idx, tool_record in enumerate(final_state.get("visited_tools", []), 1):
            table.add_row(str(idx), tool_record["tool"], str(tool_record["args"]))

        console.print(table)

        # Print Final Answer
        final_response = final_state["messages"][-1].content
        console.print(Panel(
            final_response,
            title="🎯 Final Agent Response",
            border_style="green"
        ))

    except Exception as e:
        console.print(f"[bold red]❌ Runtime execution error:[/bold red] {e}")


def main():
    print_banner()

    # Scenario 1: Compound Multi-Step Query (Stock -> Calculation -> FX Conversion -> SEC Filing)
    run_scenario(
        title="1. Multi-Step Compound Financial Research",
        query="What is the current stock price of Apple (AAPL), what is the total value of 75 shares converted to EUR, and what was Apple's total revenue in fiscal year 2023?",
        max_iterations=8
    )

    # Scenario 2: Error Recovery on Invalid Ticker
    run_scenario(
        title="2. Self-Healing from Tool Argument Error",
        query="Can you fetch the stock price for APLE and convert $1000 to EUR?",
        max_iterations=6
    )


if __name__ == "__main__":
    main()
