# Pattern 06: Human-in-the-Loop (HITL)

## 🎯 Purpose
Demonstrates how to safely pause agent execution before high-stakes actions using LangGraph checkpointers and `interrupt()`, collect human feedback/approval/edits, and resume state execution.

## 📐 Architecture
```mermaid
flowchart TD
    UserQuery["High-Value Transaction / Sensitive Action"] --> AgentNode["Agent Preparation Node"]
    AgentNode --> PolicyCheck{"Policy Review"}
    PolicyCheck -- "Safe / Low Risk" --> AutoExec["Execute Directly"]
    PolicyCheck -- "High Stakes / Threshold Exceeded" --> Interrupt["LangGraph interrupt() Gate"]
    Interrupt --> HumanSupervisor["Human Supervisor (Approve / Edit / Reject)"]
    HumanSupervisor -- "Approved / Modified" --> Resume["Resume Workflow with Updated State"]
    Resume --> ExecAction["Execute Action"]
    HumanSupervisor -- "Rejected" --> Abort["Abort & Notify User"]
```
