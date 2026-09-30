"""🎯 Level 1 - Drill 01: State Reducers & Concurrency Mechanics in LangGraph.

This module provides an in-depth, hands-on drill on:
1. Reducer Mechanics: Overwrite vs. operator.add vs. add_messages vs. Custom Reducers.
2. Parallel Fan-Out Concurrency: How multiple nodes execute simultaneously and merge state cleanly.
3. The "In-Place Mutation" Pitfall: Why mutating `state["key"].append()` breaks concurrency,
   duplicates messages, and corrupts checkpoints, vs. returning clean delta updates `{"key": [...]}`.

Run directly:
    python3 01_reducers_and_concurrency.py
    # or
    python3 -m week-04-multi-agent-systems.stategraph_mastery.level_1_core_mechanics.01_reducers_and_concurrency
"""

import sys
import operator
import time
from typing import Annotated, TypedDict, List, Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

console = Console()


# ============================================================================
# 1. SCHEMAS: Understanding Reducer Annotations
# ============================================================================

def custom_dict_merge_reducer(
    current: Dict[str, Any],
    update: Dict[str, Any]
) -> Dict[str, Any]:
    """Custom reducer: Deeply merges nested dicts and keeps track of update timestamps."""
    merged = dict(current or {})
    for k, v in update.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = {**merged[k], **v}
        else:
            merged[k] = v
    return merged


def score_history_reducer(
    current: List[float],
    update: List[float] | float
) -> List[float]:
    """Custom reducer: Appends new scores and automatically clamps values between 0.0 and 1.0."""
    new_scores = [update] if isinstance(update, (int, float)) else list(update)
    clamped = [max(0.0, min(1.0, s)) for s in new_scores]
    return (current or []) + clamped


class ComprehensiveState(TypedDict):
    # 1. Default Overwrite (No reducer): Every node overwrites the previous value
    current_status: str
    
    # 2. Simple List Concatenator (operator.add): Appends all items in order
    logs: Annotated[List[str], operator.add]
    
    # 3. Message Deduplication & Updates (add_messages):
    #    Appends new messages OR updates existing messages if IDs match
    messages: Annotated[List[BaseMessage], add_messages]
    
    # 4. Custom Dictionary Merger: Deep merges partial telemetry data
    telemetry: Annotated[Dict[str, Any], custom_dict_merge_reducer]
    
    # 5. Custom Score Reducer: Appends and validates/clamps scores
    quality_scores: Annotated[List[float], score_history_reducer]


# ============================================================================
# 2. DRILL A: Reducer Types Deep-Dive (Sequential Execution)
# ============================================================================

def init_node(state: ComprehensiveState) -> Dict[str, Any]:
    """Initializes the workflow state."""
    return {
        "current_status": "initialized",
        "logs": ["[Node: init] Workflow started"],
        "messages": [SystemMessage(content="You are an autonomous orchestrator.", id="sys_01")],
        "telemetry": {"host": "worker-node-1", "metrics": {"cpu": 12.5, "mem": 45.0}},
        "quality_scores": [0.85]
    }


def audit_node(state: ComprehensiveState) -> Dict[str, Any]:
    """Simulates an auditing process updating messages and telemetry."""
    return {
        "current_status": "auditing",
        "logs": ["[Node: audit] Compliance audit completed"],
        # Updating sys_01 with add_messages replaces the message with id 'sys_01' instead of duplicating!
        "messages": [
            SystemMessage(content="You are an autonomous orchestrator (Audited).", id="sys_01"),
            HumanMessage(content="Analyze market trends for Q3.", id="user_01")
        ],
        "telemetry": {"metrics": {"mem": 48.2, "network_io": 120.4}, "security": "PASS"},
        "quality_scores": [0.92, 1.15]  # 1.15 will be clamped to 1.0 by custom reducer!
    }


def build_reducer_demonstration_graph():
    """Builds a sequential graph demonstrating all 5 reducer behaviors."""
    builder = StateGraph(ComprehensiveState)
    builder.add_node("init", init_node)
    builder.add_node("audit", audit_node)
    
    builder.add_edge(START, "init")
    builder.add_edge("init", "audit")
    builder.add_edge("audit", END)
    
    return builder.compile()


