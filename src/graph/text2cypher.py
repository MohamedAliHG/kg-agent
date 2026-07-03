"""Experimental Text2Cypher generation helpers."""

import re
import textwrap

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from graph.query_validator import validate_readonly_cypher
from graph.schema import SchemaProfile

_FENCED_BLOCK_RE = re.compile(r"```(?:cypher)?\s*(.*?)```", flags=re.DOTALL | re.IGNORECASE)
_LIMIT_RE = re.compile(r"\bLIMIT\s+(\d+)\b", flags=re.IGNORECASE)


def build_schema_context(schema_profile: SchemaProfile) -> str:
    """Render schema profile details for Text2Cypher prompting."""
    relationships = "\n".join(
        f"- ({rel.source})-[:{rel.type}]->({rel.target})" for rel in schema_profile.relationships
    )
    aliases = "\n".join(
        f"- {entity_type}: {', '.join(values)}"
        for entity_type, values in sorted(schema_profile.label_aliases.items())
    )
    return f"""Node labels:
- {schema_profile.document_label}
- {schema_profile.chunk_label}
- {schema_profile.entity_label}

Document properties:
- {schema_profile.document_id_property}

Chunk properties:
- {schema_profile.chunk_id_property}
- {schema_profile.chunk_text_property}
- {schema_profile.chunk_page_property or schema_profile.chunk_id_property}

Entity properties:
- {schema_profile.entity_type_property}
- {schema_profile.entity_id_property}
- {schema_profile.entity_name_property}
- {schema_profile.entity_code_property}
- {schema_profile.entity_raw_text_property}

Entity types:
{chr(10).join(f"- {entity_type}" for entity_type in schema_profile.entity_types)}

Relationships:
{relationships}

Label aliases:
{aliases or "- none"}"""


def build_text2cypher_prompt(schema_profile: SchemaProfile, question: str, limit: int) -> list:
    """Build messages for a read-only Text2Cypher generation call."""
    schema_context = build_schema_context(schema_profile)
    text2cypher_context = render_text2cypher_profile(schema_profile, limit)
    system = f"""You generate read-only Cypher for a Neo4j graph.

Rules:
- Return only one Cypher query.
- Use only the labels, relationships, properties, and entity types in the schema.
- Relationship direction matters. Do not connect two nodes with a relationship unless that exact
  directed relationship appears in the schema.
- Do not include explanations, markdown, comments, or apologies.
- Do not write data. Never use CREATE, MERGE, DELETE, DETACH, SET, REMOVE, DROP, LOAD CSV, or CALL.
- Prefer MATCH / OPTIONAL MATCH / WITH / RETURN queries.
- Always include LIMIT {limit} or lower.
- For fuzzy text matching, prefer stable user tokens with all(token IN [...] WHERE text CONTAINS token)
  over one exact full phrase.

Schema:
{schema_context}

Profile-specific Text2Cypher guidance:
{text2cypher_context}"""
    return [
        SystemMessage(content=system),
        HumanMessage(content=f"Question: {question}\nCypher:"),
    ]


def render_text2cypher_profile(schema_profile: SchemaProfile, limit: int) -> str:
    """Render profile-specific Text2Cypher hints and examples."""
    profile = schema_profile.text2cypher
    sections = []

    if profile and profile.description:
        sections.append(f"Description:\n{profile.description}")

    rules = list(profile.rules) if profile else []
    if rules:
        sections.append("Additional rules:\n" + "\n".join(f"- {rule}" for rule in rules))

    grounded_values = render_grounded_values(profile.grounded_values if profile else {})
    if grounded_values:
        sections.append("Grounded value hints:\n" + grounded_values)

    examples = render_examples(profile.examples if profile else [], limit)
    if examples:
        sections.append("Cypher examples:\n" + examples)
    else:
        sections.append("Cypher examples:\n" + _build_generic_examples(schema_profile, limit))

    return "\n\n".join(sections)


def render_grounded_values(grounded_values: dict) -> str:
    """Render grounded value hints from the schema profile."""
    rendered = []
    for name, hint in grounded_values.items():
        lines = [f"- {name}:"]
        if hint.description:
            lines.append(f"  description: {hint.description}")
        if hint.pattern:
            lines.append(f"  pattern: {hint.pattern}")
        if hint.properties:
            lines.append(f"  properties: {', '.join(hint.properties)}")
        if hint.examples:
            lines.append(f"  examples: {', '.join(hint.examples)}")
        rendered.append("\n".join(lines))
    return "\n".join(rendered)


def render_examples(examples: list, limit: int) -> str:
    """Render configured Text2Cypher few-shot examples."""
    rendered = []
    for example in examples:
        cypher = normalize_generated_cypher(example.cypher, limit=limit)
        parts = [f"# Question: {example.question}"]
        if example.notes:
            parts.append(f"# Notes: {example.notes}")
        parts.append(cypher)
        rendered.append("\n".join(parts))
    return "\n\n".join(rendered)


def generate_text2cypher_query(
    llm: BaseChatModel,
    schema_profile: SchemaProfile,
    question: str,
    limit: int = 10,
) -> str:
    """Generate, normalize, and validate a read-only Cypher query."""
    response = llm.invoke(build_text2cypher_prompt(schema_profile, question, limit))
    content = response.content if isinstance(response.content, str) else str(response.content)
    cypher = normalize_generated_cypher(content, limit=limit)
    validate_readonly_cypher(cypher)
    return cypher


def normalize_generated_cypher(raw: str, limit: int) -> str:
    """Strip formatting and enforce a safe result limit on generated Cypher."""
    cypher = textwrap.dedent(_strip_code_fence(raw)).strip()
    cypher = cypher.rstrip(";").strip()
    cypher = _cap_or_append_limit(cypher, limit)
    return cypher


def _strip_code_fence(raw: str) -> str:
    match = _FENCED_BLOCK_RE.search(raw)
    if match:
        return match.group(1)
    return raw


def _cap_or_append_limit(cypher: str, limit: int) -> str:
    match = _LIMIT_RE.search(cypher)
    if not match:
        return f"{cypher}\nLIMIT {limit}"

    current_limit = int(match.group(1))
    if current_limit <= limit:
        return cypher
    return _LIMIT_RE.sub(f"LIMIT {limit}", cypher, count=1)


def _build_generic_examples(schema_profile: SchemaProfile, limit: int) -> str:
    entity_label = schema_profile.entity_label
    entity_type = schema_profile.entity_type_property
    entity_name = schema_profile.entity_name_property
    chunk_label = schema_profile.chunk_label
    chunk_text = schema_profile.chunk_text_property
    chunk_entity = schema_profile.chunk_entity_relationship
    return f"""# Find chunks mentioning an entity by name
MATCH (entity:{entity_label})<-[:{chunk_entity}]-(chunk:{chunk_label})
WHERE toLower(coalesce(entity.{entity_name}, entity.{schema_profile.entity_id_property})) CONTAINS toLower("example")
RETURN chunk.{schema_profile.chunk_id_property} AS chunk_id, chunk.{chunk_text} AS chunk_text
LIMIT {limit}

# Count entities by type
MATCH (entity:{entity_label})
RETURN entity.{entity_type} AS entity_type, count(*) AS count
ORDER BY count DESC
LIMIT {limit}"""
