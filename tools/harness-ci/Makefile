.PHONY: ci fix
ci:
	uv run --locked ruff check .
	uv run --locked ruff format --check .
	uv run --locked mypy src
	uv run --locked complexipy src
	uv run --locked pytest
	bash -n src/harness_ci/assets/install.sh
fix:
	uv run --locked ruff check --fix .
	uv run --locked ruff format .
