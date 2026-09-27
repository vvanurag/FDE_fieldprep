# 📚 Course Table of Contents & Syllabus

A structured roadmap covering Agentic AI from foundational reflex agents to production-grade enterprise multi-agent systems.

---

## 🔹 Week 1: Agentic AI Foundations & Reflex Agents

- The agent equation: prompt, tools, memory, and LLM
- The ReAct loop and the five core agentic design patterns
- Agentic-vs-autonomous decision-making and prompt engineering
- **Live Project:** [CRM Lead Qualifier Agent]
- **Outcome:** Decide when a task needs an agent — and wire up the first one that works.

---

## 🔹 Weeks 2–3: RAG-Powered Knowledge Agents

- Retrieve → augment → generate pipelines with LangChain LCEL
- Multi-turn RAG with history and hallucination prevention
- Retrieval and generation metrics: Precision@K, groundedness
- **Live Project:** [Grounded IT Support Knowledge Assistant]
- **Outcome:** Ship a RAG agent that answers only from its sources and proves it with metrics.

---

## 🔹 Week 4: Multi-Agent Systems (Planner–Executor–Critic)

- Role-based design: orchestrator, planner, synthesizer
- Task decomposition, routing, and delegation
- LangGraph state, nodes, edges, and checkpointer persistence
- **Live Project:** [Multi-Agent Travel Planner]
- **Outcome:** Split a task that breaks one agent across a team that doesn't.

---

## 🔹 Week 5: Conversational & Multimodal Agents

- Cascaded STT→LLM→TTS vs. realtime speech-to-speech trade-offs
- Reusable LangGraph subgraphs for coordination
- Human-in-the-loop approve, review-and-edit, and interrupt patterns
- **Live Project:** [Voice-Enabled E-Commerce Assistant with HITL]
- **Outcome:** Put a human in the loop without killing the conversation's UX.

---

## 🔹 Week 6: Agent Communication Protocols (MCP, A2A, ACP)

- Structured tool access via MCP and FastMCP servers
- Reliable messaging with finite state machines and validated transitions
- Networked agents over the A2A protocol via Google ADK
- **Live Project:** [Real Estate Negotiation Simulator]
- **Outcome:** Kill the ten failure modes that come from agents talking in free text.

---

## 🔹 Week 7: Hybrid Search & Retrieval

- Sparse vs. dense vectors; k-NN, ANN, and HNSW
- SPLADE for learned lexical matching
- Hybrid search with Reciprocal Rank Fusion in Qdrant
- **Live Project:** [Hybrid Product Search Agent (SPLADE + BGE + RRF)]
- **Outcome:** Beat pure-vector recall by fusing lexical and semantic retrieval.

---

## 🔹 Week 8: Agent Observability, Evaluation & Safety

- LangSmith tracing and eval datasets from curated traces
- LLM-as-judge, DeepEval metrics, and Guardrails AI
- PII redaction with Presidio; cost control via routing, caching, and batching
- **Live Project:** [Production-Ready Fintech Support Agent]
- **Outcome:** Cut an agent's cost-per-query while proving its quality didn't drop.

---

## 🔹 Week 9: Fine-Tuning & Domain Adaptation

- The prompt-vs-RAG-vs-fine-tune escalation framework
- The PEFT landscape: LoRA, QLoRA, prefix tuning, and adapters
- 4-bit quantization, TRL SFTTrainer, and deployment to the HF Hub
- **Live Project:** [Fine-Tuned Healthcare Q&A Agent]
- **Outcome:** Know when fine-tuning beats prompting — then train and ship an adapter.

---

## 🔹 Weeks 10–11: Capstone — Enterprise Multi-Agent System

- Own a real enterprise problem from architecture to build
- Integrate retrieval, orchestration, evals, safety, and cost monitoring
- Defend reliability, latency, and cost the way production systems are reviewed
- **Live Project:** [Enterprise Multi-Agent Platform (LangGraph, LangChain, Streamlit, AWS)]
- **Outcome:** Stand up a production-grade agentic system you can defend in review.
