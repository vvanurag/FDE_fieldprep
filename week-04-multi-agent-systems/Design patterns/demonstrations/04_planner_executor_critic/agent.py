"""LangGraph StateGraph implementation of Pattern 04: Planner-Executor-Critic."""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from common.llm_factory import get_llm
from common.logging import get_logger
from .schemas import PlannerExecutorState, Plan, CriticAuditResult
from .tools import search_flight_options, search_hotel_options, search_activity_options

logger = get_logger("planner_critic")

PLANNER_SYSTEM_PROMPT = """You are an Executive Travel Planner Agent.
Your job is to decompose the user's travel request into a structured subtask Plan.

You must assign 3 specific subtasks:
1. 'task_flights' to 'flight_specialist' (specify tier: 'premium', 'standard', or 'budget')
2. 'task_hotels' to 'hotel_specialist' (specify tier: 'luxury', 'boutique', or 'budget')
3. 'task_activities' to 'activity_specialist' (specify tier: 'deluxe', 'standard', or 'budget')

Allocate budget estimates to each subtask such that the sum respects the total budget ceiling.
If Critic feedback is provided, adjust tier selections to eliminate budget overages.
"""

SYNTHESIZER_SYSTEM_PROMPT = """You are the Executive Travel Dossier Synthesizer.
Combine the approved flight, hotel, and activity options into a structured, markdown travel itinerary.
Include:
- Trip Executive Summary & Destination
- Flight & Transit Details
- Hotel & Accommodation Details
- Curated Daily Activities & Passes
- Financial Budget Breakdown (Total Cost, Budget Limit, Savings/Deficit)
- If the Critic flagged unresolved violations, add a clear Warning Disclaimer.
"""


