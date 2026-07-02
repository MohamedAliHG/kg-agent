#!/usr/bin/env python
"""Inspect high-level Neo4j schema information."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from core.config import load_settings
from core.logging import configure_logging
from graph.neo4j_client import Neo4jClient
from graph.template_engine import validate_schema_identifier


def _print_rows(title: str, rows: list[dict]) -> None:
    print(f"\n{title}")
    if not rows:
        print("- none")
        return
    for row in rows:
        print(f"- {row}")


def main() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)
    profile = settings.schema_profile
    client = Neo4jClient(settings)
    entity_label = validate_schema_identifier(profile.entity_label)
    chunk_label = validate_schema_identifier(profile.chunk_label)
    entity_type_property = validate_schema_identifier(profile.entity_type_property)
    chunk_text_property = validate_schema_identifier(profile.chunk_text_property)
    try:
        _print_rows(
            "Node label counts",
            client.query(
                "MATCH (n) UNWIND labels(n) AS label RETURN label, count(*) AS count "
                "ORDER BY count DESC"
            ),
        )
        _print_rows(
            "Entity types",
            client.query(
                f"MATCH (n:{entity_label}) "
                f"RETURN n.{entity_type_property} AS type, count(*) AS count "
                "ORDER BY count DESC LIMIT 50"
            ),
        )
        _print_rows(
            "Relationship types",
            client.query(
                "MATCH ()-[r]->() RETURN type(r) AS type, count(*) AS count ORDER BY count DESC"
            ),
        )
        _print_rows(
            "Sample chunks",
            client.query(
                f"MATCH (c:{chunk_label}) "
                f"RETURN c.{chunk_text_property} AS text LIMIT 5"
            ),
        )
        _print_rows("Sample nodes", client.query("MATCH (n) RETURN labels(n) AS labels, n LIMIT 5"))
        _print_rows(
            "Sample relationships",
            client.query(
                "MATCH (a)-[r]->(b) "
                "RETURN labels(a) AS source_labels, type(r) AS type, labels(b) AS target_labels LIMIT 5"
            ),
        )
    finally:
        client.close()


if __name__ == "__main__":
    main()
