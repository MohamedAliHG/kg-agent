"""Custom exceptions for GraphRAG."""


class GraphRAGError(Exception):
    """Base exception for GraphRAG errors."""


class ConfigurationError(GraphRAGError):
    """Raised when configuration cannot be loaded or validated."""


class Neo4jConnectionError(GraphRAGError):
    """Raised when Neo4j cannot be reached or queried."""


class UnsafeCypherError(GraphRAGError):
    """Raised when a Cypher query violates read-only safety rules."""


class ToolExecutionError(GraphRAGError):
    """Raised when a graph tool cannot complete successfully."""


class NoContextFoundError(GraphRAGError):
    """Raised when no relevant graph context is found."""


class ToolInputError(GraphRAGError):
    """Raised when tool input is missing or invalid."""


class LLMConfigurationError(GraphRAGError):
    """Raised when the LLM cannot be configured."""
