"""LangGraph Router & Intent Classifier StateGraph Implementation."""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from common.llm_factory import get_llm
from common.logging import get_logger
from .schemas import RouterAgentState, IntentClassificationResult, IntentCategory
from .specialists import execute_specialist, handle_clarification

logger = get_logger("router_agent")

ROUTER_SYSTEM_PROMPT = """You are an Enterprise Intent Classification and Routing Engine.
Analyze the user's incoming query and classify it into exactly ONE primary intent category:

Intent Categories:
- 'billing': Invoices, charges, receipts, refund requests, subscription renewals, credit cards.
- 'technical_support': API bugs, 500/504 errors, SDK issues, rate limits, server outages, latency.
- 'sales_inquiry': Enterprise contracts, volume pricing, demo requests, SOC2/security reviews, team licenses.
- 'general_faq': General company info, business hours, office locations, generic high-level questions.
- 'ambiguous': Queries that are too vague or span multiple unrelated intents without enough detail.

Guidelines:
1. Assign a confidence_score between 0.0 and 1.0 based on how clear and unambiguous the intent is.
2. Extract relevant entities (e.g. invoice_id, error_code, seat_count, service_name).
3. If the query is vague (e.g., 'My account is broken'), score confidence low (< 0.70) and set intent to 'ambiguous'.
"""


def build_router_agent(provider: str = "openai", model_name: str = "gpt-4o-mini"):
    """Builds and compiles the Router LangGraph StateGraph."""
    
    base_llm = get_llm(provider=provider, model_name=model_name, temperature=0.0)
    structured_router_llm = base_llm.with_structured_output(IntentClassificationResult)

    # 1. Router Classification Node
    def router_classifier_node(state: RouterAgentState) -> Dict[str, Any]:
        query = state["user_query"]
        logger.info(f"[bold cyan]🔀 [Router Node] Classifying intent for query:[/bold cyan] '{query}'")
        
        result: IntentClassificationResult = structured_router_llm.invoke([
            SystemMessage(content=ROUTER_SYSTEM_PROMPT),
            HumanMessage(content=f"User Query:\n{query}")
        ])
        
        logger.info(
            f"   [yellow]Result:[/yellow] Intent=[bold]{result.primary_intent.value}[/bold] | "
            f"Confidence=[bold]{result.confidence_score:.2f}[/bold] | "
            f"Entities={result.detected_entities}"
        )
        
        return {
            "classification": result.model_dump()
        }

    # 2. Specialist Nodes
    def billing_specialist_node(state: RouterAgentState) -> Dict[str, Any]:
        logger.info("[bold green]💳 [Node: Billing Specialist] Processing financial inquiry...[/bold green]")
        cls_data = state["classification"] or {}
        resp = execute_specialist(
            domain="billing",
            query=state["user_query"],
            entities=cls_data.get("detected_entities", {})
        )
        return {"routed_specialist": "Billing Specialist", "specialist_response": resp}

    def tech_support_node(state: RouterAgentState) -> Dict[str, Any]:
        logger.info("[bold green]🛠 [Node: Tech Support Specialist] Diagnosing technical issue...[/bold green]")
        cls_data = state["classification"] or {}
        resp = execute_specialist(
            domain="technical_support",
            query=state["user_query"],
            entities=cls_data.get("detected_entities", {})
        )
        return {"routed_specialist": "Technical Support Specialist", "specialist_response": resp}

    def sales_node(state: RouterAgentState) -> Dict[str, Any]:
        logger.info("[bold green]💼 [Node: Sales Specialist] Handling enterprise inquiry...[/bold green]")
        cls_data = state["classification"] or {}
        resp = execute_specialist(
            domain="sales_inquiry",
            query=state["user_query"],
            entities=cls_data.get("detected_entities", {})
        )
        return {"routed_specialist": "Enterprise Sales Specialist", "specialist_response": resp}

    def faq_node(state: RouterAgentState) -> Dict[str, Any]:
        logger.info("[bold green]ℹ️ [Node: General FAQ] Providing knowledge base response...[/bold green]")
        cls_data = state["classification"] or {}
        resp = execute_specialist(
            domain="general_faq",
            query=state["user_query"],
            entities=cls_data.get("detected_entities", {})
        )
        return {"routed_specialist": "General FAQ Handler", "specialist_response": resp}

    def clarification_node(state: RouterAgentState) -> Dict[str, Any]:
        logger.warning("[bold red]❓ [Node: Clarification] Low confidence detected. Requesting disambiguation...[/bold red]")
        cls_data = state["classification"] or {}
        resp = handle_clarification(
            query=state["user_query"],
            confidence=cls_data.get("confidence_score", 0.0),
            reasoning=cls_data.get("reasoning", "Ambiguous query context.")
        )
        return {"routed_specialist": "Clarification / Fallback Gate", "specialist_response": resp}

    # 3. Conditional Routing Function
    def route_decision(state: RouterAgentState) -> str:
        cls_data = state.get("classification") or {}
        confidence = cls_data.get("confidence_score", 0.0)
        threshold = state.get("confidence_threshold", 0.75)
        intent = cls_data.get("primary_intent", IntentCategory.AMBIGUOUS.value)

        # If confidence is below threshold or intent is explicitly ambiguous -> route to clarification
        if confidence < threshold or intent == IntentCategory.AMBIGUOUS.value:
            logger.info(f"   [Router Edge] Confidence ({confidence:.2f}) < Threshold ({threshold:.2f}) -> Routing to Clarification.")
            return "clarification"
        
        # Route directly to domain specialist
        route_map = {
            IntentCategory.BILLING.value: "billing",
            IntentCategory.TECHNICAL_SUPPORT.value: "technical_support",
            IntentCategory.SALES_INQUIRY.value: "sales",
            IntentCategory.GENERAL_FAQ.value: "faq"
        }
        
        target = route_map.get(intent, "clarification")
        logger.info(f"   [Router Edge] High confidence ({confidence:.2f}) -> Routing to [bold]{target}[/bold].")
        return target

    # Assemble StateGraph
    workflow = StateGraph(RouterAgentState)
    
    workflow.add_node("router", router_classifier_node)
    workflow.add_node("billing", billing_specialist_node)
    workflow.add_node("technical_support", tech_support_node)
    workflow.add_node("sales", sales_node)
    workflow.add_node("faq", faq_node)
    workflow.add_node("clarification", clarification_node)

    workflow.set_entry_point("router")

    workflow.add_conditional_edges(
        "router",
        route_decision,
        {
            "billing": "billing",
            "technical_support": "technical_support",
            "sales": "sales",
            "faq": "faq",
            "clarification": "clarification"
        }
    )

    workflow.add_edge("billing", END)
    workflow.add_edge("technical_support", END)
    workflow.add_edge("sales", END)
    workflow.add_edge("faq", END)
    workflow.add_edge("clarification", END)

    return workflow.compile()
