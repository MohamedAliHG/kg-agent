"""Pydantic schemas for graph tools."""

from pydantic import BaseModel, Field, model_validator


class PreparationContextInput(BaseModel):
    """Input schema for resolving preparation context."""

    fault_code: str | None = None
    malfunction: str | None = None
    preparation_id: str | None = None
    limit: int = Field(default=5, ge=1, le=100)

    @model_validator(mode="after")
    def require_search_parameter(self) -> "PreparationContextInput":
        """Require at least one lookup field."""
        if not (self.fault_code or self.malfunction or self.preparation_id):
            raise ValueError("One of fault_code, malfunction, or preparation_id is required.")
        return self


class PreparationContextResult(BaseModel):
    """Normalized preparation context row returned by tools."""

    malfunction: str | None = None
    fault_code: str | None = None
    reference: str | None = None
    figure: str | None = None
    preparation: str | None = None
    chunk_id: str
    chunk_text: str
    page_no: int | str | None = None
    document_id: str | None = None


class Text2CypherInput(BaseModel):
    """Input schema for experimental Text2Cypher graph queries."""

    question: str = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=100)


class Text2CypherResult(BaseModel):
    """Output schema for experimental Text2Cypher graph queries."""

    cypher: str
    rows: list[dict]
    row_count: int
