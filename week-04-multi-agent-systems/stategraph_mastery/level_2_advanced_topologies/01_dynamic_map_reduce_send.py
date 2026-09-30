"""🎯 Level 2 - Drill 01: Dynamic Map-Reduce & Runtime Fan-Out with the Send API.

This module demonstrates:
1. Dynamic Runtime Fan-Out: When the number of parallel workers (N) is not known at compile time.
2. The `Send` API: `from langgraph.types import Send` for dispatching isolated sub-payloads.
3. State Reducer Aggregation: Merging N dynamic worker responses into a single master state.
4. Executive Synthesis: Reducing all parallel findings into a coherent summary.

Run directly:
    python3 01_dynamic_map_reduce_send.py
    # or
    python3 -m week-04-multi-agent-systems.stategraph_mastery.level_2_advanced_topologies.01_dynamic_map_reduce_send
"""

import time
import operator
from typing import Annotated, TypedDict, List, Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

console = Console()


# ============================================================================
# 1. STATE SCHEMAS: Master State vs. Worker Input Payload
# ============================================================================

class SubTask(TypedDict):
    task_id: str
    target_company: str
    research_domain: str  # e.g. "Financials", "Competitors", "AI_Strategy", "Regulatory"
    priority: int


class WorkerResult(TypedDict):
    task_id: str
    target_company: str
    domain: str
    key_findings: List[str]
    confidence_score: float
    execution_time_ms: float


class MarketResearchMasterState(TypedDict):
    # User Query & Decomposed Plan
    inquiry: str
    subtasks: List[SubTask]
    
    # Reducer: Gathers all N dynamic worker results as they complete
    collected_results: Annotated[List[WorkerResult], operator.add]
    
    # Final Output Synthesis
    executive_summary: Optional[str]
    total_latency_seconds: Optional[float]


# Worker-specific input state schema
class WorkerInputState(TypedDict):
    task_id: str
    target_company: str
    research_domain: str
    priority: int


# ============================================================================
# 2. NODES: DECOMPOSER (MAPPER), WORKER, AND SYNTHESIZER (REDUCER)
# ============================================================================

def query_decomposer_node(state: MarketResearchMasterState) -> Dict[str, Any]:
    """Inspects the inquiry and dynamically breaks it down into N specialized subtasks.
    
    In a production agent, an LLM generates this list based on the prompt complexity.
    """
    inquiry = state["inquiry"]
    console.print(f"[bold cyan]🔍 Decomposer analyzing inquiry:[/bold cyan] '{inquiry}'")
    
    # Dynamic task generation logic based on query content
    generated_tasks: List[SubTask] = []
    
    if "NVIDIA" in inquiry:
        generated_tasks.extend([
            {"task_id": "NVDA-01", "target_company": "NVIDIA", "research_domain": "Datacenter_Revenue", "priority": 1},
            {"task_id": "NVDA-02", "target_company": "NVIDIA", "research_domain": "Blackwell_Architecture", "priority": 1},
            {"task_id": "NVDA-03", "target_company": "NVIDIA", "research_domain": "Custom_Silicon_Competition", "priority": 2},
        ])
        
    if "Apple" in inquiry:
        generated_tasks.extend([
            {"task_id": "AAPL-01", "target_company": "Apple", "research_domain": "Apple_Intelligence_Rollout", "priority": 1},
            {"task_id": "AAPL-02", "target_company": "Apple", "research_domain": "Services_Ecosystem_Growth", "priority": 2},
        ])
        
    if not generated_tasks:
        generated_tasks.append({
            "task_id": "GEN-01",
            "target_company": "General Tech Market",
            "research_domain": "Macroeconomic_Outlook",
            "priority": 1
        })
    
    console.print(f"[bold green]✔ Decomposer generated {len(generated_tasks)} dynamic subtasks.[/bold green]")
    return {"subtasks": generated_tasks}