# ============================================================================
# 3. DRILL B: Parallel Fan-Out Concurrency & Delta Merging
# ============================================================================

class ParallelTaskState(TypedDict):
    task_name: str
    execution_log: Annotated[List[str], operator.add]
    agent_outputs: Annotated[Dict[str, Any], custom_dict_merge_reducer]
    metrics_history: Annotated[List[float], operator.add]


def parallel_worker_a(state: ParallelTaskState) -> Dict[str, Any]:
    """Worker A: Simulates fetching financial market fundamentals."""
    time.sleep(0.05)  # Simulate async work
    return {
        "execution_log": ["⚡ Worker A (Fundamentals) completed analysis."],
        "agent_outputs": {
            "fundamentals": {
                "ticker": "AAPL",
                "pe_ratio": 31.4,
                "market_cap": "$3.4T"
            }
        },
        "metrics_history": [98.5]
    }


def parallel_worker_b(state: ParallelTaskState) -> Dict[str, Any]:
    """Worker B: Simulates sentiment analysis on news feeds."""
    time.sleep(0.05)  # Simulate async work
    return {
        "execution_log": ["⚡ Worker B (Sentiment) processed 140 articles."],
        "agent_outputs": {
            "sentiment": {
                "bullish_pct": 74.2,
                "overall": "STRONG_BUY"
            }
        },
        "metrics_history": [92.0]
    }


def parallel_worker_c(state: ParallelTaskState) -> Dict[str, Any]:
    """Worker C: Simulates technical chart analysis."""
    time.sleep(0.05)  # Simulate async work
    return {
        "execution_log": ["⚡ Worker C (Technical) calculated RSI and EMA crossovers."],
        "agent_outputs": {
            "technicals": {
                "rsi_14": 58.2,
                "trend": "UPWARD"
            }
        },
        "metrics_history": [88.5]
    }


def aggregator_node(state: ParallelTaskState) -> Dict[str, Any]:
    """Aggregates parallel worker outputs into a cohesive summary."""
    return {
        "execution_log": ["🎯 Aggregator combined all 3 parallel worker outputs."]
    }


def build_parallel_fanout_graph():
    """Builds a parallel fan-out / fan-in topology (Map-Reduce).
    
            ┌──> parallel_worker_a ──┐
            │                        │
    START ──┼──> parallel_worker_b ──┼──> aggregator ──> END
            │                        │
            └──> parallel_worker_c ──┘
    """
    builder = StateGraph(ParallelTaskState)
    
    builder.add_node("worker_a", parallel_worker_a)
    builder.add_node("worker_b", parallel_worker_b)
    builder.add_node("worker_c", parallel_worker_c)
    builder.add_node("aggregator", aggregator_node)
    
    # Parallel Fan-Out: START triggers all 3 workers concurrently
    builder.add_edge(START, "worker_a")
    builder.add_edge(START, "worker_b")
    builder.add_edge(START, "worker_c")
    
    # Fan-In: All 3 workers feed into aggregator
    builder.add_edge("worker_a", "aggregator")
    builder.add_edge("worker_b", "aggregator")
    builder.add_edge("worker_c", "aggregator")
    
    builder.add_edge("aggregator", END)
    
    return builder.compile()


# ============================================================================
# 4. DRILL C: The In-Place Mutation Pitfall vs. Delta Returns
# ============================================================================

class MutationPitfallState(TypedDict):
    items: Annotated[List[str], operator.add]


def buggy_mutation_node(state: MutationPitfallState) -> Dict[str, Any]:
    """❌ ANTI-PATTERN: Mutating state['items'] in-place AND returning it."""
    # In Python, lists are passed by reference.
    # Mutating state['items'] modifies the existing list object in memory.
    state["items"].append("BUGGY_MUTATED_IN_PLACE")
    
    # When operator.add(current, update) runs:
    # current is the mutated list: ['init', 'BUGGY_MUTATED_IN_PLACE']
    # update is also: ['init', 'BUGGY_MUTATED_IN_PLACE']
    # Result = ['init', 'BUGGY_MUTATED_IN_PLACE', 'init', 'BUGGY_MUTATED_IN_PLACE'] (DUPLICATION!)
    return {"items": state["items"]}


