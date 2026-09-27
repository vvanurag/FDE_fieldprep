# 🛠 Week 4: Agentic AI Core Design Pattern Demonstrations

This folder contains focused, production-grade demonstrations for the **6 fundamental Agentic AI design patterns**, implemented using LangGraph, LangChain, Pydantic schemas, and structured error handling.

---

## 📌 Matrix of Demonstrations

| # | Design Pattern | Core Mechanism | Focus / Key Concepts |
| :--- | :--- | :--- | :--- |
| **01** | **[ReAct / Tool-Loop Pattern](01_react_tool_loop/)** | Dynamic `Thought → Action → Observation` | Dynamic tool calling loop, argument extraction, tool output ingestion. |
| **02** | **[Evaluator-Optimizer & Self-Healing](02_evaluator_optimizer_self_healing/)** | Generator $\rightarrow$ Validator $\rightarrow$ Refiner | Schema validation, Pydantic guardrails, automatic error-guided correction loops. |
| **03** | **[Router & Intent Classifier](03_router_intent_classifier/)** | Single prompt / classifier $\rightarrow$ Branch | Dynamic branch routing, semantic / rule-based classification, specialized subgraphs. |
| **04** | **[Planner-Executor-Critic](04_planner_executor_critic/)** | Plan DAG $\rightarrow$ Parallel Workers $\rightarrow$ Audit | Task decomposition, dependency graphs, milestone validation, budget/time audits. |
| **05** | **[Multi-Agent Collaboration](05_multi_agent_collaboration/)** | Role specialization & state sharing | LangGraph multi-node state coordination (Researcher, Coder, Reviewer, Synthesizer). |
| **06** | **[Human-in-the-Loop (HITL)](06_human_in_the_loop/)** | Pausing, Approval & State Editing | LangGraph `interrupt()`, human verification gates, state modification before resumption. |

---

## 🚀 Execution Guide

Each demonstration includes standalone runnable scripts (`demo.py` or `main.py`) with test inputs and verbose execution tracing.
