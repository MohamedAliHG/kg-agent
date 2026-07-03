"""LangGraph node factories."""

from collections.abc import Callable, Sequence
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool

from agent.state import GraphRAGState


def create_call_model_node(
    llm: BaseChatModel,
    tools: Sequence[BaseTool],
) -> Callable[[GraphRAGState], dict[str, Any]]:
    """Create a model-calling node bound to graph tools."""
    llm_with_tools = llm.bind_tools(tools) if tools else llm

    def call_model(state: GraphRAGState) -> dict[str, Any]:
        response = llm_with_tools.invoke(state["messages"])
        update: dict[str, Any] = {"messages": [response]}
        if isinstance(response, AIMessage) and not response.tool_calls:
            update["answer"] = response.content if isinstance(response.content, str) else str(response.content)
        return update

    return call_model
