"""Settings loader for environment, YAML config, and schema profiles."""

from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.exceptions import ConfigurationError
from graph.schema import SchemaProfile, load_schema_profile


class EnvSettings(BaseSettings):
    """Environment variables used by GraphRAG."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_username: str = Field(default="neo4j", alias="NEO4J_USERNAME")
    neo4j_password: str = Field(default="your_password", alias="NEO4J_PASSWORD")
    neo4j_database: str | None = Field(default=None, alias="NEO4J_DATABASE")
    llm_base_url: str = Field(default="http://localhost:8080/v1", alias="LLM_BASE_URL")
    llm_api_key: str = Field(default="not-needed", alias="LLM_API_KEY")
    llm_model: str = Field(default="local-model", alias="LLM_MODEL")
    llm_temperature: float | None = Field(default=None, alias="LLM_TEMPERATURE")
    log_level: str | None = Field(default=None, alias="LOG_LEVEL")


class Settings(BaseSettings):
    """Resolved application settings."""

    neo4j_uri: str
    neo4j_username: str
    neo4j_password: str
    neo4j_database: str
    llm_base_url: str
    llm_api_key: str
    llm_model: str
    llm_temperature: float
    schema_profile_path: str
    max_results: int
    log_level: str
    max_tool_iterations: int
    require_tool_for_cross_reference: bool
    schema_profile: SchemaProfile


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        return yaml.safe_load(path.read_text()) or {}
    except OSError as exc:
        msg = f"Unable to read config file: {path}"
        raise ConfigurationError(msg) from exc


def load_settings(config_path: str | None = None) -> Settings:
    """Load settings from `.env`, YAML config, and schema profile YAML."""
    load_dotenv()

    root = Path.cwd()
    path = Path(config_path or "configs/default.yaml")
    config = _read_yaml(path)
    env = EnvSettings()

    schema_profile_path = str(config.get("schema_profile_path", "configs/schema_profiles/technical_manual.yaml"))
    profile_path = Path(schema_profile_path)
    if not profile_path.is_absolute():
        profile_path = root / profile_path

    neo4j_config = config.get("neo4j", {})
    llm_config = config.get("llm", {})
    retrieval_config = config.get("retrieval", {})
    logging_config = config.get("logging", {})
    agent_config = config.get("agent", {})

    database = env.neo4j_database or neo4j_config.get("database") or "neo4j"
    temperature = env.llm_temperature
    if temperature is None:
        temperature = float(llm_config.get("temperature", 0))

    log_level = env.log_level or logging_config.get("level") or "INFO"

    return Settings(
        neo4j_uri=env.neo4j_uri,
        neo4j_username=env.neo4j_username,
        neo4j_password=env.neo4j_password,
        neo4j_database=database,
        llm_base_url=env.llm_base_url,
        llm_api_key=env.llm_api_key,
        llm_model=env.llm_model,
        llm_temperature=temperature,
        schema_profile_path=schema_profile_path,
        max_results=int(retrieval_config.get("max_results", 5)),
        log_level=log_level,
        max_tool_iterations=int(agent_config.get("max_tool_iterations", 4)),
        require_tool_for_cross_reference=bool(
            agent_config.get("require_tool_for_cross_reference", True)
        ),
        schema_profile=load_schema_profile(profile_path),
    )