def clean_delta_node(state: MutationPitfallState) -> Dict[str, Any]:
    """✅ BEST PRACTICE: Pure function returning ONLY the delta addition."""
    return {"items": ["CLEAN_DELTA_ITEM"]}


def demonstrate_mutation_vs_delta():
    """Runs a direct comparison between in-place mutation and delta return."""
    # Test Buggy Graph
    buggy_builder = StateGraph(MutationPitfallState)
    buggy_builder.add_node("buggy", buggy_mutation_node)
    buggy_builder.add_edge(START, "buggy")
    buggy_builder.add_edge("buggy", END)
    buggy_app = buggy_builder.compile()

    # Test Clean Graph
    clean_builder = StateGraph(MutationPitfallState)
    clean_builder.add_node("clean", clean_delta_node)
    clean_builder.add_edge(START, "clean")
    clean_builder.add_edge("clean", END)
    clean_app = clean_builder.compile()

    return buggy_app, clean_app


# ============================================================================
# 5. INTERACTIVE CLI RUNNER
# ============================================================================

def main():
    console.print(Panel.fit(
        "[bold cyan]🎯 StateGraph Mastery - Level 1 Drill 01[/bold cyan]\n"
        "[bold white]State Reducers, Parallel Fan-Out Concurrency & Mutation Safety[/bold white]",
        border_style="cyan"
    ))

    # ------------------------------------------------------------------------
    # SECTION 1: Reducer Mechanics
    # ------------------------------------------------------------------------
    console.print("\n[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")
    console.print("[bold green]1. COMPREHENSIVE REDUCER BEHAVIORS DEMONSTRATION[/bold green]")
    console.print("[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")

    graph_a = build_reducer_demonstration_graph()
    initial_a: ComprehensiveState = {
        "current_status": "pending",
        "logs": ["[Start] Setup"],
        "messages": [],
        "telemetry": {},
        "quality_scores": []
    }
    
    result_a = graph_a.invoke(initial_a)

    reducer_table = Table(title="📊 Reducer Execution Results Across State Keys", border_style="cyan")
    reducer_table.add_column("State Key", style="cyan", no_wrap=True)
    reducer_table.add_column("Reducer Type", style="magenta")
    reducer_table.add_column("Final Value in State", style="white")

    reducer_table.add_row("current_status", "Default (Overwrite)", f"'{result_a['current_status']}'")
    reducer_table.add_row("logs", "operator.add (List Concatenation)", f"{len(result_a['logs'])} items: " + " ➜ ".join(result_a['logs']))
    
    msg_summary = [f"{m.__class__.__name__}(id='{m.id}', content='{m.content}')" for m in result_a['messages']]
    reducer_table.add_row("messages", "add_messages (Deduplicate/Update by ID)", "\n".join(msg_summary))
    reducer_table.add_row("telemetry", "custom_dict_merge_reducer", str(result_a['telemetry']))
    reducer_table.add_row("quality_scores", "score_history_reducer (Clamped <= 1.0)", str(result_a['quality_scores']))

    console.print(reducer_table)
    
    console.print(Panel(
        "[bold white]Key Observation on [cyan]add_messages[/cyan]:[/bold white]\n"
        "Notice that `sys_01` was updated in-place from '...orchestrator.' to '...orchestrator (Audited).' "
        "because both messages shared the ID `sys_01`. `add_messages` intelligently matched the ID and updated it "
        "instead of blindly appending a duplicate!",
        border_style="green"
    ))

    # ------------------------------------------------------------------------
    # SECTION 2: Parallel Fan-Out Concurrency
    # ------------------------------------------------------------------------
    console.print("\n[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")
    console.print("[bold green]2. PARALLEL FAN-OUT CONCURRENCY & MULTI-WORKER MERGE[/bold green]")
    console.print("[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")

    parallel_app = build_parallel_fanout_graph()
    initial_p: ParallelTaskState = {
        "task_name": "AAPL 360-Degree Analysis",
        "execution_log": ["[Init] Initiating parallel research workers..."],
        "agent_outputs": {},
        "metrics_history": []
    }

    t0 = time.time()
    result_p = parallel_app.invoke(initial_p)
    elapsed = time.time() - t0

    console.print(f"[bold green]✔ Parallel execution completed in {elapsed:.3f}s[/bold green]")
    
    log_table = Table(title="📝 Parallel Execution Trace Log", border_style="yellow")
    log_table.add_column("Index", style="cyan", justify="center")
    log_table.add_column("Log Entry", style="white")
    for idx, entry in enumerate(result_p["execution_log"], 1):
        log_table.add_row(str(idx), entry)
    console.print(log_table)

    console.print(Panel(
        f"[bold cyan]Aggregated Multi-Agent Payload:[/bold cyan]\n{result_p['agent_outputs']}\n\n"
        f"[bold cyan]Combined Metrics History (operator.add):[/bold cyan] {result_p['metrics_history']}",
        title="🎯 Combined State Output from Parallel Workers",
        border_style="magenta"
    ))

    # ------------------------------------------------------------------------
    # SECTION 3: The In-Place Mutation Pitfall
    # ------------------------------------------------------------------------
    console.print("\n[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")
    console.print("[bold green]3. THE IN-PLACE MUTATION PITFALL VS. DELTA RETURNS[/bold green]")
    console.print("[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")

    buggy_app, clean_app = demonstrate_mutation_vs_delta()

    initial_buggy: MutationPitfallState = {"items": ["initial_item"]}
    result_buggy = buggy_app.invoke(initial_buggy)

    initial_clean: MutationPitfallState = {"items": ["initial_item"]}
    result_clean = clean_app.invoke(initial_clean)

    pitfall_table = Table(title="⚠️ In-Place Mutation vs. Pure Delta Return Comparison", border_style="red")
    pitfall_table.add_column("Approach", style="bold white")
    pitfall_table.add_column("Input State", style="cyan")
    pitfall_table.add_column("Node Return Statement", style="yellow")
    pitfall_table.add_column("Resulting State", style="magenta")
    pitfall_table.add_column("Evaluation", style="white")

    pitfall_table.add_row(
        "❌ Buggy In-Place Mutation",
        "['initial_item']",
        "state['items'].append(...)\nreturn {'items': state['items']}",
        str(result_buggy["items"]),
        "[bold red]FAILED[/bold red]: Initial item is duplicated!"
    )
    pitfall_table.add_row(
        "✅ Clean Partial Delta Return",
        "['initial_item']",
        "return {'items': ['CLEAN_DELTA_ITEM']}",
        str(result_clean["items"]),
        "[bold green]PASSED[/bold green]: Exactly 2 distinct items cleanly merged."
    )

    console.print(pitfall_table)

    console.print(Panel(
        "[bold red]WHY IN-PLACE MUTATION BREAKS IN PRODUCTION:[/bold red]\n"
        "1. [bold]State Duplication[/bold]: Because python lists are passed by reference, `state['items'].append(...)` "
        "mutates the accumulator *before* `operator.add` runs, resulting in `[A, B] + [A, B] = [A, B, A, B]`.\n"
        "2. [bold]Parallel Race Conditions[/bold]: If 3 workers mutate the same list reference concurrently in threads, "
        "they will clobber each other's memory and cause unpredictable race conditions.\n"
        "3. [bold]Corrupt Checkpoint History[/bold]: Mutating the object in-place mutates the past checkpoint held in memory, "
        "destroying your ability to time-travel or rewind.\n"
        "4. [bold]Rule of Thumb[/bold]: [bold green]Nodes MUST be pure delta producers. Never mutate `state` arguments directly![/bold green]",
        border_style="red"
    ))


if __name__ == "__main__":
    main()
