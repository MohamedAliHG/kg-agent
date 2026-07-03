# KG_AGENT

KG_AGENT is a standalone, read-only Python/LangGraph agent for experimenting with GraphRAG over an
existing Neo4j knowledge graph. The repo is intentionally small and configurable so you can compare
different retrieval strategies: curated/predefined Cypher tools, LLM-generated Text2Cypher, hybrid
fallbacks, and direct model responses with no graph tools.

The project does not build or repair the knowledge graph. It focuses on the agent layer: tool
routing, schema-profile-driven graph access, query validation, retrieval debugging, and optional
observability.

## Architecture

- `src/core`: settings, logging, common exceptions, and shared types.
- `src/graph`: Neo4j access, schema profiles, query validation, and template rendering.
- `src/tools`: reusable Python tools plus LangChain tool wrappers.
- `src/agent`: LangGraph `StateGraph` using `MessagesState`, `ToolNode`, `tools_condition`, and `llm.bind_tools(...)`.
- `src/retrieval`: context formatting for final answers.
- `configs/schema_profiles`: graph-shape profiles, Text2Cypher rules, grounded values, and examples.

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

The default public profile is generic and expects a document/chunk/entity graph shape defined in
`configs/schema_profiles/generic.yaml`.

Add new graph shapes as separate schema profiles rather than hardcoding labels, relationship names,
entity types, or few-shot examples in Python.

Schema profiles control:

- Neo4j labels and property names.
- Chunk/document/entity relationships.
- Domain entity types and relationship directions.
- Label aliases.
- Text2Cypher rules, grounded value hints, and few-shot examples.

## Local LLM

The default config targets a local OpenAI-compatible server:

```env
LLM_BASE_URL=http://localhost:8080/v1
LLM_API_KEY=not-needed
LLM_MODEL=local-model
```

## Run The Agent

```bash
python scripts/run_agent.py --question "Which chunks mention ITEM-001?"
python scripts/run_agent.py --question "Which chunks mention ITEM-001?" --debug
```

`--debug` prints tool calls, returned chunk IDs, generated Cypher for Text2Cypher runs, and raw tool
results.

## Experiment Variables

Most experiments happen in `configs/default.yaml`, `.env`, and the active schema profile.

```yaml
schema_profile_path: configs/schema_profiles/generic.yaml

retrieval:
  max_results: 5

llm:
  temperature: 0

agent:
  tool_mode: text2cypher
  max_tool_iterations: 4
  require_tool_for_cross_reference: true
```

Useful variables to play with:

- `schema_profile_path`: switch graph schemas and Text2Cypher examples.
- `agent.tool_mode`: compare predefined tools, Text2Cypher, hybrid fallback, or no tools.
- `retrieval.max_results`: change how much graph context the tools return.
- `agent.max_tool_iterations`: control how many tool-calling loops LangGraph can run.
- `llm.temperature`: test deterministic vs more exploratory Cypher generation.
- `.env` model settings: swap local models, OpenAI-compatible endpoints, Groq-compatible endpoints,
  or other hosted OpenAI-compatible APIs.

## Tool Modes

The agent can run in four modes:

```yaml
agent:
  tool_mode: text2cypher
```

Supported modes:

- `predefined`: only curated tools such as `get_preparation_context`.
- `text2cypher`: only the experimental LLM-generated Cypher tool.
- `hybrid`: curated tools plus experimental Text2Cypher fallback.
- `none`: no graph tools; direct model answers only.

### Predefined Cypher

Predefined tools are the safest path for stable workflows. The LLM only chooses a tool and provides
typed arguments. Python renders controlled Cypher templates from schema-profile identifiers, passes
user values as parameters, and validates the final query as read-only before execution.

### Text2Cypher

`text2cypher_query` is intended for schema-development and exploratory graph experiments. The tool
builds a schema-aware prompt from the active schema profile, asks the configured model to generate
Cypher, normalizes the query, enforces a result limit, validates it as read-only, then executes it.

Domain-specific behavior should live in the active schema profile YAML:

```yaml
text2cypher:
  description: ...
  rules:
    - ...
  grounded_values:
    identifiers:
      pattern: "..."
      properties: [code, name, id]
      examples: [...]
  examples:
    - question: ...
      notes: ...
      cypher: |
        MATCH ...
```

### Hybrid

Hybrid mode exposes both curated tools and Text2Cypher. Use it when you want the agent to try stable
paths first, then fall back to generated read-only Cypher for graph questions that the predefined
tools do not cover.

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

Configuration is split between `.env`, `configs/default.yaml`, and a schema profile YAML file.
Predefined Cypher is generated only from whitelisted templates and validated schema identifiers.
Text2Cypher output is normalized and checked by the read-only query validator before execution.
