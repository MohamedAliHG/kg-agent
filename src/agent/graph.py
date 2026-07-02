"""Build the LangGraph tool-calling workflow."""

from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agent.nodes import create_call_model_node
from agent.state import GraphRAGState
from core.config import Settings
from core.exceptions import LLMConfigurationError
from graph.neo4j_client import Neo4jClient
from tools.registry import build_tool_registry


def build_graph(client: Neo4jClient, settings: Settings):
    """Build and compile the LangGraph workflow."""
    if not settings.llm_model:
        raise LLMConfigurationError("LLM_MODEL is required.")

    llm = ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=settings.llm_temperature,
    )
    tools = build_tool_registry(client, settings.schema_profile, default_limit=settings.max_results)
    call_model = create_call_model_node(llm, tools)

    builder = StateGraph(GraphRAGState)
    builder.add_node("call_model", call_model)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "call_model")
    builder.add_conditional_edges("call_model", tools_condition, {"tools": "tools", END: END})
    builder.add_edge("tools", "call_model")
    return builder.compile()
