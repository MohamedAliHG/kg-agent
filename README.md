# GraphRAG

GraphRAG is a standalone, read-only Python agent for answering technical-document questions from an existing Neo4j knowledge graph. It uses an OpenAI-compatible chat model with tool calling, predefined graph tools, and controlled dynamic Cypher templates.

## Architecture

- `src/core`: settings, logging, common exceptions, and shared types.
- `src/graph`: Neo4j access, schema profiles, query validation, and template rendering.
- `src/tools`: reusable Python tools plus LangChain tool wrappers.
- `src/agent`: LangGraph `StateGraph` using `MessagesState`, `ToolNode`, `tools_condition`, and `llm.bind_tools(...)`.
- `src/retrieval`: context formatting for final answers.

The project does not build or repair the knowledge graph. It only reads from Neo4j.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
make install
```

## Environment

```bash
cp .env.example .env
```

Set your Neo4j URI, username, password, database, and OpenAI-compatible model settings in `.env`.

## Neo4j Requirements

The default profile expects document, chunk, and entity nodes connected by the relationships defined in `configs/schema_profiles/technical_manual.yaml`. Add new graph shapes as separate schema profiles rather than hardcoding labels or relationship names in code.

## Local LLM

The default config targets a local OpenAI-compatible server:

```env
LLM_BASE_URL=http://localhost:8080/v1
LLM_API_KEY=not-needed
LLM_MODEL=local-model
```

## Run The Agent

```bash
python scripts/run_agent.py --question "What actions should I perform if fault code 3310B01 occurs?"
```

## Optional Local Langfuse Tracing

Langfuse tracing is disabled by default. To use a local Langfuse instance, start Langfuse on
`http://localhost:3000`, create a project, copy its API keys, then set:

```env
LANGFUSE_ENABLED=true
LANGFUSE_BASE_URL=http://localhost:3000
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_SESSION_ID=local-dev
```

When enabled, the agent passes a Langfuse `CallbackHandler` into the LangGraph run config so LLM
calls, tool calls, and graph execution are visible in the local Langfuse UI.

## Inspect Neo4j

```bash
make check-neo4j
python scripts/inspect_schema.py
```

## Tests

```bash
pytest
```

## Reproducibility

Configuration is split between `.env`, `configs/default.yaml`, and a schema profile YAML file. Cypher is generated only from whitelisted templates and validated schema identifiers. User values are always passed as query parameters.

