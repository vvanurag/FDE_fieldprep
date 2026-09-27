# Pattern 04: Planner-Executor-Critic

## 🎯 Purpose
Demonstrates advanced decomposition and planning. A Planner generates structured subtasks, specialized Executor nodes process subtasks concurrently, and a Critic validates the integrated output against constraints (budget, feasibility, completeness) before synthesis.

## 📐 Architecture
```mermaid
flowchart TD
    Goal["Complex Objective"] --> Planner["Planner Agent"]
    Planner --> PlanDAG["Structured Plan / Subtasks"]
    PlanDAG --> Exec1["Executor 1 (Research)"]
    PlanDAG --> Exec2["Executor 2 (Implementation)"]
    PlanDAG --> Exec3["Executor 3 (Formatting)"]
    Exec1 --> Critic{"Critic / Auditor Node"}
    Exec2 --> Critic
    Exec3 --> Critic
    Critic -- "Deficiencies Detected" --> Planner
    Critic -- "Passed All Constraints" --> Synthesizer["Synthesizer Agent"]
    Synthesizer --> Final["Completed Dossier"]
```
