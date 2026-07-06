from __future__ import annotations

import inspect
from pathlib import Path

from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agent import graph as agent_graph
from agent import nodes as agent_nodes
from agent import state as agent_state
from retrieval.context_builder import build_resolved_context


def test_agent_state_uses_messages_state() -> None:
    source = inspect.getsource(agent_state)

    assert "from langgraph.graph import MessagesState" in source
    assert "class GraphRAGState(MessagesState):" in source


def test_agent_graph_uses_official_langgraph_primitives() -> None:
    graph_source = inspect.getsource(agent_graph)
    node_source = inspect.getsource(agent_nodes)

    assert StateGraph.__name__ in graph_source
    assert ToolNode.__name__ in graph_source
    assert tools_condition.__name__ in graph_source
    assert "bind_tools" in node_source


def test_agent_implementation_does_not_use_legacy_agent_executor() -> None:
    src_root = Path(__file__).resolve().parents[2] / "src"
    source = "\n".join(path.read_text() for path in src_root.rglob("*.py"))

    assert "AgentExecutor" not in source


def test_answer_context_uses_returned_chunk_text() -> None:
    context = build_resolved_context(
        [
            {
                "chunk_id": "c1",
                "reference": "Perform figure 2-1, Preparation A",
                "chunk_text": "Disconnect electrical power before opening the panel.",
            }
        ]
    )

    assert "Disconnect electrical power" in context
    assert context.strip() != "Perform figure 2-1, Preparation A"
