from __future__ import annotations

from types import SimpleNamespace

import pytest

from core.exceptions import ConfigurationError
from tools.registry import build_tool_registry


class MockClient:
    pass


class MockLLM:
    pass


def _settings(mode: str, schema_profile):
    return SimpleNamespace(tool_mode=mode, schema_profile=schema_profile, max_results=5)


def test_tool_registry_predefined_mode(technical_profile) -> None:
    tools = build_tool_registry(MockClient(), _settings("predefined", technical_profile), MockLLM())

    assert [tool.name for tool in tools] == ["get_preparation_context"]


def test_tool_registry_text2cypher_mode(technical_profile) -> None:
    tools = build_tool_registry(MockClient(), _settings("text2cypher", technical_profile), MockLLM())

    assert [tool.name for tool in tools] == ["text2cypher_query"]


def test_tool_registry_hybrid_mode(technical_profile) -> None:
    tools = build_tool_registry(MockClient(), _settings("hybrid", technical_profile), MockLLM())

    assert [tool.name for tool in tools] == ["get_preparation_context", "text2cypher_query"]


def test_tool_registry_none_mode(technical_profile) -> None:
    tools = build_tool_registry(MockClient(), _settings("none", technical_profile), MockLLM())

    assert tools == []


def test_tool_registry_rejects_unknown_mode(technical_profile) -> None:
    with pytest.raises(ConfigurationError):
        build_tool_registry(MockClient(), _settings("bad", technical_profile), MockLLM())
