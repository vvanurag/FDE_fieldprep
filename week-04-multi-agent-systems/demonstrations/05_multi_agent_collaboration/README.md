# Pattern 05: Multi-Agent Collaboration & Networked Teams

## 🎯 Purpose
Demonstrates role-based multi-agent collaboration with specialized agent nodes communicating through shared state graphs (Orchestrator, Research Specialist, Coding Specialist, Reviewer, and Synthesizer).

## 📐 Architecture
```mermaid
flowchart TD
    Task["Complex Enterprise Task"] --> Orchestrator["Orchestrator Agent"]
    Orchestrator --> Researcher["Research Agent"]
    Researcher --> State[(Shared Graph State)]
    State --> Coder["Implementation Agent"]
    Coder --> State
    State --> Reviewer["Code Reviewer Agent"]
    Reviewer -- "Revisions Needed" --> Coder
    Reviewer -- "Approved" --> Synthesizer["Synthesizer Agent"]
    Synthesizer --> Done["Final Deliverable"]
```
