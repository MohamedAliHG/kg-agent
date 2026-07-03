"""Tool registry for current and future graph tools."""

from typing import TYPE_CHECKING

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool

from core.exceptions import ConfigurationError
from graph.neo4j_client import Neo4jClient
from tools.preparation_tools import build_langchain_tools
from tools.text2cypher_tools import build_text2cypher_tools

if TYPE_CHECKING:
    from core.config import Settings


def build_tool_registry(
    client: Neo4jClient,
    settings: "Settings",
    llm: BaseChatModel,
) -> list[BaseTool]:
    """Return all LangChain tools exposed to the agent."""
    mode = settings.tool_mode.lower()

    if mode == "none":
        return []
    if mode == "predefined":
        return [
            *build_langchain_tools(
                client,
                settings.schema_profile,
                default_limit=settings.max_results,
            )
        ]
    if mode == "text2cypher":
        return [
            *build_text2cypher_tools(
                client,
                settings.schema_profile,
                llm,
                default_limit=settings.max_results,
            )
        ]
    if mode == "hybrid":
        return [
            *build_langchain_tools(
                client,
                settings.schema_profile,
                default_limit=settings.max_results,
            ),
            *build_text2cypher_tools(
                client,
                settings.schema_profile,
                llm,
                default_limit=settings.max_results,
            ),
        ]

    msg = "agent.tool_mode must be one of: predefined, text2cypher, hybrid, none"
    raise ConfigurationError(msg)
