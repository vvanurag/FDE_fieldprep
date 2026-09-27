"""LangGraph Implementation of the ReAct (Reason + Act) Tool-Calling Loop."""

from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage, ToolMessage, SystemMessage
from common.llm_factory import get_llm
from common.logging import get_logger
from .schemas import ReActAgentState
from .tools import ALL_REACT_TOOLS

logger = get_logger("react_agent")

SYSTEM_PROMPT = """You are a precise Financial & Market Intelligence Agent.
You have access to real-time tools for stock quotes, SEC filings, currency conversion, and portfolio calculations.

Rules:
1. Always reason step-by-step before invoking any tool.
2. If a tool returns an error or missing ticker, read the error message carefully and adjust your approach.
3. Perform exact calculations using the calculator tool rather than estimating.
4. When all necessary data is gathered, provide a clear, concise, and structured final summary to the user.
"""


def build_react_agent(provider: str = "openai", model_name: str = "gpt-4o-mini"):
    """Compiles and returns a pure LangGraph ReAct StateGraph agent."""
    
    # 1. Initialize LLM and bind tool definitions
    llm = get_llm(provider=provider, model_name=model_name, temperature=0.0)
    llm_with_tools = llm.bind_tools(ALL_REACT_TOOLS)
    
    # Map tool name -> callable
    tool_map = {t.name: t for t in ALL_REACT_TOOLS}

    # 2. Define Node: LLM Reasoner
    def llm_reasoner_node(state: ReActAgentState) -> Dict[str, Any]:
        """Model analyzes conversation history and emits either a Tool Call or Final Response."""
        current_iter = state.get("iteration_count", 0) + 1
        messages = state["messages"]
        
        # Inject system prompt at the beginning if not present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
            
        logger.info(f"[bold cyan]🧠 [Step {current_iter}] LLM Reasoner running...[/bold cyan]")
        response = llm_with_tools.invoke(messages)
        
        return {
            "messages": [response],
            "iteration_count": current_iter,
        }

    # 3. Define Node: Tool Executor
    def tool_executor_node(state: ReActAgentState) -> Dict[str, Any]:
        """Dispatches and executes all tool_calls emitted by the LLM in the last turn."""
        last_message = state["messages"][-1]
        tool_messages: List[ToolMessage] = []
        visited: List[Dict[str, Any]] = []

        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            for tool_call in last_message.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                call_id = tool_call["id"]
                
                logger.info(f"   [yellow]🔧 Invoking Tool:[/yellow] [bold]{tool_name}[/bold] with args={tool_args}")
                
                if tool_name in tool_map:
                    try:
                        tool_output = tool_map[tool_name].invoke(tool_args)
                    except Exception as e:
                        tool_output = f'{{"status": "error", "message": "Exception during execution: {str(e)}"}}'
                else:
                    tool_output = f'{{"status": "error", "message": "Tool \'{tool_name}\' is not registered."}}'
                
                tool_messages.append(
                    ToolMessage(
                        content=str(tool_output),
                        tool_call_id=call_id,
                        name=tool_name
                    )
                )
                visited.append({"tool": tool_name, "args": tool_args, "iteration": state.get("iteration_count", 0)})

        return {
            "messages": tool_messages,
            "visited_tools": visited
        }

    # 4. Conditional Edge: Routing & Safeguards
    def should_continue(state: ReActAgentState) -> str:
        """Determines whether to continue tool execution, stop on completion, or halt on limit."""
        current_iter = state.get("iteration_count", 0)
        max_iter = state.get("max_iterations", 6)
        
        # Safeguard 1: Max iteration limit reached
        if current_iter >= max_iter:
            logger.warning(f"[bold red]⚠️ Safeguard Triggered: Max iterations ({max_iter}) reached. Halting loop.[/bold red]")
            return "end"

        # Check last message for tool calls
        last_message = state["messages"][-1]
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "tools"
        
        # No tool calls -> Model emitted final answer
        logger.info("[bold green]✅ Model reached final conclusion (no further tool calls required).[/bold green]")
        return "end"

    # 5. Assemble StateGraph
    workflow = StateGraph(ReActAgentState)
    
    workflow.add_node("reasoner", llm_reasoner_node)
    workflow.add_node("tools", tool_executor_node)

    workflow.set_entry_point("reasoner")
    workflow.add_conditional_edges(
        "reasoner",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )
    workflow.add_edge("tools", "reasoner")

    return workflow.compile()
