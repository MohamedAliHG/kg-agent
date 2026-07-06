from __future__ import annotations

from retrieval.context_builder import build_resolved_context, format_tool_result_for_answer


def test_context_builder_includes_metadata_and_chunk_text() -> None:
    row = {
        "chunk_id": "c1",
        "document_id": "d1",
        "page_no": 12,
        "fault_code": "3310B01",
        "chunk_text": "Open the access panel and inspect the connector.",
    }

    formatted = format_tool_result_for_answer(row)

    assert "chunk_id=c1" in formatted
    assert "3310B01" in formatted
    assert "Open the access panel" in formatted


def test_context_builder_deduplicates_chunks() -> None:
    rows = [
        {"chunk_id": "c1", "chunk_text": "Do the actual preparation steps."},
        {"chunk_id": "c1", "chunk_text": "Do the actual preparation steps."},
    ]

    context = build_resolved_context(rows)

    assert context.count("Do the actual preparation steps.") == 1
