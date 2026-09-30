"""🎯 Level 1 - Drill 02: Cyclic Feedback Loops, Termination Criteria & Recursion Bounds.

This module provides an in-depth, hands-on drill on:
1. Dynamic Cyclic Feedback Loops: Generator <-> Critic iterative refinement loop.
2. State-Tracked Retry Budgets: Application-level loop control preventing infinite cycling.
3. Engine-Level Recursion Limits: `config={"recursion_limit": N}` and handling `GraphRecursionError`.
4. Circuit Breaker Fallback: Ensuring production graphs degrade gracefully instead of crashing.

Run directly:
    python3 02_loops_and_recursion_bounds.py
    # or
    python3 -m week-04-multi-agent-systems.stategraph_mastery.level_1_core_mechanics.02_loops_and_recursion_bounds
"""

import operator
from typing import Annotated, TypedDict, List, Dict, Any, Optional, Literal
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from langgraph.graph import StateGraph, START, END
from langgraph.errors import GraphRecursionError

console = Console()


# ============================================================================
# 1. STATE SCHEMA FOR CYCLIC FEEDBACK LOOPS
# ============================================================================

class CyclicRefinementState(TypedDict):
    # Core Task & Current Draft
    task_description: str
    current_draft: str
    
    # Evaluation & Feedback
    quality_score: float
    critique_notes: Annotated[List[str], operator.add]
    
    # Loop Bounds & Safety Controls
    iteration_count: int
    max_retries: int
    
    # Status & Output
    status: Literal["in_progress", "converged", "fallback_circuit_breaker", "exhausted"]
    final_output: Optional[str]


# ============================================================================
# 2. GRAPH NODES: GENERATOR, CRITIC, FINALIZER, FALLBACK
# ============================================================================

def generator_node(state: CyclicRefinementState) -> Dict[str, Any]:
    """Generates or iteratively refines the draft based on critic feedback."""
    current_iter = state.get("iteration_count", 0) + 1
    last_critique = state["critique_notes"][-1] if state["critique_notes"] else "Initial Generation"
    
    # Simulated improvement across iterations
    draft_quality_map = {
        1: "Draft v1: Basic outline with high-level points (Lacks detail and citations).",
        2: "Draft v2: Added technical details and architecture diagrams (Lacks benchmarks).",
        3: "Draft v3: Added latency benchmarks and production failure-mode analysis (Comprehensive).",
        4: "Draft v4: Polished executive summary with complete mathematical proofs."
    }
    
    new_draft = draft_quality_map.get(current_iter, f"Draft v{current_iter}: Further refined content.")
    
    return {
        "current_draft": new_draft,
        "iteration_count": current_iter,
        "status": "in_progress"
    }


def critic_node(state: CyclicRefinementState) -> Dict[str, Any]:
    """Evaluates the draft and assigns a quality score."""
    iteration = state["iteration_count"]
    
    # Simulated scoring: Improves on each iteration
    # Iter 1: 0.55 -> Iter 2: 0.78 -> Iter 3: 0.94
    simulated_scores = {
        1: (0.55, "Critique: Needs explicit benchmarks and failure modes."),
        2: (0.78, "Critique: Quality improved, but still missing p99 latency guarantees."),
        3: (0.94, "Critique: Excellent quality! Meets all rigorous production standards."),
        4: (0.99, "Critique: Outstanding perfection.")
    }
    
    score, feedback = simulated_scores.get(
        iteration,
        (0.60, f"Critique for iter {iteration}: Generic feedback.")
    )
    
    return {
        "quality_score": score,
        "critique_notes": [f"[Iter {iteration} | Score {score:.2f}] {feedback}"]
    }


def finalizer_node(state: CyclicRefinementState) -> Dict[str, Any]:
    """Finalizes the output once quality threshold is satisfied."""
    return {
        "status": "converged",
        "final_output": f"🏆 APPROVED FINAL OUTPUT (Score {state['quality_score']:.2f}):\n{state['current_draft']}"
    }