def build_planner_critic_agent(provider: str = "openai", model_name: str = "gpt-4o-mini"):
    """Builds and compiles the Planner-Executor-Critic LangGraph StateGraph."""
    
    base_llm = get_llm(provider=provider, model_name=model_name, temperature=0.0)
    structured_planner_llm = base_llm.with_structured_output(Plan)
    structured_critic_llm = base_llm.with_structured_output(CriticAuditResult)

    # 1. Planner Node
    def planner_node(state: PlannerExecutorState) -> Dict[str, Any]:
        rev = state.get("revision_count", 0)
        logger.info(f"[bold cyan]📋 [Node: Planner] Generating Travel Decomposition Plan (Revision {rev})...[/bold cyan]")
        
        prompt = f"Travel Request: {state['travel_request']}\nBudget Limit: ${state['budget_limit_usd']:.2f}\n"
        if state.get("critic_audit") and not state["critic_audit"].get("is_approved"):
            prompt += (
                f"\nCRITIC REJECTION FEEDBACK FROM PREVIOUS RUN:\n"
                f"- Violations: {state['critic_audit'].get('constraint_violations')}\n"
                f"- Actionable Instructions: {state['critic_audit'].get('feedback_for_planner')}\n"
                f"Please select more economical tiers (e.g. switch 'premium' to 'standard', or 'luxury' to 'boutique/budget').\n"
            )
        
        plan_obj: Plan = structured_planner_llm.invoke([
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])
        
        logger.info(f"   [yellow]Plan Strategy:[/yellow] {plan_obj.strategy_notes}")
        for st in plan_obj.subtasks:
            logger.info(f"   - [Subtask {st.task_id}] -> {st.assigned_specialist}: {st.description}")

        return {
            "plan": plan_obj.model_dump()
        }

    # 2. Worker Nodes (Executors)
    def flight_specialist_node(state: PlannerExecutorState) -> Dict[str, Any]:
        plan = state["plan"] or {}
        dest = plan.get("destination", "Tokyo")
        
        # Determine tier from subtask description/notes
        desc = ""
        for st in plan.get("subtasks", []):
            if st.get("assigned_specialist") == "flight_specialist":
                desc = st.get("description", "").lower()
                
        tier = "budget" if "budget" in desc else ("premium" if "premium" in desc else "standard")
        logger.info(f"[bold green]✈️ [Flight Specialist] Searching flights for {dest} (Tier: {tier})...[/bold green]")
        
        result = search_flight_options(destination=dest, tier=tier)
        return {"flight_results": result}

    def hotel_specialist_node(state: PlannerExecutorState) -> Dict[str, Any]:
        plan = state["plan"] or {}
        dest = plan.get("destination", "Tokyo")
        nights = plan.get("duration_days", 6)
        
        desc = ""
        for st in plan.get("subtasks", []):
            if st.get("assigned_specialist") == "hotel_specialist":
                desc = st.get("description", "").lower()
                
        tier = "budget" if "budget" in desc else ("luxury" if "luxury" in desc else "boutique")
        logger.info(f"[bold green]🏨 [Hotel Specialist] Searching hotels for {dest} ({nights} nights, Tier: {tier})...[/bold green]")
        
        result = search_hotel_options(destination=dest, nights=nights, tier=tier)
        return {"hotel_results": result}

    def activity_specialist_node(state: PlannerExecutorState) -> Dict[str, Any]:
        plan = state["plan"] or {}
        dest = plan.get("destination", "Tokyo")
        
        desc = ""
        for st in plan.get("subtasks", []):
            if st.get("assigned_specialist") == "activity_specialist":
                desc = st.get("description", "").lower()
                
        tier = "budget" if "budget" in desc else ("deluxe" if "deluxe" in desc else "standard")
        logger.info(f"[bold green]⛩️ [Activity Specialist] Searching activities for {dest} (Tier: {tier})...[/bold green]")
        
        result = search_activity_options(destination=dest, tier=tier)
        return {"activity_results": result}

    # 3. Critic Node (Audits the Aggregated State)
    def critic_node(state: PlannerExecutorState) -> Dict[str, Any]:
        rev = state.get("revision_count", 0) + 1
        budget_limit = state["budget_limit_usd"]
        
        flights = state.get("flight_results") or {}
        hotels = state.get("hotel_results") or {}
        activities = state.get("activity_results") or {}
        
        flight_cost = flights.get("price_usd", 0.0)
        hotel_cost = hotels.get("total_cost_usd", 0.0)
        activity_cost = activities.get("total_cost_usd", 0.0)
        
        total_cost = round(flight_cost + hotel_cost + activity_cost, 2)
        surplus = round(budget_limit - total_cost, 2)
        
        logger.info(f"[bold magenta]🧐 [Node: Critic] Auditing Total Cost: ${total_cost:.2f} vs Budget Limit: ${budget_limit:.2f}...[/bold magenta]")
        
        violations = []
        is_approved = True
        feedback = None
        
        if total_cost > budget_limit:
            is_approved = False
            overage = abs(surplus)
            violations.append(f"Total itinerary cost (${total_cost:.2f}) exceeds budget ceiling (${budget_limit:.2f}) by ${overage:.2f}.")
            feedback = f"Reduce costs by at least ${overage:.2f}. Downgrade hotel or flights to a more economical tier."
            logger.warning(f"[bold red]❌ Critic Rejection:[/bold red] Over budget by ${overage:.2f}")
        else:
            logger.info(f"[bold green]✅ Critic Approval:[/bold green] Within budget (Surplus: ${surplus:.2f})")
            
        audit_res = CriticAuditResult(
            is_approved=is_approved,
            total_estimated_cost_usd=total_cost,
            budget_surplus_or_deficit=surplus,
            constraint_violations=violations,
            feedback_for_planner=feedback
        )
        
        return {
            "critic_audit": audit_res.model_dump(),
            "revision_count": rev
        }

    # 4. Synthesizer Node
    def synthesizer_node(state: PlannerExecutorState) -> Dict[str, Any]:
        logger.info("[bold blue]📝 [Node: Synthesizer] Compiling Executive Travel Dossier...[/bold blue]")
        
        summary_payload = f"""
        User Request: {state['travel_request']}
        Budget Ceiling: ${state['budget_limit_usd']:.2f}
        
        Selected Flights:
        {state.get('flight_results')}
        
        Selected Accommodations:
        {state.get('hotel_results')}
        
        Selected Activities & Tours:
        {state.get('activity_results')}
        
        Critic Audit Verdict:
        {state.get('critic_audit')}
        """
        
        response = base_llm.invoke([
            SystemMessage(content=SYNTHESIZER_SYSTEM_PROMPT),
            HumanMessage(content=summary_payload)
        ])
        
        return {"final_dossier": response.content.strip()}

    # 5. Routing Function
    def route_critic_decision(state: PlannerExecutorState) -> str:
        audit = state.get("critic_audit") or {}
        is_approved = audit.get("is_approved", False)
        rev = state.get("revision_count", 0)
        max_rev = state.get("max_revisions", 2)
        
        if is_approved:
            logger.info("[Router Edge] Critic approved plan -> Routing to Synthesizer.")
            return "synthesizer"
        elif rev < max_rev:
            logger.warning(f"[Router Edge] Critic rejected plan -> Routing back to Planner for Revision {rev + 1}.")
            return "planner"
        else:
            logger.error(f"[Router Edge] Max revisions ({max_rev}) reached. Synthesizing best effort with disclaimers.")
            return "synthesizer"

    # Assemble StateGraph
    workflow = StateGraph(PlannerExecutorState)
    
    workflow.add_node("planner", planner_node)
    workflow.add_node("flight_specialist", flight_specialist_node)
    workflow.add_node("hotel_specialist", hotel_specialist_node)
    workflow.add_node("activity_specialist", activity_specialist_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("synthesizer", synthesizer_node)

    workflow.set_entry_point("planner")

    # Fan-out from planner to worker specialists
    workflow.add_edge("planner", "flight_specialist")
    workflow.add_edge("planner", "hotel_specialist")
    workflow.add_edge("planner", "activity_specialist")

    # Fan-in from worker specialists to critic
    workflow.add_edge("flight_specialist", "critic")
    workflow.add_edge("hotel_specialist", "critic")
    workflow.add_edge("activity_specialist", "critic")

    # Conditional feedback loop from critic
    workflow.add_conditional_edges(
        "critic",
        route_critic_decision,
        {
            "synthesizer": "synthesizer",
            "planner": "planner"
        }
    )

    workflow.add_edge("synthesizer", END)

    return workflow.compile()
