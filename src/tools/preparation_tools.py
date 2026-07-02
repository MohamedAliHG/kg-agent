"""Preparation-context graph tools."""

import json
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import ValidationError

from core.exceptions import ToolExecutionError, ToolInputError
from core.logging import get_logger
from graph.neo4j_client import Neo4jClient
from graph.schema import SchemaProfile
from graph.template_engine import build_preparation_query
from tools.schemas import PreparationContextInput, PreparationContextResult

logger = get_logger(__name__)

TOOL_DESCRIPTION = (
    'Use this when a question mentions a fault code, malfunction, or cross-reference such as '
    '"Perform figure 2-1, Preparation A". The tool resolves the reference through Neo4j and '
    "returns the target preparation chunk text."
)


def _validate_input(
    fault_code: str | None,
    malfunction: str | None,
    preparation_id: str | None,
    limit: int,
) -> PreparationContextInput:
    try:
        return PreparationContextInput(
            fault_code=fault_code,
            malfunction=malfunction,
            preparation_id=preparation_id,
            limit=limit,
        )
    except ValidationError as exc:
        raise ToolInputError(str(exc)) from exc


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = PreparationContextResult.model_validate(row)
    return normalized.model_dump()


def get_preparation_context(
    client: Neo4jClient,
    schema_profile: SchemaProfile,
    fault_code: str | None = None,
    malfunction: str | None = None,
    preparation_id: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Resolve preparation context from a fault code, malfunction, or preparation id."""
    args = _validate_input(fault_code, malfunction, preparation_id, limit)
    logger.info(
        "Running preparation context tool",
        extra={
            "has_fault_code": bool(args.fault_code),
            "has_malfunction": bool(args.malfunction),
            "has_preparation_id": bool(args.preparation_id),
            "limit": args.limit,
        },
    )
    try:
        query, params = build_preparation_query(
            schema_profile=schema_profile,
            fault_code=args.fault_code,
            malfunction=args.malfunction,
            preparation_id=args.preparation_id,
            limit=args.limit,
        )
        rows = client.query(query, params)
        return [_normalize_row(row) for row in rows]
    except ToolInputError:
        raise
    except Exception as exc:
        raise ToolExecutionError("Failed to retrieve preparation context.") from exc


def get_preparation_context_from_code(
    client: Neo4jClient,
    schema_profile: SchemaProfile,
    fault_code: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Compatibility wrapper for fault-code lookups."""
    return get_preparation_context(
        client=client,
        schema_profile=schema_profile,
        fault_code=fault_code,
        limit=limit,
    )


def get_preparation_context_from_malfunction(
    client: Neo4jClient,
    schema_profile: SchemaProfile,
    malfunction: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Compatibility wrapper for malfunction text lookups."""
    return get_preparation_context(
        client=client,
        schema_profile=schema_profile,
        malfunction=malfunction,
        limit=limit,
    )


def get_preparation_context_from_preparation_id(
    client: Neo4jClient,
    schema_profile: SchemaProfile,
    preparation_id: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Compatibility wrapper for preparation-id lookups."""
    return get_preparation_context(
        client=client,
        schema_profile=schema_profile,
        preparation_id=preparation_id,
        limit=limit,
    )


def build_langchain_tools(
    client: Neo4jClient,
    schema_profile: SchemaProfile,
    default_limit: int = 5,
) -> list[StructuredTool]:
    """Build LangChain tool wrappers over reusable Python tools."""

    def _tool_impl(
        fault_code: str | None = None,
        malfunction: str | None = None,
        preparation_id: str | None = None,
        limit: int = 5,
    ) -> str:
        effective_limit = default_limit if limit == 5 else limit
        rows = get_preparation_context(
            client=client,
            schema_profile=schema_profile,
            fault_code=fault_code,
            malfunction=malfunction,
            preparation_id=preparation_id,
            limit=effective_limit,
        )
        return json.dumps(rows)

    return [
        StructuredTool.from_function(
            func=_tool_impl,
            name="get_preparation_context",
            description=TOOL_DESCRIPTION,
            args_schema=PreparationContextInput,
        )
    ]
