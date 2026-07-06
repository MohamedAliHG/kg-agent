from __future__ import annotations

import pytest

from core.exceptions import ConfigurationError
from graph.template_engine import build_preparation_query, validate_schema_identifier


@pytest.mark.parametrize("identifier", ["Bad-Label", "1Bad", "Thing`) MATCH (n)"])
def test_schema_identifier_validator_rejects_unsafe(identifier: str) -> None:
    with pytest.raises(ConfigurationError):
        validate_schema_identifier(identifier)


def test_query_builder_reads_schema_profile_identifiers(custom_profile) -> None:
    query, params = build_preparation_query(custom_profile, fault_code="ABC", limit=3)

    assert "Thing" in query
    assert "TextBlock" in query
    assert "MENTIONS" in query
    assert "HAS_SIGNAL" in query
    assert "POINTS_TO_ILLUSTRATION" in query
    assert "body AS chunk_text" in query
    assert params == {"limit": 3, "fault_code": "ABC"}


def test_query_builder_uses_aliases_and_properties_from_profile(custom_profile) -> None:
    query, _ = build_preparation_query(custom_profile, fault_code="ABC")

    assert "AltSignal" in query
    assert "code.code" not in query
    assert "code.identifier" in query
    assert "m.display" in query


def test_dynamic_query_builder_chooses_preparation_id_over_fault_code(technical_profile) -> None:
    query, params = build_preparation_query(
        technical_profile,
        preparation_id="Figure:2-1:Preparation:A",
        fault_code="3310B01",
    )

    assert "$preparation_id" in query
    assert "$fault_code" not in query
    assert params == {"limit": 5, "preparation_id": "Figure:2-1:Preparation:A"}


def test_dynamic_query_builder_chooses_fault_code_over_malfunction(technical_profile) -> None:
    query, params = build_preparation_query(
        technical_profile,
        fault_code="3310B01",
        malfunction="some malfunction",
    )

    assert "$fault_code" in query
    assert "$malfunction" not in query
    assert params == {"limit": 5, "fault_code": "3310B01"}


def test_dynamic_query_builder_parameterizes_values(technical_profile) -> None:
    malicious = "3310B01' MATCH (n) DELETE n //"
    query, params = build_preparation_query(technical_profile, fault_code=malicious)

    assert malicious not in query
    assert params["fault_code"] == malicious