def fallback_circuit_breaker_node(state: CyclicRefinementState) -> Dict[str, Any]:
    """Graceful degradation circuit breaker when iteration budget is exhausted."""
    return {
        "status": "fallback_circuit_breaker",
        "final_output": (
            f"⚠️ DEGRADED BEST-EFFORT OUTPUT (Max retries {state['max_retries']} exhausted, "
            f"Last Score: {state['quality_score']:.2f}):\n{state['current_draft']}"
        )
    }


# ============================================================================
# 3. CONDITIONAL ROUTING LOGIC
# ============================================================================

def evaluate_loop_condition(
    state: CyclicRefinementState
) -> Literal["finalizer", "generator", "circuit_breaker"]:
    """Determines whether to exit, retry, or trip the circuit breaker.
    
    Decision Matrix:
    1. Score >= 0.90 -> 'finalizer' (Success)
    2. Score < 0.90 AND iteration_count < max_retries -> 'generator' (Loop back)
    3. Score < 0.90 AND iteration_count >= max_retries -> 'circuit_breaker' (Fallback)
    """
    quality_threshold = 0.90
    
    if state["quality_score"] >= quality_threshold:
        return "finalizer"
    
    if state["iteration_count"] < state["max_retries"]:
        return "generator"
    
    return "circuit_breaker"


# ============================================================================
# 4. GRAPH BUILDERS
# ============================================================================

def build_cyclic_refinement_graph():
    """Builds a robust, production-grade cyclic graph with circuit breaking.
    
               ┌───────────────────────┐
               ▼                       │ (Score < 0.90 & Retries < Max)
    START ──> generator ──> critic ────┤
                                       ├──> finalizer ──> END (Score >= 0.90)
                                       │
                                       └──> circuit_breaker ──> END (Retries Exhausted)
    """
    builder = StateGraph(CyclicRefinementState)
    
    builder.add_node("generator", generator_node)
    builder.add_node("critic", critic_node)
    builder.add_node("finalizer", finalizer_node)
    builder.add_node("circuit_breaker", fallback_circuit_breaker_node)
    
    builder.add_edge(START, "generator")
    builder.add_edge("generator", "critic")
    
    builder.add_conditional_edges(
        "critic",
        evaluate_loop_condition,
        {
            "finalizer": "finalizer",
            "generator": "generator",
            "circuit_breaker": "circuit_breaker"
        }
    )
    
    builder.add_edge("finalizer", END)
    builder.add_edge("circuit_breaker", END)
    
    return builder.compile()


def build_infinite_loop_buggy_graph():
    """Builds a buggy graph with an unconditional infinite loop to test recursion_limit."""
    def infinite_ping(state: CyclicRefinementState) -> Dict[str, Any]:
        return {"iteration_count": state.get("iteration_count", 0) + 1}
    
    def infinite_pong(state: CyclicRefinementState) -> Dict[str, Any]:
        return {"iteration_count": state.get("iteration_count", 0) + 1}
    
    builder = StateGraph(CyclicRefinementState)
    builder.add_node("ping", infinite_ping)
    builder.add_node("pong", infinite_pong)
    
    builder.add_edge(START, "ping")
    builder.add_edge("ping", "pong")
    builder.add_edge("pong", "ping")  # 💥 Infinite loop!
    
    return builder.compile()


# ============================================================================
# 5. INTERACTIVE CLI RUNNER & SCENARIOS
# ============================================================================

def run_scenario_1_convergence(app):
    """Scenario 1: Graph converges cleanly on Iteration 3 when score reaches 0.94."""
    console.print("\n[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")
    console.print("[bold green]SCENARIO 1: CLEAN CONVERGENCE (Quality Threshold Satisfied)[/bold green]")
    console.print("[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")

    initial_state: CyclicRefinementState = {
        "task_description": "Write High-Throughput Distributed Cache Architecture",
        "current_draft": "",
        "quality_score": 0.0,
        "critique_notes": [],
        "iteration_count": 0,
        "max_retries": 5,
        "status": "in_progress",
        "final_output": None
    }

    result = app.invoke(initial_state)

    trace_table = Table(title="🔁 Iterative Refinement Trace", border_style="cyan")
    trace_table.add_column("Iteration", justify="center", style="cyan")
    trace_table.add_column("Critique & Quality Log", style="white")

    for idx, log in enumerate(result["critique_notes"], 1):
        trace_table.add_row(str(idx), log)

    console.print(trace_table)

    console.print(Panel(
        f"[bold green]Status:[/bold green] {result['status']}\n"
        f"[bold green]Total Iterations:[/bold green] {result['iteration_count']} / {result['max_retries']}\n\n"
        f"{result['final_output']}",
        title="🎯 Final Graph Result",
        border_style="green"
    ))


