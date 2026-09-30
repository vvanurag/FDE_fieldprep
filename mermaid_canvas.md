# 🏗️ LangGraph Complete Agent Architecture & Coordination Diagram

This diagram illustrates how **START/END**, **StateGraph Nodes**, **LLMs**, **Tools**, **Conditional Edges**, and the **Checkpointer (Memory)** coordinate at every step of execution.

```mermaid
flowchart TD
    %% Global Entry
    UserInput["👤 User Input / Interaction<br/><code>graph.invoke(state, config={'thread_id': '...'})</code>"] --> START([🟢 START])

    %% State & Checkpointer Layer
    subgraph StateAndMemory ["🧠 Shared State & Persistence Layer"]
        CurrentState[("📋 Graph State (TypedDict)<br/>• messages: Annotated[list, add_messages]<br/>• user_context, turn_counter, metadata")]
        Checkpointer[("💾 Checkpointer (MemorySaver / Postgres)<br/>Auto-saves snapshot at every node boundary")]
    end

    START -->|1. Initializes State| CurrentState
    CurrentState <-->|Loads/Saves| Checkpointer

    %% Agent / LLM Node
    subgraph AgentNodeBlock ["📦 Node: 'agent_node' / 'interviewer_node'"]
        direction TB
        PromptPrep["1. Assemble Context<br/>(System Prompt + State Messages)"]
        LLMCall["2. Invoke LLM<br/><code>llm_with_tools.invoke(messages)</code>"]
        DeltaReturn["3. Return Delta State<br/><code>{'messages': [AIMessage]}</code>"]
        
        PromptPrep --> LLMCall --> DeltaReturn
    end

    CurrentState -->|2. Reads State| PromptPrep
    DeltaReturn -->|3. Updates State via Reducer| CurrentState

    %% External LLM Provider
    subgraph ExternalLLM ["🤖 Foundation Model (LLM)"]
        direction TB
        LLMEngine["Gemini / GPT-4o / Claude<br/><i>Inspects prompt & schemas</i>"]
        DecisionTree{"Model Decides:<br/>Call a Tool or Answer User?"}
        LLMEngine --> DecisionTree
    end

    LLMCall <-->|API Request / Response| LLMEngine

    %% Conditional Routing Edge
    subgraph ConditionalEdgeBlock ["🚦 Conditional Edge: router() / should_continue()"]
        direction TB
        InspectLastMsg{"Check last message:<br/><code>if last_msg.tool_calls:</code>"}
    end

    DeltaReturn -->|4. Triggers Routing Check| InspectLastMsg

    %% Tools Node & Python Tool Functions
    subgraph ToolExecutionBlock ["🛠️ Node: 'tools_node' (Tool Execution)"]
        direction TB
        ParseToolCall["1. Parse Tool Calls<br/>(Extract tool name & arguments)"]
        RunPythonTools["2. Execute Python Functions<br/>• <code>get_job_requirements()</code><br/>• <code>evaluate_response()</code><br/>• <code>calculator / search / sql</code>"]
        WrapToolMessage["3. Wrap Output as ToolMessage<br/><code>ToolMessage(content=..., tool_call_id=...)</code>"]
        
        ParseToolCall --> RunPythonTools --> WrapToolMessage
    end

    %% Branching Logic
    InspectLastMsg -->|"YES (Tools Needed)"| ParseToolCall
    WrapToolMessage -->|5. Update State with Tool Output| CurrentState
    WrapToolMessage -->|6. Static Edge: Loop back to LLM| PromptPrep

    %% Termination Branch
    InspectLastMsg -->|"NO (Tool calling finished)"| END([🔴 END])
    END --> FinalOutput["💬 Yield Final Response to User / Terminal<br/><i>(Graph pauses and waits for next turn)</i>"]

    %% Styling
    classDef startEnd fill:#10b981,stroke:#047857,stroke-width:2px,color:#ffffff,font-weight:bold;
    classDef llmBlock fill:#6366f1,stroke:#4338ca,stroke-width:2px,color:#ffffff;
    classDef toolBlock fill:#f59e0b,stroke:#b45309,stroke-width:2px,color:#ffffff;
    classDef memoryBlock fill:#0ea5e9,stroke:#0284c7,stroke-width:2px,color:#ffffff;
    classDef routerBlock fill:#8b5cf6,stroke:#6d28d9,stroke-width:2px,color:#ffffff;

    class START,END startEnd;
    class ExternalLLM llmBlock;
    class ToolExecutionBlock toolBlock;
    class StateAndMemory memoryBlock;
    class ConditionalEdgeBlock routerBlock;
```
