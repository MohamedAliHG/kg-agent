"""Agent state definitions."""

from typing import Any

from langgraph.graph import MessagesState


class GraphRAGState(MessagesState):
    """Serializable LangGraph state for GraphRAG runs."""

    question: str
    chunk_text: str | None
    tool_results: list[dict[str, Any]]
    resolved_context: str | None
    answer: str | None
    errors: list[str]
