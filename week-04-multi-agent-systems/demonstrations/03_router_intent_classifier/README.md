# Pattern 03: Router & Intent Classifier

## 🎯 Purpose
Demonstrates an intelligent routing pattern where incoming queries or tasks are classified to invoke specialized subgraphs, prompt pipelines, or specialized toolsets.

## 📐 Architecture
```mermaid
flowchart TD
    Input["User Query"] --> Router{"Intent Router Node"}
    Router -- "Billing / Payment" --> BillingAgent["Billing Specialist Agent"]
    Router -- "Technical Bug" --> TechAgent["Tech Support Agent"]
    Router -- "Sales / Inbound" --> SalesAgent["Sales Agent"]
    BillingAgent --> Synthesizer["Unified Response"]
    TechAgent --> Synthesizer
    SalesAgent --> Synthesizer
```