def run_scenario_2_circuit_breaker(app):
    """Scenario 2: Low retry budget (max_retries=2) triggers the Circuit Breaker fallback."""
    console.print("\n[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")
    console.print("[bold green]SCENARIO 2: APPLICATION CIRCUIT BREAKER (Budget Exhaustion)[/bold green]")
    console.print("[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")

    initial_state: CyclicRefinementState = {
        "task_description": "Time-Sensitive Incident Report",
        "current_draft": "",
        "quality_score": 0.0,
        "critique_notes": [],
        "iteration_count": 0,
        "max_retries": 2,  # Strict budget: Not enough iterations to reach 0.90!
        "status": "in_progress",
        "final_output": None
    }

    result = app.invoke(initial_state)

    console.print(Panel(
        f"[bold yellow]Status:[/bold yellow] {result['status']}\n"
        f"[bold yellow]Iterations Executed:[/bold yellow] {result['iteration_count']} (Budget: {result['max_retries']})\n\n"
        f"{result['final_output']}",
        title="⚠️ Circuit Breaker Triggered (Graceful Fallback)",
        border_style="yellow"
    ))


def run_scenario_3_engine_recursion_limit():
    """Scenario 3: Engine-level recursion_limit trips GraphRecursionError on a runaway graph."""
    console.print("\n[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")
    console.print("[bold green]SCENARIO 3: ENGINE-LEVEL RECURSION_LIMIT SAFEGUARD[/bold green]")
    console.print("[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")

    buggy_app = build_infinite_loop_buggy_graph()
    initial_state: CyclicRefinementState = {
        "task_description": "Infinite Loop Test",
        "current_draft": "",
        "quality_score": 0.0,
        "critique_notes": [],
        "iteration_count": 0,
        "max_retries": 100,
        "status": "in_progress",
        "final_output": None
    }

    # Pass config with a low recursion_limit of 6 steps
    recursion_limit = 6
    console.print(f"[dim]Running infinite ping-pong graph with config={{'recursion_limit': {recursion_limit}}}...[/dim]")

    try:
        buggy_app.invoke(initial_state, config={"recursion_limit": recursion_limit})
        console.print("[bold red]❌ Error: Graph should have failed with GraphRecursionError![/bold red]")
    except GraphRecursionError as e:
        console.print(Panel(
            f"[bold red]✔ CAUGHT EXPECTED GraphRecursionError:[/bold red]\n{str(e)}\n\n"
            f"[bold white]Key Takeaway:[/bold white]\n"
            f"LangGraph's engine automatically terminates graph execution if step count exceeds `recursion_limit`.\n"
            f"Default is 25 steps. Always configure this in production invocations to prevent runaway API spend.",
            title="🛡️ Engine Safeguard Fired",
            border_style="red"
        ))


def main():
    console.print(Panel.fit(
        "[bold cyan]🎯 StateGraph Mastery - Level 1 Drill 02[/bold cyan]\n"
        "[bold white]Cyclic Loops, Dynamic Termination Bounds & Recursion Safeguards[/bold white]",
        border_style="cyan"
    ))

    cyclic_app = build_cyclic_refinement_graph()
    
    # 1. Successful iterative refinement convergence
    run_scenario_1_convergence(cyclic_app)
    
    # 2. Budget exhaustion with graceful fallback circuit breaker
    run_scenario_2_circuit_breaker(cyclic_app)
    
    # 3. Engine-level recursion limit protection
    run_scenario_3_engine_recursion_limit()


if __name__ == "__main__":
    main()
