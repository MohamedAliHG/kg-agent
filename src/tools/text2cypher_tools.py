"""Experimental Text2Cypher graph tool."""

import json
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import StructuredTool
from pydantic import ValidationError

from core.exceptions import ToolExecutionError, ToolInputError
from core.logging import get_logger
from graph.neo4j_client import Neo4jClient
from graph.schema import SchemaProfile
from graph.text2cypher import generate_text2cypher_query
from tools.schemas import Text2CypherInput, Text2CypherResult

logger = get_logger(__name__)

TEXT2CYPHER_DESCRIPTION = (
    "Experimental fallback tool for querying Neo4j with generated read-only Cypher when "
    "predefined graph tools are unavailable, insufficient, or return no useful context. "
    "Use this for exploratory graph questions. The generated Cypher is validated before execution."
)


def _validate_input(question: str, limit: int) -> Text2CypherInput:
    try:
        return Text2CypherInput(question=question, limit=limit)
    except ValidationError as exc:
        raise ToolInputError(str(exc)) from exc


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, list | tuple | set):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if hasattr(value, "items"):
        return {str(key): _jsonable(item) for key, item in dict(value).items()}
    return str(value)


def text2cypher_query(
    client: Neo4jClient,
    schema_profile: SchemaProfile,
    llm: BaseChatModel,
    question: str,
    limit: int = 10,
) -> dict[str, Any]:
    """Generate read-only Cypher for a question, execute it, and return rows."""
    args = _validate_input(question, limit)
    logger.info("Running experimental Text2Cypher tool", extra={"limit": args.limit})
    try:
        cypher = generate_text2cypher_query(
            llm=llm,
            schema_profile=schema_profile,
            question=args.question,
            limit=args.limit,
        )
        rows = [_jsonable(row) for row in client.query(cypher)]
        result = Text2CypherResult(cypher=cypher, rows=rows, row_count=len(rows))
        return result.model_dump()
    except ToolInputError:
        raise
    except Exception as exc:
        raise ToolExecutionError("Failed to run experimental Text2Cypher query.") from exc


def build_text2cypher_tools(
    client: Neo4jClient,
    schema_profile: SchemaProfile,
    llm: BaseChatModel,
    default_limit: int = 10,
) -> list[StructuredTool]:
    """Build LangChain tool wrappers for experimental Text2Cypher."""

    def _tool_impl(question: str, limit: int = 10) -> str:
        effective_limit = default_limit if limit == 10 else limit
        result = text2cypher_query(
            client=client,
            schema_profile=schema_profile,
            llm=llm,
            question=question,
            limit=effective_limit,
        )
        return json.dumps(result)

    return [
        StructuredTool.from_function(
            func=_tool_impl,
            name="text2cypher_query",
            description=TEXT2CYPHER_DESCRIPTION,
            args_schema=Text2CypherInput,
        )
    ]
