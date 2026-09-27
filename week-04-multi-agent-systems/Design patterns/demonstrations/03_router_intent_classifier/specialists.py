"""Specialized domain handlers and subgraphs for the Router pattern."""

from langchain_core.messages import SystemMessage, HumanMessage
from common.llm_factory import get_llm
from common.logging import get_logger

logger = get_logger("router_specialists")

BILLING_PROMPT = """You are the Senior Billing & Accounts Specialist.
You handle invoices, subscriptions, payment receipts, Stripe charge IDs, and refund policies.

Guidelines:
1. Always reference invoice or transaction IDs if provided in the context.
2. Clearly explain billing cycles (annual vs monthly) and payment terms.
3. Be professional, empathetic, and precise regarding financial numbers.
"""

TECH_SUPPORT_PROMPT = """You are the Senior Technical Support & SRE Specialist.
You handle API errors, SDK integrations, rate limits, 500/504 errors, and system health status.

Guidelines:
1. Diagnose root causes based on error codes and system architecture.
2. Provide actionable debugging steps (e.g. headers, curl commands, timeout configurations).
3. Reference relevant system components (Gateway, Database connection pool, Auth token refresh).
"""

SALES_PROMPT = """You are the Enterprise Sales & Solutions Architect.
You handle volume pricing, custom SLA agreements, dedicated VPC deployments, and seat tiers.

Guidelines:
1. Emphasize enterprise value (SOC2 compliance, 99.99% uptime SLA, dedicated support).
2. Ask qualifying questions regarding team size and integration timeline.
3. Offer scheduling a solutions architecture call with our technical sales team.
"""

FAQ_PROMPT = """You are the General Knowledge & FAQ Assistant.
You answer standard company questions (office locations, supported platforms, business hours).
Keep responses concise, polite, and direct.
"""


def execute_specialist(domain: str, query: str, entities: dict, provider: str = "openai", model_name: str = "gpt-4o-mini") -> str:
    """Executes the specialized prompt with the optimal model configuration."""
    llm = get_llm(provider=provider, model_name=model_name, temperature=0.0)
    
    prompts = {
        "billing": BILLING_PROMPT,
        "technical_support": TECH_SUPPORT_PROMPT,
        "sales_inquiry": SALES_PROMPT,
        "general_faq": FAQ_PROMPT
    }
    
    system_instruction = prompts.get(domain, FAQ_PROMPT)
    
    context_str = f"User Query: {query}\n"
    if entities:
        context_str += f"Extracted Entities from Router: {entities}\n"
        
    response = llm.invoke([
        SystemMessage(content=system_instruction),
        HumanMessage(content=context_str)
    ])
    
    return response.content.strip()


def handle_clarification(query: str, confidence: float, reasoning: str) -> str:
    """Generates a structured clarification request when classification confidence is below threshold."""
    return (
        f"I want to make sure I connect you with the right team. Your request ('{query}') could relate to multiple areas "
        f"(confidence: {confidence:.2f} - {reasoning}).\n\n"
        f"Please select the option that best describes what you need:\n"
        f"1. 💳 **Billing & Invoices** (Payments, receipts, subscription tiers, refunds)\n"
        f"2. 🛠 **Technical Support** (API errors, SDK bugs, latency issues, integration help)\n"
        f"3. 💼 **Enterprise Sales** (Custom contracts, volume discounts, security reviews)\n"
        f"4. ℹ️ **General Questions** (Company information, documentation links)"
    )
