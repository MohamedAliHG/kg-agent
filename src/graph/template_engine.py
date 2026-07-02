"""Controlled dynamic Cypher builder."""

import re

from core.exceptions import ConfigurationError, ToolInputError
from graph.cypher import QueryName, TEMPLATES
from graph.query_validator import validate_readonly_cypher
from graph.schema import SchemaProfile

_SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def validate_schema_identifier(value: str) -> str:
    """Validate a Neo4j label, relationship type, or property identifier."""
    if not _SAFE_IDENTIFIER_RE.fullmatch(value):
        raise ConfigurationError(f"Unsafe schema identifier: {value!r}")
    return value


def _id(value: str) -> str:
    return validate_schema_identifier(value)


def _type_predicate(variable: str, schema_profile: SchemaProfile, entity_type: str) -> str:
    type_property = _id(schema_profile.entity_type_property)
    aliases = [_id(alias) for alias in schema_profile.aliases_for(entity_type)]
    labels = " OR ".join(f"{variable}:{alias}" for alias in aliases)
    params = ", ".join(repr(alias) for alias in aliases)
    return f"({variable}.{type_property} IN [{params}] OR {labels})"


def _template_values(schema_profile: SchemaProfile) -> dict[str, str]:
    path = schema_profile.preparation_path()
    malfunction_type = path[0].source
    code_type = path[0].target
    reference_type = path[1].target
    figure_type = path[2].target
    preparation_type = path[3].target

    page_property = schema_profile.chunk_page_property or schema_profile.chunk_id_property

    return {
        "document_label": _id(schema_profile.document_label),
        "document_id_property": _id(schema_profile.document_id_property),
        "chunk_label": _id(schema_profile.chunk_label),
        "chunk_id_property": _id(schema_profile.chunk_id_property),
        "chunk_text_property": _id(schema_profile.chunk_text_property),
        "chunk_page_property": _id(page_property),
        "entity_label": _id(schema_profile.entity_label),
        "entity_id_property": _id(schema_profile.entity_id_property),
        "entity_name_property": _id(schema_profile.entity_name_property),
        "entity_code_property": _id(schema_profile.entity_code_property),
        "entity_raw_text_property": _id(schema_profile.entity_raw_text_property),
        "chunk_entity_relationship": _id(schema_profile.chunk_entity_relationship),
        "chunk_document_relationship": _id(schema_profile.chunk_document_relationship),
        "fault_code_relationship": _id(path[0].type),
        "reference_relationship": _id(path[1].type),
        "figure_relationship": _id(path[2].type),
        "preparation_relationship": _id(path[3].type),
        "preparation_label": _id(preparation_type),
        "malfunction_type_predicate": _type_predicate("m", schema_profile, malfunction_type),
        "code_type_predicate": _type_predicate("code", schema_profile, code_type),
        "reference_type_predicate": _type_predicate("ref", schema_profile, reference_type),
        "figure_type_predicate": _type_predicate("fig", schema_profile, figure_type),
        "preparation_type_predicate": _type_predicate("prep", schema_profile, preparation_type),
    }


def build_preparation_query(
    schema_profile: SchemaProfile,
    fault_code: str | None = None,
    malfunction: str | None = None,
    preparation_id: str | None = None,
    limit: int = 5,
) -> tuple[str, dict[str, str | int]]:
    """Build a safe parameterized preparation-context query from whitelisted templates."""
    if limit < 1 or limit > 100:
        raise ToolInputError("limit must be between 1 and 100")

    values = _template_values(schema_profile)
    params: dict[str, str | int] = {"limit": int(limit)}

    if preparation_id:
        template = TEMPLATES[QueryName.GET_PREPARATION_CONTEXT_FROM_PREPARATION_ID]
        params["preparation_id"] = preparation_id
    elif fault_code:
        template = TEMPLATES[QueryName.GET_PREPARATION_CONTEXT_FROM_CODE]
        params["fault_code"] = fault_code
    elif malfunction:
        template = TEMPLATES[QueryName.GET_PREPARATION_CONTEXT_FROM_MALFUNCTION]
        params["malfunction"] = malfunction
    else:
        raise ToolInputError("At least one of preparation_id, fault_code, or malfunction is required.")

    query = template.format(**values).strip()
    validate_readonly_cypher(query)
    return query, params
