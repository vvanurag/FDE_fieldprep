# 🤖 AI Job Interviewer Agent (LangGraph + Gemini Reference)

Source: [github.com/rakia/ai-interviewer](https://github.com/rakia/ai-interviewer)

An AI Job Interviewer agent that conducts technical interviews, evaluates candidate answers, and adapts questions dynamically using **LangGraph** and **Google Gemini**.

---

## 📑 Walkthrough Examples

### 1. [`1_basic.py`](1_basic.py) — Part 1.1: The Skeleton (Basic Graph)
Builds the minimal foundational structure: `InterviewState` (TypedDict with `add_messages`) and a single greeting Node.

### 2. [`2_tools.py`](2_tools.py) — Part 1.2: Adding Brains & Tools (ReAct Loop)
Adds tool calling (`get_job_requirements`), a tool execution node, and a cyclic ReAct edge that loops back from `tools` to `chatbot`.

### 3. [`3_final.py`](3_final.py) — Part 1.3: The Final Agent (Memory & Interactive Loop)
Integrates `MemorySaver` for persistent multi-turn thread memory (`thread_id`), dynamic candidate assessment tools (`evaluate_response`), and an interactive terminal chat loop.

---

## 🚀 Running the Examples

```bash
# Set your Google Gemini API key
export GOOGLE_API_KEY="your-key-here"

# Run Part 1.1: Basic Graph
python3 1_basic.py

# Run Part 1.2: Tool ReAct Loop
python3 2_tools.py

# Run Part 1.3: Interactive Interviewer with Memory
python3 3_final.py
```
