"""Read-only Cypher validation."""

import re

from core.exceptions import UnsafeCypherError

_BLOCKED_PATTERNS = [
    r"\bCREATE\b",
    r"\bMERGE\b",
    r"\bDELETE\b",
    r"\bDETACH\b",
    r"\bSET\b",
    r"\bREMOVE\b",
    r"\bDROP\b",
    r"\bLOAD\s+CSV\b",
    r"\bCALL\s+DBMS\b",
    r"\bCALL\s+APOC\b",
    r"\bCALL\s+DB\.",
]


def _strip_string_literals(query: str) -> str:
    return re.sub(r"""(['"])(?:\\.|(?!\1).)*\1""", " ", query)


def validate_readonly_cypher(query: str) -> None:
    """Raise if a Cypher query contains blocked write or dangerous operations."""
    normalized = _strip_string_literals(query).upper()
    for pattern in _BLOCKED_PATTERNS:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            raise UnsafeCypherError(f"Blocked unsafe Cypher operation matching {pattern!r}.")
