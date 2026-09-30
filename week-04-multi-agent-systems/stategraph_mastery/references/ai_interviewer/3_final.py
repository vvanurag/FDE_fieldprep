import uuid
from typing import Annotated, TypedDict, Literal

from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# ================= STATE =================
class InterviewState(TypedDict):
    messages: Annotated[list, add_messages]
    candidate_name: str
    job_role: str
    question_count: int  # Track how many questions asked

# ================= TOOLS =================
@tool
def get_job_requirements(role: str) -> str:
    """Get technical requirements for a role."""
    reqs = {
        "Backend": "Python, SQL, API design, scalable systems.",
        "Frontend": "React, CSS, Accessibility, State management.",
    }
    return reqs.get(role, "General software engineering skills.")

@tool
def evaluate_response(response: str) -> str:
    """Analyze the candidate's response for quality."""
    # In a real app, this might call another LLM or use complex logic
    length = len(response.split())
    if length < 5:
        return "Assessment: Too short. Ask them to elaborate."
    return "Assessment: Good length. Verify specific technical details next."

tools = [get_job_requirements, evaluate_response]

# ================= MODEL =================
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
llm_with_tools = llm.bind_tools(tools)

# ================= NODES =================
def interviewer_node(state: InterviewState):
    """Main logic: Interview the candidate."""
    name = state["candidate_name"]
    role = state["job_role"]
    count = state.get("question_count", 0)
    
    # System prompt injection
    system_msg = (
        f"You are an expert technical interviewer for a {role} position. "
        f"Candidate name: {name}. "
        f"You have asked {count} questions so far. "
        "Goal: Assess their skills. Use tools to check requirements or evaluate answers. "
        "Be professional but encouraging. Keep questions concise."
    )
    
    # We prepend the system message to the history for this call only
    messages = [("system", system_msg)] + state["messages"]
    
    response = llm_with_tools.invoke(messages)
    
    # If the response is text (not a tool call), we count it as a question
    # (unless it's just the very first greeting)
    is_question = bool(response.content and not response.tool_calls)
    new_count = count + 1 if is_question else count
    
    return {"messages": [response], "question_count": new_count}

def tool_node(state: InterviewState):
    """Execute tools."""
    last_msg = state["messages"][-1]
    tool_map = {t.name: t for t in tools}
    results = []
    
    for call in last_msg.tool_calls:
        tool_func = tool_map[call["name"]]
        res = tool_func.invoke(call["args"])
        results.append(ToolMessage(content=str(res), tool_call_id=call["id"]))
        
    return {"messages": results}

# ================= ROUTING =================
def router(state: InterviewState) -> Literal["tools", "end"]:
    last_msg = state["messages"][-1]
    if last_msg.tool_calls:
        return "tools"
    return "end"

# ================= GRAPH BUILD =================
builder = StateGraph(InterviewState)

builder.add_node("interviewer", interviewer_node)
builder.add_node("tools", tool_node)

builder.add_edge(START, "interviewer")
builder.add_conditional_edges("interviewer", router, {"tools": "tools", "end": END})
builder.add_edge("tools", "interviewer")

# ADD MEMORY
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

# ================= MAIN LOOP =================
if __name__ == "__main__":
    print("--- AI INTERVIEWER LIVE ---")
    name = input("Your Name: ") or "Guest"
    role = input("Role (Backend/Frontend): ") or "Backend"
    
    # Unique thread ID for this conversation
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # Initialize State
    initial_update = {
        "candidate_name": name, 
        "job_role": role, 
        "question_count": 0,
        # Injection to start the conversation
        "messages": [("user", "I am ready for my interview.")] 
    }
    
    # First turn (Agent starts)
    for event in graph.stream(initial_update, config=config):
        for val in event.values():
            if "messages" in val:
                msg = val["messages"][-1]
                if msg.content:
                    print(f"\nAI: {msg.content}")

    # Conversation Loop
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["quit", "exit"]:
            break
            
        # Stream the agent's response
        # We only pass the NEW message. MemorySaver loads the rest.
        for event in graph.stream({"messages": [("user", user_input)]}, config=config):
            for val in event.values():
                if "messages" in val:
                    msg = val["messages"][-1]
                    # Only print actual text, not internal tool messages
                    if msg.content and not msg.tool_calls:
                        print(f"\nAI: {msg.content}")
