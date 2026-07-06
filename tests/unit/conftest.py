from __future__ import annotations

import pytest

from graph.schema import RelationshipProfile, SchemaProfile


@pytest.fixture
def technical_profile() -> SchemaProfile:
    return SchemaProfile(
        name="technical_manual",
        document_label="Document",
        document_id_property="id",
        chunk_label="Chunk",
        chunk_id_property="id",
        chunk_text_property="text",
        chunk_page_property="page_no",
        entity_label="Entity",
        entity_type_property="type",
        entity_id_property="id",
        entity_name_property="name",
        entity_code_property="code",
        entity_raw_text_property="raw_text",
        chunk_entity_relationship="HAS_ENTITY",
        chunk_document_relationship="PART_OF",
        entity_types=[
            "Malfunction",
            "AlphanumericFaultCode",
            "FaultIsolationReference",
            "Figure",
            "Preparation",
        ],
        relationships=[
            RelationshipProfile(
                source="Malfunction",
                type="HAS_FAULT_CODE",
                target="AlphanumericFaultCode",
            ),
            RelationshipProfile(
                source="Malfunction",
                type="HAS_FAULT_ISOLATION_REFERENCE",
                target="FaultIsolationReference",
            ),
            RelationshipProfile(
                source="FaultIsolationReference",
                type="REFERENCES_FIGURE",
                target="Figure",
            ),
            RelationshipProfile(source="Figure", type="DEFINES_PREPARATION", target="Preparation"),
            RelationshipProfile(source="Chunk", type="HAS_ENTITY", target="Entity"),
            RelationshipProfile(source="Chunk", type="PART_OF", target="Document"),
        ],
        label_aliases={
            "AlphanumericFaultCode": ["Alphanumericfaultcode"],
            "FaultIsolationReference": ["Faultisolationreference"],
        },
        text2cypher={
            "description": "Technical maintenance document graph.",
            "rules": [
                "Relationship direction must exactly match the schema.",
                "Use chunks as final evidence.",
            ],
            "grounded_values": {
                "fault_codes": {
                    "description": "Alphanumeric maintenance fault codes.",
                    "pattern": "^[0-9]{4}[A-Z][0-9]{2}$",
                    "properties": ["code", "name", "id"],
                    "examples": ["3310B01"],
                }
            },
            "examples": [
                {
                    "question": "What actions should I perform if fault code 3310B01 occurs?",
                    "notes": "Correctly resolves from fault code through malfunction.",
                    "cypher": """
                    MATCH (code:Entity)
                    WHERE code.type IN ["AlphanumericFaultCode", "Alphanumericfaultcode"]
                      AND coalesce(code.code, code.name, code.id) = "3310B01"
                    MATCH (malfunction:Entity)-[:HAS_FAULT_CODE]->(code)
                    MATCH (malfunction)-[:HAS_FAULT_ISOLATION_REFERENCE]->(reference:Entity)
                    MATCH (reference)-[:REFERENCES_FIGURE]->(figure:Entity)
                    MATCH (figure)-[:DEFINES_PREPARATION]->(preparation:Entity)
                    MATCH (chunk:Chunk)-[:HAS_ENTITY]->(preparation)
                    RETURN chunk.id AS chunk_id, chunk.text AS chunk_text
                    LIMIT 5
                    """,
                }
            ],
        },
    )


@pytest.fixture
def custom_profile() -> SchemaProfile:
    return SchemaProfile(
        name="custom",
        document_label="DocNode",
        document_id_property="doc_key",
        chunk_label="TextBlock",
        chunk_id_property="block_key",
        chunk_text_property="body",
        chunk_page_property="sheet",
        entity_label="Thing",
        entity_type_property="kind",
        entity_id_property="thing_key",
        entity_name_property="display",
        entity_code_property="identifier",
        entity_raw_text_property="verbatim",
        chunk_entity_relationship="MENTIONS",
        chunk_document_relationship="IN_DOC",
        entity_types=["Issue", "Signal", "ManualRef", "Illustration", "Task"],
        relationships=[
            RelationshipProfile(source="Issue", type="HAS_SIGNAL", target="Signal"),
            RelationshipProfile(source="Issue", type="HAS_MANUAL_REF", target="ManualRef"),
            RelationshipProfile(source="ManualRef", type="POINTS_TO_ILLUSTRATION", target="Illustration"),
            RelationshipProfile(source="Illustration", type="DEFINES_TASK", target="Task"),
            RelationshipProfile(source="TextBlock", type="MENTIONS", target="Thing"),
            RelationshipProfile(source="TextBlock", type="IN_DOC", target="DocNode"),
        ],
        label_aliases={"Signal": ["AltSignal"]},
    )
