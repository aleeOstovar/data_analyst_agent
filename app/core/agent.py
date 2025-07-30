import os
import asyncio
from typing import Annotated, List, Dict, Any, Optional
from typing_extensions import TypedDict
import logging

# LangGraph and LangChain imports
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain.tools import StructuredTool
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg import Connection

from ..config.settings import (
    OPENAI_API_KEY,
    DEFAULT_MODEL_NAME,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_AUTHORIZED_IMPORTS,
    POSTGRESS_CONNECTION_STRING,
)
from .interpreter_tool import local_python_executor

logger = logging.getLogger(__name__)

# Define the state for our graph
class AgentState(TypedDict):
    messages: Annotated[List, add_messages]
    tool_status: Optional[Dict[str, Any]]
    error_message: Optional[str]
    stop_requested: bool

class DataAnalysisAgent:
    def __init__(
        self,
        llm=None,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        authorized_imports: List[str] = DEFAULT_AUTHORIZED_IMPORTS,
        additional_tools: List = []
    ):
        self.llm = llm or self._get_llm()
        self.system_prompt = system_prompt
        self.authorized_imports = authorized_imports
        self._checkpointer = None
        self.agent = None
        
    def _get_llm(self, api_key: str = OPENAI_API_KEY, model_name: str = DEFAULT_MODEL_NAME, **kwargs):
        """Create an LLM instance"""
        return ChatOpenAI(
            api_key=api_key,
            model=model_name,
            **kwargs
        )
    
    async def _get_checkpointer(self):
        """Lazy initialization of checkpointer"""
        if self._checkpointer is None:
            # Run connection creation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            connection_kwargs = {
                "autocommit": True,
                "prepare_threshold": 0,
            }
            
            def create_checkpointer():
                conn = Connection.connect(POSTGRESS_CONNECTION_STRING, **connection_kwargs)
                checkpointer = PostgresSaver(conn)
                checkpointer.setup()
                return checkpointer
            
            self._checkpointer = await loop.run_in_executor(None, create_checkpointer)
        return self._checkpointer
        
    async def _create_agent(self, additional_tools: List):
        """Create the agent graph"""
        # Create the Python executor tool
        def _local_python_executor(code: str):
            """Execute Python code safely with restricted imports."""
            try:
                result = local_python_executor(code, self.authorized_imports)
                return {"status": "success", "result": result}
            except Exception as e:
                return {"status": "error", "error": str(e)}

        python_tool = StructuredTool.from_function(
            func=_local_python_executor,
            name="python_tool",
            description="Execute Python code. Inputs: code (str)."
        )
        
        tools = [python_tool] + additional_tools
        llm_with_tools = self.llm.bind_tools(tools=tools)
        
        # Define nodes
        def llm_node(state: AgentState) -> AgentState:
            if state.get("stop_requested", False):
                return {
                    "messages": [AIMessage(content="Process stopped by user.")],
                    "stop_requested": True
                }
                
            if state.get("error_message"):
                return {
                    "messages": [AIMessage(content=f"Error occurred: {state['error_message']}")],
                    "stop_requested": True
                }
                
            messages = state["messages"]
            payload = [SystemMessage(content=self.system_prompt)] + messages
            response = llm_with_tools.invoke(payload)
            return {"messages": response}
        
        def tools_node(state: AgentState) -> AgentState:
            if state.get("stop_requested", False):
                return {
                    "messages": [AIMessage(content="Process stopped by user.")],
                    "stop_requested": True
                }
            
            tool_calls = state["messages"][-1].tool_calls
            results = []
            tools_dict = {tool.name: tool for tool in tools}
            
            for tool_call in tool_calls:
                try:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    tool_call_id = tool_call["id"]
                    
                    if tool_name not in tools_dict:
                        error_msg = f"Tool {tool_name} not found."
                        results.append(ToolMessage(content=error_msg, tool_call_id=tool_call_id))
                        return {
                            "messages": results,
                            "tool_status": {"status": "error", "error": error_msg},
                            "error_message": error_msg,
                            "stop_requested": False
                        }
                        
                    tool = tools_dict[tool_name]
                    tool_result = tool.invoke(tool_args)
                    
                    if tool_result.get("status") == "error":
                        error_msg = f"Tool {tool_name} failed: {tool_result['error']}"
                        results.append(ToolMessage(content=error_msg, tool_call_id=tool_call_id))
                        return {
                            "messages": results,
                            "tool_status": tool_result,
                            "error_message": error_msg,
                            "stop_requested": False
                        }
                    
                    results.append(ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call_id
                    ))
                    
                except Exception as e:
                    error_msg = f"Tool execution failed: {str(e)}"
                    results.append(ToolMessage(
                        content=error_msg,
                        tool_call_id=tool_call.get("id", "unknown")
                    ))
                    return {
                        "messages": results,
                        "tool_status": {"status": "error", "error": str(e)},
                        "error_message": error_msg,
                        "stop_requested": False
                    }
            
            return {
                "messages": results,
                "tool_status": {"status": "success"},
                "stop_requested": False
            }
    
        def route_tools(state: AgentState):
            if state.get("stop_requested", False) or state.get("error_message"):
                return "end"
            last_message = state["messages"][-1]
            if last_message.tool_calls:
                return "tools"
            return "end"
        
        # Build graph
        builder = StateGraph(AgentState)
        builder.add_node("llm", llm_node)
        builder.add_node("tools", tools_node)
        builder.add_conditional_edges("llm", route_tools, {"tools": "tools", "end": END})
        builder.add_edge("tools", "llm")
        builder.set_entry_point("llm")
        
        checkpointer = await self._get_checkpointer()
        return builder.compile(checkpointer=checkpointer)
    
    async def analyze(self, query: str, thread_id: str = "default", stop: bool = False) -> Dict[str, Any]:
        """Analyze data asynchronously"""
        # Lazy initialization of agent
        if self.agent is None:
            self.agent = await self._create_agent([])
            
        config = {"configurable": {"thread_id": thread_id}}
        initial_state = {
            "messages": [HumanMessage(content=query)],
            "stop_requested": stop,
            "tool_status": None,
            "error_message": None
        }
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: self.agent.invoke(initial_state, config=config)
        )
        return response