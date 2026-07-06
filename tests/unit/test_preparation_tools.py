from __future__ import annotations

from tools.preparation_tools import (
    get_preparation_context,
    get_preparation_context_from_code,
    get_preparation_context_from_malfunction,
    get_preparation_context_from_preparation_id,
)


class MockClient:
    def __init__(self) -> None:
        self.calls = []

    def query(self, cypher, params):
        self.calls.append((cypher, params))
        return [
            {
                "malfunction": "Failure",
                "fault_code": params.get("fault_code"),
                "reference": "Perform figure 2-1, Preparation A",
                "figure": "2-1",
                "preparation": params.get("preparation_id") or "A",
                "chunk_id": "chunk-1",
                "chunk_text": "Actual preparation procedure.",
                "page_no": 3,
                "document_id": "doc-1",
            }
        ]


def test_get_preparation_context_calls_neo4j_with_correct_params(technical_profile) -> None:
    client = MockClient()

    rows = get_preparation_context(client, technical_profile, fault_code="3310B01", limit=2)

    assert client.calls[0][1] == {"limit": 2, "fault_code": "3310B01"}
    assert rows[0]["chunk_text"] == "Actual preparation procedure."


def test_get_preparation_context_from_code_wrapper(technical_profile) -> None:
    client = MockClient()

    get_preparation_context_from_code(client, technical_profile, "3310B01")

    assert client.calls[0][1]["fault_code"] == "3310B01"


def test_get_preparation_context_from_malfunction_wrapper(technical_profile) -> None:
    client = MockClient()

    get_preparation_context_from_malfunction(client, technical_profile, "failure")

    assert client.calls[0][1]["malfunction"] == "failure"


def test_get_preparation_context_from_preparation_id_wrapper(technical_profile) -> None:
    client = MockClient()

    get_preparation_context_from_preparation_id(client, technical_profile, "Figure:2-1:Preparation:A")

    assert client.calls[0][1]["preparation_id"] == "Figure:2-1:Preparation:A"
