# Pattern 01: ReAct / Tool-Calling Loop

## 🎯 Purpose
Demonstrates the foundational **Reason + Act** agentic pattern where the model dynamically decides which tools to invoke, receives external observations, and iterates until the goal is achieved.

## 📐 Architecture
```mermaid
flowchart TD
    UserQuery["User Query"] --> LLM["LLM (Reasoning Step)"]
    LLM --> Decision{"Tool Needed?"}
    Decision -- "Yes" --> ToolCall["Execute Tool"]
    ToolCall --> Observation["Observation / Tool Output"]
    Observation --> LLM
    Decision -- "No (Final Answer)" --> Output["Final Response"]
```
