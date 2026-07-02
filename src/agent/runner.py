"""High-level runner for GraphRAG agent calls."""

import ast
import json
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage

from agent.graph import build_graph
from agent.prompts import build_initial_messages
from core.config import load_settings
from core.logging import configure_logging
from core.observability import build_langfuse_run_config, flush_langfuse
from graph.neo4j_client import Neo4jClient
from retrieval.context_builder import build_resolved_context


def _message_to_dict(message: BaseMessage) -> dict[str, Any]:
    return {
        "type": message.type,
        "content": message.content,
        "name": getattr(message, "name", None),
        "tool_call_id": getattr(message, "tool_call_id", None),
        "tool_calls": getattr(message, "tool_calls", None),
    }


def _parse_tool_content(content: Any) -> list[dict[str, Any]]:
    if isinstance(content, list):
        return [item for item in content if isinstance(item, dict)]
    if isinstance(content, dict):
        return [content]
    if not isinstance(content, str) or not content.strip():
        return []
    for parser in (json.loads, ast.literal_eval):
        try:
            parsed = parser(content)
        except Exception:
            continue
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
        if isinstance(parsed, dict):
            return [parsed]
    return []


def _extract_tool_results(messages: list[BaseMessage]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for message in messages:
        if isinstance(message, ToolMessage):
            rows.extend(_parse_tool_content(message.content))
    return rows


def _extract_answer(messages: list[BaseMessage]) -> str | None:
    for message in reversed(messages):
        if isinstance(message, AIMessage) and not message.tool_calls:
            return message.content if isinstance(message.content, str) else str(message.content)
    return None


def run_graphrag_agent(
    question: str,
    chunk_text: str | None = None,
    config_path: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Run the GraphRAG tool-calling agent for one question."""
    settings = load_settings(config_path)
    if limit is not None:
        settings.max_results = limit
    configure_logging(settings.log_level)
    client = Neo4jClient(settings)
    try:
        graph = build_graph(client, settings)
        initial_state = {
            "question": question,
            "chunk_text": chunk_text,
            "messages": build_initial_messages(question, chunk_text),
            "tool_results": [],
            "resolved_context": None,
            "answer": None,
            "errors": [],
        }
        recursion_limit = max(4, settings.max_tool_iterations * 2 + 2)
        run_config = {"recursion_limit": recursion_limit}
        run_config.update(build_langfuse_run_config(settings))
        state = graph.invoke(initial_state, config=run_config)
        messages = state.get("messages", [])
        tool_results = _extract_tool_results(messages)
        resolved_context = build_resolved_context(tool_results)
        answer = state.get("answer") or _extract_answer(messages)
        return {
            "question": question,
            "messages": [_message_to_dict(message) for message in messages],
            "tool_results": tool_results,
            "resolved_context": resolved_context,
            "answer": answer,
            "errors": state.get("errors", []),
        }
    finally:
        flush_langfuse(settings)
        client.close()
