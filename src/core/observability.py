"""Optional observability integrations."""

from typing import TYPE_CHECKING, Any

from core.exceptions import ConfigurationError
from core.logging import get_logger

if TYPE_CHECKING:
    from core.config import Settings

logger = get_logger(__name__)


def build_langfuse_run_config(settings: "Settings") -> dict[str, Any]:
    """Build LangGraph runnable config for optional Langfuse tracing."""
    if not settings.langfuse_enabled:
        return {}

    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        msg = (
            "Langfuse is enabled but LANGFUSE_PUBLIC_KEY or LANGFUSE_SECRET_KEY is missing."
        )
        raise ConfigurationError(msg)

    try:
        from langfuse.langchain import CallbackHandler
    except ImportError as exc:
        msg = "Langfuse is enabled but the `langfuse` package is not installed."
        raise ConfigurationError(msg) from exc

    logger.info(
        "Langfuse tracing enabled",
        extra={"langfuse_base_url": settings.langfuse_base_url},
    )
    return {
        "callbacks": [CallbackHandler()],
        "run_name": "graphrag-agent",
        "tags": ["graphrag", "local"],
        "metadata": {
            "langfuse_session_id": settings.langfuse_session_id,
            "langfuse_tags": ["graphrag", "local"],
        },
    }


def flush_langfuse(settings: "Settings") -> None:
    """Flush Langfuse events for short-lived CLI runs."""
    if not settings.langfuse_enabled:
        return

    try:
        from langfuse import get_client
    except ImportError:
        return

    client = get_client()
    flush = getattr(client, "flush", None)
    if callable(flush):
        flush()
