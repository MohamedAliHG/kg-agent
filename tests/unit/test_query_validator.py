from __future__ import annotations

import pytest

from core.exceptions import UnsafeCypherError
from graph.query_validator import validate_readonly_cypher


@pytest.mark.parametrize(
    "query",
    [
        "CREATE (n)",
        "MATCH (n) DETACH DELETE n",
        "MERGE (n:Thing {id: $id})",
        "MATCH (n) SET n.name = $name",
        "MATCH (n) REMOVE n.name",
        "DROP INDEX some_index",
        "LOAD CSV FROM 'file:///a.csv' AS row RETURN row",
        "CALL dbms.components()",
        "CALL apoc.meta.schema()",
        "CALL db.labels()",
        "CALL gds.pageRank.stream('graph') YIELD nodeId RETURN nodeId",
        "MATCH (n) RETURN n; MATCH (m) RETURN m",
        "MATCH (n) // comment\nRETURN n",
        "CREATE INDEX FOR (n:Thing) ON (n.id)",
    ],
)
def test_query_validator_blocks_unsafe_cypher(query: str) -> None:
    with pytest.raises(UnsafeCypherError):
        validate_readonly_cypher(query)


def test_query_validator_allows_readonly_traversal() -> None:
    validate_readonly_cypher(
        """
        MATCH (a)-[:REL]->(b)
        OPTIONAL MATCH (b)-[:NEXT]->(c)
        WHERE a.id = $id
        WITH a, b, c
        RETURN a, b, c
        ORDER BY a.id
        LIMIT $limit
        """
    )


def test_query_validator_allows_semicolon_inside_string_literal() -> None:
    validate_readonly_cypher("MATCH (n) WHERE n.text = 'a;b' RETURN n LIMIT 1")
