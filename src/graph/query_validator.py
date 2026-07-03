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
    r"\bCALL\b",
    r"\bCALL\s+DBMS\b",
    r"\bCALL\s+APOC\b",
    r"\bCALL\s+DB\.",
]

_READONLY_START_PATTERNS = (
    "MATCH ",
    "OPTIONAL MATCH ",
    "WITH ",
    "UNWIND ",
)


def _strip_string_literals(query: str) -> str:
    return re.sub(r"""(['"])(?:\\.|(?!\1).)*\1""", " ", query)


def validate_readonly_cypher(query: str) -> None:
    """Raise if a Cypher query contains blocked write or dangerous operations."""
    stripped = query.strip()
    if not stripped:
        raise UnsafeCypherError("Cypher query is empty.")

    without_strings = _strip_string_literals(stripped)
    if "//" in without_strings or "/*" in without_strings or "*/" in without_strings:
        raise UnsafeCypherError("Cypher comments are not allowed.")

    body = stripped[:-1] if stripped.endswith(";") else stripped
    body_without_strings = _strip_string_literals(body)
    if ";" in body_without_strings:
        raise UnsafeCypherError("Multiple Cypher statements are not allowed.")

    normalized = body_without_strings.upper().lstrip()
    if not normalized.startswith(_READONLY_START_PATTERNS):
        raise UnsafeCypherError("Cypher query must start with a read-only clause.")

    for pattern in _BLOCKED_PATTERNS:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            raise UnsafeCypherError(f"Blocked unsafe Cypher operation matching {pattern!r}.")
