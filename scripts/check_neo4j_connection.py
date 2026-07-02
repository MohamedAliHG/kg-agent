#!/usr/bin/env python
"""Check Neo4j connectivity and basic graph counts."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from core.config import load_settings
from core.logging import configure_logging
from graph.neo4j_client import Neo4jClient
from graph.template_engine import validate_schema_identifier


def main() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)
    profile = settings.schema_profile
    client = Neo4jClient(settings)
    try:
        client.verify_connection()
        labels = {
            "Document": validate_schema_identifier(profile.document_label),
            "Chunk": validate_schema_identifier(profile.chunk_label),
            "Entity": validate_schema_identifier(profile.entity_label),
        }
        print("connection: ok")
        print(f"database: {settings.neo4j_database}")
        for display_name, label in labels.items():
            rows = client.query(f"MATCH (n:{label}) RETURN count(n) AS count")
            print(f"{display_name} nodes: {rows[0]['count'] if rows else 0}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
