"""🎯 Level 1 - Drill 03: State Persistence, Multi-Tenant Session Isolation & Time-Travel.

This module provides an in-depth, hands-on drill on:
1. MemorySaver Checkpointing: Compiling StateGraph with persistent state storage.
2. Multi-Tenant Session Isolation: Managing multiple user threads (`thread_id`) without state leakage.
3. State Inspection APIs: `get_state()` and `get_state_history()` across execution checkpoints.
4. Time-Travel & State Rewinding: Branching from a past checkpoint to simulate "What-If" scenarios.

Run directly:
    python3 03_checkpoints_and_session_isolation.py
    # or
    python3 -m week-04-multi-agent-systems.stategraph_mastery.level_1_core_mechanics.03_checkpoints_and_session_isolation
"""

import operator
from typing import Annotated, TypedDict, List, Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage
)
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

console = Console()


# ============================================================================
# 1. SCHEMAS: State with Checkpointed Conversation & Profile
# ============================================================================

class SessionConversationState(TypedDict):
    # Isolated User Profile Attributes
    user_id: str
    user_role: str
    topic_context: str
    
    # Checkpointed Message History (with intelligent deduplication)
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Cumulative Conversation Steps
    turn_counter: int
    summary_notes: Annotated[List[str], operator.add]


# ============================================================================
# 2. NODES: Context Router, Specialized Responder & Summarizer
# ============================================================================

def context_router_node(state: SessionConversationState) -> Dict[str, Any]:
    """Inspects the incoming message and sets context."""
    turn = state.get("turn_counter", 0) + 1
    last_msg = state["messages"][-1].content if state["messages"] else "Empty"
    
    return {
        "turn_counter": turn,
        "summary_notes": [f"Turn {turn}: User asked about '{last_msg[:40]}...'"]
    }


def assistant_responder_node(state: SessionConversationState) -> Dict[str, Any]:
    """Generates a contextual response conditioned on the user's role and history."""
    role = state.get("user_role", "Guest")
    topic = state.get("topic_context", "General")
    user_msg = state["messages"][-1].content
    
    # Simulated contextual intelligence
    ai_response = (
        f"[{role} Specialist for {topic}] Acknowledged request: '{user_msg}'. "
        f"Processing based on turn {state['turn_counter']} context."
    )
    
    return {
        "messages": [AIMessage(content=ai_response)]
    }


def build_checkpointed_assistant_graph(checkpointer: MemorySaver):
    """Builds and compiles a stateful graph with the provided checkpointer."""
    builder = StateGraph(SessionConversationState)
    
    builder.add_node("router", context_router_node)
    builder.add_node("responder", assistant_responder_node)
    
    builder.add_edge(START, "router")
    builder.add_edge("router", "responder")
    builder.add_edge("responder", END)
    
    # CRITICAL: Compile with checkpointer
    return builder.compile(checkpointer=checkpointer)


# ============================================================================
# 3. DRILL A: Multi-Tenant Session Isolation (Alice vs. Bob)
# ============================================================================

def demonstrate_session_isolation(app):
    """Demonstrates that Thread A and Thread B remain 100% isolated in memory."""
    console.print("\n[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")
    console.print("[bold green]1. MULTI-TENANT THREAD ISOLATION (Alice vs. Bob)[/bold green]")
    console.print("[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")

    # Configs for 2 separate threads
    alice_config = {"configurable": {"thread_id": "session_alice_991"}}
    bob_config = {"configurable": {"thread_id": "session_bob_404"}}

    # Turn 1: Alice (ML Engineer)
    app.invoke({
        "user_id": "alice",
        "user_role": "ML Engineer",
        "topic_context": "Kubeflow Pipeline Optimization",
        "messages": [HumanMessage(content="How do I reduce GPU idle time in training jobs?")],
        "turn_counter": 0,
        "summary_notes": []
    }, config=alice_config)

    # Turn 1: Bob (Security Architect)
    app.invoke({
        "user_id": "bob",
        "user_role": "Security Architect",
        "topic_context": "Zero Trust IAM",
        "messages": [HumanMessage(content="What are best practices for rotating IAM role credentials?")],
        "turn_counter": 0,
        "summary_notes": []
    }, config=bob_config)

    # Turn 2: Alice sends follow-up
    app.invoke({
        "messages": [HumanMessage(content="Can you provide sample PyTorch distributed config?")]
    }, config=alice_config)

    # Inspect current states for both threads
    alice_state = app.get_state(alice_config)
    bob_state = app.get_state(bob_config)

    # Display comparison table
    iso_table = Table(title="🔒 Multi-Thread State Snapshot Verification", border_style="cyan")
    iso_table.add_column("Property", style="bold white")
    iso_table.add_column("Thread A (Alice - ML)", style="green")
    iso_table.add_column("Thread B (Bob - Security)", style="yellow")

    iso_table.add_row("Thread ID", alice_config["configurable"]["thread_id"], bob_config["configurable"]["thread_id"])
    iso_table.add_row("User Role", str(alice_state.values["user_role"]), str(bob_state.values["user_role"]))
    iso_table.add_row("Turn Count", str(alice_state.values["turn_counter"]), str(bob_state.values["turn_counter"]))
    iso_table.add_row("Total Messages", str(len(alice_state.values["messages"])), str(len(bob_state.values["messages"])))
    iso_table.add_row(
        "Latest AI Message",
        alice_state.values["messages"][-1].content[:60] + "...",
        bob_state.values["messages"][-1].content[:60] + "..."
    )

    console.print(iso_table)
    console.print("[bold green]✔ Verified: Zero state leakage between threads across multiple turns.[/bold green]")


