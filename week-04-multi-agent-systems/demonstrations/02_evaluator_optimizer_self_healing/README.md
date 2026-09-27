# Pattern 02: Evaluator-Optimizer & Self-Healing

## 🎯 Purpose
Demonstrates an agent architecture where a Generator creates a candidate output, an Evaluator/Validator audits it against strict rules/schemas, and errors trigger an automated Self-Correction refinement loop (as seen in `tfs_agent`).

## 📐 Architecture
```mermaid
flowchart TD
    Prompt["Initial Task"] --> Generator["Generator Node"]
    Generator --> Candidate["Draft Output"]
    Candidate --> Evaluator{"Validator / Critic"}
    Evaluator -- "Validation Failed (with feedback)" --> Refiner["Self-Healing Refiner Node"]
    Refiner --> Candidate
    Evaluator -- "Passed" --> Final["Validated Production Output"]
```
