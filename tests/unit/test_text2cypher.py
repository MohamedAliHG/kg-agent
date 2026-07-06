from __future__ import annotations

import pytest
from langchain_core.messages import AIMessage

from core.exceptions import UnsafeCypherError
from graph.text2cypher import (
    build_schema_context,
    build_text2cypher_prompt,
    generate_text2cypher_query,
    normalize_generated_cypher,
    render_grounded_values,
)


class FakeLLM:
    def __init__(self, content: str) -> None:
        self.content = content
        self.messages = None

    def invoke(self, messages):
        self.messages = messages
        return AIMessage(content=self.content)


def test_build_schema_context_includes_profile_shape(technical_profile) -> None:
    context = build_schema_context(technical_profile)

    assert "Document" in context
    assert "Chunk" in context
    assert "HAS_FAULT_CODE" in context
    assert "AlphanumericFaultCode" in context


def test_text2cypher_prompt_includes_fault_code_traversal_example(technical_profile) -> None:
    messages = build_text2cypher_prompt(technical_profile, "fault code 3310B01", limit=5)
    system_content = messages[0].content

    assert "Grounded value hints" in system_content
    assert "fault_codes" in system_content
    assert "3310B01" in system_content
    assert "Correctly resolves from fault code through malfunction." in system_content
    assert "MATCH (malfunction)-[:HAS_FAULT_ISOLATION_REFERENCE]->" in system_content


def test_render_grounded_values_is_config_driven(technical_profile) -> None:
    rendered = render_grounded_values(technical_profile.text2cypher.grounded_values)

    assert "fault_codes" in rendered
    assert "^[0-9]{4}[A-Z][0-9]{2}$" in rendered


def test_normalize_generated_cypher_strips_fence_and_caps_limit() -> None:
    cypher = normalize_generated_cypher(
        """
        ```cypher
        MATCH (n:Entity)
        RETURN n
        LIMIT 500
        ```
        """,
        limit=10,
    )

    assert cypher == "MATCH (n:Entity)\nRETURN n\nLIMIT 10"


def test_generate_text2cypher_query_validates_generated_query(technical_profile) -> None:
    llm = FakeLLM("MATCH (n:Entity) RETURN n")

    cypher = generate_text2cypher_query(llm, technical_profile, "show entities", limit=3)

    assert cypher.endswith("LIMIT 3")


def test_generate_text2cypher_query_blocks_write_query(technical_profile) -> None:
    llm = FakeLLM("MATCH (n) DELETE n")

    with pytest.raises(UnsafeCypherError):
        generate_text2cypher_query(llm, technical_profile, "delete everything", limit=3)
