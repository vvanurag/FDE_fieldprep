"""🎯 Level 2 - Drill 02: Hierarchical Subgraphs as Isolated Nodes (Compositionality).

This module demonstrates:
1. Subgraph Modular Architecture: Breaking down monolithic graphs into isolated, reusable sub-units.
2. Independent Child State Schemas: Scoping internal iteration counts and private logs to the child.
3. Embedding Compiled Subgraphs: `parent_builder.add_node("sub_team", child_graph.compile())`.
4. State Interface Boundaries: Clean input/output contracts between Parent State and Child State.
5. Checkpoint Propagation: How Checkpointers (e.g. MemorySaver) track state across nested hierarchies.

Run directly:
    python3 02_subgraph_composition.py
    # or
    python3 -m week-04-multi-agent-systems.stategraph_mastery.level_2_advanced_topologies.02_subgraph_composition
"""

import time
import operator
from typing import Annotated, TypedDict, List, Dict, Any, Optional, Literal
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

console = Console()


# ============================================================================
# 1. SCHEMAS: PARENT ORCHESTRATOR STATE & SPECIALIZED SUBGRAPH STATES
# ============================================================================

# --- CHILD 1: Research Subgraph State ---
class ResearchSubgraphState(TypedDict):
    # Overlapping keys inherited from parent
    project_title: str
    feature_requirements: List[str]
    
    # Private internal child state (does NOT pollute parent)
    literature_notes: Annotated[List[str], operator.add]
    research_iteration: int
    
    # Exported output field back to parent
    research_dossier: str


# --- CHILD 2: Engineering & Code Review Subgraph State ---
class CodeEngineeringSubgraphState(TypedDict):
    # Overlapping keys inherited from parent
    project_title: str
    research_dossier: str
    
    # Private internal self-healing loop state
    draft_code: str
    review_score: float
    review_comments: Annotated[List[str], operator.add]
    fix_attempts: int
    
    # Exported output field back to parent
    verified_code_artifact: str


# --- PARENT ORCHESTRATOR STATE ---
class EnterpriseProjectMasterState(TypedDict):
    project_title: str
    feature_requirements: List[str]
    
    # High-level outputs produced by child subgraphs
    research_dossier: Optional[str]
    verified_code_artifact: Optional[str]
    
    # Orchestrator audit log
    orchestrator_log: Annotated[List[str], operator.add]
    final_deliverable: Optional[str]


# ============================================================================
# 2. CHILD SUBGRAPH 1: RESEARCH & ARCHITECTURE TEAM
# ============================================================================

def literature_scout_node(state: ResearchSubgraphState) -> Dict[str, Any]:
    """Child Node: Scouts technical whitepapers and RFCs."""
    console.print("[dim cyan]  [Research Subgraph] 🔬 Scouting RFCs & architectural whitepapers...[/dim cyan]")
    return {
        "literature_notes": [
            "RFC 9114: HTTP/3 QUIC transport multiplexing.",
            "Distributed Token Bucket algorithm for zero-lock rate limiting."
        ],
        "research_iteration": state.get("research_iteration", 0) + 1
    }


def architectural_synthesizer_node(state: ResearchSubgraphState) -> Dict[str, Any]:
    """Child Node: Produces the research dossier for the parent."""
    notes_str = "\n".join(f"    - {n}" for n in state["literature_notes"])
    dossier = (
        f"Technical Architecture Dossier for {state['project_title']}:\n"
        f"  Key Requirements: {', '.join(state['feature_requirements'])}\n"
        f"  Foundational Principles:\n{notes_str}\n"
        f"  Design Decision: Implement atomic Redis-backed sliding window with sub-millisecond p99."
    )
    return {"research_dossier": dossier}


def build_research_subgraph():
    """Builds and compiles the Research Subgraph."""
    builder = StateGraph(ResearchSubgraphState)
    builder.add_node("scout", literature_scout_node)
    builder.add_node("synthesizer", architectural_synthesizer_node)
    
    builder.add_edge(START, "scout")
    builder.add_edge("scout", "synthesizer")
    builder.add_edge("synthesizer", END)
    
    return builder.compile()


# ============================================================================
# 3. CHILD SUBGRAPH 2: CODING & SELF-HEALING REVIEW TEAM
# ============================================================================

