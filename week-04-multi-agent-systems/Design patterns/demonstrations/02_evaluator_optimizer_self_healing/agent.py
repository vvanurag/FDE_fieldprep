"""LangGraph StateGraph implementation of Evaluator-Optimizer & Self-Healing Pattern."""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from common.llm_factory import get_llm
from common.logging import get_logger
from .schemas import EvaluatorOptimizerState
from .evaluator import validate_incident_report

logger = get_logger("evaluator_optimizer")

GENERATOR_PROMPT = """You are an SRE Incident Extraction Agent.
Your job is to read an unstructured incident narrative and extract a structured JSON report.

Required JSON Fields:
- incident_id: (string) Must match format 'INC-XXXXX' (e.g. 'INC-10294').
- severity: (string) Must be one of: 'SEV-1', 'SEV-2', 'SEV-3'.
- root_cause_summary: (string) Detailed root cause (minimum 20 characters).
- impacted_services: (list of strings) Non-empty list of impacted services.
- estimated_downtime_minutes: (number) Total system downtime in minutes.
- sla_breached: (boolean) true or false.
- remediation_steps: (list of strings) At least 2 concrete engineering actions taken.

IMPORTANT BUSINESS RULE:
Any SEV-1 incident with downtime > 15 minutes MUST have 'sla_breached': true.

Output ONLY valid raw JSON with no wrapping text or markdown ticks.
"""

REFINER_PROMPT = """You are a Self-Healing Code & Schema Correction Agent.
The candidate JSON output generated for an incident report failed strict schema validation and business rules.

Raw Incident Narrative:
{narrative}

Previous Draft:
{draft}

Validation Errors Encountered:
{errors}

Past Error History:
{error_history}

Instructions:
1. Carefully analyze each validation error and past error history.
2. Fix every failing field, type mismatch, or business rule violation.
3. Return ONLY the corrected raw JSON object.
"""


def build_evaluator_optimizer_agent(provider: str = "openai", model_name: str = "gpt-4o-mini"):
    """Builds and compiles the LangGraph Evaluator-Optimizer state machine."""
    
    llm = get_llm(provider=provider, model_name=model_name, temperature=0.0)

    # 1. Generator Node (Initial Draft)
    def generator_node(state: EvaluatorOptimizerState) -> Dict[str, Any]:
        logger.info("[bold cyan]📝 [Node: Generator] Generating initial structured JSON draft...[/bold cyan]")
        narrative = state["raw_incident_narrative"]
        
        response = llm.invoke([
            SystemMessage(content=GENERATOR_PROMPT),
            HumanMessage(content=f"Incident Narrative:\n{narrative}")
        ])
        
        return {
            "draft_output": response.content.strip(),
            "retry_count": 0,
            "error_history": []
        }

    # 2. Evaluator Node (Deterministic Validator)
    def evaluator_node(state: EvaluatorOptimizerState) -> Dict[str, Any]:
        draft = state["draft_output"]
        retries = state.get("retry_count", 0)
        logger.info(f"[bold magenta]🔍 [Node: Evaluator] Auditing draft (Attempt {retries + 1})...[/bold magenta]")
        
        is_valid, errors, parsed_data = validate_incident_report(draft)
        
        if is_valid:
            logger.info("[bold green]✅ [Evaluator] Draft passed all schema and business rule validations![/bold green]")
            return {
                "is_approved": True,
                "parsed_report": parsed_data,
                "validation_errors": None,
                "final_message": "Incident report successfully extracted and validated."
            }
        else:
            logger.warning(f"[bold yellow]⚠️ [Evaluator] Validation failed with {len(errors)} error(s):[/bold yellow]")
            for err in errors:
                logger.warning(f"   - {err}")
                
            updated_history = state.get("error_history", []) + errors
            return {
                "is_approved": False,
                "validation_errors": errors,
                "error_history": updated_history,
                "parsed_report": None
            }

    # 3. Refiner Node (Self-Healing Loop)
    def refiner_node(state: EvaluatorOptimizerState) -> Dict[str, Any]:
        current_retries = state.get("retry_count", 0) + 1
        errors_str = "\n".join(f"- {e}" for e in state.get("validation_errors", []))
        history_str = "\n".join(f"- {h}" for h in state.get("error_history", []))
        
        logger.info(f"[bold red]🔧 [Node: Refiner] Executing Self-Healing Refinement (Retry {current_retries}/{state.get('max_retries', 3)})...[/bold red]")
        
        prompt = REFINER_PROMPT.format(
            narrative=state["raw_incident_narrative"],
            draft=state["draft_output"],
            errors=errors_str,
            error_history=history_str
        )
        
        response = llm.invoke([
            SystemMessage(content="You are a precision JSON bug-fixer."),
            HumanMessage(content=prompt)
        ])
        
        return {
            "draft_output": response.content.strip(),
            "retry_count": current_retries
        }

    # 4. Router Edge (Conditional branching)
    def route_evaluation(state: EvaluatorOptimizerState) -> str:
        if state.get("is_approved", False):
            return "approved"
        
        retries = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 3)
        
        if retries < max_retries:
            return "refine"
        else:
            logger.error(f"[bold red]❌ [Router] Max retries ({max_retries}) exhausted. Routing to Dead-Letter/Fallback.[/bold red]")
            return "failed"

    # Assemble StateGraph
    workflow = StateGraph(EvaluatorOptimizerState)
    
    workflow.add_node("generator", generator_node)
    workflow.add_node("evaluator", evaluator_node)
    workflow.add_node("refiner", refiner_node)

    workflow.set_entry_point("generator")
    workflow.add_edge("generator", "evaluator")
    
    workflow.add_conditional_edges(
        "evaluator",
        route_evaluation,
        {
            "approved": END,
            "refine": "refiner",
            "failed": END
        }
    )
    
    workflow.add_edge("refiner", "evaluator")

    return workflow.compile()
