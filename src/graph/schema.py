"""Typed graph schema profile models."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from core.exceptions import ConfigurationError


class RelationshipProfile(BaseModel):
    """A relationship type allowed by a schema profile."""

    source: str
    type: str
    target: str


class GroundedValueHint(BaseModel):
    """Hints for grounding common literal values during Text2Cypher generation."""

    description: str | None = None
    pattern: str | None = None
    properties: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)


class Text2CypherExample(BaseModel):
    """A few-shot Text2Cypher example loaded from the schema profile."""

    question: str
    cypher: str
    notes: str | None = None


class Text2CypherProfile(BaseModel):
    """Schema-profile-specific Text2Cypher prompting configuration."""

    description: str | None = None
    rules: list[str] = Field(default_factory=list)
    grounded_values: dict[str, GroundedValueHint] = Field(default_factory=dict)
    examples: list[Text2CypherExample] = Field(default_factory=list)


class SchemaProfile(BaseModel):
    """A typed representation of graph-shape names loaded from YAML."""

    name: str
    document_label: str
    document_id_property: str
    chunk_label: str
    chunk_id_property: str
    chunk_text_property: str
    chunk_page_property: str | None = None
    entity_label: str
    entity_type_property: str
    entity_id_property: str = "id"
    entity_name_property: str = "name"
    entity_code_property: str = "code"
    entity_raw_text_property: str = "raw_text"
    chunk_entity_relationship: str
    chunk_document_relationship: str
    entity_types: list[str] = Field(default_factory=list)
    relationships: list[RelationshipProfile] = Field(default_factory=list)
    label_aliases: dict[str, list[str]] = Field(default_factory=dict)
    text2cypher: Text2CypherProfile | None = None

    def aliases_for(self, entity_type: str) -> list[str]:
        """Return the canonical entity type plus configured aliases."""
        return [entity_type, *self.label_aliases.get(entity_type, [])]

    def preparation_path(self) -> list[RelationshipProfile]:
        """Return the ordered semantic traversal for preparation context."""
        semantic_edges = [
            edge
            for edge in self.relationships
            if edge.type
            not in {
                self.chunk_entity_relationship,
                self.chunk_document_relationship,
            }
        ]
        if len(semantic_edges) < 4:
            msg = "Schema profile must define at least four semantic preparation edges."
            raise ConfigurationError(msg)
        return semantic_edges[:4]


def load_schema_profile(path: str | Path) -> SchemaProfile:
    """Load a schema profile from YAML."""
    profile_path = Path(path)
    try:
        data: dict[str, Any] = yaml.safe_load(profile_path.read_text()) or {}
    except OSError as exc:
        msg = f"Unable to read schema profile: {profile_path}"
        raise ConfigurationError(msg) from exc

    try:
        return SchemaProfile.model_validate(data)
    except Exception as exc:
        msg = f"Invalid schema profile: {profile_path}"
        raise ConfigurationError(msg) from exc