def domain_research_worker_node(task: WorkerInputState) -> Dict[str, Any]:
    """Parallel worker executed dynamically for EACH SubTask via the Send API.
    
    Notice that this node takes `WorkerInputState` (the individual sub-payload),
    NOT the entire MasterState!
    """
    t0 = time.time()
    time.sleep(0.04)  # Simulate parallel I/O or LLM inference
    
    company = task["target_company"]
    domain = task["research_domain"]
    task_id = task["task_id"]
    
    # Simulated domain intelligence
    knowledge_base = {
        "Datacenter_Revenue": [
            "Datacenter segment grew 154% YoY driven by Hopper & Blackwell GPUs.",
            "Gross margins expanded to 75.1% due to hyperscaler demand."
        ],
        "Blackwell_Architecture": [
            "Blackwell Ultra B200 delivers 30x inference speedup for trillion-parameter LLMs.",
            "Liquid cooling infrastructure adoption is accelerating data center deployments."
        ],
        "Custom_Silicon_Competition": [
            "Hyperscalers (Google TPU, AWS Trainium, MSFT Maia) are increasing internal workload allocation.",
            "CUDA moat remains formidable for enterprise software developers."
        ],
        "Apple_Intelligence_Rollout": [
            "On-device 3B parameter model utilizes Private Cloud Compute for complex tasks.",
            "Siri revamp driving accelerated iPhone upgrade super-cycle."
        ],
        "Services_Ecosystem_Growth": [
            "Services segment hit all-time revenue record with >1B paid subscriptions.",
            "High margin recurring revenue buffers hardware cyclicality."
        ]
    }
    
    findings = knowledge_base.get(domain, [f"Standard market analysis for {company} in domain {domain}."])
    elapsed_ms = (time.time() - t0) * 1000
    
    result_item: WorkerResult = {
        "task_id": task_id,
        "target_company": company,
        "domain": domain,
        "key_findings": findings,
        "confidence_score": 0.95 if task["priority"] == 1 else 0.88,
        "execution_time_ms": elapsed_ms
    }
    
    # Return delta for the master state's `collected_results` list
    return {"collected_results": [result_item]}


def executive_synthesizer_node(state: MarketResearchMasterState) -> Dict[str, Any]:
    """Reduces and synthesizes all gathered parallel worker results into an executive brief."""
    results = state.get("collected_results", [])
    
    summary_lines = [
        f"═══════════════════════════════════════════════════════════════════",
        f"📊 EXECUTIVE MARKET INTELLIGENCE SYNTHESIS",
        f"Inquiry: {state['inquiry']}",
        f"Total Specialized Research Threads Merged: {len(results)}",
        f"═══════════════════════════════════════════════════════════════════",
    ]
    
    by_company: Dict[str, List[WorkerResult]] = {}
    for r in results:
        by_company.setdefault(r["target_company"], []).append(r)
        
    for company, comp_results in by_company.items():
        summary_lines.append(f"\n🏢 [{company.upper()}]")
        for res in comp_results:
            summary_lines.append(f"  • Domain: {res['domain']} (Confidence: {res['confidence_score']:.0%})")
            for finding in res["key_findings"]:
                summary_lines.append(f"    - {finding}")
                
    summary_lines.append("\n🎯 STRATEGIC CONCLUSION:")
    summary_lines.append("  Enterprise AI infrastructure investment remains at historic highs.")
    summary_lines.append("  Edge AI deployment is creating complementary hardware upgrade cycles.")
    
    return {
        "executive_summary": "\n".join(summary_lines)
    }


# ============================================================================
# 3. DYNAMIC ROUTING FUNCTION USING THE SEND API
# ============================================================================

def fan_out_to_researchers(state: MarketResearchMasterState) -> List[Send]:
    """Inspects state['subtasks'] and dynamically dispatches N worker nodes.
    
    This is the core of the LangGraph Map-Reduce pattern:
    Instead of hardcoded edges, returning a list of `Send("node_name", payload)`
    spawns exactly len(subtasks) concurrent executions of domain_research_worker_node!
    """
    subtasks = state.get("subtasks", [])
    
    # Return a Send object for each subtask
    return [
        Send("research_worker", {
            "task_id": task["task_id"],
            "target_company": task["target_company"],
            "research_domain": task["research_domain"],
            "priority": task["priority"]
        })
        for task in subtasks
    ]