def code_writer_node(state: CodeEngineeringSubgraphState) -> Dict[str, Any]:
    """Child Node: Writes or refines code based on review comments."""
    attempts = state.get("fix_attempts", 0) + 1
    console.print(f"[dim magenta]  [Engineering Subgraph] 💻 Generating code (Attempt {attempts})...[/dim magenta]")
    
    if attempts == 1:
        code = (
            "class RateLimiter:\n"
            "    def __init__(self, capacity):\n"
            "        self.tokens = capacity\n"
            "    def allow(self): # BUG: Missing lock synchronization & time decay\n"
            "        if self.tokens > 0:\n"
            "            self.tokens -= 1\n"
            "            return True\n"
            "        return False"
        )
    else:
        code = (
            "import time, threading\n"
            "class ProductionRateLimiter:\n"
            "    def __init__(self, rate_per_sec: float, capacity: int):\n"
            "        self.rate = rate_per_sec\n"
            "        self.capacity = capacity\n"
            "        self.tokens = capacity\n"
            "        self.last_leak = time.monotonic()\n"
            "        self._lock = threading.Lock()\n\n"
            "    def allow(self, cost: int = 1) -> bool:\n"
            "        with self._lock:\n"
            "            now = time.monotonic()\n"
            "            elapsed = now - self.last_leak\n"
            "            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)\n"
            "            self.last_leak = now\n"
            "            if self.tokens >= cost:\n"
            "                self.tokens -= cost\n"
            "                return True\n"
            "            return False"
        )
    
    return {
        "draft_code": code,
        "fix_attempts": attempts
    }


def code_reviewer_node(state: CodeEngineeringSubgraphState) -> Dict[str, Any]:
    """Child Node: Automated lint, security, and thread-safety review."""
    code = state["draft_code"]
    
    if "threading.Lock()" in code and "time.monotonic()" in code:
        score = 0.98
        critique = "PASS: Thread-safe, time-decay token bucket with sub-microsecond overhead."
    else:
        score = 0.60
        critique = "FAIL: Missing thread synchronization lock and timestamp-based token replenishment."
    
    return {
        "review_score": score,
        "review_comments": [f"[Attempt {state['fix_attempts']} | Score {score:.2f}] {critique}"]
    }


def should_refine_code(state: CodeEngineeringSubgraphState) -> Literal["writer", "package"]:
    """Conditional loop inside the child engineering subgraph."""
    if state["review_score"] >= 0.90 or state["fix_attempts"] >= 3:
        return "package"
    return "writer"


def package_artifact_node(state: CodeEngineeringSubgraphState) -> Dict[str, Any]:
    """Child Node: Packages the final verified code deliverable."""
    return {
        "verified_code_artifact": state["draft_code"]
    }


def build_engineering_subgraph():
    """Builds and compiles the Engineering & Code Review Subgraph."""
    builder = StateGraph(CodeEngineeringSubgraphState)
    
    builder.add_node("writer", code_writer_node)
    builder.add_node("reviewer", code_reviewer_node)
    builder.add_node("package", package_artifact_node)
    
    builder.add_edge(START, "writer")
    builder.add_edge("writer", "reviewer")
    
    builder.add_conditional_edges(
        "reviewer",
        should_refine_code,
        {
            "writer": "writer",
            "package": "package"
        }
    )
    
    builder.add_edge("package", END)
    return builder.compile()


# ============================================================================
# 4. PARENT ORCHESTRATOR GRAPH (NESTING BOTH SUBGRAPHS)
# ============================================================================

def project_kickoff_node(state: EnterpriseProjectMasterState) -> Dict[str, Any]:
    """Parent Node: Initializes project scope and requirements."""
    return {
        "orchestrator_log": [f"🚀 [Kickoff] Project '{state['project_title']}' started."]
    }


def final_qa_node(state: EnterpriseProjectMasterState) -> Dict[str, Any]:
    """Parent Node: Assembles and signs off on the complete project deliverable."""
    deliverable = (
        f"════════════════════════════════════════════════════════════════════\n"
        f"📦 ENTERPRISE SHIPMENT ARTIFACT: {state['project_title'].upper()}\n"
        f"════════════════════════════════════════════════════════════════════\n"
        f"[1. RESEARCH DOSSIER]:\n{state['research_dossier']}\n\n"
        f"[2. PRODUCTION CODE ARTIFACT]:\n{state['verified_code_artifact']}\n"
        f"════════════════════════════════════════════════════════════════════\n"
        f"✔ Signed off by Master Orchestrator Pipeline."
    )
    return {
        "final_deliverable": deliverable,
        "orchestrator_log": ["✅ [Signoff] Project successfully verified and packaged for production."]
    }


