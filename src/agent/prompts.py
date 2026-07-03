"""Prompts for the GraphRAG tool-calling agent."""

from langchain_core.messages import HumanMessage, SystemMessage

SYSTEM_PROMPT = """You are a GraphRAG assistant.

Use the available graph retrieval tools when the question requires information from the knowledge graph
or when provided context is insufficient.

Do not ask the user to write graph queries. Do not propose or execute write operations.

Base answers on retrieved graph context and provided chunk context. Do not invent facts, actions,
relationships, or procedural steps that are not supported by retrieved context.

If retrieval returns no relevant context, say that the requested graph context was not found.

Ask a clarifying question only when the user request is ambiguous and the missing detail is required
to retrieve the answer."""


def build_initial_messages(question: str, chunk_text: str | None = None) -> list[SystemMessage | HumanMessage]:
    """Build initial chat messages for an agent run."""
    user_content = question
    if chunk_text:
        user_content = f"{question}\n\nProvided chunk context:\n{chunk_text}"
    return [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_content)]