# ============================================================================
# 4. GRAPH CONSTRUCTION
# ============================================================================

def build_dynamic_map_reduce_graph():
    """Builds the dynamic Map-Reduce graph.
    
    Topology:
                               ┌── Send ──> research_worker (Task 1) ──┐
                               ├── Send ──> research_worker (Task 2) ──┤
    START ──> query_decomposer ┼── Send ──> research_worker (Task 3) ──┼──> synthesizer ──> END
                               ├── Send ──> ...                        ┤
                               └── Send ──> research_worker (Task N) ──┘
    """
    builder = StateGraph(MarketResearchMasterState)
    
    # Add Nodes
    builder.add_node("decomposer", query_decomposer_node)
    builder.add_node("research_worker", domain_research_worker_node)
    builder.add_node("synthesizer", executive_synthesizer_node)
    
    # Linear edge: START -> decomposer
    builder.add_edge(START, "decomposer")
    
    # Dynamic Map Fan-Out Edge: decomposer -> N research_workers
    builder.add_conditional_edges(
        "decomposer",
        fan_out_to_researchers,
        ["research_worker"]  # Declares the target node types reachable by Send
    )
    
    # Fan-In Edge: All research_workers feed into synthesizer
    builder.add_edge("research_worker", "synthesizer")
    builder.add_edge("synthesizer", END)
    
    return builder.compile()


# ============================================================================
# 5. INTERACTIVE CLI RUNNER & BENCHMARKS
# ============================================================================

def run_scenario(title: str, query: str, app):
    console.print(f"\n[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")
    console.print(f"[bold green]▶ SCENARIO: {title}[/bold green]")
    console.print(f"[bold cyan]💬 Query:[/bold cyan] {query}")
    console.print(f"[bold yellow]══════════════════════════════════════════════════════════════════[/bold yellow]")

    initial_state: MarketResearchMasterState = {
        "inquiry": query,
        "subtasks": [],
        "collected_results": [],
        "executive_summary": None,
        "total_latency_seconds": None
    }

    t0 = time.time()
    final_state = app.invoke(initial_state)
    elapsed = time.time() - t0

    # Display dynamic workers table
    results_table = Table(title="⚡ Dynamic Worker Execution Log (Collected via Send API)", border_style="cyan")
    results_table.add_column("Task ID", style="cyan", justify="center")
    results_table.add_column("Company", style="bold white")
    results_table.add_column("Research Domain", style="magenta")
    results_table.add_column("Confidence", justify="center", style="green")
    results_table.add_column("Worker Latency", justify="center", style="yellow")

    for r in final_state["collected_results"]:
        results_table.add_row(
            r["task_id"],
            r["target_company"],
            r["domain"],
            f"{r['confidence_score']:.0%}",
            f"{r['execution_time_ms']:.1f}ms"
        )

    console.print(results_table)
    console.print(f"[bold green]✔ All {len(final_state['collected_results'])} dynamic workers merged in parallel in {elapsed:.3f}s total.[/bold green]")
    
    console.print(Panel(
        final_state["executive_summary"],
        title="🎯 Final Synthesizer Output",
        border_style="green"
    ))


def main():
    console.print(Panel.fit(
        "[bold cyan]🎯 StateGraph Mastery - Level 2 Drill 01[/bold cyan]\n"
        "[bold white]Dynamic Map-Reduce Fan-Out with the Send API[/bold white]",
        border_style="cyan"
    ))

    app = build_dynamic_map_reduce_graph()

    # Scenario 1: Dual-Company inquiry producing 5 dynamic parallel workers
    run_scenario(
        title="Compound Dual-Company Multi-Domain Research (5 Parallel Workers)",
        query="Provide an in-depth semiconductor and mobile ecosystem comparison between NVIDIA and Apple.",
        app=app
    )

    # Scenario 2: Single-Company inquiry producing 3 dynamic parallel workers
    run_scenario(
        title="Targeted Single-Company Research (3 Parallel Workers)",
        query="Analyze NVIDIA datacenter growth and Blackwell architecture adoption.",
        app=app
    )


if __name__ == "__main__":
    main()
