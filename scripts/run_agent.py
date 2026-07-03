#!/usr/bin/env python
"""Run the GraphRAG agent from the command line."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent.runner import run_graphrag_agent


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the GraphRAG agent.")
    parser.add_argument("--question", required=True)
    parser.add_argument("--chunk-text")
    parser.add_argument("--config")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    result = run_graphrag_agent(
        question=args.question,
        chunk_text=args.chunk_text,
        config_path=args.config,
        limit=args.limit,
    )

    tool_messages = [message for message in result["messages"] if message["type"] == "tool"]
    chunk_ids = [row.get("chunk_id") for row in result["tool_results"] if row.get("chunk_id")]

    print("Tool calls used:")
    ai_tool_calls = [
        tool_call
        for message in result["messages"]
        for tool_call in (message.get("tool_calls") or [])
        if message["type"] == "ai"
    ]
    if args.debug and ai_tool_calls:
        for tool_call in ai_tool_calls:
            print(f"- {tool_call}")
    elif args.debug:
        print("- no ai tool_calls found")

    if tool_messages:
        for message in tool_messages:
            print(f"- {message.get('name') or 'tool'}")
    else:
        print("- none")

    print("\nReturned chunk IDs:")
    if chunk_ids:
        for chunk_id in chunk_ids:
            print(f"- {chunk_id}")
    else:
        print("- none")

    if args.debug:
        text2cypher_results = [
            row
            for row in result["tool_results"]
            if isinstance(row, dict) and row.get("cypher") is not None
        ]
        if text2cypher_results:
            print("\nGenerated Cypher:")
            for row in text2cypher_results:
                print(row["cypher"])
                print(f"row_count={row.get('row_count', 0)}")

        print("\nRaw tool results:")
        print(json.dumps(result["tool_results"], indent=2))

    print("\nFinal answer:")
    print(result.get("answer") or "No answer returned.")


if __name__ == "__main__":
    main()