def build_hierarchical_enterprise_graph(checkpointer: Optional[MemorySaver] = None):
    """Builds the Parent Orchestrator Graph embedding both child subgraphs as single nodes!
    
    Parent Topology:
    
    START ──> kickoff ──> [RESEARCH SUBGRAPH] ──> [ENGINEERING SUBGRAPH] ──> final_qa ──> END
                                │                               │
                                ▼                               ▼
                         (scout ➜ synth)              (writer ➜ review ⟲)
    """
    # 1. Compile independent child subgraphs
    research_subgraph = build_research_subgraph()
    engineering_subgraph = build_engineering_subgraph()
    
    # 2. Build Parent Graph
    parent_builder = StateGraph(EnterpriseProjectMasterState)
    
    parent_builder.add_node("kickoff", project_kickoff_node)
    
    # 🌟 MAGIC: Adding compiled subgraphs directly as nodes!
    parent_builder.add_node("research_subgraph_node", research_subgraph)
    parent_builder.add_node("engineering_subgraph_node", engineering_subgraph)
    
    parent_builder.add_node("final_qa", final_qa_node)
    
    # Parent linear workflow
    parent_builder.add_edge(START, "kickoff")
    parent_builder.add_edge("kickoff", "research_subgraph_node")
    parent_builder.add_edge("research_subgraph_node", "engineering_subgraph_node")
    parent_builder.add_edge("engineering_subgraph_node", "final_qa")
    parent_builder.add_edge("final_qa", END)
    
    return parent_builder.compile(checkpointer=checkpointer)


# ============================================================================
# 5. INTERACTIVE CLI RUNNER
# ============================================================================

def main():
    console.print(Panel.fit(
        "[bold cyan]🎯 StateGraph Mastery - Level 2 Drill 02[/bold cyan]\n"
        "[bold white]Hierarchical Subgraph Composition & State Boundary Scoping[/bold white]",
        border_style="cyan"
    ))

    checkpointer = MemorySaver()
    app = build_hierarchical_enterprise_graph(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "proj_rate_limiter_001"}}

    initial_state: EnterpriseProjectMasterState = {
        "project_title": "High-Concurrency Distributed Rate Limiter",
        "feature_requirements": [
            "Token bucket algorithm",
            "Thread-safe synchronization",
            "Time-decay token replenishment",
            "Sub-millisecond p99 latency"
        ],
        "research_dossier": None,
        "verified_code_artifact": None,
        "orchestrator_log": [],
        "final_deliverable": None
    }

    console.print("\n[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")
    console.print("[bold green]EXECUTING PARENT GRAPH WITH NESTED SUBGRAPHS[/bold green]")
    console.print("[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")

    result = app.invoke(initial_state, config=config)

    # Display orchestrator trace
    orch_table = Table(title="📜 Parent Orchestrator Trace", border_style="cyan")
    orch_table.add_column("Step", style="cyan", justify="center")
    orch_table.add_column("Log Entry", style="white")
    for idx, entry in enumerate(result["orchestrator_log"], 1):
        orch_table.add_row(str(idx), entry)
    console.print(orch_table)

    console.print(Panel(
        result["final_deliverable"],
        title="🎯 Complete Deliverable Assembled Across Subgraphs",
        border_style="green"
    ))

    console.print(Panel(
        "[bold green]WHY SUBGRAPHS ARE A GAME-CHANGER IN PRODUCTION:[/bold green]\n"
        "1. [bold]State Boundary Isolation[/bold]: The internal loop counter `fix_attempts` and `literature_notes` "
        "never polluted the parent orchestrator state.\n"
        "2. [bold]Independent Testability[/bold]: You can write isolated unit tests for `build_research_subgraph()` "
        "and `build_engineering_subgraph()` without running the entire 4-stage pipeline.\n"
        "3. [bold]Modular Reusability[/bold]: The `engineering_subgraph` can be reused inside 5 different parent graphs "
        "(e.g., in a code refactoring graph, an incident response graph, or a migration graph).",
        border_style="cyan"
    ))


if __name__ == "__main__":
    main()
