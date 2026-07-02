"""Build resolved context strings from graph tool results."""

from typing import Any


def format_tool_result_for_answer(row: dict[str, Any]) -> str:
    """Format one graph result row for answer generation."""
    metadata = [
        f"chunk_id={row.get('chunk_id')}",
        f"document_id={row.get('document_id')}",
        f"page_no={row.get('page_no')}",
        f"fault_code={row.get('fault_code')}",
        f"malfunction={row.get('malfunction')}",
        f"reference={row.get('reference')}",
        f"figure={row.get('figure')}",
        f"preparation={row.get('preparation')}",
    ]
    text = row.get("chunk_text") or ""
    return f"[{'; '.join(item for item in metadata if not item.endswith('=None'))}]\n{text}".strip()


def build_resolved_context(tool_results: list[dict[str, Any]]) -> str:
    """Combine unique chunk texts and metadata from tool results."""
    seen: set[str] = set()
    formatted: list[str] = []
    for row in tool_results:
        chunk_id = str(row.get("chunk_id") or "")
        chunk_text = str(row.get("chunk_text") or "")
        key = chunk_id or chunk_text
        if not key or key in seen:
            continue
        seen.add(key)
        formatted.append(format_tool_result_for_answer(row))
    return "\n\n---\n\n".join(formatted)
