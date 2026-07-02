"""Neo4j client wrapper."""

from typing import Any

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError, ServiceUnavailable

from core.config import Settings
from core.exceptions import Neo4jConnectionError
from core.logging import get_logger
from graph.query_validator import validate_readonly_cypher

logger = get_logger(__name__)


class Neo4jClient:
    """Read-only Neo4j client with centralized query validation."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password),
        )

    def query(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Execute a validated read-only Cypher query and return dictionaries."""
        validate_readonly_cypher(cypher)
        logger.debug("Executing read-only Neo4j query", extra={"database": self.settings.neo4j_database})
        try:
            with self._driver.session(database=self.settings.neo4j_database) as session:
                result = session.run(cypher, params or {})
                return [dict(record) for record in result]
        except Neo4jError as exc:
            raise Neo4jConnectionError("Neo4j query failed.") from exc

    def close(self) -> None:
        """Close the Neo4j driver."""
        self._driver.close()

    def verify_connection(self) -> bool:
        """Return True when Neo4j connectivity can be verified."""
        try:
            self._driver.verify_connectivity()
        except ServiceUnavailable as exc:
            raise Neo4jConnectionError("Neo4j is unavailable.") from exc
        return True
