import os
from typing import Annotated, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# 1. Define State
# The "clipboard" that holds data as it moves through the graph.
class InterviewState(TypedDict):
    # add_messages: Appends new messages to the history instead of overwriting
    messages: Annotated[list, add_messages]
    candidate_name: str
    job_role: str

# 2. Define the LLM
if not os.environ.get("GOOGLE_API_KEY"):
    print("Error: GOOGLE_API_KEY is not set!")
    exit(1)

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)

# 3. Define Nodes
def greet_node(state: InterviewState):
    """Generates a greeting."""
    name = state["candidate_name"]
    role = state["job_role"]

    greeting = (
        f"Hello {name}! I'm your AI interviewer for the {role} position. "
        "Let's start: Tell me about yourself."
    )
    # We return ONLY the update (the new message)
    return {"messages": [("assistant", greeting)]}

# 4. Build Graph
builder = StateGraph(InterviewState)
builder.add_node("greeter", greet_node)

builder.add_edge(START, "greeter")
builder.add_edge("greeter", END)

graph = builder.compile()

# 5. Run It
if __name__ == "__main__":
    print("--- Running Basic Graph ---")
    initial_state = {
        "candidate_name": "Alice",
        "job_role": "Python Developer",
        "messages": []
    }
    result = graph.invoke(initial_state)
    print(result["messages"][-1].content)
