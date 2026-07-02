"""Tool registry for current and future graph tools."""

from langchain_core.tools import BaseTool

from graph.neo4j_client import Neo4jClient
from graph.schema import SchemaProfile
from tools.preparation_tools import build_langchain_tools


def build_tool_registry(
    client: Neo4jClient,
    schema_profile: SchemaProfile,
    default_limit: int = 5,
) -> list[BaseTool]:
    """Return all LangChain tools exposed to the agent."""
    return [*build_langchain_tools(client, schema_profile, default_limit=default_limit)]
