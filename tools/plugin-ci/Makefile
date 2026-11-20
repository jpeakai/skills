.PHONY: ci fix
ci:
	uv run --locked ruff check .
	uv run --locked ruff format --check .
	uv run --locked mypy src
	uv run --locked complexipy src
	uv run --locked pytest
fix:
	uv run --locked ruff check --fix .
	uv run --locked ruff format .
