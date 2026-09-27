"""Specialist agents for the Multi-Agent Collaboration team."""

from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from common.llm_factory import get_llm
from common.logging import get_logger
from .schemas import MultiAgentState, SupervisorDecision, SecurityReviewResult, AgentRole

logger = get_logger("multi_agent_team")

SUPERVISOR_PROMPT = """You are the Technical Lead & Supervisor of a specialized software engineering agent team.
Team Roles:
1. 'researcher': Researches architectural algorithms, concurrency safety, and optimal library design.
2. 'coder': Implements complete, typed, robust Python code.
3. 'reviewer': Conducts rigorous security, concurrency, and performance reviews.
4. 'synthesizer': Compiles the final executive solution with documentation and usage guide.

Workflow Policy:
- If research is missing -> Delegate to 'researcher'.
- If research is done but code is missing -> Delegate to 'coder'.
- If code is written but not yet reviewed -> Delegate to 'reviewer'.
- If review failed (is_approved=False) -> Delegate back to 'coder' with review feedback.
- If review passed (is_approved=True) -> Delegate to 'synthesizer'.
- If synthesizer has finished -> Select 'FINISH'.
"""

RESEARCHER_PROMPT = """You are a Senior Staff Systems Researcher.
Analyze the user's software engineering goal.
Detail the necessary data structures (e.g. OrderedDict / Doubly Linked List for LRU, RLock for thread safety), time complexity (O(1) get/put), TTL eviction algorithms, and race condition mitigations.
Provide clear, actionable design notes for the Coder.
"""

CODER_PROMPT = """You are a Principal Software Engineer in Python.
Your job is to implement clean, production-ready, type-annotated, thread-safe Python code.
Follow the Researcher's architecture notes and address all feedback points from the Reviewer if this is a revision.
Write complete, runnable code with docstrings, type annotations, and unit-test examples.
"""

REVIEWER_PROMPT = """You are an Adversarial QA & Security Auditor.
Review the candidate Python code artifact against:
1. Thread-safety & Concurrency: Are locks properly acquired/released during read/write?
2. Memory leaks & TTL eviction edge cases.
3. Type safety & Error Handling.

Return structured verdict: is_approved (bool), vulnerabilities, and actionable fix instructions if rejected.
"""

SYNTHESIZER_PROMPT = """You are the Technical Documentation & Release Engineer.
Compile the validated code, architecture decisions, and verification tests into a clean markdown release package.
"""


def build_supervisor_agent(provider: str = "openai", model_name: str = "gpt-4o-mini"):
    llm = get_llm(provider=provider, model_name=model_name, temperature=0.0)
    return llm.with_structured_output(SupervisorDecision)


def build_reviewer_agent(provider: str = "openai", model_name: str = "gpt-4o-mini"):
    llm = get_llm(provider=provider, model_name=model_name, temperature=0.0)
    return llm.with_structured_output(SecurityReviewResult)


def build_specialist_llm(provider: str = "openai", model_name: str = "gpt-4o-mini"):
    return get_llm(provider=provider, model_name=model_name, temperature=0.0)
