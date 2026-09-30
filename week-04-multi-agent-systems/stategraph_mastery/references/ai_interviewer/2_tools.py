import os
from typing import Annotated, TypedDict, Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# --- STATE ---
class InterviewState(TypedDict):
    messages: Annotated[list, add_messages]
    candidate_name: str
    job_role: str

# --- TOOLS ---
@tool
def get_job_requirements(role: str) -> str:
    """Get the key skills needed for a job role."""
    requirements = {
        "Python Developer": "Must know: Python, SQL, FastAPI, Git.",
        "Frontend Developer": "Must know: React, CSS, JavaScript, TypeScript.",
    }
    return requirements.get(role, "General software engineering skills.")

tools = [get_job_requirements]

# --- MODEL WITH TOOLS ---
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
llm_with_tools = llm.bind_tools(tools)

# --- NODES ---
def chatbot_node(state: InterviewState):
    """Decides what to do: call a tool or speak to the user."""
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

def tools_node(state: InterviewState):
    """Executes the tool calls requested by the LLM."""
    last_message = state["messages"][-1]
    results = []
    
    # Map tool names to actual functions
    tool_map = {t.name: t for t in tools}
    
    for tool_call in last_message.tool_calls:
        selected_tool = tool_map[tool_call["name"]]
        output = selected_tool.invoke(tool_call["args"])
        results.append(
            ToolMessage(content=str(output), tool_call_id=tool_call["id"])
        )
    return {"messages": results}

# --- ROUTING LOGIC ---
def should_continue(state: InterviewState) -> Literal["tools", "end"]:
    last_message = state["messages"][-1]
    # If LLM wants to use tools, go to 'tools' node
    if last_message.tool_calls:
        return "tools"
    # Otherwise, stop and wait for user input
    return "end"

# --- GRAPH ---
builder = StateGraph(InterviewState)

builder.add_node("chatbot", chatbot_node)
builder.add_node("tools", tools_node)

builder.add_edge(START, "chatbot")

# Conditional Edge: Chatbot -> (Tools OR End)
builder.add_conditional_edges(
    "chatbot",
    should_continue,
    {"tools": "tools", "end": END}
)

# Tool Edge: Tools -> Chatbot (Loop back so LLM can read the tool output)
builder.add_edge("tools", "chatbot")

graph = builder.compile()

# --- RUN IT ---
if __name__ == "__main__":
    print("--- Running Tool Graph ---")
    
    # We simulate a conversation history where the user just answered
    simulation_state = {
        "candidate_name": "Bob",
        "job_role": "Python Developer",
        "messages": [
            ("user", "Hi, I'm applying for Python Developer. What do I need to know?"),
        ]
    }
    
    # The agent should call 'get_job_requirements' then answer
    events = graph.stream(simulation_state)
    for event in events:
        for key, value in event.items():
            print(f"\n[Node: {key}]")
            # Print the last message content from this node
            if "messages" in value:
                print(value["messages"][-1])
