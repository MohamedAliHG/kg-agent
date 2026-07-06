from __future__ import annotations

import pytest
from pydantic import ValidationError

from tools.schemas import PreparationContextInput


def test_tool_schema_validates_at_least_one_search_parameter() -> None:
    with pytest.raises(ValidationError):
        PreparationContextInput()


def test_tool_schema_accepts_fault_code() -> None:
    args = PreparationContextInput(fault_code="3310B01")

    assert args.limit == 5
