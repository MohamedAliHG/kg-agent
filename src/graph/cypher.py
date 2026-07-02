"""Controlled Cypher templates."""

from enum import StrEnum


class QueryName(StrEnum):
    """Names for predefined read-only query templates."""

    GET_PREPARATION_CONTEXT_FROM_CODE = "get_preparation_context_from_code"
    GET_PREPARATION_CONTEXT_FROM_MALFUNCTION = "get_preparation_context_from_malfunction"
    GET_PREPARATION_CONTEXT_FROM_PREPARATION_ID = "get_preparation_context_from_preparation_id"


GET_PREPARATION_CONTEXT_FROM_CODE = """
MATCH (code:{entity_label})
WHERE {code_type_predicate}
AND coalesce(code.{entity_code_property}, code.{entity_name_property}, code.{entity_id_property}) = $fault_code

MATCH (m:{entity_label})-[:{fault_code_relationship}]->(code)
WHERE {malfunction_type_predicate}

MATCH (m)-[:{reference_relationship}]->(ref:{entity_label})
WHERE {reference_type_predicate}

MATCH (ref)-[:{figure_relationship}]->(fig:{entity_label})
WHERE {figure_type_predicate}

MATCH (fig)-[:{preparation_relationship}]->(prep:{entity_label})
WHERE {preparation_type_predicate}

MATCH (chunk:{chunk_label})-[:{chunk_entity_relationship}]->(prep)
OPTIONAL MATCH (chunk)-[:{chunk_document_relationship}]->(doc:{document_label})

RETURN
  coalesce(m.{entity_name_property}, m.{entity_id_property}) AS malfunction,
  coalesce(code.{entity_code_property}, code.{entity_name_property}, code.{entity_id_property}) AS fault_code,
  coalesce(ref.{entity_raw_text_property}, ref.{entity_name_property}, ref.{entity_id_property}) AS reference,
  coalesce(fig.{entity_name_property}, fig.{entity_id_property}) AS figure,
  coalesce(prep.{entity_name_property}, prep.{entity_id_property}) AS preparation,
  chunk.{chunk_id_property} AS chunk_id,
  chunk.{chunk_text_property} AS chunk_text,
  chunk.{chunk_page_property} AS page_no,
  doc.{document_id_property} AS document_id
LIMIT $limit
"""

GET_PREPARATION_CONTEXT_FROM_MALFUNCTION = """
MATCH (m:{entity_label})
WHERE {malfunction_type_predicate}
  AND (
    toLower(coalesce(m.{entity_name_property}, m.{entity_id_property})) CONTAINS toLower($malfunction)
    OR toLower($malfunction) CONTAINS toLower(coalesce(m.{entity_name_property}, m.{entity_id_property}))
  )

MATCH (m)-[:{fault_code_relationship}]->(code:{entity_label})
WHERE {code_type_predicate}

MATCH (m)-[:{reference_relationship}]->(ref:{entity_label})
WHERE {reference_type_predicate}

MATCH (ref)-[:{figure_relationship}]->(fig:{entity_label})
WHERE {figure_type_predicate}

MATCH (fig)-[:{preparation_relationship}]->(prep:{entity_label})
WHERE {preparation_type_predicate}

MATCH (chunk:{chunk_label})-[:{chunk_entity_relationship}]->(prep)
OPTIONAL MATCH (chunk)-[:{chunk_document_relationship}]->(doc:{document_label})

RETURN
  coalesce(m.{entity_name_property}, m.{entity_id_property}) AS malfunction,
  coalesce(code.{entity_code_property}, code.{entity_name_property}, code.{entity_id_property}) AS fault_code,
  coalesce(ref.{entity_raw_text_property}, ref.{entity_name_property}, ref.{entity_id_property}) AS reference,
  coalesce(fig.{entity_name_property}, fig.{entity_id_property}) AS figure,
  coalesce(prep.{entity_name_property}, prep.{entity_id_property}) AS preparation,
  chunk.{chunk_id_property} AS chunk_id,
  chunk.{chunk_text_property} AS chunk_text,
  chunk.{chunk_page_property} AS page_no,
  doc.{document_id_property} AS document_id
LIMIT $limit
"""

GET_PREPARATION_CONTEXT_FROM_PREPARATION_ID = """
MATCH (prep:{preparation_label} {{{entity_id_property}: $preparation_id}})
MATCH (chunk:{chunk_label})-[:{chunk_entity_relationship}]->(prep)
OPTIONAL MATCH (chunk)-[:{chunk_document_relationship}]->(doc:{document_label})
RETURN
  prep.{entity_id_property} AS preparation,
  chunk.{chunk_id_property} AS chunk_id,
  chunk.{chunk_text_property} AS chunk_text,
  chunk.{chunk_page_property} AS page_no,
  doc.{document_id_property} AS document_id
LIMIT $limit
"""

TEMPLATES = {
    QueryName.GET_PREPARATION_CONTEXT_FROM_CODE: GET_PREPARATION_CONTEXT_FROM_CODE,
    QueryName.GET_PREPARATION_CONTEXT_FROM_MALFUNCTION: GET_PREPARATION_CONTEXT_FROM_MALFUNCTION,
    QueryName.GET_PREPARATION_CONTEXT_FROM_PREPARATION_ID: GET_PREPARATION_CONTEXT_FROM_PREPARATION_ID,
}
