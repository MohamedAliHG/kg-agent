from __future__ import annotations

import os

import pytest

from core.config import load_settings
from graph.neo4j_client import Neo4jClient
from tools.preparation_tools import get_preparation_context_from_code


@pytest.mark.integration
def test_neo4j_preparation_tool_smoke() -> None:
    if os.getenv("RUN_NEO4J_INTEGRATION") != "1":
        pytest.skip("Set RUN_NEO4J_INTEGRATION=1 to run Neo4j integration tests.")

    settings = load_settings()
    client = Neo4jClient(settings)
    try:
        rows = get_preparation_context_from_code(
            client,
            settings.schema_profile,
            "3310B01",
            limit=1,
        )
        assert isinstance(rows, list)
    finally:
        client.close()
