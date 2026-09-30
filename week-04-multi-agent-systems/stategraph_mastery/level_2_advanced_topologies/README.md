# 🚀 Level 2: Advanced Dynamic Topologies & Composition

Mastering the next tier of StateGraph architecture: **Dynamic Map-Reduce with `Send`**, **Modular Subgraph Composition**, and the **Native `interrupt()` / `Command` Human-in-the-Loop Pattern**.

---

## 📑 Exercises in this Level

| Exercise File | Core Topic & Concept | Key API / Functions Learned |
| :--- | :--- | :--- |
| **[`01_dynamic_map_reduce_send.py`](01_dynamic_map_reduce_send.py)** | Dynamic Map-Reduce Fan-Out with `Send` | `from langgraph.types import Send`, dynamic runtime task decomposition, isolated worker execution, multi-worker reducer collection, synthesis. |
| **[`02_subgraph_composition.py`](02_subgraph_composition.py)** | Hierarchical Subgraph Nesting & Composition | Compiling child StateGraphs into independent units, embedding subgraphs as parent nodes, state interface boundaries, cross-graph checkpoint propagation. |
| **[`03_native_interrupt_and_command.py`](03_native_interrupt_and_command.py)** | Native `interrupt()` & `Command(resume=...)` | `from langgraph.types import interrupt, Command`, in-node state freezing, payload serialization for human UI, dynamic branch resumption (Approve / Modify / Reject). |

---

## 🚀 Running the Drills

Run each drill directly with your Python interpreter:

```bash
# Drill 1: Dynamic Map-Reduce with the Send API
python3 week-04-multi-agent-systems/stategraph_mastery/level_2_advanced_topologies/01_dynamic_map_reduce_send.py

# Drill 2: Modular Subgraphs as Nodes
python3 week-04-multi-agent-systems/stategraph_mastery/level_2_advanced_topologies/02_subgraph_composition.py

# Drill 3: Native interrupt() & Command HITL
python3 week-04-multi-agent-systems/stategraph_mastery/level_2_advanced_topologies/03_native_interrupt_and_command.py
```
