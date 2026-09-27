"""LangGraph StateGraph implementation of Pattern 05: Multi-Agent Collaboration."""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from common.logging import get_logger
from .schemas import MultiAgentState, AgentRole, SupervisorDecision, SecurityReviewResult
from .agents import (
    build_supervisor_agent,
    build_reviewer_agent,
    build_specialist_llm,
    SUPERVISOR_PROMPT,
    RESEARCHER_PROMPT,
    CODER_PROMPT,
    REVIEWER_PROMPT,
    SYNTHESIZER_PROMPT
)

logger = get_logger("multi_agent_graph")


def build_multi_agent_team(provider: str = "openai", model_name: str = "gpt-4o-mini"):
    """Compiles the Hierarchical Supervisor Multi-Agent Team graph."""
    
    supervisor_llm = build_supervisor_agent(provider=provider, model_name=model_name)
    reviewer_llm = build_reviewer_agent(provider=provider, model_name=model_name)
    general_llm = build_specialist_llm(provider=provider, model_name=model_name)

    # 1. Supervisor Node
    def supervisor_node(state: MultiAgentState) -> Dict[str, Any]:
        iter_count = state.get("iteration_count", 0) + 1
        max_iter = state.get("max_iterations", 8)
        
        logger.info(f"[bold cyan]👑 [Supervisor Node] Evaluating team progress (Turn {iter_count}/{max_iter})...[/bold cyan]")
        
        # Build context snapshot for supervisor
        status_context = (
            f"Goal: {state['task_goal']}\n"
            f"Research Status: {'Completed' if state.get('research_summary') else 'Not Started'}\n"
            f"Code Status: {'Implemented' if state.get('code_artifact') else 'Not Started'}\n"
            f"Review Status: {state.get('review_verdict')}\n"
            f"Synthesizer Status: {'Completed' if state.get('final_deliverable') else 'Not Started'}\n"
        )
        
        if iter_count >= max_iter:
            logger.warning("[bold red]⚠️ Max team turns reached. Forcing synthesis.[/bold red]")
            return {"next_agent": AgentRole.SYNTHESIZER.value, "iteration_count": iter_count}
            
        decision: SupervisorDecision = supervisor_llm.invoke([
            SystemMessage(content=SUPERVISOR_PROMPT),
            HumanMessage(content=status_context)
        ])
        
        logger.info(f"   [yellow]Decision:[/yellow] Delegate -> [bold]{decision.next_agent.value}[/bold] | Notes: {decision.delegation_instructions}")
        
        return {
            "next_agent": decision.next_agent.value,
            "supervisor_notes": decision.delegation_instructions,
            "iteration_count": iter_count
        }

    # 2. Researcher Node
    def researcher_node(state: MultiAgentState) -> Dict[str, Any]:
        logger.info("[bold blue]🔬 [Researcher Node] Conducting architectural research & algorithm design...[/bold blue]")
        
        prompt = f"Goal: {state['task_goal']}\nSupervisor Notes: {state.get('supervisor_notes')}"
        response = general_llm.invoke([
            SystemMessage(content=RESEARCHER_PROMPT),
            HumanMessage(content=prompt)
        ])
        
        return {
            "research_summary": response.content.strip(),
            "messages": [AIMessage(content=f"[Researcher]: {response.content.strip()}")]
        }

    # 3. Coder Node
    def coder_node(state: MultiAgentState) -> Dict[str, Any]:
        logger.info("[bold green]💻 [Coder Node] Implementing / refining Python code artifact...[/bold green]")
        
        prompt = f"Goal: {state['task_goal']}\n\nArchitecture Notes:\n{state.get('research_summary')}"
        if state.get("code_artifact"):
            prompt += f"\n\nExisting Code:\n{state.get('code_artifact')}"
        if state.get("review_verdict") and not state["review_verdict"].get("is_approved"):
            prompt += f"\n\nReviewer Feedback to Fix:\n{state['review_verdict'].get('actionable_fix_instructions')}"
            
        response = general_llm.invoke([
            SystemMessage(content=CODER_PROMPT),
            HumanMessage(content=prompt)
        ])
        
        return {
            "code_artifact": response.content.strip(),
            "messages": [AIMessage(content="[Coder]: Implementation complete and updated.")]
        }

    # 4. Reviewer Node
    def reviewer_node(state: MultiAgentState) -> Dict[str, Any]:
        logger.info("[bold magenta]🛡️ [Reviewer Node] Conducting security and concurrency audit...[/bold magenta]")
        
        prompt = (
            f"Goal: {state['task_goal']}\n\n"
            f"Code to Review:\n{state.get('code_artifact')}\n\n"
            f"Design Architecture:\n{state.get('research_summary')}"
        )
        
        verdict: SecurityReviewResult = reviewer_llm.invoke([
            SystemMessage(content=REVIEWER_PROMPT),
            HumanMessage(content=prompt)
        ])
        
        logger.info(f"   [Review Verdict]: is_approved=[bold]{verdict.is_approved}[/bold] | Issues: {len(verdict.security_vulnerabilities) + len(verdict.performance_issues)}")
        
        return {
            "review_verdict": verdict.model_dump(),
            "messages": [AIMessage(content=f"[Reviewer]: Approved={verdict.is_approved}. Feedback: {verdict.actionable_fix_instructions}")]
        }

    # 5. Synthesizer Node
    def synthesizer_node(state: MultiAgentState) -> Dict[str, Any]:
        logger.info("[bold yellow]📦 [Synthesizer Node] Packaging final deliverable and documentation...[/bold yellow]")
        
        prompt = (
            f"Goal: {state['task_goal']}\n\n"
            f"Architecture Research:\n{state.get('research_summary')}\n\n"
            f"Validated Code Artifact:\n{state.get('code_artifact')}\n\n"
            f"QA & Security Verdict:\n{state.get('review_verdict')}"
        )
        
        response = general_llm.invoke([
            SystemMessage(content=SYNTHESIZER_PROMPT),
            HumanMessage(content=prompt)
        ])
        
        return {
            "final_deliverable": response.content.strip(),
            "next_agent": AgentRole.FINISH.value
        }

    # Routing Function
    def route_supervisor(state: MultiAgentState) -> str:
        next_role = state.get("next_agent", AgentRole.FINISH.value)
        if next_role == AgentRole.FINISH.value:
            logger.info("[bold green]🏁 Supervisor signaled task completion -> Routing to END.[/bold green]")
            return "finish"
        return next_role

    # Assemble StateGraph
    workflow = StateGraph(MultiAgentState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("synthesizer", synthesizer_node)

    workflow.set_entry_point("supervisor")

    workflow.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {
            "researcher": "researcher",
            "coder": "coder",
            "reviewer": "reviewer",
            "synthesizer": "synthesizer",
            "finish": END
        }
    )

    # All specialists report back to the Supervisor
    workflow.add_edge("researcher", "supervisor")
    workflow.add_edge("coder", "supervisor")
    workflow.add_edge("reviewer", "supervisor")
    workflow.add_edge("synthesizer", "supervisor")

    return workflow.compile()
