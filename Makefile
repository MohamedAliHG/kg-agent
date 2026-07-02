.PHONY: install test lint format check-neo4j run-example

install:
	python -m pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

check-neo4j:
	python scripts/check_neo4j_connection.py

run-example:
	python scripts/run_agent.py --question "What actions should I perform if fault code 3310B01 occurs?"