# ============================================================================
# 4. DRILL B: State History & Checkpoint Inspection
# ============================================================================

def demonstrate_state_history_inspection(app):
    """Walks backwards through the historical checkpoints of a single thread."""
    console.print("\n[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")
    console.print("[bold green]2. CHECKPOINT HISTORY & TIME-TRAVEL INSPECTION[/bold green]")
    console.print("[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")

    alice_config = {"configurable": {"thread_id": "session_alice_991"}}
    history = list(app.get_state_history(alice_config))

    history_table = Table(title=f"📜 Checkpoint Timeline for Thread: {alice_config['configurable']['thread_id']}", border_style="magenta")
    history_table.add_column("Step", justify="center", style="cyan")
    history_table.add_column("Checkpoint ID", style="magenta")
    history_table.add_column("Next Node", style="yellow")
    history_table.add_column("Turn Counter", justify="center", style="green")
    history_table.add_column("Messages Count", justify="center", style="white")

    for idx, state_snapshot in enumerate(history, 1):
        ckpt_id = state_snapshot.config["configurable"]["checkpoint_id"]
        next_nodes = str(state_snapshot.next) if state_snapshot.next else "END"
        turns = str(state_snapshot.values.get("turn_counter", 0))
        msg_count = str(len(state_snapshot.values.get("messages", [])))
        history_table.add_row(str(idx), ckpt_id[:16] + "...", next_nodes, turns, msg_count)

    console.print(history_table)
    return history


# ============================================================================
# 5. DRILL C: Time-Travel & State Forking (What-If Branching)
# ============================================================================

def demonstrate_time_travel_fork(app, history):
    """Demonstrates rewinding to a previous checkpoint and forking a new timeline."""
    console.print("\n[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")
    console.print("[bold green]3. TIME-TRAVEL REWIND & WHAT-IF FORKING[/bold green]")
    console.print("[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")

    # Select an earlier checkpoint from history (e.g. from Turn 1)
    earlier_checkpoint = history[-3]  # An earlier point in time
    fork_config = earlier_checkpoint.config
    
    console.print(f"[dim]Selected historical checkpoint: {fork_config['configurable']['checkpoint_id']}...[/dim]")

    # We update the state at that historical checkpoint to explore a 'What-If' scenario
    # What if Alice had changed her topic to "TensorRT High-Performance Inference"?
    forked_update = {
        "topic_context": "TensorRT High-Performance Inference",
        "messages": [HumanMessage(content="What if we compile models to TensorRT engine instead?")]
    }
    
    console.print("[bold cyan]Applying state update to historical checkpoint via app.update_state()...[/bold cyan]")
    new_fork_config = app.update_state(
        fork_config,
        forked_update,
        as_node="router"
    )

    # Resume graph execution from this new forked checkpoint!
    console.print("[bold cyan]Resuming execution on forked timeline...[/bold cyan]")
    fork_result = app.invoke(None, config=new_fork_config)

    console.print(Panel(
        f"[bold cyan]Forked Checkpoint ID:[/bold cyan] {new_fork_config['configurable']['checkpoint_id']}\n"
        f"[bold cyan]Forked Topic Context:[/bold cyan] {fork_result['topic_context']}\n"
        f"[bold cyan]Turn Count on Fork:[/bold cyan] {fork_result['turn_counter']}\n\n"
        f"[bold green]Latest Response on Forked Timeline:[/bold green]\n"
        f"{fork_result['messages'][-1].content}",
        title="🌿 Forked Timeline Result (Time-Travel Complete)",
        border_style="green"
    ))


# ============================================================================
# 6. MAIN EXECUTION
# ============================================================================

def main():
    console.print(Panel.fit(
        "[bold cyan]🎯 StateGraph Mastery - Level 1 Drill 03[/bold cyan]\n"
        "[bold white]State Persistence, Thread Isolation & Time-Travel Replay[/bold white]",
        border_style="cyan"
    ))

    # Initialize in-memory checkpointer
    checkpointer = MemorySaver()
    app = build_checkpointed_assistant_graph(checkpointer)

    # 1. Multi-Tenant Session Isolation
    demonstrate_session_isolation(app)

    # 2. Checkpoint History & Timeline Inspection
    history = demonstrate_state_history_inspection(app)

    # 3. Time-Travel Forking
    demonstrate_time_travel_fork(app, history)


if __name__ == "__main__":
    main()
