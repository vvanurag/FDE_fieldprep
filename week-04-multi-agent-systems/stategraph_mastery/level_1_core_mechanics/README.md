# 🎯 Level 1: StateGraph Core Mechanics Drills

Mastering the foundational building blocks of LangGraph: **State Reducers**, **Cyclic Loops & Safeguards**, and **Persistent Checkpointing with Thread Isolation**.

---

## 📑 Exercises in this Level

| Exercise File | Core Topic & Concept | Key API / Functions Learned |
| :--- | :--- | :--- |
| **[`01_reducers_and_concurrency.py`](01_reducers_and_concurrency.py)** | State Reducers & Parallel Fan-Out Safety | `operator.add`, `add_messages`, Custom Reducer functions, Parallel Fan-Out, Mutation Pitfall vs. Delta Returns. |
| **[`02_loops_and_recursion_bounds.py`](02_loops_and_recursion_bounds.py)** | Cyclic Feedback Loops & Recursion Bounds | `add_conditional_edges`, `recursion_limit` config, state-tracked retry budgets, graceful fallback routing. |
| **[`03_checkpoints_and_session_isolation.py`](03_checkpoints_and_session_isolation.py)** | State Persistence, Sessions & Time-Travel | `MemorySaver`, `thread_id` session isolation, `get_state()`, `get_state_history()`, and checkpoint rewinding. |

---

## 🚀 Running the Drills

Run each drill directly from the workspace root:

```bash
# Exercise 1: Reducers & Concurrency Safety
python3 -m week-04-multi-agent-systems.stategraph_mastery.level_1_core_mechanics.01_reducers_and_concurrency

# Exercise 2: Cyclic Loops & Recursion Safeguards
python3 -m week-04-multi-agent-systems.stategraph_mastery.level_1_core_mechanics.02_loops_and_recursion_bounds

# Exercise 3: Checkpointing, Thread Isolation & Time-Travel
python3 -m week-04-multi-agent-systems.stategraph_mastery.level_1_core_mechanics.03_checkpoints_and_session_isolation
```
